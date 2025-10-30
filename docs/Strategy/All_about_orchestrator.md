# 🎭 Strategy Orchestrators Guide

**What is an Orchestrator?**
An orchestrator is a **ready-to-use trading scenario** that combines order execution, risk management, and automated position handling into a single, reusable workflow.

Think of it as a "trading recipe" — you provide the ingredients (symbol, risk parameters), and the orchestrator handles the entire execution flow automatically.

---

## 🎯 Quick Comparison

| Orchestrator | Type | When to Use | Key Feature |
|--------------|------|-------------|-------------|
| **market_one_shot** | 🚀 Market | Instant entries, scalping | Fast execution + auto management |
| **pending_bracket** | ⏰ Limit/Stop | Precise entry price | Wait for fill + timeout protection |
| **spread_guard** | 💰 Filter | Cost control | Block trades when spreads too wide |
| **session_guard** | 🕐 Time filter | Session-specific trading | Trade only during defined hours |
| **oco_straddle** | 🔀 Breakout | Two-way entry (OCO) | Buy stop + Sell stop, cancel other |
| **bracket_trailing_activation** | 📈 Trail | Conditional trailing | Activate trail only after threshold |
| **equity_circuit_breaker** | 🛑 Safety | Drawdown protection | Emergency stop on equity drop |
| **dynamic_deviation_guard** | 🎯 Slippage | Adaptive deviation | Adjust slippage based on volatility |
| **rollover_avoidance** | 💸 Cost | Swap time protection | Block trades near rollover |
| **grid_dca_common_sl** | 📊 Grid | DCA/Grid strategies | Multiple entries, shared stop loss |
| **kill_switch_review** | 🔴 Emergency | Manual intervention | Review and kill all positions |
| **ladder_builder** | 🪜 Scaling | Scale in/out | Build position gradually |
| **cleanup** | 🧹 Maintenance | Close/cancel all | Clean slate for new strategy |

---

## 📚 Core Orchestrators (Demonstrated in Examples)

### 1. 🚀 **market_one_shot** - Instant Market Execution

**Purpose:** Fast market entry with automatic management.

**Perfect for:**
- Scalping and quick entries
- Breakout trading (immediate execution)
- News trading (fast during volatility)
- "Set and forget" style

**What it does:**
```python
from Strategy.orchestrator.market_one_shot import run_market_one_shot
from Strategy.presets import MarketEURUSD, Balanced

result = await run_market_one_shot(svc, MarketEURUSD, Balanced)
```

**Flow:**
1. Buy at current market price
2. Set SL/TP automatically
3. Activate trailing stop (if configured)
4. Move to breakeven when profitable (if configured)
5. Return execution report

**Related:** [market_one_shot.py](../../Strategy/orchestrator/market_one_shot.py)

---

### 2. ⏰ **pending_bracket** - Limit Order with Timeout

**Purpose:** Enter at specific price, wait patiently for fill.

**Perfect for:**
- Support/resistance trading
- Buy dips / sell rallies
- Mean reversion strategies
- Better entry price than market

**What it does:**
```python
from Strategy.orchestrator.pending_bracket import run_pending_bracket
from Strategy.presets import LimitEURUSD, Conservative

strategy = LimitEURUSD(price=1.0850)
result = await run_pending_bracket(svc, strategy, Conservative, timeout_s=900)
```

**Flow:**
1. Place limit order at specified price
2. Wait for market to reach your level (max: timeout_s)
3. Once filled → set SL/TP
4. Activate trailing/breakeven (if configured)
5. If timeout expires → cancel order

**Visual:**
```
Current: 1.1020  ─────────  (Market here)
                     ↓
Target:  1.1000  ═════════  (Your limit order)
                     ↓
Filled!  1.1000  ─────────  (SL/TP set automatically)
```

**Related:** [pending_bracket.py](../../Strategy/orchestrator/pending_bracket.py)

---

### 3. 💰 **spread_guard** - Cost Protection Filter

**Purpose:** Block trades when spreads are too wide (expensive).

**Perfect for:**
- Scalping (where spread = major cost)
- News trading protection (spreads spike)
- Rollover avoidance (spreads widen)
- Cost-conscious trading

