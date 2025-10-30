# Market Data

## 📊 `async bars(symbol, timeframe, *, count=None, since=None, until=None)`

**What it does:** Fetches historical OHLC bars for the given symbol and timeframe.

**Used in:**

* Technical analysis, backtesting, visualization.
* Indicator calculations and statistical modeling.

**Related to:** [quote_history.md](../MT4Account/Market_quota_symbols/quote_history.md)

**Example**

```python
bars = sugar.await sugar.bars("EURUSD", timeframe="H1", count=500)
for b in bars:
    print(b.time, b.open, b.high, b.low, b.close)
```

---

## 🪶 `async ticks(symbol, *, since=None, until=None, limit=None)`

**What it does:** Returns historical tick data for the symbol starting from `since` (if provided).

**Used in:**

* High‑frequency analysis, custom bar building.
* Testing trading logic on raw tick data.

**Related to:** [quote_history.md](../MT4Account/Market_quota_symbols/quote_history.md)

**Example**

```python
# Pull last 100 ticks
# Pull last 100 ticks
ticks = await sugar.ticks("EURUSD", limit=100)
for t in ticks:
    print(t.time, t.bid, t.ask)
```

---

## ⏳ `async wait_price(symbol, target, direction='>=', timeout_s=None)`

**What it does:** Waits until a price condition defined by `predicate(quote)` becomes true.
Returns `True` if satisfied within `timeout`, otherwise `False`.

**Used in:**

* Automation flows that must "wait for price" before placing/closing orders.
* Syncing with real market movement without busy polling.

**Related to:** [on_symbol_tick.md](../MT4Account/Streams/on_symbol_tick.md)

**Example**

```python
# Wait until bid crosses above a threshold
TARGET = 1.1050

def crossed(q):
    return getattr(q, "bid", None) and q.bid > TARGET

if await sugar.wait_price("EURUSD", crossed, timeout_s=15):
    print("Target price reached!")
else:
    print("Timeout waiting for price")
```
