# ✅ Getting Historical Quotes — `quote_history`

> **Request:** retrieve **OHLCV bars** for a symbol and timeframe within a time range as `QuoteHistoryData`.
> Use this for charts, backtests, and indicators.

**Source files (SDK):**

* `MetaRpcMT4/mt4_account.py` — method `quote_history(symbol, timeframe, from_time, to_time, ...)`
* `MetaRpcMT4/mt4_term_api_market_info_pb2.py` — `QuoteHistory*` + `ENUM_QUOTE_HISTORY_TIMEFRAME`

### RPC

* **Service:** `mt4_term_api.MarketInfo`
* **Method:** `QuoteHistory(QuoteHistoryRequest) → QuoteHistoryReply`
* **Low‑level client:** `MarketInfoStub.QuoteHistory(request, metadata, timeout)`
* **SDK wrapper:** `MT4Account.quote_history(symbol: str, timeframe: ENUM_QUOTE_HISTORY_TIMEFRAME, from_time: datetime, to_time: datetime, deadline=None, cancellation_event=None) → QuoteHistoryData`

**Request message:** `QuoteHistoryRequest { symbol: string, timeframe: ENUM_QUOTE_HISTORY_TIMEFRAME, from_time: Timestamp, to_time: Timestamp }`
**Reply message:** `QuoteHistoryReply { data: QuoteHistoryData }`

---

### 🔗 Code Example

```python
from datetime import datetime, timedelta, timezone
from MetaRpcMT4 import mt4_term_api_market_info_pb2 as market_pb2

symbol = "EURUSD"
end = datetime.now(timezone.utc)
start = end - timedelta(days=7)

bars = await acct.quote_history(
    symbol=symbol,
    timeframe=market_pb2.QH_PERIOD_H1,
    from_time=start,
    to_time=end,
)

# Print a compact ledger of bars
for b in bars.items:  # list[QuoteBar]
    ts = b.date_time.ToDatetime().replace(tzinfo=timezone.utc)
    print(f"{ts.isoformat()} O={b.open:.5f} H={b.high:.5f} L={b.low:.5f} C={b.close:.5f} TV={b.tick_volume}")
```

---

### Method Signature

```python
async def quote_history(
    self,
    symbol: str,
    timeframe: market_info_pb2.ENUM_QUOTE_HISTORY_TIMEFRAME,
    from_time: datetime,
    to_time: datetime,
    deadline: datetime | None = None,
    cancellation_event: asyncio.Event | None = None,
) -> market_info_pb2.QuoteHistoryData
```

---

## 💬 Just the essentials

* **What it is.** Server‑side historical bars (OHLC + volumes) for a symbol/timeframe.
* **Why.** Drive charts, compute indicators (MA/RSI), and feed backtests.
* **Windowing.** Bars are returned for `[from_time, to_time]` in **UTC**.

---

## 🔽 Input

| Parameter            | Type                           | Description                      |                                           |
| -------------------- | ------------------------------ | -------------------------------- | ----------------------------------------- |
| `symbol`             | `str`                          | Symbol (e.g., `EURUSD`).         |                                           |
| `timeframe`          | `ENUM_QUOTE_HISTORY_TIMEFRAME` | Bar timeframe (see enum below).  |                                           |
| `from_time`          | `datetime` (UTC)               | Start of the requested interval. |                                           |
| `to_time`            | `datetime` (UTC)               | End of the requested interval.   |                                           |
| `deadline`           | `datetime                      | None`                            | Absolute per‑call deadline.               |
| `cancellation_event` | `asyncio.Event                 | None`                            | Cooperative cancel for the retry wrapper. |

---

## ⬆️ Output

### Payload: `QuoteHistoryData`

Contains `items: list[QuoteBar]`.

| Field         | Proto Type                  | Description                                |
| ------------- | --------------------------- | ------------------------------------------ |
| `date_time`   | `google.protobuf.Timestamp` | Bar timestamp (UTC, aligned to timeframe). |
| `open`        | `double`                    | Open price.                                |
| `high`        | `double`                    | High price.                                |
| `low`         | `double`                    | Low price.                                 |
| `close`       | `double`                    | Close price.                               |
| `tick_volume` | `int64`                     | Tick volume for the bar.                   |
| `real_volume` | `int64`                     | Real volume (if broker provides).          |

> The exact field list can vary slightly by integration; check `mt4_term_api_market_info_pb2.py` for the authoritative schema.

---

## 🧱 Related enums (from pb)

### `ENUM_QUOTE_HISTORY_TIMEFRAME`

Common members:

* `QH_PERIOD_M1`
* `QH_PERIOD_M5`
* `QH_PERIOD_M15`
* `QH_PERIOD_M30`
* `QH_PERIOD_H1`
* `QH_PERIOD_H4`
* `QH_PERIOD_D1`
* `QH_PERIOD_W1`
* `QH_PERIOD_MN1`

> Use `market_info_pb2.ENUM_QUOTE_HISTORY_TIMEFRAME.Name(value)` to map numbers → labels.

---

### 🎯 Purpose

Use this method to:

* Build charts and compute indicators.
* Backtest strategies on a bounded window.
* Export OHLCV for analytics.

### 🧩 Notes & Tips

* Wrapper uses `execute_with_reconnect(...)` for transient gRPC retries.
* Ensure `from_time < to_time` and keep windows reasonably sized to avoid timeouts.
* Respect symbol `Digits/Point` for formatting and rounding.
* Some brokers omit `real_volume`; rely on `tick_volume` if so.

**See also:**
`quote(...)`, `quote_many(...)` — live snapshots.
`symbol_params_many(...)` — symbol constraints (digits/point).
`tick_value_with_size(...)` — monetary value per tick.

---

## Usage Examples

### 1) Build a pandas‑friendly structure

```python
from datetime import datetime, timedelta, timezone
from MetaRpcMT4 import mt4_term_api_market_info_pb2 as market_pb2

bars = await acct.quote_history(
    symbol="XAUUSD",
    timeframe=market_pb2.QH_PERIOD_M15,
    from_time=datetime.now(timezone.utc) - timedelta(days=2),
    to_time=datetime.now(timezone.utc),
)

rows = [
    {
        "ts": b.date_time.ToDatetime().replace(tzinfo=timezone.utc),
        "open": b.open,
        "high": b.high,
        "low": b.low,
        "close": b.close,
        "tv": getattr(b, "tick_volume", None),
        "rv": getattr(b, "real_volume", None),
    }
    for b in bars.items
]
```

### 2) Rolling SMA example

```python
# Compute a simple moving average over the closes
N = 20
closes = [b.close for b in bars.items]
sma = [sum(closes[i-N:i])/N for i in range(N, len(closes)+1)]
```

### 3) Guardrails for big windows

```python
from datetime import timedelta

MAX_DAYS = 120  # example policy
if (to_time - from_time) > timedelta(days=MAX_DAYS):
    raise ValueError("Window too large; request in chunks or lower timeframe.")
```