**What it does:**
```python
from Strategy.orchestrator.spread_guard import market_with_spread_guard

result = await market_with_spread_guard(
    svc, strategy, risk,
    max_spread_pips=1.5  # Trade only if spread ≤ 1.5 pips
)
```

**Example:**
- ✅ Spread: 0.8 pips → TRADE (good conditions)
- ✅ Spread: 1.5 pips → TRADE (acceptable)
- ❌ Spread: 3.0 pips → BLOCKED (too expensive)

**Why it matters:**
```
Normal spread (2 pips):  Need 1.10040 for 2 pip profit
Wide spread (10 pips):   Need 1.10200 for 2 pip profit
                        → 5x more movement required!
```

**Related:** [spread_guard.py](../../Strategy/orchestrator/spread_guard.py)

---

### 4. 🕐 **session_guard** - Time Window Control

**Purpose:** Trade only during specific hours/sessions.

**Perfect for:**
- Session-specific strategies (London breakout, NY reversal)
- Avoiding low-liquidity periods (Asian session)
- Overlap trading (London + NY = max volume)
- Weekend/overnight risk avoidance

**What it does:**
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

**Visual:**
```
00:00 ────────────  ❌ Blocked (outside windows)
08:00 ════════════╗ ✓ Window 1: Trading allowed
11:30 ════════════╝
12:00 ────────────  ❌ Blocked (lunch break)
13:00 ════════════╗ ✓ Window 2: Trading allowed
17:00 ════════════╝
18:00 ────────────  ❌ Blocked (after hours)
```

**Trading Sessions:**
- 🇯🇵 Tokyo: 00:00-08:00 GMT (low volatility)
- 🇬🇧 London: 07:00-16:30 GMT (high liquidity)
- 🇺🇸 New York: 12:00-21:00 GMT (highest volume)
- Overlap: 12:00-16:30 GMT (best time)

**Related:** [session_guard.py](../../Strategy/orchestrator/session_guard.py)

---

## 🔧 Advanced Orchestrators

### 5. 🔀 **oco_straddle** - Two-Way Breakout Entry

**Purpose:** Place both buy stop and sell stop, cancel the other when one fills.

