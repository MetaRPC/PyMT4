# -*- coding: utf-8 -*-
"""
Kill-Switch with Review Orchestrator
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Purpose: Emergency shutdown mechanism with detailed post-action review.
         Closes positions and cancels pending orders with granular control.

Use Cases:
🚨 Emergency Situations:
   - Major news event / market crash
   - Strategy malfunction detected
   - Unexpected market behavior
   - End of trading session
   - System maintenance required

📊 Selective Cleanup:
   - Take profits only (close winners, keep losers)
   - Symbol-specific cleanup (e.g., only EURUSD)
   - Full account shutdown (nuclear option)

Features:
┌──────────────────────┬────────────────────────────────────────────────────┐
│ Scope Control        │ Single symbol OR entire account                    │
├──────────────────────┼────────────────────────────────────────────────────┤
│ Profit Filter        │ Close all / only winners / only losers             │
├──────────────────────┼────────────────────────────────────────────────────┤
│ Pending Orders       │ Automatically cancelled in scope                   │
├──────────────────────┼────────────────────────────────────────────────────┤
│ Post-Action Review   │ Detailed snapshot + aggregated summary             │
├──────────────────────┼────────────────────────────────────────────────────┤
│ Error Safety         │ Errors collected but don't stop execution          │
└──────────────────────┴────────────────────────────────────────────────────┘

Parameters:
- symbol: Target symbol (None = entire account)
- only_profit: None (all) / True (only winners) / False (only losers)
- include_snapshot: Return full diagnostic snapshot (default: True)

Safe by Design:
✓ Non-blocking errors: Each step wrapped in try/catch
✓ Error collection: All errors reported but don't halt execution
✓ Tolerant parsing: Review extraction works with various snapshot formats
✓ Audit trail: All actions logged with scope and filters

Execution Flow:
1. Ensure connection is active
2. Close positions in scope (with profit filter if specified)
   - Log action and scope (symbol or ALL)
   - Collect errors but continue
3. Cancel all pending orders in scope
   - Log action and scope
   - Collect errors but continue
4. Capture diagnostic snapshot (if enabled)
5. Generate quick review summary:
   - Remaining open positions count
   - Remaining pending orders count
   - Unrealized P/L
   - Account metrics (equity, balance, margin, free margin)
6. Return structured result with actions, errors, review, and snapshot

Returns:
dict {
  "status": "ok" | "ok_with_warnings",
  "actions": [...],              # List of executed actions
  "errors": [...] | None,        # Errors encountered (if any)
  "review": {                    # Quick summary
    "scope": {...},
    "remaining_open_positions": int,
    "remaining_pendings": int,
    "unrealized_pl": float,
    "equity": float,
    "balance": float,
    ...
  },
  "snapshot": {...}              # Full diagnostic snapshot (if enabled)
}

Requirements (svc.sugar API):
- ensure_connected: Verify connection is active
- close_all: Close positions (with symbol and only_profit filters)
- cancel_pendings: Cancel pending orders (with symbol filter)
- diag_snapshot: Get full account diagnostics
"""

from __future__ import annotations
from typing import Optional, Dict, Any


