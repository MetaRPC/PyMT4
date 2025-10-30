# -*- coding: utf-8 -*-
"""
Bracket + Trailing Activation Orchestrator
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Strategy: Opens a position with bracket (SL/TP), then activates trailing stop
         only after the position reaches a specified profit threshold.

Execution Flow:
1. Entry: Place market or limit order with immediate SL/TP bracket protection
2. Wait: Wait for order fill (with timeout for pending orders)
3. Breakeven: Optional auto-breakeven guard (if configured in RiskPreset)
4. Monitor: Poll position profit in pips until it reaches activation threshold
5. Trail: Enable trailing stop with specified distance/step once threshold is hit
6. Return: Provide detailed execution report with snapshots

Parameters:
- activate_trailing_at_pips: Profit threshold to enable trailing (e.g., 12.0 pips)
- trailing_distance_pips: Distance from current price for trailing SL (from RiskPreset)
- trailing_step_pips: Minimum price movement to update trailing SL (e.g., 1.0 pip)
- wait_fill_timeout_s: Max seconds to wait for pending order fill (default 1200s)
- max_spread_pips: Optional spread guard - skip trade if spread too wide

Requirements (svc.sugar API):
- Core: set_defaults, ensure_connected, ensure_symbol, calc_lot_by_risk
- Entry: buy_market, sell_market, buy_limit, sell_limit
- Management: wait_filled, cancel_pendings, set_trailing_stop
- Monitoring: position_unrealized_pips (or fallback: pips_between_prices helpers)
- Optional: auto_breakeven, diag_snapshot

Returns:
dict with 'status', 'ticket', 'filled', 'subscriptions', 'activation', 'snapshot', 'meta'
"""

from __future__ import annotations
import asyncio
from dataclasses import asdict
from typing import Optional

from Strategy.presets import StrategyPreset, RiskPreset


