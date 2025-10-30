# ✅ Getting a Quote

> **Request:** retrieve the latest **bid/ask + OHLC snapshot** for a single symbol as `QuoteData`.
> Use it for price displays, quick validation, and point/tick computations.

**Source files (SDK):**

* `MetaRpcMT4/mt4_account.py` — method `quote(symbol, ...)`
* `MetaRpcMT4/mt4_term_api_market_info_pb2.py` — `Quote*` messages (`QuoteRequest`, `QuoteReply`, `QuoteData`)

### RPC

* **Service:** `mt4_term_api.MarketInfo`
* **Method:** `Quote(QuoteRequest) → QuoteReply`
* **Low‑level client:** `MarketInfoStub.Quote(request, metadata, timeout)`
* **SDK wrapper:** `MT4Account.quote(symbol: str, deadline=None, cancellation_event=None) → QuoteData`

**Request message:** `QuoteRequest { symbol: string }`
**Reply message:** `QuoteReply { data: QuoteData }`

---

### 🔗 Code Example

```python
# Fetch a fresh price snapshot for a symbol
q = await acct.quote("EURUSD")
print(
    f"{q.symbol} bid={q.bid:.5f} ask={q.ask:.5f} "
    f"high={q.high:.5f} low={q.low:.5f} spread={getattr(q,'spread',0)}"
)
```

---

### Method Signature

```python
async def quote(
    self,
    symbol: str,
    deadline: datetime | None = None,
    cancellation_event: asyncio.Event | None = None,
) -> market_info_pb2.QuoteData
```

---

## 💬 Just the essentials

* **What it is.** A single‑symbol **price snapshot** (bid/ask + basic OHLC) with a server timestamp.
* **Why.** UI price tiles, input validation (SL/TP distances), and point/tick conversions.
* **Consistency.** Pair with `symbol_params_many(...)` to respect digits/point/SL‑TP rules.

---

## 🔽 Input

| Parameter            | Type           | Description                       |                                       |
| -------------------- | -------------- | --------------------------------- | ------------------------------------- |
| `symbol`             | `str`          | Symbol to query (e.g., `EURUSD`). |                                       |
| `deadline`           | `datetime      | None`                             | Absolute per‑call deadline.           |
| `cancellation_event` | `asyncio.Event | None`                             | Cooperative cancel for retry wrapper. |

---

## ⬆️ Output

### Payload: `QuoteData`

| Field       | Proto Type                  | Description                          |
| ----------- | --------------------------- | ------------------------------------ |
| `symbol`    | `string`                    | Symbol name.                         |
| `bid`       | `double`                    | Best bid price.                      |
| `ask`       | `double`                    | Best ask price.                      |
| `high`      | `double`                    | Session high.                        |
| `low`       | `double`                    | Session low.                         |
| `date_time` | `google.protobuf.Timestamp` | Server timestamp of the quote (UTC). |

---

## 🧱 Related enums (from pb)

This RPC **does not use method‑specific enums**.
For historical bars/timeframes see `ENUM_QUOTE_HISTORY_TIMEFRAME` used by `QuoteHistory` (separate method).

---

### 🎯 Purpose

Use this method to:

* Render price tiles/cards and keep UX responsive.
* Validate SL/TP/limit distances against current price.
* Convert points ↔ price deltas when combined with `symbol_params_many(...)`.

### 🧩 Notes & Tips

* Wrapper uses `execute_with_reconnect(...)` for transient gRPC retries.
* Respect `Digits/Point` from `symbol_params_many(...)` when formatting prices.
* Combine with `tick_value_with_size(...)` to translate price moves into monetary values.

**See also:**
`symbol_params_many(...)` — per‑symbol constraints and enums.
`tick_value_with_size(...)` — tick value/size & contract size for PnL math.
`quote_history(...)` — historical data (bars) with timeframe enum.

---

## Usage Examples

### 1) Spread and mid price

```python
q = await acct.quote("XAUUSD")
mid = (q.bid + q.ask) / 2
spread_pts = getattr(q, "spread", 0)
print(f"mid={mid:.2f} spread_pts={spread_pts}")
```

### 2) Enforce SL/TP distance vs StopsLevel

```python
p = (await acct.symbol_params_many("GBPUSD")).params_info[0]
q = await acct.quote("GBPUSD")
min_pts = max(p.StopsLevel, p.FreezeLevel)
# Example check for a BUY SL
min_price_delta = min_pts * p.Point
sl_ok = (q.bid - 1.5 * min_price_delta) > 0
```

### 3) Price → money per tick

```python
info = await acct.tick_value_with_size(["EURUSD"])  # one symbol
r = info.items[0]
# money per 1 tick per 1 lot
money_per_tick = r.TradeTickValue
```

