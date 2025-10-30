# 📚 MT4 API Examples

Examples demonstrating PyMT4 usage across four levels of abstraction.

## 🎬 Demo Files

### 1. 🔧 **Low_level_call.py** - Low-Level API (19 methods)
Direct gRPC calls without wrappers, maximum control.

```bash
python examples/Low_level_call.py
```

**Demonstrates:**
- 🔌 Connection (2 methods): `connect_by_server_name()`, `connect_by_host_port()`
- 👤 Account (1 method): `account_summary()`
- 📊 Market Data (6 methods): `symbols()`, `quote()`, `quote_many()`, `quote_history()`, etc.
- 📋 Orders (3 methods): `opened_orders()`, `orders_history()`, etc.
- 💼 Trading (4 methods): `order_send()`, `order_modify()`, `order_close_delete()`, `order_close_by()`
- 🌊 Streaming (4 methods): `on_symbol_tick()`, `on_trade()`, `on_opened_orders_tickets()`, etc.

**Features:**
- ⏱️ Enforced timeouts for streams (freezing issue resolved)
- 🎯 3-priority connection system
- 🔒 Trading disabled by default (`ENABLE_TRADING=0`)

---

### 2. 🍬 **Call_sugar.py** - Sugar API (~20 methods)
High-level wrappers with convenient interface and pip-based operations.

```bash
python examples/Call_sugar.py
```

**Demonstrates:**
- 🔌 Connection: `ensure_connected()`, `ping()`
- 📐 Symbol Info: `digits()`, `point()`, `pip_size()`, `spread_pips()`, `mid_price()`
- 🎲 Risk Management: `calc_lot_by_risk()`, `calc_cash_risk()`
- 📊 Exposure: `exposure_summary()`, `opened_orders()`
- 💰 Trading: `buy_market()`, `sell_market()`, `buy_limit()`, `sell_stop()`
- ⚙️ Order Management: `modify_sl_tp_by_pips()`, `close()`, `close_partial()`

**Features:**
- 📏 All SL/TP specified in pips
- 🤖 Automatic lot calculation based on risk
- 🛠️ Convenient price helpers

---

### 3. 🎭 **Orchestrator_demo.py** - Strategy Orchestrators
Modular trading scenarios with presets and guards.

```bash
python examples/Orchestrator_demo.py
```

**Demonstrates 4 orchestrators:**

#### 1. 🎯 `market_one_shot` - Market order with automation
```python
from Strategy.presets import MarketEURUSD, Balanced
from Strategy.orchestrator.market_one_shot import run_market_one_shot

result = await run_market_one_shot(svc, MarketEURUSD, Balanced)
# Opens market order + trailing stop + auto-breakeven
```

#### 2. ⏰ `pending_bracket` - Pending order with timeout
```python
from Strategy.presets import LimitEURUSD, Conservative
from Strategy.orchestrator.pending_bracket import run_pending_bracket

strategy = LimitEURUSD(price=1.0850)
result = await run_pending_bracket(svc, strategy, Conservative, timeout_s=900)
# Waits for execution, cancels if not triggered
```

#### 3. 📊 `spread_guard` - Spread filter
```python
from Strategy.orchestrator.spread_guard import market_with_spread_guard

result = await market_with_spread_guard(
    svc, strategy, risk,
    max_spread_pips=1.5  # Trades only if spread <= 1.5 pips
)
```

#### 4. 🕐 `session_guard` - Trading windows
```python
from Strategy.orchestrator.session_guard import run_with_session_guard

windows = [('08:00', '11:30'), ('13:00', '17:00')]
result = await run_with_session_guard(
    svc=svc,
    runner_coro_factory=lambda: run_market_one_shot(svc, strategy, risk),
    windows=windows,
    tz='Europe/London',
    weekdays=[0,1,2,3,4]  # Mon-Fri
)
```

**Available presets:**

**📋 Strategy Presets:**
- `MarketEURUSD` - market order
- `LimitEURUSD(price)` - limit order
- `BreakoutBuy(symbol, offset_pips)` - level breakout

**🎲 Risk Presets:**
- `Conservative` - 0.5% risk, SL=25p, TP=50p
- `Balanced` - 1.0% risk, SL=20p, TP=40p
- `Aggressive` - 2.0% risk, SL=15p, TP=30p
- `Scalper` - 1.0% risk, SL=8p, TP=12p, trailing=6p
- `Walker` - 0.75% risk, SL=30p, TP=60p, breakeven=20p+2p

**🎭 Other orchestrators (available in code):**
- `oco_straddle` - two-way entry (OCO)
- `bracket_trailing_activation` - conditional trailing activation
- `equity_circuit_breaker` - emergency stop on drawdown
- `dynamic_deviation_guard` - adaptive deviation
- `rollover_avoidance` - swap time avoidance
- `grid_dca_common_sl` - grid with common SL

---

## 🚀 Running Examples

### Via appsettings.json (recommended)
```bash
python examples/Low_level_call.py
python examples/Call_sugar.py
python examples/Orchestrator_demo.py
```

