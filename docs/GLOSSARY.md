# 📖 Glossary — PyMT4 Trading Terms

*Your quick reference for trading terminology, PyMT4 concepts, and SDK-specific terms.*

---

## 🎯 Quick Cheat Sheet

| Term | Example | Meaning |
|------|---------|---------|
| **Symbol** | `EURUSD`, `XAUUSD`, `BTCUSD` | Trading instrument identifier (currency pair, metal, index, crypto). |
| **Lot** | `1.00` → 100,000 units | Standard trade size. 0.01 = micro lot (1,000 units). |
| **Volume** | `0.10`, `2.50` | Lots to trade (can be fractional). |
| **Pips** | `20 pips` = 0.0020 for EURUSD | Common distance unit. Sugar API uses pips for SL/TP. |
| **Point** | `0.00001` (EURUSD 5-digit) | Smallest price step for the symbol. |
| **Digits** | `5` | Quote precision; e.g., 1.23456 for 5 digits. |
| **Bid** | `1.10000` | Price to SELL at (what broker pays you). |
| **Ask** | `1.10020` | Price to BUY at (what you pay broker). |
| **Spread** | `2 pips` = Ask - Bid | Cost per trade (broker commission). |
| **SL** | `1.09800` or `20 pips` | Stop Loss — protective exit level. |
| **TP** | `1.10400` or `40 pips` | Take Profit — target exit level. |
| **Ticket** | `12345678` | Unique order/position ID (int64). |
| **Magic** | `771` | Order identifier (organize by strategy). Range: 771-859. |
| **Deviation** | `5 pips` | Allowed slippage (price can move this much). |
| **Slippage** | `3 pips` | Actual price difference from requested. |
| **Margin** | `100.00` | Funds locked for open position. |
| **Equity** | `1000.00` | Balance ± floating P/L. |
| **Free Margin** | `900.00` | Equity − Margin (available for new trades). |
| **Balance** | `950.00` | Account balance (realized P/L only). |
| **Profit** | `+50.00` | Current position P/L (unrealized). |
| **Leverage** | `1:500` | Borrowed funds ratio (500x buying power). |
| **Retcode** | `10009`, `TRADE_RETCODE_DONE` | Trade server return code (success/error). |
| **Enum** | `ORDER_TYPE_BUY`, `ORDER_TYPE_SELL` | Strongly-typed constants (no magic numbers). |
| **Stream** | `on_symbol_tick()`, `on_trade()` | Long-lived server push (events until cancelled). |
| **Cancellation** | `asyncio.Event()` | Cooperative stop signal for streams. |
| **Deadline** | `now() + 3s` | Per-call timeout → turned into gRPC timeout. |

---

## 📊 Trading Concepts

### Order Types

| Type | Symbol | Description | Use Case |
|------|--------|-------------|----------|
| **Market Order** | 🚀 | Execute immediately at current price | Fast entry, breakout trading |
| **Limit Order** | ⏰ | Execute at specific price or better | Buy dips, sell rallies, better fill |
| **Stop Order** | 🧨 | Execute when price reaches trigger | Breakout entries, stop-out protection |
| **Pending Order** | ⏸️ | Placed but not yet filled | Limit + Stop orders |

### Position States

| State | Description |
|-------|-------------|
| **Open** | Active position, accumulating P/L |
| **Pending** | Order placed but not filled yet |
| **Closed** | Position closed, P/L realized |
| **Cancelled** | Pending order cancelled before fill |

### Risk Management Terms

| Term | Example | Description |
|------|---------|-------------|
| **Risk %** | `1.0%` | Percentage of equity to risk per trade |
| **Risk:Reward (R:R)** | `1:2` | Ratio of SL distance to TP distance |
| **Lot Sizing** | `calc_lot_by_risk()` | Calculate lot based on risk % and SL distance |
| **Breakeven** | Move SL to entry price | Lock in zero loss |
| **Trailing Stop** | SL follows price | Protect profits as price moves favorably |
| **Circuit Breaker** | Emergency stop | Close all on equity drop threshold |

---

## 🎭 PyMT4 Specific Terms

### Architecture Layers

| Layer | Description | Example |
|-------|-------------|---------|
| **Orchestrator** | Complete trading workflow | `market_one_shot`, `pending_bracket` |
| **Preset** | Reusable configuration | `Balanced`, `MarketEURUSD` |
| **Sugar API** | High-level convenience methods | `buy_market()`, `modify_sl_tp_by_pips()` |
| **Service Layer** | Connection management, hooks | `MT4Service`, `MT4Service_Trade_mod` |
| **SDK (Low-level)** | Direct gRPC wrappers | `MT4Account.order_send()` |

