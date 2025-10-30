# -*- coding: utf-8 -*-
"""
Risk Profiles: Scalper vs Swing 📊
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Purpose: Trading style-specific risk presets - optimized for timeframe and approach.
         "Scalpers need tight stops, swing traders need breathing room" 🎯

What are Risk Profiles? 🎭
Risk profiles = Pre-tuned RiskPresets for specific trading styles:
- Scalper Tight: Fast entries/exits, tight stops, active trailing
- Swing Wide: Patient approach, wider stops, room to breathe

Think of it as: "Your trading style = your risk profile"

Why Use Risk Profiles? ✓
✓ Style-matched: Risk parameters aligned with your trading timeframe
✓ Proven settings: Battle-tested configurations per style
✓ Quick setup: One function call, instant configuration
✓ Symbol variants: EUR/USD vs Gold optimized separately
✓ Consistency: Same risk approach across all trades
✓ Flexibility: Fully customizable via parameters

Perfect For:
🎯 Scalpers (M1-M5 timeframes, quick in/out)
🎯 Day traders (M15-H1 timeframes, intraday)
🎯 Swing traders (H4-D1 timeframes, multi-day holds)
🎯 Style separation (different accounts/strategies)
🎯 Risk matching (tight stops for fast markets, wide for slow)

Trading Style Comparison:

┌─────────────┬──────────┬─────────┬───────────┬──────────────┐
│ Style       │ Timeframe│ Avg Hold│ Stop Size │ Management   │
├─────────────┼──────────┼─────────┼───────────┼──────────────┤
│ Scalper     │ M1-M5    │ Minutes │ 5-12 pips │ Very Active  │
│ Day Trader  │ M15-H1   │ Hours   │ 15-30 pips│ Active       │
│ Swing Trader│ H4-D1    │ Days    │ 40-100 pips│ Patient     │
└─────────────┴──────────┴─────────┴───────────┴──────────────┘

Profile Philosophies:

🏃 Scalper Tight Philosophy:
   - "Get in, get out, protect capital"
   - Tight SL (8-12 pips) - minimize exposure
   - Quick TP (12-18 pips) - small consistent wins
   - Early BE (6 pips) - fast breakeven protection
   - Active trailing (6 pips) - lock profits immediately
   - High frequency - many small trades

🚶 Swing Wide Philosophy:
   - "Let the trade breathe, catch big moves"
   - Wide SL (45-100 pips) - room for volatility
   - Big TP (90-160 pips) - capture major swings
   - Late BE (25-40 pips) - don't get stopped early
   - No/mild trailing - let winners run
   - Low frequency - fewer high-quality trades

Ready-to-Use Factories:

🔹 make_scalper_tight():
   - Default: Risk=1.0%, SL=8, TP=12, Trail=6, BE=6
   - Fully customizable via parameters
   - Perfect for: M1-M5, major pairs, high liquidity
   - Returns: RiskPreset

🔹 make_swing_wide():
   - Default: Risk=1.0%, SL=50, TP=100, BE=30
   - Trailing disabled by default (let winners run)
   - Perfect for: H4-D1, trend following, patience
   - Returns: RiskPreset

Symbol-Specific Shortcuts:

🔸 ScalperEURUSD(): 8/12 pips (tight for liquid major)
🔸 ScalperXAUUSD(): 12/18 pips (wider for gold volatility)
🔸 SwingEURUSD(): 45/90 pips (standard swing)
🔸 SwingXAUUSD(): 80/160 pips (gold needs more room)

Visual Comparison - Scalper vs Swing:

Scalper Tight (8-12 pips):
Price ─────●═══●───── (quick in/out, tight range)
       Entry  TP

Swing Wide (50-100 pips):
Price ───────────────●═══════════════════●────────
                  Entry                 TP
              (room to breathe)

Factory Parameters:

📊 make_scalper_tight() Parameters:
   - risk_percent: float = 1.0 (% of equity per trade)
   - sl_pips: float = 8.0 (tight stop loss)
   - tp_pips: float = 12.0 (quick target)
   - be_trigger_pips: float = 6.0 (early BE)
   - be_plus_pips: float = 1.0 (small cushion)
   - trailing_pips: float = 6.0 (active trailing)

📊 make_swing_wide() Parameters:
   - risk_percent: float = 1.0 (% of equity per trade)
   - sl_pips: float = 50.0 (wide stop loss)
   - tp_pips: float = 100.0 (big target)
   - be_trigger_pips: float | None = 30.0 (patient BE)
   - be_plus_pips: float | None = 2.0 (standard cushion)
   - trailing_pips: float | None = None (disabled - let run)

Usage Patterns:

💡 Quick Start (default scalper):
   from Strategy.presets.risk_profiles import make_scalper_tight
   risk = make_scalper_tight()
   # Returns: RiskPreset(risk=1.0%, SL=8, TP=12, trail=6)

💡 Custom Scalper (tighter settings):
   risk = make_scalper_tight(
       risk_percent=0.75,
       sl_pips=6.0,
       tp_pips=9.0,
       trailing_pips=4.0
   )

💡 Symbol-Specific Scalper:
   from Strategy.presets.risk_profiles import ScalperEURUSD, ScalperXAUUSD
   risk_eur = ScalperEURUSD()  # 8/12 pips
   risk_gold = ScalperXAUUSD() # 12/18 pips (gold needs more)

💡 Default Swing:
   from Strategy.presets.risk_profiles import make_swing_wide
   risk = make_swing_wide()
   # Returns: RiskPreset(risk=1.0%, SL=50, TP=100, BE=30, no trailing)

💡 Conservative Swing:
   risk = make_swing_wide(
       risk_percent=0.5,  # half risk
       sl_pips=60.0,
       tp_pips=120.0
   )

💡 Symbol-Specific Swing:
   from Strategy.presets.risk_profiles import SwingEURUSD, SwingXAUUSD
   risk_eur = SwingEURUSD()   # 45/90 pips
   risk_gold = SwingXAUUSD()  # 80/160 pips

💡 Combined with Orchestrator:
   from Strategy.presets.strategy_symbols import MarketEURUSD
   from Strategy.presets.risk_profiles import ScalperEURUSD
   from Strategy.orchestrator.market_one_shot import run_market_one_shot

   risk = ScalperEURUSD()
   result = await run_market_one_shot(svc, MarketEURUSD, risk)

When to Use Each Profile:

🏃 Use Scalper Tight When:
✓ Trading M1-M5 timeframes
✓ High liquidity markets (EUR/USD, GBP/USD during London/NY)
✓ Targeting small consistent wins (5-15 pips)
✓ Active monitoring possible (not set-and-forget)
✓ Low spread environment (scalping requires tight spreads)
✓ News avoidance strategy (quick in/out before volatility)

🚶 Use Swing Wide When:
✓ Trading H4-D1 timeframes
✓ Trend-following strategies
✓ Targeting major moves (50-200+ pips)
✓ Set-and-forget approach (check once/twice per day)
✓ Capturing multi-day trends
✓ Avoiding intraday noise (wider stops survive volatility)

Symbol-Specific Tuning Logic:

💱 EUR/USD (Most Liquid):
   - Scalper: 8/12 pips (tightest possible)
   - Swing: 45/90 pips (standard swing)
   - Rationale: Low spread, high liquidity, clean charts

💰 XAU/USD (Gold - Volatile):
   - Scalper: 12/18 pips (50% wider than EUR)
   - Swing: 80/160 pips (80% wider than EUR)
   - Rationale: Higher volatility, wider spreads, bigger moves

Pro Tips:

💡 Scalpers need tight spreads (< 1 pip ideal)
💡 Scalpers should avoid news events (volatility kills tight stops)
💡 Swing traders should trade with the trend (H4/D1)
💡 Swing traders can survive news (wider stops absorb spikes)
💡 Test scalper settings on demo first (very unforgiving)
💡 Adjust SL/TP based on ATR (volatility adaptation)
💡 Combine with session risk (scalp during overlap, swing anytime)
💡 Use scalper profile only during high-liquidity sessions
💡 Use swing profile for overnight holds (less stress)

Risk:Reward Ratios:

📊 Scalper Tight:
   - Default: 8 SL / 12 TP = 1:1.5 (acceptable)
   - ScalperXAUUSD: 12 SL / 18 TP = 1:1.5
   - Rationale: Higher win rate compensates (60-70%)

📊 Swing Wide:
   - Default: 50 SL / 100 TP = 1:2 (good)
   - SwingXAUUSD: 80 SL / 160 TP = 1:2
   - Rationale: Lower win rate (40-50%) but bigger wins

Common Mistakes to Avoid:

❌ Using scalper settings on H4 charts (stops too tight)
❌ Using swing settings on M5 charts (stops too wide)
❌ Scalping during Asian session (low liquidity)
❌ Swing trading without respecting major support/resistance
❌ Scalping with wide spreads (eats into profits)
❌ Swing trading without trend confirmation (counter-trend fails)
"""

