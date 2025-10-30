# -*- coding: utf-8 -*-
"""
OCO-Straddle Orchestrator 🎢
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Purpose: Bi-directional breakout strategy using OCO (One-Cancels-the-Other) logic.
         Catches breakouts regardless of direction - let the market decide! 📈📉

Strategy Concept:
Place two pending stop orders around current price:
  ▲ BUY STOP  above mid-price (+offset_pips)  → Catches upward breakouts
  ▼ SELL STOP below mid-price (-offset_pips)  → Catches downward breakouts

When one side triggers → automatically cancel the other side (OCO logic)

Perfect For:
🎯 Range breakouts (consolidation zones)
🎯 News events (direction uncertain, volatility expected)
🎯 Support/resistance breaks
🎯 Market open volatility
🎯 "I don't know direction, but I know there will be movement"

Visual Example:
  Current Price (mid): 1.1000

        ▲ BUY STOP:  1.1010  (+10 pips)
        ─────────────────────
             1.1000  (mid)
        ─────────────────────
        ▼ SELL STOP: 1.0990  (-10 pips)

Features:
┌──────────────────────┬─────────────────────────────────────────────────┐
│ OCO Logic            │ First fill cancels opposite side automatically  │
├──────────────────────┼─────────────────────────────────────────────────┤
│ Spread Guard         │ Skip trade if spread too wide (optional)        │
├──────────────────────┼─────────────────────────────────────────────────┤
│ Risk Modes           │ Full risk per leg OR split risk (half/half)     │
├──────────────────────┼─────────────────────────────────────────────────┤
│ Auto Management      │ Optional trailing stop + auto breakeven         │
├──────────────────────┼─────────────────────────────────────────────────┤
│ Timeout Protection   │ Auto-cancel both if no fill within timeout      │
└──────────────────────┴─────────────────────────────────────────────────┘

Parameters:
- sp: StrategyPreset (symbol, magic, deviation_pips, comment)
- rp: RiskPreset (risk_percent, sl_pips, tp_pips, trailing_pips, be_trigger_pips)
- offset_pips: Distance from mid-price to place stops (e.g., 10 pips)
- timeout_s: Max wait for fill before canceling both (default 1200s = 20min)
- risk_mode:
    * "per_leg_full" - Full risk on each (only one expected to fill)
    * "per_leg_half" - Split risk 50/50 (safer if both could fill)
- max_spread_pips: Skip if spread exceeds this (optional guard)

Risk Modes Explained:
🔸 per_leg_full: Total risk = risk_percent (assumes only ONE leg fills)
   Example: 2% risk → BUY Stop: 2%, SELL Stop: 2% (but only one triggers)

🔸 per_leg_half: Total risk = risk_percent ÷ 2 per leg
   Example: 2% risk → BUY Stop: 1%, SELL Stop: 1% (safer if both could fill)

Execution Flow:
1. Setup defaults (symbol, magic, deviation, risk%)
2. Check spread guard (skip if too wide)
3. Get mid-price and calculate BUY/SELL stop prices
4. Calculate lot sizes based on risk_mode
5. Place BUY STOP above mid (+offset_pips) with SL/TP
6. Place SELL STOP below mid (-offset_pips) with SL/TP
7. Wait for FIRST_COMPLETED (race between two legs)
8. When one fills:
   - Identify filled leg (buy or sell)
   - Cancel opposite leg immediately (OCO)
   - Setup optional management (trailing + breakeven)
9. If timeout → cancel both legs and exit
10. Return detailed execution report

Returns:
dict {
  "status": "filled" | "timeout_no_fill" | "skipped_due_to_spread",
  "filled_side": "buy" | "sell",        # Which leg triggered
  "filled": {...},                      # Fill details
  "canceled_side": "buy" | "sell",      # Which leg was canceled
  "tickets": {"buy": int, "sell": int}, # Both ticket numbers
  "subscriptions": {                    # Active management
    "trailing": {...},
    "auto_be": {...}
  },
  "snapshot": {...},                    # Account diagnostic
  "meta": {...}                         # Strategy configuration
}

Requirements (svc.sugar API):
- Core: set_defaults, ensure_connected, ensure_symbol
- Pricing: mid_price, pips_to_price, spread_pips
- Risk: calc_lot_by_risk, normalize_lots
- Entry: buy_stop, sell_stop (or place_stop with side parameter)
- Management: wait_filled, cancel_order (or cancel_pendings), auto_breakeven, set_trailing_stop
- Monitoring: diag_snapshot

Safety Features:
✓ Robust timeout handling (auto-cancel if no action)
✓ Spread guard protection (skip expensive trades)
✓ Fallback cancellation logic (multiple cancel methods)
✓ Error handling for management features (non-blocking)
"""

