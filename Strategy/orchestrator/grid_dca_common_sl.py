# -*- coding: utf-8 -*-
"""
Grid-DCA with Common Stop/TP Orchestrator
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Strategy: Dollar Cost Averaging (DCA) via grid of limit orders with dynamic
          basket management - all filled positions share a common stop loss.

Concept:
BUY Grid:  Place limit orders BELOW current price (catching dips)
SELL Grid: Place limit orders ABOVE current price (catching rallies)

As positions fill → dynamically calculate and update:
- Common SL: Single basket stop for all filled positions (no individual SLs)
- Common TP: Optional unified take profit (VWAP-based or RR multiple)

Why Common Stop/TP?
✓ Manage basket as single unit - reduces risk of partial stops
✓ Better average entry via VWAP (Volume Weighted Average Price)
✓ Simplified management - one SL/TP instead of tracking individual levels
✓ Useful for mean-reversion strategies and range trading

Grid Parameters:
┌─────────────────────┬──────────────────────────────────────────────────────┐
│ steps               │ Number of limit orders in grid (e.g., 5 steps)      │
├─────────────────────┼──────────────────────────────────────────────────────┤
│ step_pips           │ Distance between each grid level (e.g., 10 pips)    │
├─────────────────────┼──────────────────────────────────────────────────────┤
│ base_price          │ Starting price (None = use mid/last price)          │
├─────────────────────┼──────────────────────────────────────────────────────┤
│ arm_when_filled     │ Start common SL after N fills (default: 1)          │
└─────────────────────┴──────────────────────────────────────────────────────┘

Risk Modes:
- per_leg_full: Each leg sized independently with full risk% (aggressive)
- split_total: Divide total risk% across all legs (conservative)

SL Anchor Options:
- lowest_leg: Anchor SL from lowest filled entry (BUY) / highest (SELL)
- avg_entry: Anchor SL from VWAP (average entry price)

TP Modes (Optional):
- fixed_pips_from_avg: TP at fixed pips from VWAP
- rr_multiple: TP based on Risk:Reward ratio (e.g., 2.0 = 2R)

Execution Flow:
1. Setup defaults and ensure symbol/connection
2. Calculate base price (mid/last if not provided)
3. Build price ladder (steps × step_pips apart)
4. Size lots per leg based on risk_mode
5. Place all limit orders with temporary individual SLs
6. Management loop:
   - Poll for fills (non-blocking waiters)
   - When fills >= arm_when_filled:
     * Calculate VWAP from filled positions
     * Compute common SL (from anchor: lowest_leg or avg_entry)
     * Compute common TP (if tp_mode configured)
     * Update ALL filled positions to common levels
7. Continue management until timeout or all exits
8. Return diagnostic snapshot with grid state

Returns:
dict with 'tickets', 'filled', 'common_sl', 'common_tp', 'snapshot', 'meta'

Requirements (svc.sugar API):
- Core: ensure_connected, ensure_symbol, set_defaults
- Pricing: pips_to_price, mid_price (or last_price)
- Risk: calc_lot_by_risk
- Entry: buy_limit, sell_limit
- Management: wait_filled, order_info, modify_order (or set_sl/set_tp)
- Monitoring: diag_snapshot
"""

from __future__ import annotations
import asyncio
from dataclasses import asdict
from typing import Literal, Optional

from Strategy.presets import StrategyPreset, RiskPreset


Side = Literal["buy", "sell"]
SLAnchor = Literal["lowest_leg", "avg_entry"]     # how to anchor common SL
TPMode = Literal["fixed_pips_from_avg", "rr_multiple"]


