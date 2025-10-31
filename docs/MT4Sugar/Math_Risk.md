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
* Validating position sizes don't exceed risk limits.
* Portfolio risk aggregation.
* Risk reporting and monitoring.

**Parameters:**

* `symbol` - Trading symbol
* `lots` - Position size in lots
* `stop_pips` - Stop loss distance in pips

**Returns:** Cash risk amount in account currency (float)

**Related to:** [tick_value_with_size.md](../MT4Account/Market_quota_symbols/tick_value_with_size.md)

**Example 1: Verify risk before opening**

```python
# Check if risk is acceptable
risk_cash = await sugar.calc_cash_risk("EURUSD", lots=0.2, stop_pips=25)
print(f"This trade risks ${risk_cash:.2f}")

if risk_cash > 100:
    logger.warning("Risk too high - reducing position size")
else:
    await sugar.buy_market("EURUSD", lots=0.2, sl_pips=25)
```

**Example 2: Calculate total portfolio risk**

```python
# Get all open positions
orders = await sugar._svc.opened_orders()

total_risk = 0
for order in orders:
    # Calculate risk for each position
    risk = await sugar.calc_cash_risk(
        symbol=order.symbol,
        lots=order.lots,
        stop_pips=abs(order.stop_loss - order.open_price) / pip_size
    )
    total_risk += risk

print(f"Total portfolio risk: ${total_risk:.2f}")
```

**Example 3: Risk as percentage of balance**

```python
balance = 10000  # Account balance
risk_cash = await sugar.calc_cash_risk("EURUSD", lots=0.1, stop_pips=20)
risk_pct = (risk_cash / balance) * 100

print(f"Risk: ${risk_cash:.2f} ({risk_pct:.2f}% of balance)")
```

---

## 🧮 `async calc_lot_by_risk(symbol, risk_percent, stop_pips, *, balance=None)`

**What it does:** Derives lot size from desired `%` risk of balance and SL distance in pips. This is THE MOST IMPORTANT method for proper position sizing.

**Used in:**

* Auto‑sizing position before sending an order.
* Implementing consistent risk management across all trades.
* Adjusting position size based on stop loss distance.
* Portfolio risk management.

**Parameters:**

* `symbol` - Trading symbol
* `risk_percent` - Percentage of balance to risk (e.g., 1.0 = 1%, 2.5 = 2.5%)
* `stop_pips` - Stop loss distance in pips
* `balance` - (Optional) Account balance. If None, fetches current balance automatically.

**Returns:** Lot size (float) that risks exactly the specified percentage

**Important notes:**

* Automatically fetches account balance if not provided
* Accounts for symbol-specific tick values
* Returns normalized lot size (valid for broker)
* Higher risk_percent = larger position
* Wider stop_pips = smaller position (for same risk)

**Related to:** [tick_value_with_size.md](../MT4Account/Market_quota_symbols/tick_value_with_size.md)

**Example 1: Risk 1% on each trade**

```python
# Risk 1% of balance with 20 pip stop
lots = await sugar.calc_lot_by_risk("EURUSD", risk_percent=1.0, stop_pips=20)
await sugar.buy_market("EURUSD", lots=lots, sl_pips=20)
```

**Example 2: Adaptive position sizing**

```python
# Tighter stops = larger position
# Wider stops = smaller position

# Volatile market - wide stop, automatically smaller position
lots_volatile = await sugar.calc_lot_by_risk("EURUSD", risk_percent=1.0, stop_pips=50)

# Calm market - tight stop, automatically larger position
lots_calm = await sugar.calc_lot_by_risk("EURUSD", risk_percent=1.0, stop_pips=10)

print(f"50 pip stop = {lots_volatile} lots")  # e.g., 0.04
print(f"10 pip stop = {lots_calm} lots")      # e.g., 0.20
```

**Example 3: Different risk levels for different strategies**

```python
# Conservative: 0.5% risk
conservative_lots = await sugar.calc_lot_by_risk("EURUSD", risk_percent=0.5, stop_pips=20)

# Standard: 1% risk
standard_lots = await sugar.calc_lot_by_risk("EURUSD", risk_percent=1.0, stop_pips=20)

# Aggressive: 2% risk
aggressive_lots = await sugar.calc_lot_by_risk("EURUSD", risk_percent=2.0, stop_pips=20)

# Use based on signal confidence
if signal_confidence > 0.8:
    lots = aggressive_lots
elif signal_confidence > 0.5:
    lots = standard_lots
else:
    lots = conservative_lots
```

**Example 4: Portfolio risk management**

```python
# Never risk more than 5% total across all positions
MAX_TOTAL_RISK = 5.0
current_risk = 2.5  # Already 2.5% at risk in other positions

remaining_risk = MAX_TOTAL_RISK - current_risk  # 2.5%

if remaining_risk > 0:
    lots = await sugar.calc_lot_by_risk("EURUSD", risk_percent=remaining_risk, stop_pips=20)
    await sugar.buy_market("EURUSD", lots=lots, sl_pips=20)
else:
    logger.warning("Max portfolio risk reached - no new positions")
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

**What it does:** Normalizes lot to the instrument's step/min/max constraints.

**Used in:**

* Before `order_send` / `order_modify` to avoid broker rejections.
* Ensuring lot sizes comply with broker requirements.
* Rounding calculated lot sizes to valid values.

**Parameters:**

* `symbol` - Trading symbol
* `lots` - Lot size to normalize

**Returns:** Normalized lot size (float) that meets broker requirements

**Important notes:**

* Rounds to nearest valid lot step (usually 0.01)
* Clamps to min/max lot sizes
* Essential to avoid "invalid volume" errors

**Related to:** [symbol_params_many.md](../MT4Account/Market_quota_symbols/symbol_params_many.md)

**Example 1: Normalize calculated lots**

```python
lots_ok = await sugar.normalize_lot("XAUUSD", lots=0.033)  # → 0.03
```

**Example 2: Normalize before order placement**

```python
# Calculate ideal lot size
ideal_lots = 0.1234

