# MT4Account · Market / Quotes / Symbols — Overview

> Price snapshots, symbol registry, per‑symbol trading rules, and historical bars. Use this page to choose the right API for your market data layer.

## 📁 What lives here

* **[quote](./quote.md)** — **single‑symbol** snapshot (bid/ask or last, spread, time).
* **[quote_many](./quote_many.md)** — **batch** snapshots for many symbols at once.
* **[quote_history](./quote_history.md)** — **OHLCV bars** for a timeframe and time window.
* **[symbols](./symbols.md)** — list of **available symbols** from the terminal.
* **[symbol_params_many](./symbol_params_many.md)** — per‑symbol **trading constraints** (Digits, Point, VolumeMin/Max/Step, StopsLevel, FreezeLevel, etc.).
* **[tick_value_with_size](./tick_value_with_size.md)** — **monetary value per tick** for a given volume.

---

## 🧭 Plain English

* **quote / quote_many** → your **live price feed** (pull mode) for UI tiles and sanity checks.
* **symbols** → the **server truth** list; cache it and validate user inputs against it.
* **symbol_params_many** → the **rulebook** per symbol: digits, point size, min/max volume, min SL/TP distance.
* **quote_history** → **bars** for charts, indicators, and backtests.
* **tick_value_with_size** → convert **ticks → money** for risk sizing.

> Rule of thumb: need **now price** → `quote*`; need **allowed volume/SL/TP** → `symbol_params_many`; need **bars** → `quote_history`.

---

## Quick choose

| If you need…                                     | Use                    | Returns                    | Key inputs                          |
| ------------------------------------------------ | ---------------------- | -------------------------- | ----------------------------------- |
| Price for one symbol (UI tile / check)           | `quote`                | `QuoteData`                | `symbol`                            |
| Prices for many symbols at once                  | `quote_many`           | `QuoteManyData`            | `symbols: list[str]`                |
| Historical bars for charts/backtests             | `quote_history`        | `QuoteHistoryData` (OHLCV) | `symbol`, `timeframe`, `from`, `to` |
| Full symbol list from terminal                   | `symbols`              | `SymbolsData`              | *(none)*                            |
| Trading constraints (digits/point/volume/limits) | `symbol_params_many`   | `SymbolParamsManyData`     | `symbols: list[str]`                |
| Monetary tick value for a volume                 | `tick_value_with_size` | `TickValueWithSizeData`    | `symbol`, `volume`                  |

---

## ❌ Cross‑refs & gotchas

* **Cache** `symbols` and `symbol_params_many`; they rarely change intra‑session.
* **Digits vs Point**: format prices using `Digits`, compute deltas using `Point`.
* **StopsLevel & FreezeLevel**: enforce **minimum distance** for SL/TP and pending prices.
* **UTC** everywhere for `quote_history`; align bar timestamps to timeframe.
* For large symbol sets, prefer **`quote_many`** to reduce round‑trips.

---

## 🟢 Minimal snippets

```python
# Validate a user symbol and fetch its quote
s = await acct.symbols()
valid = { getattr(e, 'symbol', None) or getattr(e, 'symbolName', None) for e in getattr(s, 'items', []) }
if 'EURUSD' in valid:
    q = await acct.quote('EURUSD')
```

```python
# Pull constraints and snap a volume
p = (await acct.symbol_params_many(['XAUUSD'])).params_info[0]
def snap(vol):
    vol = max(p.VolumeMin, min(p.VolumeMax, vol))
    steps = round((vol - p.VolumeMin) / p.VolumeStep)
    return p.VolumeMin + steps * p.VolumeStep
```

```python
# Bars for last 7 days (H1)
from datetime import datetime, timedelta, timezone
end = datetime.now(timezone.utc)
start = end - timedelta(days=7)
bars = await acct.quote_history('EURUSD', timeframe=market_pb2.QH_PERIOD_H1, from_time=start, to_time=end)
```

```python
# Tick value for risk sizing
v = (await acct.tick_value_with_size('GBPUSD', volume=0.2)).tick_value
```

---

## See also

* **Streams:** [`on_symbol_tick`](../Streams/on_symbol_tick.md) — real‑time ticks without polling
* **Trading actions:** [`order_send`](../Trading_Actions/order_send.md), [`order_modify`](../Trading_Actions/order_modify.md)
* **Live state & history:** [`opened_orders`](../Orders_Positions_History/opened_orders.md), [`orders_history`](../Orders_Positions_History/orders_history.md)