async def run_grid_dca_common_sl(
    svc,
    sp: StrategyPreset,
    rp: RiskPreset,
    *,
    side: Side = "buy",
    steps: int = 5,
    step_pips: float = 10.0,
    base_price: Optional[float] = None,      # if None, use mid price
    arm_when_filled_at_least: int = 1,       # start managing common SL after at least N fills
    sl_anchor: SLAnchor = "lowest_leg",      # "lowest_leg" (for BUY) / "highest_leg" (for SELL) semantics via sign
    # Risk:
    risk_mode: Literal["per_leg_full", "split_total"] = "split_total",
    risk_total_percent: Optional[float] = None,  # used when risk_mode == "split_total"
    # Common TP (optional):
    tp_mode: Optional[TPMode] = None,
    tp_fixed_pips: Optional[float] = None,       # for "fixed_pips_from_avg"
    tp_rr_multiple: Optional[float] = None,      # for "rr_multiple", e.g. 2.0
    # Runtime:
    placement_delay_ms: int = 0,             # small spacing between placements if desired
    manage_poll_interval_s: float = 1.0,     # how often to poll fills and update basket SL/TP
    manage_timeout_s: int = 3600,            # management loop max duration (1h default)
) -> dict:
    sugar = svc.sugar

    # 1) Setup and guards
    sugar.set_defaults(
        symbol=sp.symbol,
        magic=sp.magic,
        deviation_pips=sp.deviation_pips,
        risk_percent=rp.risk_percent,
    )
    await sugar.ensure_connected()
    await sugar.ensure_symbol(sp.symbol)

    # 2) Figure out base price
    if base_price is None:
        if hasattr(sugar, "mid_price"):
            base_price = await sugar.mid_price(sp.symbol)
        else:
            # fallback to last price
            base_price = await sugar.last_price(sp.symbol)  # type: ignore

    # 3) Build price ladder
    prices = []
    for i in range(steps):
        delta = step_pips * (i + 1)
        if side == "buy":
            price = await sugar.pips_to_price(sp.symbol, base_price, -abs(delta))
        else:
            price = await sugar.pips_to_price(sp.symbol, base_price, +abs(delta))
        prices.append(price)

    # 4) Decide lots sizing per leg
    if risk_mode == "split_total":
        total_risk = float(risk_total_percent or rp.risk_percent)
        per_leg_risk = total_risk / max(1, steps)
        lots_per_leg = []
        for _ in range(steps):
            l = await sugar.calc_lot_by_risk(sp.symbol, risk_percent=per_leg_risk, stop_pips=rp.sl_pips)
            lots_per_leg.append(l)
    else:
        # per_leg_full: each leg sized as if it were a standalone trade with rp.risk_percent
        lots_per_leg = []
        for _ in range(steps):
            l = await sugar.calc_lot_by_risk(sp.symbol, risk_percent=rp.risk_percent, stop_pips=rp.sl_pips)
            lots_per_leg.append(l)

    # 5) Place the ladder of pending limits with individual SL (temporary) and optional TP
    tickets: list[int] = []
    for i, (price, lots) in enumerate(zip(prices, lots_per_leg)):
        if side == "buy":
            if hasattr(sugar, "buy_limit"):
                t = await sugar.buy_limit(
                    symbol=sp.symbol, price=price, lots=lots,
                    sl_pips=rp.sl_pips, tp_pips=rp.tp_pips, comment=f"{sp.comment or ''} DCA {i+1}/{steps}"
                )
            else:
                raise NotImplementedError("Need sugar.buy_limit")
        else:
            if hasattr(sugar, "sell_limit"):
                t = await sugar.sell_limit(
                    symbol=sp.symbol, price=price, lots=lots,
                    sl_pips=rp.sl_pips, tp_pips=rp.tp_pips, comment=f"{sp.comment or ''} DCA {i+1}/{steps}"
                )
            else:
                raise NotImplementedError("Need sugar.sell_limit")
        tickets.append(t)
        if placement_delay_ms > 0:
            await asyncio.sleep(placement_delay_ms / 1000.0)

    # 6) Management loop: track fills, compute VWAP and apply common SL/TP
    filled: dict[int, float] = {}   # ticket -> open_price
    start_ts = asyncio.get_event_loop().time()
    updated_common_sl = None
    updated_common_tp = None

    async def _get_open_px(ticket: int) -> Optional[float]:
        # Try direct open price; else order_info lookup
        if hasattr(sugar, "get_open_price"):
            try:
                px = await sugar.get_open_price(ticket)
                if px is not None:
                    return float(px)
            except Exception:
                pass
        if hasattr(sugar, "order_info"):
            info = await sugar.order_info(ticket)
            for k in ("open_price", "OpenPrice", "price_open", "PriceOpen"):
                if k in info:
                    try:
                        return float(info[k])
                    except Exception:
                        pass
        return None

    def _vwap(pairs: list[tuple[float, float]]) -> float:
        # pairs: (price, lots)
        num = sum(p * v for p, v in pairs)
        den = sum(v for _, v in pairs) or 1.0
        return num / den

    async def _compute_common_levels(vwap_px: float, lowest_or_highest_px: float):
        # Common SL:
        if sl_anchor == "avg_entry":
            sl_ref = vwap_px
        else:
            # "lowest_leg" for BUY means use lowest filled entry as anchor;
            # for SELL it's the HIGHEST filled entry (sign inversion below).
            sl_ref = lowest_or_highest_px

        if side == "buy":
            common_sl = await sugar.pips_to_price(sp.symbol, sl_ref, -abs(rp.sl_pips))
        else:
            common_sl = await sugar.pips_to_price(sp.symbol, sl_ref, +abs(rp.sl_pips))

        # Common TP (optional)
        common_tp = None
        if tp_mode == "fixed_pips_from_avg" and tp_fixed_pips:
            if side == "buy":
                common_tp = await sugar.pips_to_price(sp.symbol, vwap_px, +abs(tp_fixed_pips))
            else:
                common_tp = await sugar.pips_to_price(sp.symbol, vwap_px, -abs(tp_fixed_pips))
        elif tp_mode == "rr_multiple" and tp_rr_multiple and rp.sl_pips:
            rr_pips = float(tp_rr_multiple) * float(rp.sl_pips)
            if side == "buy":
                common_tp = await sugar.pips_to_price(sp.symbol, vwap_px, +abs(rr_pips))
            else:
                common_tp = await sugar.pips_to_price(sp.symbol, vwap_px, -abs(rr_pips))

        return common_sl, common_tp

    async def _apply_common_levels(common_sl: float, common_tp: Optional[float]):
        # Try a modify API; fall back to set_sl / set_tp if available.
        for tk in list(filled.keys()):
            try:
                if hasattr(sugar, "modify_order"):
                    await sugar.modify_order(tk, sl_price=common_sl, tp_price=common_tp)
                else:
                    if hasattr(sugar, "set_sl"):
                        await sugar.set_sl(tk, common_sl)
                    if common_tp is not None and hasattr(sugar, "set_tp"):
                        await sugar.set_tp(tk, common_tp)
            except Exception:
                # best effort, continue
                pass

    # Kick off non-blocking waiters for each ticket to detect fills
    waiters = {
        tk: asyncio.create_task(_safe_wait_fill(sugar, tk, manage_timeout_s))
        for tk in tickets
    }

    while True:
        elapsed = asyncio.get_event_loop().time() - start_ts
        if elapsed >= manage_timeout_s:
            break

        # Incorporate newly filled tickets
        for tk, task in list(waiters.items()):
            if task.done():
                res = task.result()
                if res.get("status") == "filled":
                    px = await _get_open_px(tk)
                    if px is not None:
                        # Approximate fill lots: if order_info returns volume
                        lots = res.get("lots")
                        if lots is None:
                            # If lots not provided by wait_filled result, try info
                            if hasattr(sugar, "order_info"):
                                inf = await sugar.order_info(tk)
                                for lk in ("lots", "volume", "Lots", "Volume"):
                                    if lk in inf:
                                        try:
                                            lots = float(inf[lk]); break
                                        except Exception:
                                            pass
                        if lots is None:
                            # fallback: use per-leg planned lots (rough)
                            idx = tickets.index(tk)
                            lots = lots_per_leg[idx]
                        filled[tk] = (px, float(lots))
                # remove watcher
                waiters.pop(tk, None)

        # Update common SL/TP once we have enough filled legs
        if len(filled) >= arm_when_filled_at_least:
            # Compute VWAP and anchor
            pairs = list(filled.values())  # (px, lots)
            vwap_px = _vwap(pairs)
            # lowest for BUY / highest for SELL
            if side == "buy":
                anchor_px = min(px for px, _ in pairs)
            else:
                anchor_px = max(px for px, _ in pairs)

            common_sl, common_tp = await _compute_common_levels(vwap_px, anchor_px)

            # Apply only if changed (basic hysteresis could be added if needed)
            if updated_common_sl != common_sl or updated_common_tp != common_tp:
                await _apply_common_levels(common_sl, common_tp)
                updated_common_sl, updated_common_tp = common_sl, common_tp

        # Break if nothing left to wait OR all orders processed
        if not waiters:
            # No more pendings being watched; we can exit the manager loop.
            break

        await asyncio.sleep(manage_poll_interval_s)

    snap = await sugar.diag_snapshot()
    return {
        "status": "ok",
        "side": side,
        "tickets": tickets,
        "filled_count": len(filled),
        "common_sl": updated_common_sl,
        "common_tp": updated_common_tp,
        "snapshot": snap,
        "meta": {
            "preset_strategy": asdict(sp),
            "preset_risk": asdict(rp),
            "steps": steps,
            "step_pips": step_pips,
            "base_price": base_price,
            "risk_mode": risk_mode,
            "risk_total_percent": risk_total_percent,
            "arm_when_filled_at_least": arm_when_filled_at_least,
            "sl_anchor": sl_anchor,
            "tp_mode": tp_mode,
            "tp_fixed_pips": tp_fixed_pips,
            "tp_rr_multiple": tp_rr_multiple,
        },
    }