async def run_kill_switch_with_review(
    svc,
    *,
    symbol: Optional[str] = None,        # None -> all symbols
    only_profit: Optional[bool] = None,  # None -> close all; True -> close only winners; False -> close all
    include_snapshot: bool = True,       # whether to return sugar.diag_snapshot()
) -> Dict[str, Any]:
    sugar = svc.sugar
    await sugar.ensure_connected()

    actions = []
    errors = []

    # 1) Close all (in scope)
    try:
        if symbol:
            await sugar.close_all(symbol=symbol, only_profit=only_profit)
            actions.append({"action": "close_all", "scope": {"symbol": symbol}, "only_profit": only_profit})
        else:
            # If your API supports global close_all without symbol, pass symbol=None
            await sugar.close_all(symbol=None, only_profit=only_profit)
            actions.append({"action": "close_all", "scope": "ALL", "only_profit": only_profit})
    except Exception as e:
        errors.append({"stage": "close_all", "error": f"{type(e).__name__}: {e}"})

    # 2) Cancel all pendings (in scope)
    try:
        if symbol:
            await sugar.cancel_pendings(symbol=symbol)
            actions.append({"action": "cancel_pendings", "scope": {"symbol": symbol}})
        else:
            # If your API supports cancel_pendings() global via symbol=None, use that
            await sugar.cancel_pendings(symbol=None)
            actions.append({"action": "cancel_pendings", "scope": "ALL"})
    except Exception as e:
        errors.append({"stage": "cancel_pendings", "error": f"{type(e).__name__}: {e}"})

    # 3) Snapshot after cleanup
    snapshot = None
    if include_snapshot:
        try:
            snapshot = await sugar.diag_snapshot()
        except Exception as e:
            errors.append({"stage": "diag_snapshot", "error": f"{type(e).__name__}: {e}"})

    # 4) Quick review (best-effort) from snapshot
    review = _quick_review_from_snapshot(snapshot, symbol=symbol) if snapshot else None

    result = {
        "status": "ok" if not errors else "ok_with_warnings",
        "actions": actions,
        "errors": errors or None,
        "review": review,
    }
    if include_snapshot:
        result["snapshot"] = snapshot
    return result


# --- internals ---------------------------------------------------------------

def _quick_review_from_snapshot(snapshot: dict | None, *, symbol: str | None) -> dict | None:
    """
    Tries to produce a short summary from diag_snapshot():
    - remaining open positions count (global or per symbol)
    - remaining pending orders count
    - (if present) equity, balance, margin, free margin, floating P/L
    The fields are looked up in a tolerant way; unknown keys are ignored.
    """
    if not snapshot or not isinstance(snapshot, dict):
        return None

    # tolerant getters
    def g(d, *keys, cast=float, default=None):
        for k in keys:
            if k in d:
                try:
                    return cast(d[k]) if cast else d[k]
                except Exception:
                    return default
        return default

    # Top-level account metrics (common names in your env)
    account = snapshot.get("account") or snapshot.get("Account") or snapshot
    equity = g(account, "equity", "Equity")
    balance = g(account, "balance", "Balance")
    margin = g(account, "margin", "Margin")
    free_margin = g(account, "free_margin", "FreeMargin", "freeMargin")
    floating = g(account, "floating", "Floating", "profit", "Profit")

    # Positions & pendings (assuming snapshot exposes arrays)
    positions = snapshot.get("positions") or snapshot.get("Positions") or []
    pendings  = snapshot.get("pendings")  or snapshot.get("Orders")    or []

    # Optionally filter by symbol
    if symbol:
        positions = [p for p in positions if (str(p.get("symbol") or p.get("Symbol") or "").upper() == symbol.upper())]
        pendings  = [o for o in pendings  if (str(o.get("symbol")  or o.get("Symbol")  or "").upper() == symbol.upper())]

    open_cnt = len(positions)
    pend_cnt = len(pendings)

    # Try to aggregate unrealized P/L from positions if present
    def pos_pl(p):
        return g(p, "profit", "Profit", default=0.0)

    unreal_pl = sum((pos_pl(p) or 0.0) for p in positions) if positions else None

    return {
        "scope": {"symbol": symbol} if symbol else "ALL",
        "remaining_open_positions": open_cnt,
        "remaining_pendings": pend_cnt,
        "unrealized_pl": unreal_pl,
        "equity": equity,
        "balance": balance,
        "margin": margin,
        "free_margin": free_margin,
        "floating": floating,
    }

"""
Example of launch

from app.MT4Service import MT4Service
from Strategy.orchestrator.kill_switch_review import run_kill_switch_with_review

svc = MT4Service(...)

# 1) Full stop for the entire account: close all and cancel all
res_all = await run_kill_switch_with_review(svc)

# 2) Only for the EURUSD symbol
res_eu = await run_kill_switch_with_review(svc, symbol="EURUSD")

# 3) Close only profitable XAUUSD positions (leaving unprofitable ones), but also cancel all pending orders for this symbol
res_gold = await run_kill_switch_with_review(svc, symbol="XAUUSD", only_profit=True)


"""