# Normalize to broker requirements
actual_lots = await sugar.normalize_lot("EURUSD", ideal_lots)

await sugar.buy_market("EURUSD", lots=actual_lots)
```

---

## 🎯 `async normalize_price(symbol, price)`

**What it does:** Normalizes price to the instrument's precision (`digits/point`).

**Used in:**

* Before setting SL/TP/limit/stop orders.
* Ensuring prices comply with broker requirements.
* Rounding calculated prices to valid tick sizes.

**Parameters:**

* `symbol` - Trading symbol
* `price` - Price to normalize

**Returns:** Normalized price (float) rounded to valid tick size

**Important notes:**

* Rounds to nearest valid tick
* Essential to avoid order rejections
* Different symbols have different precision (EURUSD: 5 digits, USDJPY: 3 digits)

**Related to:** [symbol_params_many.md](../MT4Account/Market_quota_symbols/symbol_params_many.md)

**Example 1: Normalize calculated price**

```python
p = await sugar.normalize_price("GBPUSD", 1.279991)  # → 1.27999
```

**Example 2: Normalize SL/TP before order**

```python
# Calculate ideal SL price
ideal_sl = 1.095678

# Normalize to broker precision
actual_sl = await sugar.normalize_price("EURUSD", ideal_sl)

await sugar.buy_market("EURUSD", lots=0.1)
await sugar.modify_sl_tp_by_price(ticket=ticket, sl_price=actual_sl)
```

---

## 📏 `async pips_to_price(symbol, pips)`

**What it does:** Converts a distance in pips to a price delta for the symbol.

**Used in:**

* Computing SL/TP/entry levels from pip values.
* Converting pip-based calculations to actual price levels.
* Setting orders at specific pip distances from current price.

**Parameters:**

* `symbol` - Trading symbol
* `pips` - Number of pips to convert

**Returns:** Price delta (float) equivalent to the pip distance

**Important notes:**

* Accounts for symbol-specific pip sizes
* For 5-digit brokers (EURUSD): 10 pips = 0.00100
* For 3-digit brokers (USDJPY): 10 pips = 0.100

**Related to:** [symbol_params_many.md](../MT4Account/Market_quota_symbols/symbol_params_many.md), [tick_value_with_size.md](../MT4Account/Market_quota_symbols/tick_value_with_size.md)

**Example 1: Basic conversion**

```python
delta = await sugar.pips_to_price("EURUSD", 15)  # ~0.0015 on 5-digit
```

**Example 2: Calculate SL/TP prices**

```python
# Get current price
quote = await sugar.last_quote("EURUSD")
entry_price = quote["ask"]

# Calculate SL and TP prices
sl_distance = await sugar.pips_to_price("EURUSD", 20)
tp_distance = await sugar.pips_to_price("EURUSD", 60)

sl_price = entry_price - sl_distance  # For buy order
tp_price = entry_price + tp_distance  # For buy order

print(f"Entry: {entry_price}, SL: {sl_price}, TP: {tp_price}")
```

**Example 3: Place order at specific pip distance**

```python
# Place buy stop 30 pips above current price
quote = await sugar.last_quote("EURUSD")
current_ask = quote["ask"]

pip_distance = await sugar.pips_to_price("EURUSD", 30)
entry_price = current_ask + pip_distance

await sugar.buy_stop("EURUSD", lots=0.1, price=entry_price, sl_pips=20)
```

---

## 🔁 `async price_to_pips(symbol, price_delta)`

**What it does:** Converts a price delta back into pips for the symbol.

**Used in:**

* Expressing spread/profit/risk in pips.
* Calculating profit/loss in pips.
* Converting technical levels to pip distances.

**Parameters:**

* `symbol` - Trading symbol
* `price_delta` - Price difference to convert

**Returns:** Number of pips (float)

**Related to:** [symbol_params_many.md](../MT4Account/Market_quota_symbols/symbol_params_many.md)

**Example 1: Convert price to pips**

```python
pips = await sugar.price_to_pips("EURUSD", 0.0007)  # ~7 pips
```

**Example 2: Calculate profit in pips**

```python
# Get position details
entry_price = 1.09500
current_price = 1.09750
price_move = current_price - entry_price

# Convert to pips
profit_pips = await sugar.price_to_pips("EURUSD", price_move)
print(f"Profit: {profit_pips:.1f} pips")  # ~25 pips
```

**Example 3: Measure distance to key levels**

```python
# Technical analysis
quote = await sugar.last_quote("EURUSD")
current_price = quote["bid"]

resistance = 1.1000
distance_to_resistance = resistance - current_price
pips_to_resistance = await sugar.price_to_pips("EURUSD", distance_to_resistance)

print(f"{pips_to_resistance:.1f} pips to resistance")
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