from __future__ import annotations
import asyncio
from dataclasses import asdict

# Types below assume your presets look like in our plan
from Strategy.presets import StrategyPreset, RiskPreset

async def run_oco_straddle(
    svc,
    sp: StrategyPreset,
    rp: RiskPreset,
    *,
    offset_pips: float = 10.0,
    timeout_s: int = 1200,
    risk_mode: str = "per_leg_full",
    max_spread_pips: float | None = None,
) -> dict:
    """
    Args:
        svc: MT4Service (has .sugar with all helpers)
        sp: StrategyPreset (symbol, magic, deviation_pips, comment)
        rp: RiskPreset (risk_percent, sl_pips, tp_pips, be_* / trailing_*)
        offset_pips: distance from mid-price to place stop entries (both sides).
        timeout_s: overall wait before auto-cancel if nothing fills.
        risk_mode:
            - "per_leg_full": full risk on each stop (only one should trigger).
            - "per_leg_half": split risk across two legs (half on each).
        max_spread_pips: optional spread guard; skip if current spread is larger.
    Returns:
        dict with tickets, filled leg info, canceled leg info, snapshot and meta.
    """
    sugar = svc.sugar

    # 1) Basic guards and defaults
    sugar.set_defaults(
        symbol=sp.symbol,
        magic=sp.magic,
        deviation_pips=sp.deviation_pips,
        risk_percent=rp.risk_percent,
    )
    await sugar.ensure_connected()
    await sugar.ensure_symbol(sp.symbol)

    # Spread guard if requested
    if max_spread_pips is not None:
        sp_now = await sugar.spread_pips(sp.symbol)
        if sp_now > max_spread_pips:
            return {
                "status": "skipped_due_to_spread",
                "spread_pips": sp_now,
                "max_spread_pips": max_spread_pips,
            }

    # 2) Compute entry prices from mid
    mid = await sugar.mid_price(sp.symbol)
    buy_price  = await sugar.pips_to_price(sp.symbol, mid, +abs(offset_pips))
    sell_price = await sugar.pips_to_price(sp.symbol, mid, -abs(offset_pips))

    # 3) Determine lots sizing
    base_lots = await sugar.calc_lot_by_risk(
        sp.symbol, risk_percent=rp.risk_percent, stop_pips=rp.sl_pips
    )
    if risk_mode == "per_leg_half":
        lots = await sugar.normalize_lots(sp.symbol, base_lots * 0.5)
    else:
        # Default: per_leg_full (since only one leg is expected to trigger)
        lots = base_lots

    # 4) Place OCO pending orders (Buy Stop above / Sell Stop below)
    # Prefer explicit buy_stop/sell_stop if your sugar provides them.
    # Fallbacks can be implemented if needed (e.g. generic place_stop with side).
    buy_ticket = await _place_buy_stop(
        sugar, sp.symbol, buy_price, lots, rp.sl_pips, rp.tp_pips, sp.comment
    )
    sell_ticket = await _place_sell_stop(
        sugar, sp.symbol, sell_price, lots, rp.sl_pips, rp.tp_pips, sp.comment
    )

    tickets = {"buy": buy_ticket, "sell": sell_ticket}

    # 5) Wait for FIRST_COMPLETED fill among both legs
    waiters = [
        asyncio.create_task(_safe_wait_filled(sugar, buy_ticket, timeout_s), name="buy"),
        asyncio.create_task(_safe_wait_filled(sugar, sell_ticket, timeout_s), name="sell"),
    ]
    done, pending = await asyncio.wait(waiters, return_when=asyncio.FIRST_COMPLETED)

    if not done:
        # Timeout before any completion -> cancel both and exit
        await _cancel_ticket(sugar, buy_ticket, sp.symbol)
        await _cancel_ticket(sugar, sell_ticket, sp.symbol)
        snap = await sugar.diag_snapshot()
        return {
            "status": "timeout_no_fill",
            "tickets": tickets,
            "snapshot": snap,
            "meta": {"preset_strategy": asdict(sp), "preset_risk": asdict(rp)},
        }

    # Identify filled leg and the other ticket
    first = done.pop()
    filled_result = first.result()  # dict from _safe_wait_filled
    filled_side = first.get_name()  # "buy" or "sell"
    other_side = "sell" if filled_side == "buy" else "buy"
    other_ticket = tickets[other_side]

    # 6) Cancel the opposite leg
    await _cancel_ticket(sugar, other_ticket, sp.symbol)

    # 7) After-fill protections (optional per RiskPreset)
    subs = {}
    try:
        main_ticket = filled_result.get("ticket") or tickets[filled_side]
        if rp.be_trigger_pips:
            subs["auto_be"] = await sugar.auto_breakeven(
                main_ticket, trigger_pips=rp.be_trigger_pips, plus_pips=rp.be_plus_pips
            )
        if rp.trailing_pips:
            subs["trailing"] = await sugar.set_trailing_stop(
                main_ticket, distance_pips=rp.trailing_pips, step_pips=1.0
            )
    except Exception as e:
        subs["setup_error"] = f"{type(e).__name__}: {e}"

    snap = await sugar.diag_snapshot()
    return {
        "status": "filled",
        "filled_side": filled_side,
        "filled": filled_result,
        "canceled_side": other_side,
        "tickets": tickets,
        "subscriptions": subs,
        "snapshot": snap,
        "meta": {
            "preset_strategy": asdict(sp),
            "preset_risk": asdict(rp),
            "offset_pips": offset_pips,
            "risk_mode": risk_mode,
            "timeout_s": timeout_s,
        },
    }