from __future__ import annotations
from Strategy.presets.risk import RiskPreset

# --- Base profiles ------------------------------------------------------------

def make_scalper_tight(
    *,
    risk_percent: float = 1.0,
    sl_pips: float = 8.0,
    tp_pips: float = 12.0,
    be_trigger_pips: float = 6.0,
    be_plus_pips: float = 1.0,
    trailing_pips: float = 6.0,
) -> RiskPreset:
    """Tight scalping profile for liquid symbols (EURUSD/GBPUSD/etc.)."""
    return RiskPreset(
        risk_percent=risk_percent,
        sl_pips=sl_pips,
        tp_pips=tp_pips,
        be_trigger_pips=be_trigger_pips,
        be_plus_pips=be_plus_pips,
        trailing_pips=trailing_pips,
    )


def make_swing_wide(
    *,
    risk_percent: float = 1.0,
    sl_pips: float = 50.0,
    tp_pips: float = 100.0,
    be_trigger_pips: float | None = 30.0,
    be_plus_pips: float | None = 2.0,
    trailing_pips: float | None = None,
) -> RiskPreset:
    """Wider swing profile for higher timeframes / broader moves."""
    return RiskPreset(
        risk_percent=risk_percent,
        sl_pips=sl_pips,
        tp_pips=tp_pips,
        be_trigger_pips=be_trigger_pips,
        be_plus_pips=be_plus_pips,
        trailing_pips=trailing_pips,
    )


