# Math & Risk

## 🤖 `async auto_breakeven(ticket, *, trigger_pips, plus_pips=0.0)`

**What it does:** Automatically moves SL to breakeven once price advances by `trigger_pips`;
sets SL to `entry ± plus_pips` depending on direction.

**Used in:**

* Semi‑automated strategies/scalping to lock in breakeven without manual intervention.

**Related to:** [order_modify.md](../MT4Account/Trading_Actions/order_modify.md), [opened_orders.md](../MT4Account/Orders_Positions_History/opened_orders.md)

**Example**

```python
await sugar.auto_breakeven(ticket=123456, trigger_pips=15, plus_pips=1.0)
```

---

## ⚖️ `breakeven_price(entry_price, commission=0.0, swap=0.0)`

**What it does:** Computes breakeven price considering commission/swap.

**Used in:**

* Determining the level to pull SL to when targeting "flat" (zero P/L).

**Related to:** *pure math helper*

**Example**

```python
be = sugar.breakeven_price(entry_price=1.10000, commission=0.5, swap=0.0)
```

---

## 💵 `async calc_cash_risk(symbol, lots, stop_pips)`

**What it does:** Calculates cash risk for a position if SL is placed `stop_pips` away.

**Used in:**

* Risk control / money management before order placement.

**Related to:** [tick_value_with_size.md](../MT4Account/Market_quota_symbols/tick_value_with_size.md)

**Example**

```python
risk_cash = await sugar.calc_cash_risk("EURUSD", lots=0.2, stop_pips=25)
```

---

## 🧮 `async calc_lot_by_risk(symbol, risk_percent, stop_pips, *, balance=None)`

**What it does:** Derives lot size from desired `%` risk of balance and SL distance in pips.

**Used in:**

* Auto‑sizing position before sending an order.

**Related to:** [tick_value_with_size.md](../MT4Account/Market_quota_symbols/tick_value_with_size.md)

**Example**

```python
lot = await sugar.calc_lot_by_risk("EURUSD", risk_percent=1.0, stop_pips=20, balance=None)
```

---

## 🧷 `async close_by_breakeven(ticket, plus_pips=0.0)`

**What it does:** Closes a position if price returns to entry (adjusted by `plus_pips`).

**Used in:**

* "Don’t give back" logic: from profit either continue or exit flat.

**Related to:** [order_close_delete.md](../MT4Account/Trading_Actions/order_close_delete.md), [opened_orders_tickets.md](../MT4Account/Orders_Positions_History/opened_orders_tickets.md)

**Example**

```python
await sugar.close_by_breakeven(ticket=123456, plus_pips=0.5)
```

---

## 🧯 `async normalize_lot(symbol, lots)`

**What it does:** Normalizes lot to the instrument’s step/min/max constraints.

**Used in:**

* Before `order_send` / `order_modify` to avoid broker rejections.

**Related to:** [symbol_params_many.md](../MT4Account/Market_quota_symbols/symbol_params_many.md)

**Example**

```python
lots_ok = await sugar.normalize_lot("XAUUSD", lots=0.033)
```

---

## 🎯 `async normalize_price(symbol, price)`

**What it does:** Normalizes price to the instrument’s precision (`digits/point`).

**Used in:**

* Before setting SL/TP/limit/stop orders.

**Related to:** [symbol_params_many.md](../MT4Account/Market_quota_symbols/symbol_params_many.md)

**Example**

```python
p = await sugar.normalize_price("GBPUSD", 1.279991)
```

---

## 📏 `async pips_to_price(symbol, pips)`

**What it does:** Converts a distance in pips to a price delta for the symbol.

**Used in:**

* Computing SL/TP/entry levels from pip values.

**Related to:** [symbol_params_many.md](../MT4Account/Market_quota_symbols/symbol_params_many.md), [tick_value_with_size.md](../MT4Account/Market_quota_symbols/tick_value_with_size.md)

**Example**

```python
delta = await sugar.pips_to_price("EURUSD", 15)  # ~0.0015 on 5-digit
```

---

## 🔁 `async price_to_pips(symbol, price_delta)`

**What it does:** Converts a price delta back into pips for the symbol.

**Used in:**

* Expressing spread/profit/risk in pips.

**Related to:** [symbol_params_many.md](../MT4Account/Market_quota_symbols/symbol_params_many.md)

**Example**

```python
pips = await sugar.price_to_pips("EURUSD", 0.0007)  # ~7 pips
```

---

## 🎫 `async tick_value(symbol, lots=1.0)`

**What it does:** Cash value of one tick move for the symbol at the given lot.

**Used in:**

* Risk management, expected P/L per tick.

**Related to:** [tick_value_with_size.md](../MT4Account/Market_quota_symbols/tick_value_with_size.md)

**Example**

```python
tv = await sugar.tick_value("USDJPY", lots=0.5)
```
