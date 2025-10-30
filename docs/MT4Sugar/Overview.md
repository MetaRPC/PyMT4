# 🍬 Sugar API - Overview

Welcome to the **Sugar API**! This is PyMT4's high-level interface that wraps raw RPC calls into readable, pip-based operations with sane defaults.

---

## 🎯 What is Sugar API?

The **Sugar API** is designed to make your trading code:
- ✅ **Readable** - Methods named like `buy_market()`, `calc_lot_by_risk()`, `spread_pips()`
- ✅ **Pip-based** - Work with pips instead of raw price values
- ✅ **Smart defaults** - Set symbol/magic once, use everywhere
- ✅ **Less boilerplate** - Auto-normalization, auto-reconnect, auto-symbol-enable
- ✅ **Production-ready** - Error handling, retries, validation built-in

### Sugar vs Low-Level

| Aspect | Sugar API | Low-Level API |
|--------|-----------|---------------|
| **Syntax** | `await sugar.buy_market("EURUSD", 0.1, sl_pips=20)` | `await api.order_send(symbol="EURUSD", cmd=0, volume=0.1, price=quote.ask, sl=price-20*pip)` |
| **Defaults** | Uses stored defaults | Every parameter explicit |
| **Pips** | Native pip support | Manual price calculations |
| **Readability** | High | Medium |
| **Control** | Simplified | Complete |
| **Best for** | Rapid development | Fine-tuned optimization |

---

## 📚 API Categories

The Sugar API is organized into **7 functional categories**:

