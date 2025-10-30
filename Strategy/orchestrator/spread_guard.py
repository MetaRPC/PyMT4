# Strategy/orchestrator/spread_guard.py
"""
Spread Guard Orchestrator 💰
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Purpose: Cost-based protection that blocks trading when spreads are too wide.
         "Don't pay extra - trade only when spreads are fair" protection.

What is Spread? 💸
Spread = Ask - Bid (the broker's commission you pay on every trade)

Example:
  EUR/USD Bid: 1.10000
  EUR/USD Ask: 1.10020
  Spread: 0.00020 = 2 pips = $20 cost on 1 lot

Normal vs Wide Spreads:
✅ EUR/USD normal: 0.5-2 pips (tight, good to trade)
⚠️ EUR/USD news time: 5-10 pips (wide, risky)
❌ EUR/USD rollover: 20-50 pips (extremely wide, avoid!)

Why Guard Against Wide Spreads? 🚫
❌ Higher trading costs (eats into profits)
❌ Worse entry/exit prices (immediate drawdown)
❌ Stop loss more likely to be hit
❌ Requires larger price movement to profit
❌ Indicates poor market conditions (low liquidity)

Example Impact:
💡 Normal spread (2 pips):
   - Buy at 1.10020, need 1.10040 to profit 2 pips

💀 Wide spread (10 pips):
   - Buy at 1.10100, need 1.10200 to profit 2 pips
   - Same 2 pip profit requires 5x more movement!

Perfect For:
🎯 Scalping strategies (spread = major cost)
🎯 High-frequency trading (minimize costs)
🎯 News trading protection (spreads spike during news)
🎯 Rollover avoidance (spreads widen at swap time)
🎯 Automated bots (prevent expensive trades)
🎯 Cost-conscious traders (maximize profit margins)

Visual Example:
  max_spread_pips = 2.0

  ✅ Spread: 0.8 pips → ALLOWED (good conditions)
  ✅ Spread: 1.5 pips → ALLOWED (acceptable)
  ✅ Spread: 2.0 pips → ALLOWED (at limit)
  ❌ Spread: 2.5 pips → BLOCKED (too expensive)
  ❌ Spread: 5.0 pips → BLOCKED (way too wide)

Features:
┌──────────────────────┬─────────────────────────────────────────────────┐
│ Simple Check         │ Compare current spread vs max threshold         │
├──────────────────────┼─────────────────────────────────────────────────┤
│ Cost Protection      │ Avoid trading during expensive conditions       │
├──────────────────────┼─────────────────────────────────────────────────┤
│ Market Quality       │ Only trade when liquidity is good               │
├──────────────────────┼─────────────────────────────────────────────────┤
│ News/Rollover Guard  │ Automatically skip wide-spread events           │
├──────────────────────┼─────────────────────────────────────────────────┤
│ Easy Integration     │ Wraps market_one_shot for instant protection    │
└──────────────────────┴─────────────────────────────────────────────────┘

Parameters:
- svc: MT4Service instance
- strategy: StrategyPreset (symbol, magic, deviation_pips, lots, comment)
- risk: RiskPreset (risk_percent, sl_pips, tp_pips, etc.)
- max_spread_pips: Maximum allowed spread in pips (default 1.2)

Spread Recommendations by Strategy:
📊 Scalping: 0.5-1.5 pips (very tight requirement)
📊 Day trading: 1.5-3.0 pips (moderate requirement)
📊 Swing trading: 3.0-5.0 pips (relaxed requirement)

Spread Recommendations by Symbol:
💱 Major pairs (EUR/USD, GBP/USD): 0.5-2.0 pips normal
💱 Cross pairs (EUR/GBP, AUD/NZD): 2.0-4.0 pips normal
💱 Exotic pairs (USD/TRY, EUR/ZAR): 10-50 pips normal
💱 Crypto (BTC/USD): 50-500 pips equivalent

Execution Flow:
1. Ensure connection and symbol availability
2. Get current spread in pips for symbol
3. Compare spread with max_spread_pips threshold
4. If spread > max:
   - Skip trade (too expensive)
   - Return blocked status with spread info
5. If spread <= max:
   - Execute market_one_shot strategy
   - Trade proceeds normally
6. Return result

Returns:
dict {
  "status": "skipped_due_to_spread",  # If blocked
  "spread_pips": float                 # Current spread
}

OR (if allowed):
dict {
  <market_one_shot_result>             # Full strategy result
}

Requirements (svc.sugar API):
- ensure_connected, ensure_symbol: Connection management
- spread_pips: Get current spread in pips

Common Scenarios:
💡 Normal conditions: spread 1.0 pip → ✅ Trade
💡 News announcement: spread 8.0 pips → ❌ Skip (protect costs)
💡 Rollover time: spread 25.0 pips → ❌ Skip (protect costs)
💡 Low liquidity: spread 4.0 pips → ❌ Skip (poor conditions)
💡 Market open: spread 1.5 pips → ✅ Trade (acceptable)

Combine with Other Guards:
🛡️ rollover_avoidance.py - Time-based swap protection
🛡️ session_guard.py - Session-based trading windows
🛡️ equity_circuit_breaker.py - Account protection
🛡️ dynamic_deviation_guard.py - Adaptive slippage

Pro Tip:
💡 Set max_spread_pips = 2-3× your typical spread
   Example: EUR/USD normal = 1 pip → set max = 2-3 pips
   This allows normal variation but blocks extreme events
"""

from .market_one_shot import run_market_one_shot

async def market_with_spread_guard(svc, strategy, risk, max_spread_pips: float = 1.2):
    sugar = svc.sugar
    await sugar.ensure_connected(); await sugar.ensure_symbol(strategy.symbol)
    sp = await sugar.spread_pips(strategy.symbol)
    if sp > max_spread_pips:
        return {"status": "skipped_due_to_spread", "spread_pips": sp}
    return await run_market_one_shot(svc, strategy, risk)