### Strategy Components

| Component | File | Description |
|-----------|------|-------------|
| **StrategyPreset** | `strategy_symbols.py` | WHAT to trade (symbol, entry type, magic) |
| **RiskPreset** | `risk.py` | HOW MUCH to risk (%, SL, TP, trailing) |
| **Orchestrator** | `orchestrator/*.py` | Complete trading scenario (guards, automation) |

### Key Classes

| Class | Purpose | Location |
|-------|---------|----------|
| **MT4Service** | Core service wrapper | `app/MT4Service.py` |
| **MT4Service_Trade_mod** | Trading operations wrapper | `app/MT4Service_Trade_mod.py` |
| **MT4Sugar** | High-level API | `app/MT4Sugar.py` |
| **MT4Account** | Low-level SDK | `package/MetaRpcMT4/mt4_account.py` |
| **HookManager** | Event hooks system | `app/Helper/hooks.py` |
| **RateLimiter** | API rate limiting | `app/Helper/rate_limit.py` |

---

## 🍬 Sugar API Concepts

### Pip-Based Operations

Sugar API uses **pips** as the universal unit:

```python
# Instead of calculating prices:
await sugar.buy_market("EURUSD", lots=0.1, sl_pips=20, tp_pips=40)

# Sugar converts:
# 20 pips → 0.0020 (for 5-digit EURUSD)
# Sets SL at: current_price - 0.0020
# Sets TP at: current_price + 0.0040
```

### Auto Lot Calculation

```python
# Calculate lot by risk percentage
lot = await sugar.calc_lot_by_risk(
    symbol="EURUSD",
    risk_percent=1.0,    # Risk 1% of equity
    stop_pips=20         # If SL is 20 pips away
)
# Returns: 0.15 (if equity=1000, 1% = $10, 20 pips = 0.15 lot)
```

### Symbol Info Caching

Sugar API caches symbol info automatically:

```python
# First call: fetches from server
digits = await sugar.digits("EURUSD")  # → 5

# Subsequent calls: cached
digits = await sugar.digits("EURUSD")  # → 5 (instant)
```

---

## 🎭 Orchestrator Concepts

### Guards

Filters that block trades under certain conditions:

| Guard | Blocks when... | Example |
|-------|---------------|---------|
| **spread_guard** | Spread too wide | `max_spread_pips=2.0` |
| **session_guard** | Outside time windows | `windows=[('08:00', '17:00')]` |
| **deviation_guard** | Slippage too high | `max_deviation_pips=5.0` |
| **equity_circuit_breaker** | Equity drop threshold | `max_drawdown_percent=5.0` |
| **rollover_avoidance** | Near swap time | `avoid_minutes=30` |

### Automation Features

| Feature | Description | Trigger |
|---------|-------------|---------|
| **Trailing Stop** | SL follows price | Price moves favorably by `distance_pips` |
| **Auto Breakeven** | Move SL to entry | Profit reaches `trigger_pips` |
| **Timeout** | Cancel pending order | Not filled within `timeout_s` seconds |
| **Kill Switch** | Emergency close all | Manual trigger or equity threshold |

---

## ⚙️ Preset Concepts

### Risk Preset Properties

| Property | Type | Description | Example |
|----------|------|-------------|---------|
| **risk_percent** | `float` | % of equity to risk | `1.0` = 1% |
| **sl_pips** | `float` | Stop loss distance | `20.0` |
| **tp_pips** | `float` | Take profit distance | `40.0` |
| **trailing_pips** | `float` | Trailing stop distance | `15.0` |
| **be_trigger_pips** | `float` | Profit to trigger BE | `20.0` |
| **be_plus_pips** | `float` | Extra pips above BE | `2.0` |

### Strategy Preset Properties

| Property | Type | Description | Example |
|----------|------|-------------|---------|
| **symbol** | `str` | Trading instrument | `"EURUSD"` |
| **magic** | `int` | Order identifier | `771` |
| **deviation_pips** | `float` | Slippage tolerance | `2.5` |
| **entry_type** | `str` | Order type | `"market"`, `"limit"`, `"stop"` |
| **entry_price** | `float` | Price for pending orders | `1.0850` |
| **comment** | `str` | Order comment | `"Scalp EUR"` |

---

## 🔧 Technical Terms

### gRPC Concepts

| Term | Description |
|------|-------------|
| **Stub** | Client-side interface to remote service |
| **Request** | Protobuf message sent to server |
| **Reply** | Protobuf message returned from server |
| **Metadata** | Headers sent with request (login, session) |
| **Timeout** | Max time to wait for response |
| **Deadline** | Absolute time when request expires |
| **Stream** | Long-lived channel for continuous data |

