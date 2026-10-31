# Quote History (OHLC)

> OHLC bar history for a symbol and timeframe over a time range — candles for charts, indicators and backtests.

**API Information:**

* **Low-level API:** `MT4Account.quote_history(...)` (defined in `package/MetaRpcMT4/mt4_account.py`)
* **gRPC service:** `mt4_term_api.MarketInfo`
* **RPC:** `QuoteHistory(QuoteHistoryRequest) -> QuoteHistoryReply`
* **Payload:** `QuoteHistoryData`

## 💬 Just the essentials

* **What it is.** A list of OHLC bars for one symbol at a chosen timeframe, between `from_time` and `to_time`.
* **Why you need it.** Charting, indicators (SMA/ATR/…), and backtests.
* **When to use.** Any analysis that needs candles rather than a single live price.

---

## 🎯 Purpose

* OHLC bars for a timeframe (M1 … MN1)
* Bounded by a from/to time range
* Tick volume and spread per bar
* Feed indicators, charts and backtests

---

## Method Signature

```python
async def quote_history(
    self,
    symbol: str,
    timeframe: ENUM_QUOTE_HISTORY_TIMEFRAME,
    from_time: datetime,
    to_time: datetime,
    deadline: Optional[datetime] = None,
    cancellation_event: Optional[asyncio.Event] = None,
)
```

**Request message:**

```protobuf
message QuoteHistoryRequest {
  string symbol = 1;
  ENUM_QUOTE_HISTORY_TIMEFRAME timeframe = 2;
  Timestamp fromTime = 3;      // (+ fromTimeUtc)
  Timestamp toTime = 5;        // (+ toTimeUtc)
}
```

**Payload message:**

```protobuf
message QuoteHistoryData {
  repeated HistoryQuote historical_quotes = 1;
}

message HistoryQuote {
  string symbol = 1;
  int32 index = 2;
  Timestamp time = 3;
  Timestamp time_utc = 4;
  double open = 5;
  double close = 6;
  double high = 7;
  double low = 8;
  int64 real_volume = 9;
  int64 tick_volume = 10;
  int32 spread = 11;
}
```

---

## 🔽 Input

| Parameter | Type | Description |
|-----------|------|-------------|
| `symbol` | `str` | Symbol name. |
| `timeframe` | `ENUM_QUOTE_HISTORY_TIMEFRAME` | Bar timeframe (`QH_PERIOD_*`). |
| `from_time` | datetime | Start of the range (UTC). |
| `to_time` | datetime | End of the range (UTC). |
| `deadline` | datetime, optional | Absolute UTC deadline for the gRPC call. |
| `cancellation_event` | asyncio.Event, optional | Set to abort the request. |

---

## ⬆️ Output — `QuoteHistoryData`

`historical_quotes` — a list of `HistoryQuote` bars:

| Field | Python Type | Description |
|-------|-------------|-------------|
| `time` / `time_utc` | `datetime` | Bar open time (server / UTC) |
| `open` / `high` / `low` / `close` | `float` | OHLC prices |
| `tick_volume` | `int` | Number of ticks in the bar |
| `real_volume` | `int` | Real volume (0 if the broker doesn't provide it) |
| `spread` | `int` | Spread at the bar, in points |
| `symbol` | `str` | Symbol |
| `index` | `int` | Bar index in the series |

---

## 🧱 Related enums (from proto)

### `ENUM_QUOTE_HISTORY_TIMEFRAME` — input `timeframe`

| Constant | Meaning |
|----------|---------|
| `QH_PERIOD_M1` | 1 minute |
| `QH_PERIOD_M5` | 5 minutes |
| `QH_PERIOD_M15` | 15 minutes |
| `QH_PERIOD_M30` | 30 minutes |
| `QH_PERIOD_H1` | 1 hour |
| `QH_PERIOD_H4` | 4 hours |
| `QH_PERIOD_D1` | 1 day |
| `QH_PERIOD_W1` | 1 week |
| `QH_PERIOD_MN1` | 1 month |

> Access via `market_info_pb2.ENUM_QUOTE_HISTORY_TIMEFRAME.QH_PERIOD_H1`. (Note: this is the
> `market_info` enum the method expects — not the similarly named `QHB_PERIOD_*` from the
> standalone `quote_history` module.)

---

## 🧩 Notes & Tips

* **Use the right enum.** The method expects `market_info_pb2.ENUM_QUOTE_HISTORY_TIMEFRAME` (`QH_PERIOD_*`). Passing a value from another module won't match.
* **`from_time` / `to_time` are required** and are datetimes (UTC) — the range bounds the number of bars you get back.
* **`tick_volume` vs `real_volume`.** On FX most brokers report tick volume; `real_volume` is often 0.
* **Bars are time-ordered** by `time`; `index` is their position in the series.
* **For a single live price** use [quote](quote.md); for a live stream use [on_symbol_tick](../5. Streaming_Methods/on_symbol_tick.md).

---

## 🔗 Usage Examples

### 1) Fetch the last N hourly bars

```python
from datetime import datetime, timedelta
import MetaRpcMT4.mt4_term_api_market_info_pb2 as mi

async def recent_bars(account, symbol: str = "EURUSD", hours: int = 48):
    end = datetime.utcnow()
    data = await account.quote_history(
        symbol, mi.ENUM_QUOTE_HISTORY_TIMEFRAME.QH_PERIOD_H1,
        end - timedelta(hours=hours), end,
    )
    bars = data.historical_quotes
    print(f"{len(bars)} H1 bars")
    for b in bars[-3:]:
        print(f"  {b.time.ToDatetime():%m-%d %H:%M}  O={b.open:.5f} H={b.high:.5f} "
              f"L={b.low:.5f} C={b.close:.5f} vol={b.tick_volume}")
    return bars
```

### 2) Simple moving average of closes

```python
from datetime import datetime, timedelta
import MetaRpcMT4.mt4_term_api_market_info_pb2 as mi

async def sma(account, symbol: str, period: int = 20):
    end = datetime.utcnow()
    data = await account.quote_history(
        symbol, mi.ENUM_QUOTE_HISTORY_TIMEFRAME.QH_PERIOD_H1,
        end - timedelta(hours=period * 2), end,
    )
    closes = [b.close for b in data.historical_quotes][-period:]
    if len(closes) < period:
        return None
    value = sum(closes) / period
    print(f"SMA({period}) {symbol} = {value:.5f}")
    return value
```

### 3) Average daily range (last 14 days)

A quick ATR-style volatility read from daily bars.

```python
from datetime import datetime, timedelta
import MetaRpcMT4.mt4_term_api_market_info_pb2 as mi

async def avg_daily_range(account, symbol: str = "EURUSD", days: int = 14):
    end = datetime.utcnow()
    data = await account.quote_history(
        symbol, mi.ENUM_QUOTE_HISTORY_TIMEFRAME.QH_PERIOD_D1,
        end - timedelta(days=days * 2), end,
    )
    ranges = [b.high - b.low for b in data.historical_quotes][-days:]
    adr = sum(ranges) / len(ranges) if ranges else 0.0
    print(f"ADR({days}) {symbol} = {adr:.5f}")
    return adr
```

---

## ⚠️ Pitfalls

* **Wrong timeframe enum.** Use `market_info_pb2.ENUM_QUOTE_HISTORY_TIMEFRAME.QH_PERIOD_*` — not `QHB_PERIOD_*` from the other module.
* **Range too wide.** A tight timeframe over a long range returns a lot of bars — scope the window to what you need.
* **Partial last bar.** The most recent bar may still be forming; treat it as provisional.
* **Empty result.** Weekends/holidays or an out-of-session range can yield few or no bars — guard before indexing.

---

## 🧪 Testing Suggestions

* **Happy path.** H1 over the last 48h returns a sensible bar count with `high >= low` and `low <= close <= high`.
* **Ordering.** Bars are ascending in `time`; the last bar's time is close to now.
* **Timeframe scaling.** D1 over 14 days returns ~10–14 bars (trading days), far fewer than H1.

---

## 📚 See also

* [Quote](quote.md)
* [Many Quotes](quote_many.md)
* [On Symbol Tick (stream)](../5. Streaming_Methods/on_symbol_tick.md)

* **Back to:** [Symbols & Quotes — Overview](Symbols_Quotes.Overview.md) · [MT4Account — Master Overview](../MT4Account.Master.Overview.md)
