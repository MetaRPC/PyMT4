# Order Management

## 📝 `async modify_sl_tp_by_pips(ticket, *, sl_pips=None, tp_pips=None)`

**What it does:** Modifies an existing order or position by setting SL/TP **in pips** relative to the entry price.

**Used in:**

* Quickly adjusting protective levels without manually converting to price.

**Related to:** [order_modify.md](../MT4Account/Trading_Actions/order_modify.md), [opened_orders_tickets.md](../MT4Account/Orders_Positions_History/opened_orders_tickets.md)

**Example**

```python
await sugar.modify_sl_tp_by_pips(ticket=123456, sl_pips=20, tp_pips=40)
```

---

## 📝 `async modify_sl_tp_by_price(ticket, *, sl_price=None, tp_price=None)`

**What it does:** Modifies SL/TP by specifying **exact price levels**.

**Used in:**

* Precise SL/TP placement from external calculations or strategy logic.

**Related to:** [order_modify.md](../MT4Account/Trading_Actions/order_modify.md)

**Example**

```python
await sugar.modify_sl_tp_by_price(ticket=123456, sl_price=1.0925, tp_price=1.1010)
```

---

## ❌ `async close(ticket)`

**What it does:** Closes a specific order or position by ticket.

**Used in:**

* Manual or automated close actions triggered by strategy conditions.

**Related to:** [order_close_delete.md](../MT4Account/Trading_Actions/order_close_delete.md)

**Example**

```python
await sugar.close(123456)
```

---

## ✂️ `async close_partial(ticket, lots)`

**What it does:** Partially closes a position by the specified lot size.

**Used in:**

* Taking partial profit or reducing exposure while keeping trade open.

**Related to:** [order_close_delete.md](../MT4Account/Trading_Actions/order_close_delete.md)

**Example**

```python
await sugar.close_partial(ticket=123456, lots=0.05)
```

---

## 🔁 `async close_by(ticket_a, ticket_b)`

**What it does:** Closes position `ticket_a` **by opposite** position `ticket_b` (Close By).

**Used in:**

* Reducing commission and swap by netting opposite trades.

**Related to:** [order_close_by.md](../MT4Account/Trading_Actions/order_close_by.md)

**Example**

```python
await sugar.close_by(ticket_a=111111, ticket_b=222222)
```

---

## 🧹 `async close_all(*, symbol=None, magic=None, only_profit=None)`

**What it does:** Closes multiple open positions filtered by symbol/magic.
If `only_profit` is True/False, closes only profitable or losing positions.

**Used in:**

* Emergency flattening, portfolio resets, strategy exits.

**Related to:** [opened_orders.md](../MT4Account/Orders_Positions_History/opened_orders.md), [order_close_delete.md](../MT4Account/Trading_Actions/order_close_delete.md)

**Example**

```python
# Close all profitable EURUSD with given magic
await sugar.close_all(symbol="EURUSD", magic=1001, only_profit=True)
```

---

## 🗑️ `async cancel_pendings(*, symbol=None, magic=None)`

**What it does:** Cancels **pending** orders filtered by symbol and magic.

**Used in:**

* Cleaning up hanging limit/stop orders before context change.

**Related to:** [order_close_delete.md](../MT4Account/Trading_Actions/order_close_delete.md)

**Example**

```python
await sugar.cancel_pendings(symbol="GBPUSD", magic=2002)
```