# --- Internals ---------------------------------------------------------------

async def _place_buy_stop(sugar, symbol, price, lots, sl_pips, tp_pips, comment):
    """Try sugar.buy_stop(); otherwise sugar.place_stop(side='buy')."""
    if hasattr(sugar, "buy_stop"):
        return await sugar.buy_stop(symbol=symbol, price=price, lots=lots,
                                    sl_pips=sl_pips, tp_pips=tp_pips, comment=comment)
    # Fallback naming
    if hasattr(sugar, "place_stop"):
        return await sugar.place_stop(symbol=symbol, side="buy", price=price, lots=lots,
                                      sl_pips=sl_pips, tp_pips=tp_pips, comment=comment)
    # If your API only has a generic 'bracket_order', adapt here:
    raise NotImplementedError("Neither sugar.buy_stop nor sugar.place_stop is available.")


async def _place_sell_stop(sugar, symbol, price, lots, sl_pips, tp_pips, comment):
    """Try sugar.sell_stop(); otherwise sugar.place_stop(side='sell')."""
    if hasattr(sugar, "sell_stop"):
        return await sugar.sell_stop(symbol=symbol, price=price, lots=lots,
                                     sl_pips=sl_pips, tp_pips=tp_pips, comment=comment)
    if hasattr(sugar, "place_stop"):
        return await sugar.place_stop(symbol=symbol, side="sell", price=price, lots=lots,
                                      sl_pips=sl_pips, tp_pips=tp_pips, comment=comment)
    raise NotImplementedError("Neither sugar.sell_stop nor sugar.place_stop is available.")


async def _safe_wait_filled(sugar, ticket, timeout_s: int):
    """Wait until the given ticket is filled or timeout; always return a dict."""
    try:
        res = await sugar.wait_filled(ticket, timeout_s=timeout_s)
        return {"ticket": ticket, "result": res}
    except asyncio.TimeoutError:
        return {"ticket": ticket, "result": {"status": "timeout"}}  # normalized format
    except Exception as e:
        return {"ticket": ticket, "error": f"{type(e).__name__}: {e}"}


async def _cancel_ticket(sugar, ticket, symbol):
    """Cancel a specific pending ticket; fallback to cancel all pendings for symbol."""
    try:
        if hasattr(sugar, "cancel_order"):
            await sugar.cancel_order(ticket)
        else:
            # Fallback: cancel all pending orders on this symbol
            await sugar.cancel_pendings(symbol=symbol)
    except Exception:
        # As a last resort, try to cancel all pending orders on the symbol
        try:
            await sugar.cancel_pendings(symbol=symbol)
        except Exception:
            pass


"""
Example of launch

# somewhere in your app
from app.MT4Service import MT4Service
from Strategy.presets.risk import Balanced
from Strategy.presets.strategy import MarketEURUSD  # symbol/magic/deviation/comment
from Strategy.orchestrator.oco_straddle import run_oco_straddle

svc = MT4Service(...)  

result = await run_oco_straddle(
svc,
MarketEURUSD, # use symbol/magic/deviation/comment from the preset
Balanced, # risk profile
offset_pips=12, # offsets from midpoint
timeout_s=1800, # wait up to 30 minutes
risk_mode="per_leg_full",
max_spread_pips=2.0, # can be removed
)
print(result)

"""