**Perfect for:**
- Breakout strategies (don't know direction)
- Range breakouts
- News trading (catch the move either way)

**Flow:**
1. Place buy stop above current price
2. Place sell stop below current price
3. When one fills → cancel the other
4. Continue with filled position

**Related:** [oco_straddle.py](../../Strategy/orchestrator/oco_straddle.py)

---

### 6. 📈 **bracket_trailing_activation** - Conditional Trailing

**Purpose:** Activate trailing stop only after price moves X pips in profit.

**Perfect for:**
- Letting winners run initially
- Avoiding early exits
- Trend-following strategies

**Related:** [bracket_trailing_activation.py](../../Strategy/orchestrator/bracket_trailing_activation.py)

---

### 7. 🛑 **equity_circuit_breaker** - Drawdown Protection

**Purpose:** Emergency stop when equity drops below threshold.

**Perfect for:**
- Risk management
- Preventing catastrophic losses
- Automated safety net

**Related:** [equity_circuit_breaker.py](../../Strategy/orchestrator/equity_circuit_breaker.py)

---

### 8. 🎯 **dynamic_deviation_guard** - Adaptive Slippage

**Purpose:** Adjust allowed slippage based on market volatility.

**Perfect for:**
- Fast markets (news, open)
- Preventing rejections
- Adaptive execution

**Related:** [dynamic_deviation_guard.py](../../Strategy/orchestrator/dynamic_deviation_guard.py)

---

### 9. 💸 **rollover_avoidance** - Swap Time Protection

**Purpose:** Block trades near daily rollover when spreads widen.

**Perfect for:**
- Avoiding expensive swap time
- Preventing wide-spread entries
- Scalping protection

**Related:** [rollover_avoidance.py](../../Strategy/orchestrator/rollover_avoidance.py)

---

### 10. 📊 **grid_dca_common_sl** - Grid Trading with Shared SL

**Purpose:** Build grid of positions with one shared stop loss.

**Perfect for:**
- DCA (Dollar Cost Averaging)
- Grid strategies
- Range-bound trading

**Related:** [grid_dca_common_sl.py](../../Strategy/orchestrator/grid_dca_common_sl.py)

---

### 11. 🔴 **kill_switch_review** - Emergency Stop

**Purpose:** Review all open positions and close them manually.

**Perfect for:**
- Emergency situations
- Manual intervention
- Clean slate before strategy change

**Related:** [kill_switch_review.py](../../Strategy/orchestrator/kill_switch_review.py)

---

### 12. 🪜 **ladder_builder** - Gradual Position Building

**Purpose:** Scale into position gradually (multiple entries).

**Perfect for:**
- Large positions (reduce slippage)
- Trend following (add to winners)
- Risk averaging

**Related:** [ladder_builder.py](../../Strategy/orchestrator/ladder_builder.py)

---

### 13. 🧹 **cleanup** - Close/Cancel All

**Purpose:** Utility to close all positions and cancel all pending orders.

**Perfect for:**
- End of day cleanup
- Strategy reset
- Emergency flatten

**Related:** [cleanup.py](../../Strategy/orchestrator/cleanup.py)

---

## 🎬 How to Use in Examples

All orchestrators are demonstrated in [examples/Orchestrator_demo.py](../../examples/Orchestrator_demo.py):

```bash
python examples/Orchestrator_demo.py
```

**Quick example:**
```python
from Strategy.orchestrator.market_one_shot import run_market_one_shot
from Strategy.presets import MarketEURUSD, Balanced

# Execute market order with Balanced risk profile
result = await run_market_one_shot(
    svc=svc,
    strategy=MarketEURUSD,
    risk=Balanced
)

print(f"Ticket: {result.ticket}")
print(f"Entry Price: {result.entry_price}")
print(f"SL: {result.sl_price}, TP: {result.tp_price}")
```

---

## 🧩 Combining Orchestrators

Orchestrators can be combined for complex scenarios:

```python
# Example: Market entry with spread + session guards
from Strategy.orchestrator.spread_guard import market_with_spread_guard
from Strategy.orchestrator.session_guard import run_with_session_guard

# 1. Session guard (only trade 08:00-17:00)
# 2. Inside session → spread guard (only if spread ≤ 2 pips)
# 3. Inside spread guard → market_one_shot execution

result = await run_with_session_guard(
    svc=svc,
    runner_coro_factory=lambda: market_with_spread_guard(
        svc, MarketEURUSD, Balanced, max_spread_pips=2.0
    ),
    windows=[('08:00', '17:00')],
    tz='Europe/London'
)
```

---

## 📖 Related Documentation

- [Strategy Presets Guide](./All_about_presets.md) - Configure strategies and risk
- [Examples Overview](../Examples/All_about_examples.md) - See orchestrators in action
- [MT4Sugar API](../MT4Sugar/) - Low-level functions used by orchestrators

---

## 🎯 Quick Decision Guide

**I want to...**

- ✅ **Trade immediately** → `market_one_shot`
- ✅ **Wait for specific price** → `pending_bracket`
- ✅ **Control costs** → `spread_guard`
- ✅ **Trade only certain hours** → `session_guard`
- ✅ **Catch breakout (either direction)** → `oco_straddle`
- ✅ **Protect from drawdown** → `equity_circuit_breaker`
- ✅ **Avoid swap time** → `rollover_avoidance`
- ✅ **Build position gradually** → `ladder_builder` or `grid_dca_common_sl`
- ✅ **Close everything** → `cleanup` or `kill_switch_review`

---

**💡 Tip:** All orchestrators work with [Strategy Presets](./All_about_presets.md) for easy configuration:
```python
from Strategy.presets import MarketEURUSD, Balanced, Conservative, Aggressive

# Same orchestrator, different risk profiles
await run_market_one_shot(svc, MarketEURUSD, Conservative)  # 0.5% risk
await run_market_one_shot(svc, MarketEURUSD, Balanced)      # 1.0% risk
await run_market_one_shot(svc, MarketEURUSD, Aggressive)    # 2.0% risk
```