# --- helpers -----------------------------------------------------------------

async def _safe_wait_fill(sugar, ticket: int, timeout_s: int) -> dict:
    """Waits for fill or timeout; returns a small dict."""
    try:
        r = await sugar.wait_filled(ticket, timeout_s=timeout_s)
        # try to extract filled lots from result if present
        lots = None
        for k in ("lots", "volume", "filled_lots", "Lots", "Volume"):
            if isinstance(r, dict) and k in r:
                try:
                    lots = float(r[k]); break
                except Exception:
                    pass
        return {"status": "filled", "res": r, "lots": lots}
    except asyncio.TimeoutError:
        return {"status": "timeout"}
    except Exception as e:
        return {"status": "error", "error": f"{type(e).__name__}: {e}"}

"""
Example of launch

from app.MT4Service import MT4Service
from Strategy.presets.risk import Balanced
from Strategy.presets.strategy import MarketEURUSD
from Strategy.orchestrator.grid_dca_common_sl import run_grid_dca_common_sl

svc = MT4Service(...)

# EURUSD BUY grid: 5 steps, 10 pip increments, common SL from the "lowest" fill,
# common TP = RR = 2.0 of VWAP, total risk of 1% per basket (divided by 5 steps)
res = await run_grid_dca_common_sl(
    svc, MarketEURUSD, Balanced,
    side="buy",
    steps=5, step_pips=10,
    base_price=None,                 
    sl_anchor="lowest_leg",
    risk_mode="split_total", risk_total_percent=1.0,
    tp_mode="rr_multiple", tp_rr_multiple=2.0,
    arm_when_filled_at_least=1,
    manage_timeout_s=3600,
)

"""