| Category | Methods | Purpose |
|----------|---------|---------|
| [Core & Defaults](#-core--defaults) | 4 methods | Connection, defaults management |
| [Symbols & Quotes](#-symbols--quotes) | 8 methods | Symbol info, quotes, prices |
| [Market Data](#-market-data) | 3 methods | Bars, ticks, price waiting |
| [Order Placement](#-order-placement) | 6 methods | Market and pending orders |
| [Order Management](#-order-management) | 5 methods | Modify, close, partial close |
| [Math & Risk](#-math--risk) | 8 methods | Lot sizing, risk calculation, conversions |
| [Automation](#-automation) | 2 methods | Trailing stops, auto-breakeven |

**Total: 36 sugar methods** to cover all your trading needs!

---

## 🔌 Core & Defaults

**[→ Full Documentation](Core_Defaults.md)**

Foundation methods for connection and configuration management.

### Methods Overview

| Method | Purpose | Use Case |
|--------|---------|----------|
| `ensure_connected()` | Auto-reconnect if lost | Before market operations |
| `ping()` | Health check | Monitoring loops |
| `get_default(key)` | Read stored default | Logic/logging |
| `set_defaults(...)` | Configure defaults | Setup phase |

### Quick Example

```python
# Set defaults once
sugar.set_defaults(
    symbol="EURUSD",
    magic=1001,
    deviation_pips=3
)

# Use everywhere without repeating
await sugar.buy_market(lots=0.1)  # Uses EURUSD, magic=1001
```

### When to use
✅ Start of every script - set defaults
✅ Before long operations - ensure connection
✅ Monitoring systems - ping for health checks

---

## 📈 Symbols & Quotes

**[→ Full Documentation](Symbols_Quotes.md)**

Get symbol information and current market prices.

### Methods Overview

| Method | Returns | Use Case |
|--------|---------|----------|
| `digits(symbol)` | Decimal places | Price formatting |
| `point(symbol)` | Minimum tick | Normalization |
| `pip_size(symbol)` | Pip value | Pip calculations |
| `ensure_symbol(symbol)` | None | Before trading |
| `last_quote(symbol)` | Quote object | Current price |
| `mid_price(symbol)` | Float | Fair price |
| `spread_pips(symbol)` | Float | Cost check |
| `spread_points(symbol)` | Int | Raw spread |

### Quick Example

```python
# Check spread before trading
spread = await sugar.spread_pips("EURUSD")
if spread < 2.0:
    await sugar.buy_market("EURUSD", 0.1)

# Get current prices
quote = await sugar.last_quote("EURUSD")
print(f"Bid: {quote.bid}, Ask: {quote.ask}")
```

### When to use
✅ Before order placement - check spread
✅ Symbol validation - ensure symbol exists
✅ Price formatting - use digits/point
✅ Analytics - mid_price for fair value

---

## 📊 Market Data

**[→ Full Documentation](Market_Data.md)**

Historical data and price monitoring.

### Methods Overview

| Method | Returns | Use Case |
|--------|---------|----------|
| `bars(symbol, tf, count)` | OHLC bars | Technical analysis |
| `ticks(symbol, limit)` | Tick data | HFT, custom bars |
| `wait_price(symbol, target)` | Boolean | Price alerts |

### Quick Example

```python
# Get last 100 H1 bars
bars = await sugar.bars("EURUSD", timeframe="H1", count=100)
closes = [b.close for b in bars]

# Wait for price to reach level
reached = await sugar.wait_price("EURUSD", target=1.1000, direction=">=", timeout_s=60)
if reached:
    await sugar.sell_market("EURUSD", 0.1)
```

### When to use
✅ Indicators - calculate from bars
✅ Backtesting - historical data analysis
✅ Price alerts - wait for specific levels
✅ HFT strategies - tick-level data

---

## 🎯 Order Placement

**[→ Full Documentation](Order_Placement.md)**

Open market and pending orders.

### Methods Overview

| Method | Order Type | Use Case |
|--------|------------|----------|
| `buy_market(...)` | Market BUY | Immediate long entry |
| `sell_market(...)` | Market SELL | Immediate short entry |
| `buy_limit(...)` | Pending BUY LIMIT | Buy below market |
| `sell_limit(...)` | Pending SELL LIMIT | Sell above market |
| `buy_stop(...)` | Pending BUY STOP | Breakout long |
| `sell_stop(...)` | Pending SELL STOP | Breakout short |

### Quick Example

```python
# Market order with SL/TP in pips
ticket = await sugar.buy_market(
    symbol="EURUSD",
    lots=0.1,
    sl_pips=20,
    tp_pips=40,
    comment="Scalp trade"
)

# Pending order at specific price
ticket = await sugar.buy_limit(
    symbol="EURUSD",
    lots=0.1,
    price=1.0950,
    sl_pips=15,
    tp_pips=30
)
```

### When to use
✅ Strategy entries - market/pending orders
✅ Quick trades - minimal parameters
✅ SL/TP in pips - easy risk management
✅ Comments - track trade reasons

---

## ✏️ Order Management

**[→ Full Documentation](Order_Management.md)**

Modify and close existing positions.

### Methods Overview

| Method | Action | Use Case |
|--------|--------|----------|
| `modify_sl_tp_by_pips(...)` | Modify by pips | Adjust protection |
| `modify_sl_tp_by_price(...)` | Modify by price | Exact levels |
| `close(ticket)` | Close position | Exit trade |
| `close_partial(ticket, lots)` | Partial close | Scale out |
| `close_all(symbol, magic)` | Close multiple | Emergency exit |

### Quick Example

```python
# Move SL to breakeven
await sugar.modify_sl_tp_by_pips(ticket=123456, sl_pips=0)

# Tighten SL by price
await sugar.modify_sl_tp_by_price(ticket=123456, sl_price=1.0985)

# Partial close - take 50% profit
await sugar.close_partial(ticket=123456, lots=0.05)

# Close all EURUSD positions
await sugar.close_all(symbol="EURUSD")
```

### When to use
✅ Trailing stops - manual or automated
✅ Scaling out - partial closes
✅ Emergency exits - close_all
✅ Breakeven moves - modify SL

---

## 🧮 Math & Risk

**[→ Full Documentation](Math_Risk.md)**

Position sizing, risk calculation, and conversions.

### Methods Overview

| Method | Returns | Use Case |
|--------|---------|----------|
| `calc_lot_by_risk(symbol, stop_pips, risk_pct)` | Float | Position sizing |
| `calc_cash_risk(symbol, lots, stop_pips)` | Float | Risk calculation |
| `pips_to_price(symbol, pips, direction)` | Float | Convert pips→price |
| `price_to_pips(symbol, price1, price2)` | Float | Convert price→pips |
| `normalize_price(symbol, price)` | Float | Round to tick |
| `normalize_lots(symbol, lots)` | Float | Valid lot size |
| `breakeven_price(entry, commission, swap)` | Float | Breakeven level |
| `auto_breakeven(ticket, trigger_pips)` | None | Auto SL move |

### Quick Example

```python
# Calculate lot size for 2% risk
lots = await sugar.calc_lot_by_risk(
    symbol="EURUSD",
    stop_pips=20,
    risk_percent=2.0
)
print(f"Trade {lots} lots for 2% risk")

# Convert 20 pips to price distance
price_dist = await sugar.pips_to_price("EURUSD", pips=20, direction="buy")

# Auto-move to breakeven after 15 pips profit
await sugar.auto_breakeven(ticket=123456, trigger_pips=15, plus_pips=1.0)
```

### When to use
✅ Every trade - calculate proper lot size
✅ Risk management - validate exposure
✅ Price conversions - pip↔price
✅ Normalization - ensure valid values
✅ Automation - auto-breakeven

---

## 🤖 Automation

**[→ Full Documentation](Automation.md)**

Automated trade management.

### Methods Overview

| Method | Action | Use Case |
|--------|--------|----------|
| `set_trailing_stop(ticket, distance_pips)` | Start trailing | Let winners run |
| `unset_trailing_stop(subscription_id)` | Stop trailing | Pause automation |

### Quick Example

```python
# Open position
ticket = await sugar.buy_market("EURUSD", 0.1, sl_pips=20)

# Enable trailing stop - 15 pips behind price
trail_id = await sugar.set_trailing_stop(
    ticket=ticket,
    distance_pips=15,
    step_pips=2  # Update every 2 pips
)

# Later: disable trailing
await sugar.unset_trailing_stop(trail_id)
```

### When to use
✅ Trend following - trail behind price
✅ Breakouts - protect running profits
✅ Hands-free trading - automated management

---

## 🚀 Getting Started

### 1. Import and Initialize

```python
from pymt4 import MT4Account
from pymt4.sugar import Sugar

# Connect to MT4
api = MT4Account(host="localhost", port=15555)
await api.connect()

# Create sugar instance
sugar = Sugar(api)
```

### 2. Set Defaults

```python
# Configure once, use everywhere
sugar.set_defaults(
    symbol="EURUSD",
    magic=1001,
    deviation_pips=3,
    risk_percent=2.0
)
```

### 3. Start Trading

```python
# Simple market order
ticket = await sugar.buy_market(lots=0.1, sl_pips=20, tp_pips=40)

# Check spread first
spread = await sugar.spread_pips()
if spread < 2.0:
    # Calculate lot size by risk
    lots = await sugar.calc_lot_by_risk(stop_pips=20, risk_percent=2.0)
    ticket = await sugar.buy_market(lots=lots, sl_pips=20)
```

---

## 📖 Complete Method Index

### Core (4 methods)
- `ensure_connected()` - Auto-reconnect
- `ping()` - Health check
- `get_default(key)` - Read default
- `set_defaults(...)` - Configure defaults

### Symbols & Quotes (8 methods)
- `digits(symbol)` - Decimal places
- `point(symbol)` - Minimum tick
- `pip_size(symbol)` - Pip value
- `ensure_symbol(symbol)` - Enable symbol
- `last_quote(symbol)` - Current quote
- `mid_price(symbol)` - Mid price
- `spread_pips(symbol)` - Spread in pips
- `spread_points(symbol)` - Spread in points

### Market Data (3 methods)
- `bars(symbol, tf, count)` - OHLC data
- `ticks(symbol, limit)` - Tick data
- `wait_price(symbol, target)` - Price alert

### Order Placement (6 methods)
- `buy_market(...)` - Market BUY
- `sell_market(...)` - Market SELL
- `buy_limit(...)` - Pending BUY LIMIT
- `sell_limit(...)` - Pending SELL LIMIT
- `buy_stop(...)` - Pending BUY STOP
- `sell_stop(...)` - Pending SELL STOP

### Order Management (5 methods)
- `modify_sl_tp_by_pips(...)` - Modify by pips
- `modify_sl_tp_by_price(...)` - Modify by price
- `close(ticket)` - Close position
- `close_partial(ticket, lots)` - Partial close
- `close_all(symbol, magic)` - Close multiple

### Math & Risk (8 methods)
- `calc_lot_by_risk(...)` - Position sizing
- `calc_cash_risk(...)` - Risk calculation
- `pips_to_price(...)` - Pips→Price
- `price_to_pips(...)` - Price→Pips
- `normalize_price(...)` - Round price
- `normalize_lots(...)` - Valid lots
- `breakeven_price(...)` - Breakeven calc
- `auto_breakeven(...)` - Auto SL move

### Automation (2 methods)
- `set_trailing_stop(...)` - Enable trailing
- `unset_trailing_stop(...)` - Disable trailing

---

## 💡 Best Practices

### 1. Always Set Defaults
```python
# Do this at startup
sugar.set_defaults(symbol="EURUSD", magic=1001)
```

### 2. Check Spread Before Trading
```python
spread = await sugar.spread_pips()
if spread > MAX_SPREAD:
    return  # Skip trade
```

### 3. Calculate Lot Size by Risk
```python
lots = await sugar.calc_lot_by_risk(stop_pips=20, risk_percent=2.0)
```

### 4. Normalize Everything
```python
price = sugar.normalize_price("EURUSD", 1.095678)  # → 1.09568
lots = sugar.normalize_lots("EURUSD", 0.123)       # → 0.12
```

### 5. Use Context Overrides for Multi-Symbol
```python
# Default: EURUSD
sugar.set_defaults(symbol="EURUSD")

# Trade other symbol temporarily
with sugar.with_defaults(symbol="GBPUSD"):
    await sugar.buy_market(lots=0.1)
```

---

## 🎓 Learning Path

### Beginner
1. Read [Core & Defaults](Core_Defaults.md) - Setup
2. Study [Order Placement](Order_Placement.md) - Basic trades
3. Practice [Order Management](Order_Management.md) - Modify/close

### Intermediate
4. Master [Math & Risk](Math_Risk.md) - Position sizing
5. Explore [Symbols & Quotes](Symbols_Quotes.md) - Market info
6. Learn [Market Data](Market_Data.md) - Historical data

### Advanced
7. Implement [Automation](Automation.md) - Trailing stops
8. Combine with [Orchestrators](../Strategy/All_about_orchestrator.md)
9. Use [Presets](../Strategy/All_about_presets.md) for scaling

---

## 🔗 Related Documentation

### Getting Started
- [Main Demo Scripts](../Main/Overview.md) - Runnable examples
- [Examples Guide](../Examples/All_about_examples.md) - Complete examples

### Advanced Topics
- [Low-Level API](../MT4Account/BASE.md) - Raw RPC methods
- [Orchestrators](../Strategy/All_about_orchestrator.md) - Trading workflows
- [Presets](../Strategy/All_about_presets.md) - Risk configurations

### Reference
- [Architecture](../ARCHITECTURE.md) - How it works
- [Glossary](../GLOSSARY.md) - All terms explained
- [Project Map](../PROJECT_MAP.md) - Project structure

---

## 🆘 Need Help?

- 🐛 [Report Issues](https://github.com/MetaRPC/PyMT4/issues)
- 💬 [Discussions](https://github.com/MetaRPC/PyMT4/discussions)
- 📧 [Contact Support](mailto:support@metarpc.com)

---

**Happy Trading with Sugar!** 🍬📈