async def run_bracket_with_trailing_activation(
    svc,
    sp: StrategyPreset,
    rp: RiskPreset,
    *,
    side: str = "buy",                          # "buy" or "sell"
    activate_trailing_at_pips: float = 12.0,    # when to turn trailing ON
    trailing_distance_pips: Optional[float] = None,  # distance for trailing; fallback to rp.trailing_pips
    trailing_step_pips: float = 1.0,            # trail step
    wait_fill_timeout_s: int = 1200,            # pending fill timeout
    max_spread_pips: Optional[float] = None,    # optional guard
    poll_interval_s: float = 1.0,               # poll cycle for profit pips
) -> dict:
    """
    Returns a dict with 'ticket', 'filled', optional 'subscriptions', 'activation',
    and final 'snapshot'.
    """
    sugar = svc.sugar

    # 1) Defaults & guards
    sugar.set_defaults(
        symbol=sp.symbol,
        magic=sp.magic,
        deviation_pips=sp.deviation_pips,
        risk_percent=rp.risk_percent,
    )
    await sugar.ensure_connected()
    await sugar.ensure_symbol(sp.symbol)

    if max_spread_pips is not None:
        cur_spread = await sugar.spread_pips(sp.symbol)
        if cur_spread > max_spread_pips:
            return {
                "status": "skipped_due_to_spread",
                "spread_pips": cur_spread,
                "max_spread_pips": max_spread_pips,
            }

    # 2) Sizing
    lots = sp.lots or await sugar.calc_lot_by_risk(
        sp.symbol, risk_percent=rp.risk_percent, stop_pips=rp.sl_pips
    )

    # 3) Place order (market or limit) with bracket (SL/TP)
    ticket = await _place_entry_with_bracket(
        sugar=sugar,
        sp=sp,
        side=side,
        lots=lots,
        sl_pips=rp.sl_pips,
        tp_pips=rp.tp_pips,
        comment=sp.comment,
    )

    # 4) Wait for fill (or cancel pending on timeout)
    try:
        filled = await sugar.wait_filled(ticket, timeout_s=wait_fill_timeout_s)
    except asyncio.TimeoutError:
        # pending never filled -> clean up and return
        await sugar.cancel_pendings(symbol=sp.symbol)
        snap = await sugar.diag_snapshot()
        return {
            "status": "cancelled_by_timeout",
            "ticket": ticket,
            "snapshot": snap,
            "meta": {"preset_strategy": asdict(sp), "preset_risk": asdict(rp)},
        }

    # 5) Optional: auto-breakeven (independent from trailing activation)
    subs = {}
    if rp.be_trigger_pips:
        try:
            subs["auto_be"] = await sugar.auto_breakeven(
                ticket,
                trigger_pips=rp.be_trigger_pips,
                plus_pips=rp.be_plus_pips,
            )
        except Exception as e:
            subs["auto_be_error"] = f"{type(e).__name__}: {e}"

    # 6) Activate trailing only after profit >= threshold
    #    If no explicit trailing_distance provided, use rp.trailing_pips.
    trailing_distance = trailing_distance_pips or rp.trailing_pips
    activation = {"activated": False, "reason": None}

    if trailing_distance and activate_trailing_at_pips > 0:
        try:
            await _wait_profit_threshold_and_start_trailing(
                sugar=sugar,
                symbol=sp.symbol,
                ticket=ticket,
                side=side,
                threshold_pips=activate_trailing_at_pips,
                trailing_distance_pips=trailing_distance,
                trailing_step_pips=trailing_step_pips,
                poll_interval_s=poll_interval_s,
            )
            activation["activated"] = True
            activation["distance_pips"] = trailing_distance
            activation["threshold_pips"] = activate_trailing_at_pips
            activation["step_pips"] = trailing_step_pips
        except Exception as e:
            activation["reason"] = f"{type(e).__name__}: {e}"
    else:
        activation["reason"] = "no_trailing_requested"

    # 7) Final snapshot for user diagnostics
    snap = await sugar.diag_snapshot()
    return {
        "status": "ok",
        "ticket": ticket,
        "filled": filled,
        "subscriptions": subs,
        "activation": activation,
        "snapshot": snap,
        "meta": {
            "preset_strategy": asdict(sp),
            "preset_risk": asdict(rp),
            "side": side,
            "wait_fill_timeout_s": wait_fill_timeout_s,
        },
    }


# --- Internals ---------------------------------------------------------------

async def _place_entry_with_bracket(
    *,
    sugar,
    sp: StrategyPreset,
    side: str,
    lots: float,
    sl_pips: float,
    tp_pips: float | None,
    comment: str | None,
):
    """Route to buy/sell and market/limit variants depending on StrategyPreset."""
    use_market = bool(sp.use_market)
    if side not in ("buy", "sell"):
        raise ValueError("side must be 'buy' or 'sell'")

    if use_market:
        if side == "buy":
            # Prefer sugar.buy_market if exists; otherwise map accordingly.
            if hasattr(sugar, "buy_market"):
                return await sugar.buy_market(
                    symbol=sp.symbol, lots=lots, sl_pips=sl_pips, tp_pips=tp_pips, comment=comment
                )
            # Fallbacks here if your API differs...
        else:
            if hasattr(sugar, "sell_market"):
                return await sugar.sell_market(
                    symbol=sp.symbol, lots=lots, sl_pips=sl_pips, tp_pips=tp_pips, comment=comment
                )
    else:
        if sp.entry_price is None:
            raise ValueError("entry_price is required for limit entries")
        if side == "buy":
            if hasattr(sugar, "buy_limit"):
                return await sugar.buy_limit(
                    symbol=sp.symbol, price=sp.entry_price, lots=lots,
                    sl_pips=sl_pips, tp_pips=tp_pips, comment=comment
                )
        else:
            if hasattr(sugar, "sell_limit"):
                return await sugar.sell_limit(
                    symbol=sp.symbol, price=sp.entry_price, lots=lots,
                    sl_pips=sl_pips, tp_pips=tp_pips, comment=comment
                )

    raise NotImplementedError("Cannot map entry to your sugar API; please adjust names.")


