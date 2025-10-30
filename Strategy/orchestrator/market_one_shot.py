# Strategy/orchestrator/market_one_shot.py
"""
Market One-Shot Orchestrator 🎯
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Purpose: Simple, fast market execution with automatic management features.
         "One shot, one kill" - single market order with full automation.

Strategy Profile:
✓ Execution: Instant market order (no pending)
✓ Protection: Automatic SL/TP on entry
✓ Management: Optional trailing stop and auto-breakeven
✓ Simplicity: Minimal configuration, maximum effect

Perfect For:
🎯 Quick scalping entries
🎯 Breakout trading (enter immediately when level breaks)
🎯 News trading (fast execution during volatility)
🎯 Simple trend following
🎯 "Set and forget" trading style

Features:
┌─────────────────────┬───────────────────────────────────────────────────┐
│ Market Execution    │ Buy at current market price immediately           │
├─────────────────────┼───────────────────────────────────────────────────┤
│ Auto SL/TP          │ Set stop loss and take profit on entry            │
├─────────────────────┼───────────────────────────────────────────────────┤
│ Trailing Stop       │ Optional: Lock profits as price moves favorably   │
├─────────────────────┼───────────────────────────────────────────────────┤
│ Auto Breakeven      │ Optional: Move SL to breakeven after threshold    │
├─────────────────────┼───────────────────────────────────────────────────┤
│ Risk Management     │ Lot sizing via risk% or fixed lots                │
└─────────────────────┴───────────────────────────────────────────────────┘

Parameters:
- strategy: StrategyPreset (symbol, magic, deviation_pips, lots, comment)
- risk: RiskPreset (risk_percent, sl_pips, tp_pips, trailing_pips,
                     be_trigger_pips, be_plus_pips)

Execution Flow:
1. Setup defaults (symbol, magic, deviation, risk%)
2. Ensure connection and symbol availability
3. Calculate lot size (use preset lots OR calc by risk%)
4. Execute BUY MARKET order with SL/TP
5. Activate management features (if configured):
   - Trailing stop: Locks profit as price moves up
   - Auto breakeven: Moves SL to entry + plus_pips after trigger
6. Wait for order fill confirmation (timeout: 300s)
7. Capture diagnostic snapshot
8. Return complete execution report

Returns:
dict {
  "ticket": int,              # Order ticket number
  "subscriptions": {          # Active management features
    "trailing": {...},        # Trailing stop details (if enabled)
    "auto_be": {...}          # Auto breakeven details (if enabled)
  },
  "filled": {...},            # Fill confirmation or timeout status
  "snapshot": {...}           # Account diagnostic snapshot
}

Requirements (svc.sugar API):
- Core: set_defaults, ensure_connected, ensure_symbol
- Risk: calc_lot_by_risk
- Entry: buy_market (with SL/TP support)
- Management: set_trailing_stop, auto_breakeven (optional)
- Monitoring: wait_filled, diag_snapshot

Note: Currently only supports BUY direction.
      For SELL, use sell_market() instead of buy_market().
"""

from Strategy.presets import RiskPreset, StrategyPreset
from app.MT4Service import MT4Service

async def run_market_one_shot(svc: MT4Service, strategy: StrategyPreset, risk: RiskPreset) -> dict:
    sugar = svc.sugar
    sugar.set_defaults(
        symbol=strategy.symbol,
        magic=strategy.magic,
        deviation_pips=strategy.deviation_pips,
        risk_percent=risk.risk_percent,
    )
    await sugar.ensure_connected()
    await sugar.ensure_symbol(strategy.symbol)

    lots = strategy.lots or await sugar.calc_lot_by_risk(strategy.symbol, risk_percent=risk.risk_percent, stop_pips=risk.sl_pips)
    ticket = await sugar.buy_market(
        symbol=strategy.symbol, lots=lots, sl_pips=risk.sl_pips, tp_pips=risk.tp_pips, comment=strategy.comment
    )

    subs = {}
    if risk.trailing_pips:
        subs["trailing"] = await sugar.set_trailing_stop(ticket, distance_pips=risk.trailing_pips, step_pips=1.0)
    if risk.be_trigger_pips:
        subs["auto_be"] = await sugar.auto_breakeven(ticket, trigger_pips=risk.be_trigger_pips, plus_pips=risk.be_plus_pips)

    try:
        filled = await sugar.wait_filled(ticket, timeout_s=300)
    except TimeoutError:
        filled = {"ticket": ticket, "status": "pending_timeout"}

    snap = await sugar.diag_snapshot()
    return {"ticket": ticket, "subscriptions": subs, "filled": filled, "snapshot": snap}
