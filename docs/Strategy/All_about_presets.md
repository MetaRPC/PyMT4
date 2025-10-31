# ⚙️ Strategy Presets Guide

**What is a Preset?**
A preset is a **pre-configured trading parameter set** that you can use instantly without manual setup. It's like a "trading profile" button — click it, and all your risk, symbol, and strategy settings are ready to go.

Think of presets as **LEGO blocks** — combine Strategy + Risk presets to build any trading scenario.

---

## 🎯 Two Main Types of Presets

### 📋 **Strategy Presets** (WHAT to trade)
Defines **what** you're trading and **how** to enter:
- Symbol (EURUSD, XAUUSD, BTCUSD...)
- Entry type (Market, Limit, Breakout)
- Magic number (for order organization)
- Deviation/slippage tolerance

### 🎲 **Risk Presets** (HOW MUCH to risk)
Defines **how much** to risk and **where** to place stops:
- Risk percent (0.5%, 1.0%, 2.0%...)
- Stop Loss distance (pips)
- Take Profit distance (pips)
- Trailing stop, Auto-breakeven

---

## 🧩 Quick Combination Example

```python
from Strategy.presets import MarketEURUSD, Balanced
from Strategy.orchestrator.market_one_shot import run_market_one_shot

# MarketEURUSD = WHAT to trade (EUR/USD, market entry)
# Balanced = HOW MUCH to risk (1% risk, SL=20, TP=40)

result = await run_market_one_shot(svc, MarketEURUSD, Balanced)
```

**Result:** Market buy on EURUSD with 1% risk, 20 pip SL, 40 pip TP ✅

---

## 📚 Available Preset Categories

| Category | File | Presets | Purpose |
|----------|------|---------|---------|
| **🎯 Basic Risk** | `risk.py` | 5 profiles | Fixed pip-based risk (Conservative, Balanced, Aggressive, Scalper, Walker) |
| **📈 ATR Risk** | `risk_atr.py` | 3 dynamic | Volatility-adaptive risk (ATR_Scalper, ATR_Balanced, ATR_Swing) |
| **🎲 Risk Profiles** | `risk_profiles.py` | 8+ combos | Symbol+style combinations (ScalperEURUSD, SwingXAUUSD...) |
| **🕐 Session Risk** | `risk_session.py` | 4 sessions | Time-based risk (Asia, London, NewYork, Overlap) |
| **💱 Symbol Strategies** | `strategy_symbols.py` | 30+ symbols | Pre-configured symbols (MarketEURUSD, LimitXAUUSD...) |

---

## 🎯 Basic Risk Presets (risk.py)

Fixed pip-based risk profiles — the foundation of risk management.

| Preset | Risk % | SL (pips) | TP (pips) | R:R | Best For |
|--------|--------|-----------|-----------|-----|----------|
| **Conservative** | 0.5% | 25 | 50 | 1:2 | Safe trading, large accounts |
| **Balanced** | 1.0% | 20 | 40 | 1:2 | Standard, general use |
| **Aggressive** | 2.0% | 15 | 30 | 1:2 | Experienced traders |
| **Scalper** | 1.0% | 8 | 12 | 1:1.5 | Quick in/out, tight stops + trailing |
| **Walker** | 0.75% | 30 | 60 | 1:2 | Patient, auto-breakeven at 20+2 pips |

### Usage:
```python
from Strategy.presets import Conservative, Balanced, Aggressive, Scalper, Walker

# Mix with any strategy
await run_market_one_shot(svc, MarketEURUSD, Conservative)  # Safe
await run_market_one_shot(svc, MarketEURUSD, Balanced)      # Standard
await run_market_one_shot(svc, MarketEURUSD, Aggressive)    # Risky
await run_market_one_shot(svc, MarketEURUSD, Scalper)       # Fast trading
await run_market_one_shot(svc, MarketEURUSD, Walker)        # Patience + BE
```

