# -*- coding: utf-8 -*-
"""
Risk Presets 🎯
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Purpose: Core risk management building blocks - reusable "risk buttons" for any strategy.
         "One dataclass to rule them all" - works with every orchestrator.

What is RiskPreset? 💰
RiskPreset = A complete risk management configuration in one object:
- How much to risk per trade (risk_percent)
- Stop loss distance (sl_pips)
- Take profit distance (tp_pips)
- Trailing stop (trailing_pips)
- Auto breakeven trigger (be_trigger_pips, be_plus_pips)

Think of it as: "Everything about RISK in one place" 📦

Why Use Risk Presets? ✓
✓ Consistency: Same risk rules across all strategies
✓ Reusability: Define once, use everywhere
✓ Flexibility: Mix and match with any strategy/symbol
✓ Safety: Pre-tested risk parameters
✓ Speed: Ready-to-use presets (no calculation needed)
✓ Clarity: Named presets clearly communicate intent

Perfect For:
🎯 Rapid strategy testing (swap risk profiles instantly)
🎯 Multi-strategy portfolios (consistent risk management)
🎯 Team trading (shared risk standards)
🎯 Backtesting (parameterized risk scenarios)
🎯 Live trading (proven risk configurations)

Visual Hierarchy:
┌─────────────────────────────────────────────────────────────┐
│ RiskPreset (Base Dataclass)                                 │
├─────────────────────────────────────────────────────────────┤
│ • risk_percent: % of equity to risk (e.g., 1.0 = 1%)       │
│ • sl_pips: Stop loss in pips (e.g., 20)                    │
│ • tp_pips: Take profit in pips (e.g., 40) [optional]       │
│ • trailing_pips: Trailing distance in pips [optional]      │
│ • be_trigger_pips: Profit to trigger breakeven [optional]  │
│ • be_plus_pips: Extra pips above BE level [optional]       │
└─────────────────────────────────────────────────────────────┘
         ↓ Ready-to-Use Presets ↓
┌──────────────┬─────────┬────────┬────────┬──────────────┐
│ Conservative │ 0.5%    │ 25 pip │ 50 pip │ Safe & slow  │
├──────────────┼─────────┼────────┼────────┼──────────────┤
│ Balanced     │ 1.0%    │ 20 pip │ 40 pip │ Standard     │
├──────────────┼─────────┼────────┼────────┼──────────────┤
│ Aggressive   │ 2.0%    │ 15 pip │ 30 pip │ Higher risk  │
├──────────────┼─────────┼────────┼────────┼──────────────┤
│ Scalper      │ 1.0%    │ 8 pip  │ 12 pip │ Tight+Trail  │
├──────────────┼─────────┼────────┼────────┼──────────────┤
│ Walker       │ 0.75%   │ 30 pip │ 60 pip │ BE+Patience  │
└──────────────┴─────────┴────────┴────────┴──────────────┘

Ready-to-Use Presets Explained:

🔹 Conservative:
   - Risk: 0.5% per trade (safest)
   - SL: 25 pips, TP: 50 pips (RR = 1:2)
   - No trailing, no breakeven
   - Perfect for: Cautious traders, large accounts, low-risk strategies

🔹 Balanced:
   - Risk: 1.0% per trade (industry standard)
   - SL: 20 pips, TP: 40 pips (RR = 1:2)
   - No trailing, no breakeven
   - Perfect for: Most strategies, day trading, general use

🔹 Aggressive:
   - Risk: 2.0% per trade (higher risk)
   - SL: 15 pips, TP: 30 pips (RR = 1:2)
   - No trailing, no breakeven
   - Perfect for: Experienced traders, small accounts, confident setups

🔹 Scalper:
   - Risk: 1.0% per trade
   - SL: 8 pips, TP: 12 pips (tight targets)
   - Trailing: 6 pips (locks profit)
   - Perfect for: High-frequency, major pairs, liquid markets

🔹 Walker:
   - Risk: 0.75% per trade
   - SL: 30 pips, TP: 60 pips (wider room)
   - Auto breakeven: Trigger at +20 pips, move to BE+2
   - Perfect for: Swing trading, letting winners run, trend following

RiskPreset Fields Explained:

📊 risk_percent (float):
   - Percentage of account equity to risk per trade
   - Example: 1.0 = risk 1% of $10,000 = $100 max loss
   - Recommended: 0.5-2.0% (never exceed 5%)

📊 sl_pips (float):
   - Stop loss distance in pips from entry
   - Example: 20 = stop is 20 pips away
   - Used for: Risk calculation (lot size) and order placement

📊 tp_pips (float | None):
   - Take profit distance in pips from entry
   - Example: 40 = target is 40 pips away
   - Optional: None = no fixed TP (manual exit)

📊 trailing_pips (float | None):
   - Trailing stop distance in pips
   - Example: 10 = stop follows price 10 pips behind
   - Optional: None = no trailing (fixed SL)

📊 be_trigger_pips (float | None):
   - Profit threshold to trigger auto-breakeven
   - Example: 15 = when +15 pips profit, move SL to BE
   - Optional: None = no auto-breakeven

📊 be_plus_pips (float | None):
   - Extra pips to add above breakeven level
   - Example: 2 = move SL to entry+2 (not exactly entry)
   - Optional: None = use 0 (exact breakeven)

Usage Patterns:

💡 Quick Start (use ready-made preset):
   from Strategy.presets.risk import Balanced
   risk = Balanced
   # Done! Pass to any orchestrator

💡 Custom Risk (modify existing preset):
   from Strategy.presets.risk import Balanced
   from dataclasses import replace
   risk = replace(Balanced, risk_percent=1.5, sl_pips=25)

💡 Build from Scratch (full control):
   from Strategy.presets.risk import RiskPreset
   risk = RiskPreset(
       risk_percent=1.0,
       sl_pips=20,
       tp_pips=40,
       trailing_pips=10,
       be_trigger_pips=15,
       be_plus_pips=2
   )

💡 Minimal Setup (only required fields):
   from Strategy.presets.risk import RiskPreset
   risk = RiskPreset(risk_percent=1.0, sl_pips=20)
   # tp, trailing, BE all default to None (disabled)

Combining with Orchestrators:

All orchestrators accept RiskPreset as input:

from Strategy.presets.risk import Balanced, Scalper
from Strategy.presets.strategy import MarketEURUSD
from Strategy.orchestrator.market_one_shot import run_market_one_shot

# Example 1: Balanced risk on market order
result = await run_market_one_shot(svc, MarketEURUSD, Balanced)

# Example 2: Scalper risk (tight SL + trailing)
result = await run_market_one_shot(svc, MarketEURUSD, Scalper)

Pro Tips:

💡 Start with Balanced preset for most strategies
💡 Use Conservative for news trading or uncertain conditions
💡 Use Scalper for liquid majors (EUR/USD, GBP/USD)
💡 Use Walker for trend-following strategies (locks in profit)
💡 Never risk more than 2% per trade (5% absolute maximum)
💡 Combine with ATR-based risk (risk_atr.py) for volatility adaptation
💡 Combine with session risk (risk_session.py) for time-based tuning

Risk Management Golden Rules:

🛡️ Rule 1: Risk % should be constant (e.g., always 1%)
🛡️ Rule 2: Stop loss adapts to volatility (use ATR or market conditions)
🛡️ Rule 3: Risk:Reward ratio should be ≥ 1:1.5 (ideally 1:2 or better)
🛡️ Rule 4: Never remove stop loss (always protect capital)
🛡️ Rule 5: Trailing stop preserves profit (use on trending moves)
🛡️ Rule 6: Breakeven locks in "free trades" (trigger after +50% of SL)
"""

from dataclasses import dataclass

@dataclass
class RiskPreset:
    risk_percent: float
    sl_pips: float
    tp_pips: float | None = None
    trailing_pips: float | None = None
    be_trigger_pips: float | None = None
    be_plus_pips: float | None = None

#Ready-made "buttons"
Conservative = RiskPreset(risk_percent=0.5, sl_pips=25, tp_pips=50)
Balanced    = RiskPreset(risk_percent=1.0, sl_pips=20, tp_pips=40)
Aggressive  = RiskPreset(risk_percent=2.0, sl_pips=15, tp_pips=30)
Scalper     = RiskPreset(risk_percent=1.0, sl_pips=8,  tp_pips=12, trailing_pips=6)
Walker      = RiskPreset(risk_percent=0.75, sl_pips=30, tp_pips=60, be_trigger_pips=20, be_plus_pips=2)

