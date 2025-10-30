# Automation

## 🌀 `async set_trailing_stop(ticket, *, distance_pips, step_pips=None)`

**What it does:** Enables a **trailing stop** for the given position. The SL trails price by `distance_pips` and (optionally) updates in discrete `step_pips` increments.

**Used in:**

* Letting winners run while automatically protecting gains.
* Hands‑off trend following and breakout strategies.

**Related to:** [order_modify.md](../MT4Account/Trading_Actions/order_modify.md), [opened_orders_tickets.md](../MT4Account/Orders_Positions_History/opened_orders_tickets.md)

**Example**

```python
# Trail 20 pips behind price; update every 2 pips
trail_id = await sugar.set_trailing_stop(ticket=123456, distance_pips=20, step_pips=2)
```

---

## 🧹 `async unset_trailing_stop(subscription_id)`

**What it does:** Disables a previously set trailing stop by its subscription/handler id.

**Used in:**

* Pausing automation around news events or switching strategy regime.

**Related to:** [order_modify.md](../MT4Account/Trading_Actions/order_modify.md)

**Example**

```python
await sugar.unset_trailing_stop(subscription_id=trail_id)
```
