# Order Management

## 📝 `async modify_sl_tp_by_pips(ticket, *, sl_pips=None, tp_pips=None)`

**What it does:** Modifies an existing order or position by setting SL/TP **in pips** relative to the entry price.

**Used in:**

* Quickly adjusting protective levels without manually converting to price.
* Moving stop loss to breakeven after reaching profit targets.
* Tightening stops as price moves favorably.
* Extending take profit targets in trending markets.

**Parameters:**

* `ticket` - Order ticket number to modify
* `sl_pips` - (Optional) Stop Loss distance in pips from entry price
* `tp_pips` - (Optional) Take Profit distance in pips from entry price

**Important notes:**

* Pips are calculated from the **entry price**, not current price
* Pass `None` to keep existing SL or TP unchanged
* Pass `0` to remove SL or TP completely
* Method automatically handles buy vs sell direction

**Related to:** [order_modify.md](../MT4Account/Trading_Actions/order_modify.md), [opened_orders_tickets.md](../MT4Account/Orders_Positions_History/opened_orders_tickets.md)

**Example 1: Move to breakeven**

```python
# Move SL to breakeven (0 pips from entry)
await sugar.modify_sl_tp_by_pips(ticket=123456, sl_pips=0)
```

**Example 2: Tighten both SL and TP**

```python
await sugar.modify_sl_tp_by_pips(ticket=123456, sl_pips=20, tp_pips=40)
```

**Example 3: Only modify SL, keep TP unchanged**

```python
# Only change SL, TP remains as is
await sugar.modify_sl_tp_by_pips(ticket=123456, sl_pips=30)
```

**Example 4: Progressive stop tightening**

```python
# Open position
ticket = await sugar.buy_market("EURUSD", lots=0.1, sl_pips=50, tp_pips=100)

# After 20 pips profit, tighten to 30 pips
await asyncio.sleep(60)
await sugar.modify_sl_tp_by_pips(ticket=ticket, sl_pips=30)

# After 40 pips profit, tighten to 15 pips
await asyncio.sleep(60)
await sugar.modify_sl_tp_by_pips(ticket=ticket, sl_pips=15)

# After 60 pips profit, move to breakeven
await asyncio.sleep(60)
await sugar.modify_sl_tp_by_pips(ticket=ticket, sl_pips=0)
```

**Example 5: Remove TP to let position run**

```python
# Remove TP, keep SL
await sugar.modify_sl_tp_by_pips(ticket=123456, sl_pips=20, tp_pips=0)
```

---

## 📝 `async modify_sl_tp_by_price(ticket, *, sl_price=None, tp_price=None)`

**What it does:** Modifies SL/TP by specifying **exact price levels**.

**Used in:**

* Precise SL/TP placement from external calculations or strategy logic.
* Setting stops at specific support/resistance levels.
* Aligning stops with technical indicators (e.g., moving averages).

**Parameters:**

* `ticket` - Order ticket number to modify
* `sl_price` - (Optional) Exact Stop Loss price level
* `tp_price` - (Optional) Exact Take Profit price level

**Important notes:**

* Prices must be valid for the order direction (SL below entry for buy, above for sell)
* Pass `None` to keep existing SL or TP unchanged
* Pass `0` to remove SL or TP

**Related to:** [order_modify.md](../MT4Account/Trading_Actions/order_modify.md)

**Example 1: Set to specific levels**

```python
await sugar.modify_sl_tp_by_price(ticket=123456, sl_price=1.0925, tp_price=1.1010)
```

**Example 2: Set SL to previous day's low**

```python
# Get yesterday's bars
bars = await sugar.bars("EURUSD", timeframe="D1", count=2)
yesterday_low = bars[-2]["low"]

# Set SL at yesterday's low
await sugar.modify_sl_tp_by_price(ticket=ticket, sl_price=yesterday_low)
```

**Example 3: Set SL at moving average**

