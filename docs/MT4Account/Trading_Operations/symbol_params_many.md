# ✅ Getting Symbol Parameters — `symbol_params_many`

> **Request:** retrieve trading parameters for **one symbol or all symbols** as a structured payload (`SymbolParamsManyData`).
> Ideal for pre‑trade validation, UI forms, and margin/risk calculations.

**Source files (SDK):**

* `MetaRpcMT4/mt4_account.py` — method `symbol_params_many(...)`
* `MetaRpcMT4/mt4_term_api_account_helper_pb2.py` — `SymbolParamsMany*` (+ related enums)

### RPC

* **Service:** `mt4_term_api.AccountHelper`
* **Method:** `SymbolParamsMany(SymbolParamsManyRequest) → SymbolParamsManyReply`
* **Low‑level client:** `AccountHelperStub.SymbolParamsMany(request, metadata, timeout)`
* **SDK wrapper:** `MT4Account.symbol_params_many(symbol_name: str | None = None, deadline=None, cancellation_event=None) → SymbolParamsManyData`

**Request message:** `SymbolParamsManyRequest { symbol_name? }`
**Reply message:** `SymbolParamsManyReply { data: SymbolParamsManyData }`

---

### 🔗 Code Example

```python
# Fetch params for a single symbol
info = await acct.symbol_params_many(symbol_name="EURUSD")
for p in info.params_info:  # list[SymbolParamsManyInfo]
    print(p.Symbol, p.Digits, p.Point, p.TradeMode)

# Fetch params for all symbols (may be large)
all_info = await acct.symbol_params_many()
print(f"Symbols returned: {len(all_info.params_info)}")
```

---

### Method Signature

```python
async def symbol_params_many(
    self,
    symbol_name: str | None = None,
    deadline: datetime | None = None,
    cancellation_event: asyncio.Event | None = None,
) -> account_helper_pb2.SymbolParamsManyData
```

---

## 💬 Just the essentials

* **What it is.** A server‑side snapshot of symbol trading parameters (tick size/value, digits, execution mode, volume bounds, etc.).
* **Why.** Validate orders (min/max/step), display constraints in UI, compute margin and risk correctly for each symbol.
* **Scope.** If `symbol_name` is `None`, returns **all** available symbols; otherwise, only the requested symbol.

---

## 🔽 Input

| Parameter            | Type           | Description |                                                    |
| -------------------- | -------------- | ----------- | -------------------------------------------------- |
| `symbol_name`        | `str           | None`       | Specific symbol to query; `None` → all symbols.    |
| `deadline`           | `datetime      | None`       | Absolute per‑call deadline (converted to timeout). |
| `cancellation_event` | `asyncio.Event | None`       | Cooperative cancel for the retry wrapper.          |

---

## ⬆️ Output

### Payload: `SymbolParamsManyData`

Contains `params_info: list[SymbolParamsManyInfo]` (naming per pb). Typical fields include:

| Field             | Proto Type / Enum                | Description                                         |
| ----------------- | -------------------------------- | --------------------------------------------------- |
| `Symbol`          | `string`                         | Symbol name (e.g., `EURUSD`).                       |
| `Digits`          | `int32`                          | Price digits.                                       |
| `Point`           | `double`                         | Minimal price increment.                            |
| `Spread`          | `int32` or `double`              | Current spread.                                     |
| `SpreadFloat`     | `bool`                           | Whether spread is floating.                         |
| `TradeMode`       | `SP_ENUM_SYMBOL_TRADE_MODE`      | Symbol trade mode (enabled/close‑only/disabled).    |
| `TradeExeMode`    | `SP_ENUM_SYMBOL_TRADE_EXECUTION` | Execution mode (Instant/Market/Exchange).           |
| `TradeCalcMode`   | `SP_ENUM_TRADE_CALC_MODE`        | Margin calculation mode (Forex/CFD/Futures…).       |
| `StopsLevel`      | `int32`                          | Min distance for SL/TP from current price (points). |
| `FreezeLevel`     | `int32`                          | Freeze level in points.                             |
| `VolumeMin`       | `double`                         | Minimal volume.                                     |
| `VolumeMax`       | `double`                         | Maximal volume.                                     |
| `VolumeStep`      | `double`                         | Volume step.                                        |
| `VolumeLow`       | `int64` (server stat)            | Session low volume metric (if provided).            |
| `VolumeHigh`      | `int64` (server stat)            | Session high volume metric (if provided).           |
| `ContractSize`    | `double`                         | Contract size (e.g., 100000 for FX).                |
| `TickSize`        | `double`                         | Minimal tick size.                                  |
| `TickValue`       | `double`                         | Tick value in deposit currency.                     |
| `MarginStop`      | `double`                         | Margin requirement for Stop orders.                 |
| `MarginStopLimit` | `double`                         | Margin requirement for Stop‑Limit orders.           |

> **Note:** Field names/types reflect the pb. The exact set can vary by integration; consult `mt4_term_api_account_helper_pb2.py` for the authoritative list.

---

## 🧱 Related enums (from pb)

These enums are present in the pb and are relevant to `symbol_params_many`:

### `SP_ENUM_SYMBOL_TRADE_MODE`

Describes whether the symbol is tradable.

### `SP_ENUM_SYMBOL_TRADE_EXECUTION`

Execution regime for orders on the symbol.

### `SP_ENUM_TRADE_CALC_MODE`

Defines how margin is calculated for the symbol class (Forex/CFD/Futures/etc.).

> Use these enums to map numeric values → human‑readable labels in your UI.

---

### 🎯 Purpose

Use this method to:

* Validate user input before sending orders (min/max/step, SL/TP distances).
* Pre‑compute margin and risk for order tickets.
* Populate UI forms with correct constraints per symbol.

### 🧩 Notes & Tips

* Wrapper uses `execute_with_reconnect(...)` to retry transient gRPC errors.
* Fetching **all symbols** can be heavy; prefer single‑symbol queries in hot paths.
* Combine with `tick_value_with_size(...)` for precise PnL/margin math for a given volume.

**See also:**
`quote(...)` — latest price for a symbol.
`tick_value_with_size(...)` — tick value scaled by volume.
`opened_orders(...)` — current positions; validate against symbol rules.

---

## Usage Examples

### 1) Enforce volume step & bounds in UI

```python
params = await acct.symbol_params_many("XAUUSD")
p = params.params_info[0]

# Clamp and snap volume to step
def snap_volume(vol: float, min_v: float, max_v: float, step: float) -> float:
    vol = max(min_v, min(max_v, vol))
    steps = round((vol - min_v) / step)
    return min_v + steps * step

v_ok = snap_volume(0.27, p.VolumeMin, p.VolumeMax, p.VolumeStep)
```

### 2) Check SL/TP distance

```python
p = (await acct.symbol_params_many("GBPUSD")).params_info[0]
min_pts = max(p.StopsLevel, p.FreezeLevel)
print(f"Minimum SL/TP distance: {min_pts} points")
```

### 3) Convert enum values to labels

```python
from MetaRpcMT4 import mt4_term_api_account_helper_pb2 as account_pb2

p = (await acct.symbol_params_many("EURUSD")).params_info[0]
trade_mode_label = account_pb2.SP_ENUM_SYMBOL_TRADE_MODE.Name(p.TradeMode)
exe_mode_label = account_pb2.SP_ENUM_SYMBOL_TRADE_EXECUTION.Name(p.TradeExeMode)
calc_mode_label = account_pb2.SP_ENUM_TRADE_CALC_MODE.Name(p.TradeCalcMode)
print(trade_mode_label, exe_mode_label, calc_mode_label)
```
