# ✅ Getting Tick Value & Tick Size — `tick_value_with_size`

> **Request:** retrieve **tick value**, **tick size**, and **contract size** for one or more symbols as a compact payload (`TickValueWithSizeData`).
> Use this for precise PnL, risk, and margin pre‑checks.

**Source files (SDK):**

* `MetaRpcMT4/mt4_account.py` — method `tick_value_with_size(...)`
* `MetaRpcMT4/mt4_term_api_account_helper_pb2.py` — `TickValueWithSize*`

### RPC

* **Service:** `mt4_term_api.AccountHelper`
* **Method:** `TickValueWithSize(TickValueWithSizeRequest) → TickValueWithSizeReply`
* **Low‑level client:** `AccountHelperStub.TickValueWithSize(request, metadata, timeout)`
* **SDK wrapper:** `MT4Account.tick_value_with_size(symbol_names: list[str], deadline=None, cancellation_event=None) → TickValueWithSizeData`

**Request message:** `TickValueWithSizeRequest { symbol_names: string[] }`
**Reply message:** `TickValueWithSizeReply { data: TickValueWithSizeData }`

---

### 🔗 Code Example

```python
# Compute PnL per one tick for several symbols
resp = await acct.tick_value_with_size(["EURUSD", "XAUUSD", "US30.cash"])
for row in resp.items:  # list[TickValueWithSizeInfo]
    print(
        f"{row.symbolName}: tick={row.TradeTickSize:g} value={row.TradeTickValue:.2f} "
        f"contract={row.ContractSize:g} base={row.CurrencyBase} profit={row.CurrencyProfit}"
    )
```

---

### Method Signature

```python
async def tick_value_with_size(
    self,
    symbol_names: list[str],
    deadline: datetime | None = None,
    cancellation_event: asyncio.Event | None = None,
) -> account_helper_pb2.TickValueWithSizeData
```

---

## 💬 Just the essentials

* **What it is.** Server‑side calculation helper that returns tick metrics for each requested symbol.
* **Why.** Required to compute expected PnL per tick and to normalize between instruments with different contract sizes.
* **Batching.** Send multiple symbols in one request; reply preserves ordering via an index field.

---

## 🔽 Input

| Parameter            | Type           | Description       |                                       |
| -------------------- | -------------- | ----------------- | ------------------------------------- |
| `symbol_names`       | `list[str]`    | Symbols to query. |                                       |
| `deadline`           | `datetime      | None`             | Absolute per‑call deadline.           |
| `cancellation_event` | `asyncio.Event | None`             | Cooperative cancel for retry wrapper. |

---

## ⬆️ Output

### Payload: `TickValueWithSizeData`

Contains `items: list[TickValueWithSizeInfo]`.

| Field            | Proto Type | Description                                            |
| ---------------- | ---------- | ------------------------------------------------------ |
| `index`          | `int32`    | Position in the reply list (maps to request order).    |
| `symbolName`     | `string`   | Symbol name.                                           |
| `TradeTickValue` | `double`   | Tick value in **deposit currency** for 1 contract lot. |
| `TradeTickSize`  | `double`   | Minimal price increment (tick size).                   |
| `ContractSize`   | `double`   | Contract size (e.g., 100000 for FX majors).            |
| `CurrencyBase`   | `string`   | Base currency code for the symbol.                     |
| `CurrencyProfit` | `string`   | Profit currency code used for PnL.                     |
| `CurrencyMargin` | `string`   | Margin currency code.                                  |

> Field names reflect `mt4_term_api_account_helper_pb2.py` (`TickValueWithSize*`). Exact list may include additional metadata fields depending on integration.

---

## 🧱 Related enums (from pb)

This RPC **does not define method‑specific enums**.

> For pricing/margin semantics, combine with enums exposed in symbol parameters (`SP_ENUM_*` in `SymbolParamsMany`).

---

### 🎯 Purpose

Use this method to:

* Convert price deltas → money deltas (per tick) consistently across instruments.
* Pre‑check whether a target PnL (in currency) corresponds to a feasible price move.
* Build UI tables showing tick metrics next to symbol constraints.

### 🧩 Notes & Tips

* Wrapper uses `execute_with_reconnect(...)` for transient gRPC retries.
* Result values are in **deposit currency**; if you display in another currency, convert explicitly.
* Pair with `symbol_params_many(...)` to enforce volume/step/SL‑TP constraints, and with `quote(...)` to compute value per **point** vs **tick**.

**See also:**
`symbol_params_many(...)` — symbol constraints and trade/margin enums.
`quote(...)` — current price snapshot.
`opened_orders(...)` — verify PnL math against live positions.

---

## Usage Examples

### 1) Compute monetary value of 1 pip (FX)

```python
from decimal import Decimal

rows = (await acct.tick_value_with_size(["EURUSD"]))
r = rows.items[0]
# For many brokers: pip = 10 * tick when price has 5 digits
pip_value = Decimal(r.TradeTickValue) * 10
print(f"EURUSD pip value (1 lot): {pip_value:.2f}")
```

### 2) PnL for N ticks

```python
r = (await acct.tick_value_with_size(["XAUUSD"]).items[0])
value = r.TradeTickValue * 12  # money per 12 ticks, 1 lot
```

### 3) Show a compact table

```python
symbols = ["EURUSD", "GBPUSD", "XAUUSD"]
data = await acct.tick_value_with_size(symbols)
for row in data.items:
    print(f"{row.symbolName:8} tick={row.TradeTickSize:g} value={row.TradeTickValue:.2f}")
```