# --- Symbol-aware shortcuts (optional but handy) ------------------------------

def ScalperEURUSD() -> RiskPreset:
    # Slightly tighter for EURUSD majors
    return make_scalper_tight(sl_pips=8, tp_pips=12, trailing_pips=6)

def ScalperXAUUSD() -> RiskPreset:
    # Gold tends to need a bit more room (broker pip spec dependent)
    return make_scalper_tight(sl_pips=12, tp_pips=18, trailing_pips=8)

def SwingEURUSD() -> RiskPreset:
    return make_swing_wide(sl_pips=45, tp_pips=90, be_trigger_pips=25)

def SwingXAUUSD() -> RiskPreset:
    return make_swing_wide(sl_pips=80, tp_pips=160, be_trigger_pips=40)

"""
Example of launch

from Strategy.presets.strategy_symbols import MarketEURUSD, MarketXAUUSD
from Strategy.presets.risk_profiles import (
    make_scalper_tight, make_swing_wide,
    ScalperEURUSD, ScalperXAUUSD, SwingEURUSD, SwingXAUUSD,
)
from Strategy.orchestrator.market_one_shot import run_market_one_shot

# 1) Pure Factories
rp_scalp = make_scalper_tight() # universal scalper
rp_swing = make_swing_wide(risk_percent=0.75)

# 2) Symbol-Specific Hotkeys
rp_eu = ScalperEURUSD()
rp_xau = SwingXAUUSD()

# 3) Launch
res1 = await run_market_one_shot(svc, MarketEURUSD, rp_eu)
res2 = await run_market_one_shot(svc, MarketXAUUSD, rp_xau)


"""