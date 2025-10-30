# Strategy/orchestrator/pending_bracket.py
"""
Pending Bracket Orchestrator ⏰
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Purpose: Place limit order at specific price with automatic bracket protection.
         "Set your price, wait for the market to come to you" strategy.

Strategy Profile:
✓ Precision: Enter at exact price (no slippage from market orders)
✓ Patience: Wait for market to reach your level
✓ Protection: Automatic SL/TP once filled
✓ Management: Optional trailing stop and auto-breakeven after fill

Perfect For:
🎯 Support/resistance trading (buy at support, sell at resistance)
🎯 Limit order entries (better price than market)
🎯 Mean reversion strategies (buy dips, sell rallies)
🎯 Range trading (buy low, sell high)
🎯 Patient traders who want specific entry prices

Visual Example (BUY LIMIT):
  Current Price: 1.1020

        ─────────────────────  (Market here)
             ↓ Waiting...
        ═════════════════════  1.1000 ← Your limit order
             ↓ Price comes down
        ─────────────────────  (Filled!)

  After fill → SL/TP automatically set + optional trailing/breakeven

Features:
┌──────────────────────┬─────────────────────────────────────────────────┐
│ Limit Order Entry    │ Enter at specified price (better than market)   │
├──────────────────────┼─────────────────────────────────────────────────┤
│ Auto Bracket         │ SL/TP set immediately on fill                   │
├──────────────────────┼─────────────────────────────────────────────────┤
│ Wait for Fill        │ Patient wait for market to reach your price     │
├──────────────────────┼─────────────────────────────────────────────────┤
│ Timeout Protection   │ Auto-cancel if not filled within timeout        │
├──────────────────────┼─────────────────────────────────────────────────┤
│ Post-Fill Management │ Optional trailing stop + auto breakeven         │
└──────────────────────┴─────────────────────────────────────────────────┘

Parameters:
- strategy: StrategyPreset (symbol, magic, deviation_pips, lots, entry_price, comment)
  ⚠️ IMPORTANT: entry_price must be set (raises ValueError if None)
- risk: RiskPreset (risk_percent, sl_pips, tp_pips, trailing_pips,
                     be_trigger_pips, be_plus_pips)
- timeout_s: Max seconds to wait for fill (default 900s = 15min)

Entry Price Logic:
🔹 BUY LIMIT: entry_price < current price (buy at lower price)
🔹 SELL LIMIT: entry_price > current price (sell at higher price)

Execution Flow:
1. Setup defaults (symbol, magic, deviation, risk%)
2. Ensure connection and symbol availability
3. Validate entry_price is provided (raise error if None)
4. Calculate lot size (use preset lots OR calc by risk%)
5. Place BUY LIMIT order with SL/TP at entry_price
6. Wait for order fill (with timeout):
   - If filled → continue to step 7
   - If timeout → cancel pending order and exit
7. After fill, activate management features (if configured):
   - Trailing stop: Locks profit as price moves favorably
   - Auto breakeven: Moves SL to entry + plus_pips after trigger
8. Capture diagnostic snapshot
9. Return complete execution report

Timeout Behavior:
⏰ If market doesn't reach entry_price within timeout_s:
   → Cancel pending order
   → Return status "cancelled_by_timeout"
   → No loss, just missed opportunity

Returns:
dict {
  "ticket": int,                    # Order ticket number
  "status": "cancelled_by_timeout"  # If timeout (only in this case)
  "filled": {...},                  # Fill confirmation (if filled)
  "subscriptions": {                # Active management features (if filled)
    "trailing": {...},              # Trailing stop details
    "auto_be": {...}                # Auto breakeven details
  },
  "snapshot": {...}                 # Account diagnostic snapshot (if filled)
}

Requirements (svc.sugar API):
- Core: set_defaults, ensure_connected, ensure_symbol
- Risk: calc_lot_by_risk
- Entry: buy_limit (with SL/TP support)
- Management: wait_filled, cancel_pendings, set_trailing_stop, auto_breakeven
- Monitoring: diag_snapshot

Note: Currently only supports BUY LIMIT direction.
      For SELL LIMIT, replace buy_limit() with sell_limit().
      For STOP orders, use buy_stop()/sell_stop() instead.
"""

from Strategy.presets import RiskPreset, StrategyPreset

async def run_pending_bracket(svc, strategy: StrategyPreset, risk: RiskPreset, *, timeout_s: int = 900) -> dict:
    sugar = svc.sugar
    sugar.set_defaults(symbol=strategy.symbol, magic=strategy.magic, deviation_pips=strategy.deviation_pips, risk_percent=risk.risk_percent)
    await sugar.ensure_connected()
    await sugar.ensure_symbol(strategy.symbol)

    if strategy.entry_price is None:
        raise ValueError("entry_price is required for pending orders")

    lots = strategy.lots or await sugar.calc_lot_by_risk(strategy.symbol, risk_percent=risk.risk_percent, stop_pips=risk.sl_pips)
    ticket = await sugar.buy_limit(symbol=strategy.symbol, price=strategy.entry_price, lots=lots, sl_pips=risk.sl_pips, tp_pips=risk.tp_pips, comment=strategy.comment)

    try:
        filled = await sugar.wait_filled(ticket, timeout_s=timeout_s)
    except TimeoutError:
        await sugar.cancel_pendings(symbol=strategy.symbol)
        return {"ticket": ticket, "status": "cancelled_by_timeout"}

    subs = {}
    if risk.trailing_pips:
        subs["trailing"] = await sugar.set_trailing_stop(ticket, distance_pips=risk.trailing_pips, step_pips=1.0)
    if risk.be_trigger_pips:
        subs["auto_be"] = await sugar.auto_breakeven(ticket, trigger_pips=risk.be_trigger_pips, plus_pips=risk.be_plus_pips)

    snap = await sugar.diag_snapshot()
    return {"ticket": ticket, "filled": filled, "subscriptions": subs, "snapshot": snap}
