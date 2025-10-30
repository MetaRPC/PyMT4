# Order Placement

## 🟢 `async buy_market(symbol, lots, *, sl_pips=None, tp_pips=None, comment=None)`

**What it does:** Opens a **BUY market** order with the specified lot size. Optionally sets SL/TP in pips.

**Used in:**

* Core trading scenarios for immediate execution.
* Fast entries at current market price.

**Related to:** [order_send.md](../MT4Account/Trading_Actions/order_send.md)

**Example**

```python
await sugar.buy_market("EURUSD", lots=0.1, sl_pips=20, tp_pips=40, comment="scalp entry")
```

---

## 🔴 `async sell_market(symbol, lots, *, sl_pips=None, tp_pips=None, comment=None)`

**What it does:** Opens a **SELL market** order.

**Used in:**

* Same usage as `buy_market`, but in the opposite direction.

**Related to:** [order_send.md](../MT4Account/Trading_Actions/order_send.md)

**Example**

```python
await sugar.sell_market("EURUSD", lots=0.1, sl_pips=20, tp_pips=40)
```

---

## 🧱 `async buy_limit(symbol, lots, price, *, sl_pips=None, tp_pips=None, comment=None)`

**What it does:** Places a **BUY LIMIT** pending order at the given price.

**Used in:**

* Pending entries below the current market.
* Buy‑the‑dip or limit‑reversal strategies.

**Related to:** [order_send.md](../MT4Account/Trading_Actions/order_send.md), [order_modify.md](../MT4Account/Trading_Actions/order_modify.md)

**Example**

```python
await sugar.buy_limit("EURUSD", lots=0.2, price=1.0850, sl_pips=25, tp_pips=50)
```

---

## 🧱 `async sell_limit(symbol, lots, price, *, sl_pips=None, tp_pips=None, comment=None)`

**What it does:** Places a **SELL LIMIT** pending order above the current price.

**Used in:**

* Entries on pullbacks to resistance levels.

**Related to:** [order_send.md](../MT4Account/Trading_Actions/order_send.md)

**Example**

```python
await sugar.sell_limit("EURUSD", lots=0.2, price=1.1150, sl_pips=25, tp_pips=50)
```

---

## 🧨 `async buy_stop(symbol, lots, price, *, sl_pips=None, tp_pips=None, comment=None)`

**What it does:** Places a **BUY STOP** order above the current price to enter on breakout.

**Used in:**

* Breakout and momentum strategies.

**Related to:** [order_send.md](../MT4Account/Trading_Actions/order_send.md)

**Example**

```python
await sugar.buy_stop("GBPUSD", lots=0.1, price=1.2800, sl_pips=30, tp_pips=60)
```

---

## 🧨 `async sell_stop(symbol, lots, price, *, sl_pips=None, tp_pips=None, comment=None)`

**What it does:** Places a **SELL STOP** order below the current price to enter on downside breakout.

**Used in:**

* Breakout strategies and continuation trades.

**Related to:** [order_send.md](../MT4Account/Trading_Actions/order_send.md)

**Example**

```python
await sugar.sell_stop("GBPUSD", lots=0.1, price=1.2700, sl_pips=30, tp_pips=60)
```

---

## ⚙️ `async place_order(symbol, side, order_type, lots, *, price=None, sl_pips=None, tp_pips=None, comment=None)`

**What it does:** Generic order placement method — supports both market and pending orders.

**Used in:**

* Strategies that dynamically choose order type and direction.
* Universal trading templates and deal generators.

**Related to:** [order_send.md](../MT4Account/Trading_Actions/order_send.md)

**Example**

```python
await sugar.place_order(
    symbol="EURUSD",
    side="buy",
    order_type="limit",
    lots=0.2,
    price=1.0900,
    sl_pips=20,
    tp_pips=40,
)
```
