# Market Data

## 📊 `async bars(symbol, timeframe, *, count=None, since=None, until=None)`

**What it does:** Fetches historical OHLC bars for the given symbol and timeframe.

**Used in:**

* Technical analysis, backtesting, visualization.
* Indicator calculations and statistical modeling.
* Pattern recognition and machine learning features.
* Strategy development and optimization.

**Parameters:**

* `symbol` - Trading symbol (e.g., "EURUSD")
* `timeframe` - Bar period: "M1", "M5", "M15", "M30", "H1", "H4", "D1", "W1", "MN"
* `count` - (Optional) Number of most recent bars to fetch
* `since` - (Optional) Start timestamp (epoch milliseconds)
* `until` - (Optional) End timestamp (epoch milliseconds)

**Returns:** List of dictionaries with keys: `time`, `open`, `high`, `low`, `close`, `volume`

**Important notes:**

* If backend doesn't support bars API, aggregates from ticks automatically
* Returns bars in chronological order (oldest first)
* Use `count` for simple "last N bars" queries
* Use `since`/`until` for date range queries

**Related to:** [quote_history.md](../MT4Account/Market_quota_symbols/quote_history.md)

**Example 1: Get last 500 hourly bars**

```python
bars = await sugar.bars("EURUSD", timeframe="H1", count=500)
for b in bars:
    print(b["time"], b["open"], b["high"], b["low"], b["close"])
```

**Example 2: Calculate simple moving average**

```python
# Get last 20 bars
bars = await sugar.bars("EURUSD", timeframe="H1", count=20)

# Calculate SMA
closes = [b["close"] for b in bars]
sma_20 = sum(closes) / len(closes)
print(f"SMA(20): {sma_20}")
```

**Example 3: Find support/resistance levels**

```python
# Get last 100 daily bars
bars = await sugar.bars("EURUSD", timeframe="D1", count=100)

# Find highest high and lowest low
highs = [b["high"] for b in bars]
lows = [b["low"] for b in bars]

resistance = max(highs)
support = min(lows)

print(f"Resistance: {resistance}, Support: {support}")
```

**Example 4: Multi-timeframe analysis**

```python
# Get bars from different timeframes
h1_bars = await sugar.bars("EURUSD", timeframe="H1", count=100)
h4_bars = await sugar.bars("EURUSD", timeframe="H4", count=100)
d1_bars = await sugar.bars("EURUSD", timeframe="D1", count=100)

# Analyze trend across timeframes
h1_trend = "up" if h1_bars[-1]["close"] > h1_bars[-20]["close"] else "down"
h4_trend = "up" if h4_bars[-1]["close"] > h4_bars[-20]["close"] else "down"
d1_trend = "up" if d1_bars[-1]["close"] > d1_bars[-20]["close"] else "down"

if h1_trend == h4_trend == d1_trend:
    print(f"Strong {h1_trend}trend across all timeframes")
```

---

## 🪶 `async ticks(symbol, *, since=None, until=None, limit=None)`

**What it does:** Returns historical tick data for the symbol starting from `since` (if provided).

**Used in:**

* High‑frequency analysis, custom bar building.
* Testing trading logic on raw tick data.
* Spread analysis and liquidity studies.
* Microsecond-level market microstructure analysis.

**Parameters:**

* `symbol` - Trading symbol
* `since` - (Optional) Start timestamp (epoch milliseconds)
* `until` - (Optional) End timestamp (epoch milliseconds)
* `limit` - (Optional) Maximum number of ticks to return

**Returns:** List of dictionaries with keys: `time`, `bid`, `ask`

**Important notes:**

* Tick data can be very large - use `limit` to control size
* Returns ticks in chronological order
* Time is in epoch milliseconds

**Related to:** [quote_history.md](../MT4Account/Market_quota_symbols/quote_history.md)

**Example 1: Get last 100 ticks**

```python
ticks = await sugar.ticks("EURUSD", limit=100)
for t in ticks:
    print(t["time"], t["bid"], t["ask"])
```

**Example 2: Analyze spread over time**

```python
# Get last 1000 ticks
ticks = await sugar.ticks("EURUSD", limit=1000)

# Calculate spread for each tick
spreads = [(t["ask"] - t["bid"]) * 10000 for t in ticks]  # in pips

avg_spread = sum(spreads) / len(spreads)
max_spread = max(spreads)
min_spread = min(spreads)

print(f"Average spread: {avg_spread:.1f} pips")
print(f"Max spread: {max_spread:.1f} pips")
print(f"Min spread: {min_spread:.1f} pips")
```