```python
# Calculate 20 EMA
bars = await sugar.bars("EURUSD", timeframe="H1", count=20)
closes = [b["close"] for b in bars]
ema_20 = sum(closes) / len(closes)  # Simplified

# Set SL at EMA
await sugar.modify_sl_tp_by_price(ticket=ticket, sl_price=ema_20)
```

---

## ❌ `async close(ticket)`

**What it does:** Closes a specific order or position by ticket.

**Used in:**

* Manual or automated close actions triggered by strategy conditions.
* Taking profit at predetermined levels.
* Emergency exits based on news or market conditions.

**Parameters:**

* `ticket` - Order ticket number to close

**Important notes:**

* Closes the entire position
* For partial closes, use `close_partial()`
* Works for both market positions and pending orders (pending orders are deleted)

**Related to:** [order_close_delete.md](../MT4Account/Trading_Actions/order_close_delete.md)

**Example 1: Simple close**

```python
await sugar.close(123456)
```

**Example 2: Close on signal reversal**

```python
# Monitor for exit signal
while True:
    if exit_signal_detected():
        logger.info("Exit signal - closing position")
        await sugar.close(ticket)
        break
    await asyncio.sleep(5)
```

**Example 3: Time-based exit**

```python
import asyncio

# Open position
ticket = await sugar.buy_market("EURUSD", lots=0.1)

# Close after 1 hour
await asyncio.sleep(3600)
await sugar.close(ticket)
```

---

## ✂️ `async close_partial(ticket, lots)`

**What it does:** Partially closes a position by the specified lot size.

**Used in:**

* Taking partial profit or reducing exposure while keeping trade open.
* Scaling out of positions as profit targets are reached.
* Risk reduction while maintaining market exposure.

**Parameters:**

* `ticket` - Order ticket number
* `lots` - Amount of lots to close (must be less than position size)

**Important notes:**

* Remaining position keeps the same ticket number (in MT4)
* Closed portion creates a new history entry
* Useful for pyramiding strategies

**Related to:** [order_close_delete.md](../MT4Account/Trading_Actions/order_close_delete.md)

**Example 1: Close half the position**

```python
await sugar.close_partial(ticket=123456, lots=0.05)
```

**Example 2: Scale out at multiple profit levels**

```python
# Open 0.3 lot position
ticket = await sugar.buy_market("EURUSD", lots=0.3, sl_pips=30)

# Take 1/3 profit at 20 pips
await sugar.wait_price("EURUSD", target=entry + 0.0020, direction=">=")
await sugar.close_partial(ticket=ticket, lots=0.1)

# Take another 1/3 at 40 pips
await sugar.wait_price("EURUSD", target=entry + 0.0040, direction=">=")
await sugar.close_partial(ticket=ticket, lots=0.1)

# Let final 1/3 run with trailing stop
await sugar.set_trailing_stop(ticket=ticket, distance_pips=20)
```

**Example 3: Reduce exposure on high volatility**

```python
# Monitor spread
spread = await sugar.spread_pips("EURUSD")

if spread > 5.0:
    # High spread - reduce exposure by 50%
    logger.warning("High spread - reducing position")
    await sugar.close_partial(ticket=ticket, lots=0.05)
```

---

## 🔁 `async close_by(ticket_a, ticket_b)`

**What it does:** Closes position `ticket_a` **by opposite** position `ticket_b` (Close By).

**Used in:**

* Reducing commission and swap by netting opposite trades.
* Hedging strategies where you want to close offsetting positions.
* Avoiding spread costs when closing opposite positions.

**Parameters:**

* `ticket_a` - First position ticket
* `ticket_b` - Opposite position ticket (must be opposite direction on same symbol)

**Important notes:**

* Both positions must be on the same symbol
* Positions must be opposite directions (one buy, one sell)
* Saves spread costs compared to closing each separately
* If positions are different sizes, smaller one closes completely, larger one is reduced

**Related to:** [order_close_by.md](../MT4Account/Trading_Actions/order_close_by.md)