### MT4 Server Concepts

| Term | Description |
|------|-------------|
| **Access** | List of host:port addresses |
| **Server Name** | Broker server identifier (e.g., "MetaQuotes-Demo") |
| **Login** | Account number |
| **Password** | Account password |
| **Session** | Active connection state |

### Error Handling

| Term | Description |
|------|-------------|
| **Retcode** | Server return code (10009 = success) |
| **Retry** | Automatic re-attempt on failure |
| **Backoff** | Delay between retries (exponential) |
| **Cancellation** | Manual stop of operation/stream |
| **Timeout** | Operation exceeded deadline |

---

## 📈 Market Terms

### Volatility

| Term | Description |
|------|-------------|
| **ATR** | Average True Range — volatility indicator |
| **Spread Widening** | Spread increases (news, rollover) |
| **Slippage** | Price difference from requested |
| **Gap** | Large price jump (weekend, news) |

### Sessions

| Session | Time (GMT) | Characteristics |
|---------|------------|-----------------|
| **Tokyo** | 00:00-08:00 | Low volatility, range-bound |
| **London** | 07:00-16:30 | High liquidity, major moves |
| **New York** | 12:00-21:00 | Highest volume, trending |
| **Overlap** | 12:00-16:30 | London+NY, max volatility |

### Order Flow

| Term | Description |
|------|-------------|
| **Fill** | Order executed |
| **Partial Fill** | Only part of volume executed |
| **Reject** | Order refused by server |
| **Requote** | Price changed, confirm new price |
| **Off Quotes** | No price available (market closed) |

---

## 🛡️ Safety Terms

### Risk Controls

| Control | Description | Example |
|---------|-------------|---------|
| **Max Lot** | Maximum position size | `symbol_params.lot_max` |
| **Min Lot** | Minimum position size | `symbol_params.lot_min` |
| **Lot Step** | Lot size increment | `0.01` (micro lots) |
| **Max Spread** | Spread threshold | `2.0 pips` |
| **Max Deviation** | Slippage threshold | `5.0 pips` |
| **Stop Level** | Min distance for SL/TP | `10.0 pips` |
| **Freeze Level** | No modify near market | `5.0 pips` |

### Trade Restrictions

| Restriction | Description |
|-------------|-------------|
| **Market Closed** | No trading outside hours |
| **Trading Disabled** | Symbol not tradeable |
| **Long Only** | Can't open short positions |
| **Close Only** | Can only close existing |
| **Margin Call** | Insufficient margin |
| **Stop Out** | Forced position close |

---

## 🔍 Debugging Terms

| Term | Description |
|------|-------------|
| **Verbose Logging** | Detailed operation logs |
| **gRPC Debug** | Log all RPC calls |
| **Dry Run** | Test without real trading (`ENABLE_TRADING=0`) |
| **Ping** | Connection health check |
| **Introspection** | Examine object/method details |

---

## 📚 Related Documentation

* **[PROJECT_MAP.md](./PROJECT_MAP.md)** — Project structure guide
* **[ARCHITECTURE.md](./ARCHITECTURE.md)** — System architecture
* **[MT4Account BASE](./MT4Account/BASE.md)** — Low-level API overview
* **[MT4Sugar API](./MT4Sugar/)** — High-level API docs
* **[Orchestrators](./Strategy/All_about_orchestrator.md)** — Trading workflows
* **[Presets](./Strategy/All_about_presets.md)** — Configuration presets

---

## 💡 Quick Tips

### Converting Between Units

```python
# Pips to price
price_delta = pips * pip_size
# Example: 20 pips * 0.0001 = 0.0020

# Price to pips
pips = price_delta / pip_size
# Example: 0.0020 / 0.0001 = 20 pips

# Risk to lot
lot = (equity * risk_percent / 100) / (sl_pips * pip_value)
# Example: (1000 * 1.0 / 100) / (20 * 0.10) = 0.50 lot
```

### Common Conversions

| From | To | Formula |
|------|----|---------|
| **Lot → Units** | 1.0 lot = 100,000 units | `lot * 100000` |
| **Pips → Price (EURUSD)** | 20 pips = 0.0020 | `pips * 0.0001` |
| **Spread → Cost** | 2 pip spread, 1 lot | `2 * pip_value * lot` |
| **% Risk → $Risk** | 1% of $1000 | `1000 * 0.01 = $10` |

---

"May your spreads be tight, your fills be clean, and your equity grow steadily. 📖"