**Example 3: Build custom 1-second bars from ticks**

```python
import time

# Get ticks for last 5 minutes
since_time = int((time.time() - 300) * 1000)  # 5 minutes ago
ticks = await sugar.ticks("EURUSD", since=since_time)

# Group ticks into 1-second bars
bars = {}
for t in ticks:
    second = t["time"] // 1000  # Round to second
    if second not in bars:
        bars[second] = {"open": t["bid"], "high": t["bid"], "low": t["bid"], "close": t["bid"]}
    else:
        bars[second]["high"] = max(bars[second]["high"], t["bid"])
        bars[second]["low"] = min(bars[second]["low"], t["bid"])
        bars[second]["close"] = t["bid"]

print(f"Created {len(bars)} 1-second bars")
```

---

## ⏳ `async wait_price(symbol, target, direction='>=', timeout_s=None)`

**What it does:** Waits until price crosses a target level in the specified direction.
Returns the actual trigger price if satisfied within timeout, otherwise raises TimeoutError.

**Used in:**

* Automation flows that must "wait for price" before placing/closing orders.
* Syncing with real market movement without busy polling.
* Implementing price alerts and notifications.
* Conditional order placement strategies.

**Parameters:**

* `symbol` - Trading symbol
* `target` - Target price level to wait for
* `direction` - Comparison operator: ">=", "<=", ">", "<"
* `timeout_s` - (Optional) Timeout in seconds. If None, waits indefinitely.

**Returns:** Actual mid-price that triggered the condition (float)

**Raises:** `TimeoutError` if timeout is reached before condition is met

**Important notes:**

* Uses mid price: (bid + ask) / 2
* Polls every 0.25 seconds (non-blocking)
* Raises TimeoutError on timeout (not returns False)

**Related to:** [on_symbol_tick.md](../MT4Account/Streams/on_symbol_tick.md)

**Example 1: Wait for breakout above resistance**

```python
# Wait until price breaks 1.1050 resistance
try:
    trigger_price = await sugar.wait_price(
        "EURUSD",
        target=1.1050,
        direction=">=",
        timeout_s=300  # 5 minutes
    )
    print(f"Breakout! Price: {trigger_price}")

    # Enter long on breakout
    await sugar.buy_market("EURUSD", lots=0.1, sl_pips=20, tp_pips=60)
except TimeoutError:
    print("Timeout - no breakout occurred")
```

**Example 2: Wait for pullback to support**

```python
# Wait for price to pull back to 1.0950 support
try:
    trigger_price = await sugar.wait_price(
        "EURUSD",
        target=1.0950,
        direction="<=",
        timeout_s=600  # 10 minutes
    )
    print(f"Support reached at {trigger_price}")
    await sugar.buy_limit("EURUSD", lots=0.1, price=1.0950, sl_pips=25)
except TimeoutError:
    print("Support not reached within 10 minutes")
```

**Example 3: Price alert system**

```python
async def price_alert(symbol, level, direction, message):
    """Send alert when price reaches level"""
    try:
        trigger_price = await sugar.wait_price(
            symbol,
            target=level,
            direction=direction,
            timeout_s=None  # Wait indefinitely
        )
        logger.info(f"ALERT: {message} - Price: {trigger_price}")
        await send_notification(message)
    except Exception as e:
        logger.error(f"Alert error: {e}")

# Run multiple alerts concurrently
import asyncio
await asyncio.gather(
    price_alert("EURUSD", 1.1000, ">=", "EURUSD broke 1.1000!"),
    price_alert("GBPUSD", 1.2500, "<=", "GBPUSD dropped to 1.2500!"),
    price_alert("USDJPY", 150.00, ">=", "USDJPY hit 150!"),
)
```

**Example 4: Conditional order entry**

```python
# Wait for price to reach specific level before entering
entry_level = 1.1000

# Wait for level to be reached
trigger_price = await sugar.wait_price("EURUSD", target=entry_level, direction=">=")

# Verify we still want to enter (conditions haven't changed)
spread = await sugar.spread_pips("EURUSD")
if spread < 2.0:
    await sugar.buy_market("EURUSD", lots=0.1, sl_pips=20)
else:
    logger.warning("Spread too high - skipping entry")
```