**Example 1: Close hedged positions**

```python
await sugar.close_by(ticket_a=111111, ticket_b=222222)
```

**Example 2: Hedge and close strategy**

```python
# Open long position
long_ticket = await sugar.buy_market("EURUSD", lots=0.1)

# Market turns against us - hedge with short
short_ticket = await sugar.sell_market("EURUSD", lots=0.1)

# Wait for favorable conditions
await asyncio.sleep(300)

# Close both positions by netting
await sugar.close_by(ticket_a=long_ticket, ticket_b=short_ticket)
```

---

## 🧹 `async close_all(*, symbol=None, magic=None, only_profit=None)`

**What it does:** Closes multiple open positions filtered by symbol/magic.
If `only_profit` is True/False, closes only profitable or losing positions.

**Used in:**

* Emergency flattening, portfolio resets, strategy exits.
* End-of-day position closure.
* Closing all positions before major news events.

**Parameters:**

* `symbol` - (Optional) Filter by specific symbol
* `magic` - (Optional) Filter by magic number
* `only_profit` - (Optional) `True`=only profitable, `False`=only losing, `None`=all

**Important notes:**

* If no filters provided, closes **all** positions in the account
* Use filters carefully to avoid closing unintended positions
* Pending orders are not affected (use `cancel_pendings()` for those)

**Related to:** [opened_orders.md](../MT4Account/Orders_Positions_History/opened_orders.md), [order_close_delete.md](../MT4Account/Trading_Actions/order_close_delete.md)

**Example 1: Close all profitable positions for specific symbol**

```python
# Close all profitable EURUSD with given magic
await sugar.close_all(symbol="EURUSD", magic=1001, only_profit=True)
```

**Example 2: Emergency flatten all positions**

```python
# Major news event - close everything
logger.warning("Major news event - closing all positions")
await sugar.close_all()
```

**Example 3: End of day routine**

```python
# Close all positions at end of trading day
if is_end_of_day():
    await sugar.close_all(magic=1001)
    logger.info("All positions closed for end of day")
```

**Example 4: Close only losing positions**

```python
# Cut all losses before weekend
if is_friday_evening():
    await sugar.close_all(only_profit=False)
    logger.info("All losing positions closed before weekend")
```

---

## 🗑️ `async cancel_pendings(*, symbol=None, magic=None)`

**What it does:** Cancels **pending** orders filtered by symbol and magic.

**Used in:**

* Cleaning up hanging limit/stop orders before context change.
* Removing unfilled orders after strategy change.
* Canceling breakout orders when range-bound conditions detected.

**Parameters:**

* `symbol` - (Optional) Filter by specific symbol
* `magic` - (Optional) Filter by magic number

**Important notes:**

* Only affects pending orders (buy/sell limit/stop)
* Does not close market positions (use `close_all()` for that)
* If no filters provided, cancels **all** pending orders

**Related to:** [order_close_delete.md](../MT4Account/Trading_Actions/order_close_delete.md)

**Example 1: Cancel symbol-specific pendings**

```python
await sugar.cancel_pendings(symbol="GBPUSD", magic=2002)
```

**Example 2: Clean up before strategy switch**

```python
# Switching from breakout to range strategy
logger.info("Switching strategy - canceling all pending orders")
await sugar.cancel_pendings(magic=1001)

# Now place new range-bound orders
await sugar.buy_limit("EURUSD", lots=0.1, price=1.0900)
await sugar.sell_limit("EURUSD", lots=0.1, price=1.1100)
```

**Example 3: Cancel unfilled orders after timeout**

```python
# Place limit orders
tickets = []
for price in [1.0900, 1.0850, 1.0800]:
    ticket = await sugar.buy_limit("EURUSD", lots=0.1, price=price)
    tickets.append(ticket)

# Wait 1 hour
await asyncio.sleep(3600)

# Cancel any unfilled orders
await sugar.cancel_pendings(symbol="EURUSD", magic=1001)
```
