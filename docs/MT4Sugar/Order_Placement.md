# Order Placement

## 🟢 `async buy_market(symbol, lots, *, sl_pips=None, tp_pips=None, comment=None)`

**What it does:** Opens a **BUY market** order with the specified lot size. Optionally sets SL/TP in pips.

**Used in:**

* Core trading scenarios for immediate execution.
* Fast entries at current market price.
* Breakout strategies when price crosses key levels.
* Momentum trading and trend following.

**Parameters:**

* `symbol` - Trading symbol (e.g., "EURUSD")
* `lots` - Position size in lots
* `sl_pips` - (Optional) Stop Loss in pips from entry
* `tp_pips` - (Optional) Take Profit in pips from entry
* `comment` - (Optional) Order comment for identification

**Returns:** Order ticket number (integer)

**Related to:** [order_send.md](../MT4Account/Trading_Actions/order_send.md)

**Example 1: Basic market buy**

```python
await sugar.buy_market("EURUSD", lots=0.1, sl_pips=20, tp_pips=40, comment="scalp entry")
```

**Example 2: Buy with risk-based lot sizing**

```python
# Calculate lot size for 2% risk
lots = await sugar.calc_lot_by_risk("EURUSD", stop_pips=20, risk_percent=2.0)

# Execute market buy
ticket = await sugar.buy_market("EURUSD", lots=lots, sl_pips=20, tp_pips=60)
print(f"Order opened: {ticket}")
```

**Example 3: Conditional entry on breakout**

```python
# Wait for price to break resistance
resistance = 1.1000
reached = await sugar.wait_price("EURUSD", target=resistance, direction=">=", timeout_s=300)

if reached:
    # Breakout confirmed - enter long
    ticket = await sugar.buy_market(
        "EURUSD",
        lots=0.2,
        sl_pips=15,
        tp_pips=45,
        comment="Resistance breakout"
    )
```

**Example 4: Multiple orders with different parameters**

```python
# Scalp trade
ticket1 = await sugar.buy_market("EURUSD", lots=0.1, sl_pips=10, tp_pips=15, comment="Scalp")

# Swing trade
ticket2 = await sugar.buy_market("EURUSD", lots=0.05, sl_pips=50, tp_pips=150, comment="Swing")

# Position trade (no TP - let it run)
ticket3 = await sugar.buy_market("EURUSD", lots=0.03, sl_pips=100, comment="Position")
```

---

## 🔴 `async sell_market(symbol, lots, *, sl_pips=None, tp_pips=None, comment=None)`

**What it does:** Opens a **SELL market** order.

**Used in:**

* Same usage as `buy_market`, but in the opposite direction.
* Short selling, range trading, mean reversion strategies.
* Hedging existing long positions.

**Parameters:**  Same as `buy_market`

**Returns:** Order ticket number (integer)

**Related to:** [order_send.md](../MT4Account/Trading_Actions/order_send.md)

**Example 1: Basic market sell**

```python
await sugar.sell_market("EURUSD", lots=0.1, sl_pips=20, tp_pips=40)
```

**Example 2: Sell on resistance rejection**

```python
# Price rejected resistance - go short
if price_rejected_resistance():
    ticket = await sugar.sell_market(
        "EURUSD",
        lots=0.15,
        sl_pips=25,
        tp_pips=75,
        comment="Resistance rejection"
    )
```

---

## 🧱 `async buy_limit(symbol, lots, price, *, sl_pips=None, tp_pips=None, comment=None)`

**What it does:** Places a **BUY LIMIT** pending order at the given price (below current market).

**Used in:**

* Pending entries below the current market.
* Buy‑the‑dip or limit‑reversal strategies.
* Support level entries.

**Parameters:**

* `price` - Order entry price (must be below current Ask for buy limit)
* Other parameters same as `buy_market`

**Returns:** Order ticket number (integer)

**Related to:** [order_send.md](../MT4Account/Trading_Actions/order_send.md), [order_modify.md](../MT4Account/Trading_Actions/order_modify.md)

**Example 1: Buy at support level**

```python
await sugar.buy_limit("EURUSD", lots=0.2, price=1.0850, sl_pips=25, tp_pips=50)
```

**Example 2: Multiple limit orders (grid/ladder)**

```python
# Place buy limits at multiple support levels
support_levels = [1.0900, 1.0850, 1.0800]

for level in support_levels:
    ticket = await sugar.buy_limit(
        "EURUSD",
        lots=0.1,
        price=level,
        sl_pips=30,
        tp_pips=60,
        comment=f"Support {level}"
    )
    print(f"Buy limit placed at {level}: {ticket}")
```

---

## 🧱 `async sell_limit(symbol, lots, price, *, sl_pips=None, tp_pips=None, comment=None)`

**What it does:** Places a **SELL LIMIT** pending order above the current price.

**Used in:**

* Entries on pullbacks to resistance levels.
* Selling at overbought conditions.

**Parameters:** Same as `buy_limit`

**Returns:** Order ticket number (integer)

**Related to:** [order_send.md](../MT4Account/Trading_Actions/order_send.md)

**Example 1: Sell at resistance**

```python
await sugar.sell_limit("EURUSD", lots=0.2, price=1.1150, sl_pips=25, tp_pips=50)
```

**Example 2: Resistance zone ladder**

```python
# Place sells across resistance zone
resistance_zone = [1.1100, 1.1120, 1.1150]

for level in resistance_zone:
    await sugar.sell_limit("EURUSD", lots=0.05, price=level, sl_pips=20, tp_pips=40)
```

---

## 🧨 `async buy_stop(symbol, lots, price, *, sl_pips=None, tp_pips=None, comment=None)`

**What it does:** Places a **BUY STOP** order above the current price to enter on breakout.

**Used in:**

* Breakout and momentum strategies.
* Entering on upside price confirmation.

**Parameters:** Same as `buy_limit` but price must be above current Ask

**Returns:** Order ticket number (integer)

**Related to:** [order_send.md](../MT4Account/Trading_Actions/order_send.md)

**Example 1: Breakout entry**

```python
await sugar.buy_stop("GBPUSD", lots=0.1, price=1.2800, sl_pips=30, tp_pips=60)
```

**Example 2: Range breakout with OCO**

```python
# Place both buy stop (upside) and sell stop (downside)
current_price = (await sugar.last_quote("EURUSD"))["bid"]

# Buy stop above range
buy_ticket = await sugar.buy_stop("EURUSD", lots=0.1, price=current_price + 0.0050, sl_pips=20)

# Sell stop below range
sell_ticket = await sugar.sell_stop("EURUSD", lots=0.1, price=current_price - 0.0050, sl_pips=20)
```

---

## 🧨 `async sell_stop(symbol, lots, price, *, sl_pips=None, tp_pips=None, comment=None)`

**What it does:** Places a **SELL STOP** order below the current price to enter on downside breakout.

**Used in:**

* Breakout strategies and continuation trades.
* Entering short on downside confirmation.

**Parameters:** Same as `sell_limit` but price must be below current Bid

**Returns:** Order ticket number (integer)

**Related to:** [order_send.md](../MT4Account/Trading_Actions/order_send.md)

**Example 1: Downside breakout**

```python
await sugar.sell_stop("GBPUSD", lots=0.1, price=1.2700, sl_pips=30, tp_pips=60)
```

**Example 2: Support break entry**

```python
# Enter short if support breaks
support = 1.0950
ticket = await sugar.sell_stop("EURUSD", lots=0.15, price=support - 0.0010, sl_pips=25, tp_pips=75, comment="Support break")
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
