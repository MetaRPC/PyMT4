# Automation

## 🌀 `async set_trailing_stop(ticket, *, distance_pips, step_pips=None)`

**What it does:** Enables a **trailing stop** for the given position. The SL trails price by `distance_pips` and (optionally) updates in discrete `step_pips` increments.

**Used in:**

* Letting winners run while automatically protecting gains.
* Hands‑off trend following and breakout strategies.
* Scalping strategies to lock in quick profits.
* Swing trading to maximize trend movements.

**Parameters:**

* `ticket` - Order ticket number to trail
* `distance_pips` - Distance in pips between price and trailing stop
* `step_pips` - (Optional) Minimum price movement in pips before updating SL. If not specified, updates on every price tick.

**How it works:**

1. Monitors the position in real-time
2. As price moves favorably, moves SL to maintain `distance_pips` distance
3. If `step_pips` is specified, only updates SL when price moves by that amount
4. Returns a subscription ID that can be used to disable trailing later
5. Stops automatically when position is closed

**Related to:** [order_modify.md](../MT4Account/Trading_Actions/order_modify.md), [opened_orders_tickets.md](../MT4Account/Orders_Positions_History/opened_orders_tickets.md)

**Example 1: Basic trailing stop**

```python
# Open a buy position
ticket = await sugar.buy_market("EURUSD", lots=0.1, sl_pips=20)

# Trail 20 pips behind price; update every 2 pips
trail_id = await sugar.set_trailing_stop(
    ticket=ticket,
    distance_pips=20,
    step_pips=2
)
```

**Example 2: Aggressive trailing for scalping**

```python
# Scalp trade with tight trailing
ticket = await sugar.buy_market("EURUSD", lots=0.2, sl_pips=10, tp_pips=15)

# Trail very closely behind price (5 pips), update every pip
trail_id = await sugar.set_trailing_stop(
    ticket=ticket,
    distance_pips=5,
    step_pips=1  # Update frequently
)
```

**Example 3: Wide trailing for swing trading**

```python
# Swing trade - let it breathe
ticket = await sugar.buy_market("GBPUSD", lots=0.1, sl_pips=50)

# Trail 30 pips behind, update every 5 pips (reduce API calls)
trail_id = await sugar.set_trailing_stop(
    ticket=ticket,
    distance_pips=30,
    step_pips=5  # Less frequent updates
)
```

**Example 4: Conditional trailing activation**

```python
# Open position
ticket = await sugar.buy_market("EURUSD", lots=0.1, sl_pips=20, tp_pips=60)

# Wait for 20 pips profit before activating trailing
await sugar.auto_breakeven(ticket=ticket, trigger_pips=20)

# Now enable trailing stop
trail_id = await sugar.set_trailing_stop(
    ticket=ticket,
    distance_pips=15,
    step_pips=2
)
```

**Example 5: Multiple positions with different trailing strategies**

```python
# Conservative position - wide trail
ticket1 = await sugar.buy_market("EURUSD", lots=0.1)
trail_id1 = await sugar.set_trailing_stop(
    ticket=ticket1,
    distance_pips=30,
    step_pips=5
)

# Aggressive position - tight trail
ticket2 = await sugar.buy_market("EURUSD", lots=0.1)
trail_id2 = await sugar.set_trailing_stop(
    ticket=ticket2,
    distance_pips=10,
    step_pips=1
)

# Store trail IDs for later management
trailing_positions = {
    ticket1: trail_id1,
    ticket2: trail_id2
}
```

---

## 🧹 `async unset_trailing_stop(subscription_id)`

**What it does:** Disables a previously set trailing stop by its subscription/handler id.

**Used in:**

* Pausing automation around news events or switching strategy regime.
* Disabling trailing when profit target is reached.
* Manual intervention to take control of position management.
* Switching from automated to manual trailing strategy.

**Parameters:**

* `subscription_id` - The ID returned by `set_trailing_stop()`

**Important notes:**

* Trailing stops automatically when position is closed
* Current SL level remains in place after unsubscribing
* Can be called multiple times safely (idempotent)
* Does not close or modify the position itself

**Related to:** [order_modify.md](../MT4Account/Trading_Actions/order_modify.md)

**Example 1: Basic unsubscribe**

```python
# Enable trailing
trail_id = await sugar.set_trailing_stop(ticket=123456, distance_pips=20, step_pips=2)

# Later: disable trailing
await sugar.unset_trailing_stop(subscription_id=trail_id)
```

**Example 2: Pause trailing during news events**

```python
import datetime

# Enable trailing
ticket = await sugar.buy_market("EURUSD", lots=0.1)
trail_id = await sugar.set_trailing_stop(ticket=ticket, distance_pips=20)

# Check for upcoming news
if is_news_time():
    logger.info("News event upcoming - pausing trailing stop")
    await sugar.unset_trailing_stop(trail_id)

    # Wait for news to pass
    await asyncio.sleep(300)  # 5 minutes

    # Resume trailing
    trail_id = await sugar.set_trailing_stop(ticket=ticket, distance_pips=20)
```

**Example 3: Disable trailing when profit target reached**

```python
# Open position with trailing
ticket = await sugar.buy_market("EURUSD", lots=0.1, sl_pips=20)
trail_id = await sugar.set_trailing_stop(ticket=ticket, distance_pips=15, step_pips=2)

# Monitor profit
while True:
    orders = await sugar._svc.opened_orders()
    position = next((o for o in orders if o.ticket == ticket), None)

    if position and position.profit >= 100.0:  # $100 profit
        logger.info("Profit target reached - locking in gains")

        # Disable trailing
        await sugar.unset_trailing_stop(trail_id)

        # Set tight manual SL
        current_price = await sugar.last_quote("EURUSD")
        tight_sl = current_price["bid"] - await sugar.pips_to_price("EURUSD", 5)
        await sugar.modify_sl_tp_by_price(ticket=ticket, sl_price=tight_sl)
        break

    await asyncio.sleep(5)
```

**Example 4: Manage multiple trailing stops**

```python
# Track all active trailing stops
active_trails = {}

# Enable trailing for multiple positions
for ticket in [111111, 222222, 333333]:
    trail_id = await sugar.set_trailing_stop(
        ticket=ticket,
        distance_pips=20,
        step_pips=2
    )
    active_trails[ticket] = trail_id

# Later: disable all trailing stops
for ticket, trail_id in active_trails.items():
    logger.info(f"Disabling trailing for ticket {ticket}")
    await sugar.unset_trailing_stop(trail_id)

active_trails.clear()
```

**Example 5: Conditional trailing management**

```python
# Enable trailing
ticket = await sugar.buy_market("EURUSD", lots=0.1)
trail_id = await sugar.set_trailing_stop(ticket=ticket, distance_pips=20)

# Monitor market volatility
while True:
    spread = await sugar.spread_pips("EURUSD")

    if spread > 5.0:
        # High spread - pause trailing
        logger.warning("High spread detected - pausing trailing")
        await sugar.unset_trailing_stop(trail_id)
        trail_id = None

    elif spread < 2.0 and trail_id is None:
        # Normal spread - resume trailing
        logger.info("Spread normalized - resuming trailing")
        trail_id = await sugar.set_trailing_stop(ticket=ticket, distance_pips=20)

    await asyncio.sleep(10)
```