Scripts automatically read `appsettings.json` from project root.

### Via environment variables (PowerShell)
```powershell
$env:MT4_LOGIN="12345678"
$env:MT4_PASSWORD="your_password"
$env:MT4_SERVER="MetaQuotes-Demo"
python examples/Low_level_call.py
```

### Enable real trading
```bash
export ENABLE_TRADING=1
python examples/Call_sugar.py
```

⚠️ **WARNING**: Trading is disabled by default (`ENABLE_TRADING=0`) - only syntax demonstration!

---

## 📊 Level Comparison

| Level | File | Components | Usage | Flexibility |
|---------|------|-------------|---------------|----------|
| **🔧 Low-Level** | `Low_level_call.py` | 19 methods | Direct gRPC calls | Maximum |
| **🍬 Sugar** | `Call_sugar.py` | ~20 methods | Convenient wrappers | High |
| **🎭 Orchestrator** | `Orchestrator_demo.py` | 4+ orchestrators | Ready scenarios | Modular |
| **⚙️ Presets** | `Presets_demo.py` | 40+ presets | Configurations | Composition |

---

### 4. ⚙️ **Presets_demo.py** - Reusable Configurations (40+ presets)
All available presets for strategies and risk management.

```bash
python examples/Presets_demo.py
```

**Demonstrates 5 preset categories:**

#### 1. 🎯 Basic Risk Presets (5 profiles)
```python
from Strategy.presets.risk import Conservative, Balanced, Aggressive, Scalper, Walker

result = await run_market_one_shot(svc, MarketEURUSD, Balanced)
```

#### 2. 📈 ATR-Based Risk (3 dynamic profiles)
```python
from Strategy.presets.risk_atr import ATR_Scalper, ATR_Balanced, ATR_Swing

risk = await ATR_Balanced(svc, "EURUSD", risk_percent=1.0)
# SL/TP automatically calculated from ATR (volatility)
```

#### 3. 🎲 Risk Profiles (8+ profiles)
```python
from Strategy.presets.risk_profiles import ScalperEURUSD, SwingXAUUSD

# Specialized for symbol and trading style
result = await run_market_one_shot(svc, MarketXAUUSD, SwingXAUUSD())
```

#### 4. 🕐 Session-Based Risk (4 sessions)
```python
from Strategy.presets.risk_session import session_risk_auto

# Automatic selection by current session
risk = await session_risk_auto(svc, "EURUSD", tz="Europe/London")
# Asia / London / NewYork / Overlap
```

#### 5. 💱 Strategy Symbol Presets (30+ symbols)
```python
from Strategy.presets.strategy_symbols import (
    MarketEURUSD, MarketXAUUSD, MarketBTCUSD,
    LimitGBPUSD, BreakoutEURUSD
)

# Symbols: Forex, Metals, Indices, Crypto
# Types: Market, Limit, Breakout
```

**All presets:**
- 💱 Forex: EURUSD, GBPUSD, USDJPY
- 🥇 Metals: XAUUSD, XAGUSD
- 📊 Indices: US100, US500, GER40
- ₿ Crypto: BTCUSD

---

## 📁 examples/ Structure

```
examples/
├── Low_level_call.py          # Low-level API demo (19 methods)
├── Call_sugar.py              # Sugar API demo (~20 methods)
├── Orchestrator_demo.py       # Orchestrators demo (4 orchestrators)
├── Presets_demo.py            # Presets demo (40+ presets)
├── .env.example               # Environment variables template
└── README.md                  # This file
```

---

## 🔧 Environment Variables

| Variable | Required | Default | Description |
|------------|-------------|--------------|----------|
| `MT4_LOGIN` | ✓* | - | MT4 login |
| `MT4_PASSWORD` | ✓* | - | MT4 password |
| `MT4_SERVER` | ✗ | MetaQuotes-Demo | Server name |
| `MT4_HOST` | ✗ | - | Host for direct connection |
| `MT4_PORT` | ✗ | 443 | Port |
| `BASE_SYMBOL` | ✗ | EURUSD | Base symbol |
| `SYMBOL` | ✗ | EURUSD | Test symbol |
| `ENABLE_TRADING` | ✗ | 0 | Enable trading (1=yes) |
| `CONNECT_TIMEOUT` | ✗ | 30 | Connection timeout |

*if not set in `appsettings.json`

---

## 🔧 Troubleshooting

### 🔴 Connection error
1. Check `appsettings.json` - must have `access` list with host:port
2. Verify login/password
3. Check server name (`MT4_SERVER`)

### ⏸️ Stream freezing
Fixed in `Low_level_call.py` - enforced timeouts added (1 sec).

### 📦 Import error
Make sure you run from project root:
```bash
cd /path/to/PyMT4
python examples/Low_level_call.py
```

---

## 📖 Additional Resources

- [MT4Sugar Documentation](../app/MT4Sugar.py)
- [Strategy Orchestrators](../Strategy/orchestrator/)
- [Strategy Presets](../Strategy/presets/)