async def _wait_profit_threshold_and_start_trailing(
    *,
    sugar,
    symbol: str,
    ticket,
    side: str,
    threshold_pips: float,
    trailing_distance_pips: float,
    trailing_step_pips: float,
    poll_interval_s: float,
):
    """
    Poll unrealized pips until it reaches threshold, then enable trailing stop.

    If sugar has `position_unrealized_pips(ticket)`, use it directly.
    Otherwise compute manually using open price, current price and side.
    """
    # Try the direct API first
    if hasattr(sugar, "position_unrealized_pips"):
        while True:
            up = await sugar.position_unrealized_pips(ticket)
            if up is None:
                # If position not found yet, keep polling
                await asyncio.sleep(poll_interval_s)
                continue
            if up >= threshold_pips:
                break
            await asyncio.sleep(poll_interval_s)
    else:
        # Manual calc fallback
        # We assume sugar has helpers: get_open_price(ticket), last_price(symbol), pips_between_prices(symbol, p1, p2)
        while True:
            open_price = await _get_open_price(sugar, ticket)
            last = await _get_last_price(sugar, symbol, side)
            # For BUY: profit if last > open; For SELL: profit if last < open.
            pips = await sugar.pips_between_prices(symbol, open_price, last)
            if side == "sell":
                pips = -pips  # reverse sign for sell to represent profit positively
            if pips >= threshold_pips:
                break
            await asyncio.sleep(poll_interval_s)

    # Activate trailing
    await sugar.set_trailing_stop(
        ticket, distance_pips=trailing_distance_pips, step_pips=trailing_step_pips
    )


async def _get_open_price(sugar, ticket) -> float:
    """Best-effort to get open price for a given ticket."""
    if hasattr(sugar, "get_open_price"):
        return await sugar.get_open_price(ticket)
    if hasattr(sugar, "order_info"):
        info = await sugar.order_info(ticket)
        for k in ("open_price", "OpenPrice", "price_open", "PriceOpen"):
            if k in info:
                return float(info[k])
    raise NotImplementedError("Need get_open_price/order_info helper in sugar.")


async def _get_last_price(sugar, symbol: str, side: str) -> float:
    """
    Get the relevant last price to estimate P/L:
    - For BUY, use Bid to be conservative (you close at Bid).
    - For SELL, use Ask (you close at Ask).
    """
    if hasattr(sugar, "last_bid_ask"):
        ba = await sugar.last_bid_ask(symbol)
        bid, ask = float(ba["bid"]), float(ba["ask"])
        return bid if side == "buy" else ask

    # Fallback if only 'last_price' or 'mid_price' exist:
    if hasattr(sugar, "last_price"):
        return await sugar.last_price(symbol)
    if hasattr(sugar, "mid_price"):
        return await sugar.mid_price(symbol)

    raise NotImplementedError("Need last price helper (last_bid_ask/last_price/mid_price).")

"""
Example of launch

from app.MT4Service import MT4Service
from Strategy.presets.risk import Balanced
from Strategy.presets.strategy import MarketEURUSD, LimitEURUSD
from Strategy.orchestrator.bracket_trailing_activation import run_bracket_with_trailing_activation

svc = MT4Service(...)

# 1) Market buy → SL/TP immediately → trailing will be activated after +12 pips
res1 = await run_bracket_with_trailing_activation(
    svc, MarketEURUSD, Balanced,
    side="buy",
    activate_trailing_at_pips=12.0,
    trailing_distance_pips=6.0,  # If you don't specify, it will take rp.trailing_pips
    max_spread_pips=2.0,
)

# 2) Limit sale (example)
res2 = await run_bracket_with_trailing_activation(
    svc, LimitEURUSD(1.07500), Balanced,
    side="sell",
    activate_trailing_at_pips=15.0,
    trailing_distance_pips=8.0,
    wait_fill_timeout_s=1800,
)

"""