**Related:** [risk.py](https://github.com/MetaRPC/PyMT4/blob/main/Strategy/presets/risk.py)

---

## 📈 ATR-Based Risk Presets (risk_atr.py)

**Dynamic risk that adapts to market volatility.**

### What is ATR?
**ATR (Average True Range)** = Volatility indicator measuring average price movement.
- Higher ATR = More volatile → Wider stops needed
- Lower ATR = Less volatile → Tighter stops possible

### Why Use ATR Risk?
✅ **Adaptive:** Stops adjust to current market conditions automatically
✅ **Smart:** Wider stops in volatile markets (avoid premature stop-outs)
✅ **Efficient:** Tighter stops in calm markets (better R:R)
✅ **Universal:** Works across all symbols and timeframes

### Example:
```
EUR/USD ATR = 8 pips (calm market)
→ SL = 1.5 × 8 = 12 pips ✓ (efficient)

EUR/USD ATR = 25 pips (volatile market)
→ SL = 1.5 × 25 = 37 pips ✓ (safe, won't get stopped out)
```

### Available Presets:

| Preset | ATR Mult | Min SL | Max SL | TP Ratio | Best For |
|--------|----------|--------|--------|----------|----------|
| **ATR_Scalper** | 1.0x | 6 | 15 | 1.5x | Short-term, tight adaptive stops |
| **ATR_Balanced** | 1.5x | 10 | 30 | 2.0x | Medium-term, standard volatility |
| **ATR_Swing** | 2.0x | 20 | 60 | 2.5x | Long-term, wide volatility buffer |

### Usage:
```python
from Strategy.presets.risk_atr import ATR_Scalper, ATR_Balanced, ATR_Swing

# Risk auto-calculates from current ATR
risk = await ATR_Balanced(svc, "EURUSD", risk_percent=1.0)
result = await run_market_one_shot(svc, MarketEURUSD, risk)
```

**Visual Flow:**
```
1. Fetch ATR(14) from market data
2. Calculate: SL = ATR × multiplier
3. Clamp to min/max range
4. Calculate: TP = SL × ratio
5. Return RiskPreset with calculated values
```

**Related:** [risk_atr.py](https://github.com/MetaRPC/PyMT4/blob/main/Strategy/presets/risk_atr.py)

---

## 🎲 Risk Profiles (risk_profiles.py)

**Pre-combined symbol + trading style risk configurations.**

Specialized risk profiles optimized for specific symbol/style combinations.

### Available Profiles:

| Profile | Symbol | Style | Risk % | SL | TP | Features |
|---------|--------|-------|--------|----|----|----------|
| **ScalperEURUSD** | EURUSD | Scalp | 1.0% | 8p | 12p | Tight + trailing 6p |
| **ScalperXAUUSD** | XAUUSD | Scalp | 0.75% | 15p | 22p | Gold scalp, wider |
| **DayTraderEURUSD** | EURUSD | Intraday | 1.0% | 20p | 40p | Standard day trade |
| **SwingEURUSD** | EURUSD | Swing | 0.5% | 40p | 100p | Patient, BE at 25p |
| **SwingXAUUSD** | XAUUSD | Swing | 0.5% | 60p | 150p | Gold swing, wide |
| **ConservativeXAUUSD** | XAUUSD | Safe | 0.3% | 50p | 100p | Very safe gold |

### Usage:
```python
from Strategy.presets.risk_profiles import ScalperEURUSD, SwingXAUUSD

# Symbol-specific optimized risk
await run_market_one_shot(svc, MarketEURUSD, ScalperEURUSD)
await run_market_one_shot(svc, MarketXAUUSD, SwingXAUUSD)
```

**Related:** [risk_profiles.py](https://github.com/MetaRPC/PyMT4/blob/main/Strategy/presets/risk_profiles.py)

---

## 🕐 Session-Based Risk (risk_session.py)

**Time-based risk that adapts to trading sessions.**

Different trading sessions have different characteristics:

| Session | Time (GMT) | Characteristics | Risk Approach |
|---------|------------|-----------------|---------------|
| **🇯🇵 Tokyo** | 00:00-08:00 | Low volatility, range-bound | Tighter stops, scalping |
| **🇬🇧 London** | 07:00-16:30 | High liquidity, major moves | Standard risk |
| **🇺🇸 New York** | 12:00-21:00 | Highest volume, trending | Wider stops, trend follow |
| **🌍 Overlap** | 12:00-16:30 | London+NY, max volatility | Conservative, wider stops |

### Available Functions:

```python
from Strategy.presets.risk_session import (
    session_risk_auto,  # Auto-detect current session
    tokyo_risk,         # Asian session
    london_risk,        # European session
    newyork_risk,       # American session
    overlap_risk        # High volatility period
)

# Auto-select based on current time
risk = await session_risk_auto(svc, "EURUSD", tz="Europe/London")

# Or specific session
risk = await london_risk(svc, "EURUSD", risk_percent=1.0)
```

**Example Auto-Selection:**
```
Current time: 08:30 GMT in London timezone
→ Detects: London session
→ Returns: Standard risk (SL=20, TP=40)

Current time: 14:00 GMT
→ Detects: Overlap (London + NY)
→ Returns: Conservative risk (SL=30, TP=60)
```

**Related:** [risk_session.py](https://github.com/MetaRPC/PyMT4/blob/main/Strategy/presets/risk_session.py)

---

## 💱 Symbol Strategy Presets (strategy_symbols.py)

**Pre-configured strategies for 30+ trading symbols.**

Each symbol has **3 entry type variants:**

### Entry Types:

| Type | Magic Range | Purpose | Example |
|------|-------------|---------|---------|
| **Market{Symbol}** | X01 | Instant market orders | `MarketEURUSD` |
| **Limit{Symbol}(price)** | X02 | Patient limit orders | `LimitEURUSD(1.0850)` |
| **Breakout{Symbol}** | X03 | Dynamic stop orders | `BreakoutEURUSD` |

### Symbol Coverage:

#### 💱 Forex Majors
```python
from Strategy.presets.strategy_symbols import (
    MarketEURUSD, LimitEURUSD, BreakoutEURUSD,  # Magic: 771-773
    MarketGBPUSD, LimitGBPUSD, BreakoutGBPUSD,  # Magic: 781-783
    MarketUSDJPY, LimitUSDJPY, BreakoutUSDJPY,  # Magic: 791-793
)
```

#### 🥇 Precious Metals
```python
from Strategy.presets.strategy_symbols import (
    MarketXAUUSD, LimitXAUUSD, BreakoutXAUUSD,  # Gold, Magic: 801-803
    MarketXAGUSD, LimitXAGUSD, BreakoutXAGUSD,  # Silver, Magic: 811-813
)
```

#### 📊 Indices
```python
from Strategy.presets.strategy_symbols import (
    MarketUS100, LimitUS100, BreakoutUS100,      # Nasdaq, Magic: 821-823
    MarketUS500, LimitUS500, BreakoutUS500,      # S&P 500, Magic: 831-833
    MarketGER40, LimitGER40, BreakoutGER40,      # DAX, Magic: 841-843
)
```

#### ₿ Crypto
```python
from Strategy.presets.strategy_symbols import (
    MarketBTCUSD, LimitBTCUSD, BreakoutBTCUSD,  # Bitcoin, Magic: 851-853
)
```

### Deviation Tuning by Volatility:

Different symbols need different slippage tolerance:

| Symbol Type | Deviation (pips) | Reason |
|-------------|------------------|--------|
| Forex Majors | 2.0-2.5 | Low-medium volatility |
| Precious Metals | 4.0-5.0 | High volatility |
| Indices | 6.0-12.0 | Very high volatility |
| Crypto | 20.0 | Extreme volatility |

### Usage Examples:

**Market Order:**
```python
from Strategy.presets import MarketXAUUSD, Balanced

# Instant gold trade
result = await run_market_one_shot(svc, MarketXAUUSD, Balanced)
```

**Limit Order:**
```python
from Strategy.presets import LimitEURUSD, Scalper

# Wait for specific price
strategy = LimitEURUSD(price=1.0850)
result = await run_pending_bracket(svc, strategy, Scalper, timeout_s=900)
```

**Multi-Symbol Portfolio:**
```python
from Strategy.presets import MarketEURUSD, MarketGBPUSD, MarketXAUUSD, Balanced

symbols = [MarketEURUSD, MarketGBPUSD, MarketXAUUSD]
for strategy in symbols:
    result = await run_market_one_shot(svc, strategy, Balanced)
```

**Related:** [strategy_symbols.py](https://github.com/MetaRPC/PyMT4/blob/main/Strategy/presets/strategy_symbols.py)

---

## 🎬 How to Use in Examples

All presets are demonstrated in [examples/Presets_demo.py](https://github.com/MetaRPC/PyMT4/blob/main/examples/Presets_demo.py):

```bash
python examples/Presets_demo.py
```

---

## 🧩 Mixing and Matching Presets

The power of presets is **flexibility** — mix any Strategy with any Risk:

```python
from Strategy.presets import (
    MarketEURUSD, MarketXAUUSD, LimitGBPUSD,
    Conservative, Balanced, Aggressive, Scalper
)

# Same strategy, different risk profiles
await run_market_one_shot(svc, MarketEURUSD, Conservative)  # 0.5% safe
await run_market_one_shot(svc, MarketEURUSD, Balanced)      # 1.0% standard
await run_market_one_shot(svc, MarketEURUSD, Aggressive)    # 2.0% risky

# Same risk, different strategies
await run_market_one_shot(svc, MarketEURUSD, Scalper)       # EURUSD scalp
await run_market_one_shot(svc, MarketXAUUSD, Scalper)       # Gold scalp
await run_market_one_shot(svc, MarketBTCUSD, Scalper)       # BTC scalp

# Adaptive risk with ATR
risk_eur = await ATR_Balanced(svc, "EURUSD", risk_percent=1.0)
risk_gold = await ATR_Balanced(svc, "XAUUSD", risk_percent=1.0)
await run_market_one_shot(svc, MarketEURUSD, risk_eur)
await run_market_one_shot(svc, MarketXAUUSD, risk_gold)
```

---

## 📊 Preset Comparison Tables

### Risk Preset Comparison

| Preset | Type | Risk % | Adaptability | Best For |
|--------|------|--------|--------------|----------|
| **Conservative** | Fixed | 0.5% | Static | Safe, large accounts |
| **Balanced** | Fixed | 1.0% | Static | General trading |
| **Aggressive** | Fixed | 2.0% | Static | High risk appetite |
| **Scalper** | Fixed | 1.0% | Static | Fast trading |
| **Walker** | Fixed | 0.75% | Static | Patient trading |
| **ATR_Scalper** | Dynamic | Custom | High | Volatile scalping |
| **ATR_Balanced** | Dynamic | Custom | High | Adaptive day trading |
| **ATR_Swing** | Dynamic | Custom | High | Volatile swing trading |
| **ScalperEURUSD** | Optimized | 1.0% | Medium | EUR scalping |
| **SwingXAUUSD** | Optimized | 0.5% | Medium | Gold swing |

---

## 🎯 Quick Decision Guide

**I want to...**

- ✅ **Trade safely** → `Conservative`
- ✅ **Standard risk** → `Balanced`
- ✅ **Take more risk** → `Aggressive`
- ✅ **Scalp quickly** → `Scalper`
- ✅ **Be patient** → `Walker`
- ✅ **Adapt to volatility** → `ATR_Balanced`, `ATR_Scalper`, `ATR_Swing`
- ✅ **Symbol-optimized risk** → `ScalperEURUSD`, `SwingXAUUSD`, etc.
- ✅ **Trade by session** → `session_risk_auto()`
- ✅ **Trade specific symbol** → `MarketEURUSD`, `LimitXAUUSD`, etc.

---

## 💡 Pro Tips

1. **Start with Balanced** — it's the industry standard (1% risk, 1:2 R:R)
2. **Use ATR risk for volatile symbols** (Gold, Bitcoin, indices)
3. **Combine session guards with session risk** for optimal timing
4. **Test deviation settings with your broker** (can vary by broker)
5. **Use unique magic numbers** per strategy for easy filtering
6. **Limit orders save spread costs** (better average entry price)
7. **Mix and match freely** — any Strategy + any Risk preset works

---

**📦 Summary:**

Presets are **building blocks**:
- **Strategy Presets** = WHAT to trade (symbol, entry type)
- **Risk Presets** = HOW MUCH to risk (%, SL, TP)
- **Combine them** = Complete trading setup in one line

```python
# One line = complete trading configuration
await run_market_one_shot(svc, MarketEURUSD, Balanced)
```
