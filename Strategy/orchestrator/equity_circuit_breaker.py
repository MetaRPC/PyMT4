# -*- coding: utf-8 -*-
"""
Equity/Drawdown Circuit-Breaker Orchestrator
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Purpose: Risk management wrapper that blocks strategy execution when account
         protection limits are breached. Acts as a safety circuit breaker.

Why Circuit Breakers Matter:
- Prevent catastrophic losses during black swan events or strategy malfunctions
- Enforce daily loss limits to preserve capital
- Limit exposure by capping open positions
- Comply with risk management rules and trading discipline

Protection Mechanisms (5 Layers):
┌───────────────────────────┬──────────────────────────────────────────────────┐
│ 1. Equity Floor           │ Block if equity < min_equity                     │
│                           │ Use: Preserve minimum account balance            │
├───────────────────────────┼──────────────────────────────────────────────────┤
│ 2. Daily Drawdown %       │ Block if daily_dd_pct <= -max_daily_drawdown_pct│
│                           │ Use: Stop trading after X% loss from day start   │
├───────────────────────────┼──────────────────────────────────────────────────┤
│ 3. Daily Loss Money       │ Block if daily_pl_money <= -max_daily_loss_money│
│                           │ Use: Hard dollar limit per day (e.g., -$150)     │
├───────────────────────────┼──────────────────────────────────────────────────┤
│ 4. Max Open Positions     │ Block if open_positions_count >= max_open        │
│                           │ Use: Limit exposure/concentration per symbol     │
├───────────────────────────┼──────────────────────────────────────────────────┤
│ 5. Risk Per Trade Cap     │ Block if estimated_risk_pct > cap                │
│                           │ Use: Prevent oversized individual trades         │
└───────────────────────────┴──────────────────────────────────────────────────┘

Parameters:
- min_equity: Minimum equity threshold (e.g., $2000)
- max_daily_drawdown_pct: Max daily loss in % (e.g., 3.0 for -3%)
- max_daily_loss_money: Max daily loss in currency (e.g., 150.0 for -$150)
- max_open_positions: Max concurrent positions (global or per symbol)
- symbol: Optional - filter position count by symbol
- risk_per_trade_pct_cap: Max risk per trade in % (e.g., 1.0 for 1%)
- est_risk_for_runner: Optional function to estimate upcoming trade risk

Execution Flow:
1. Ensure connection is active
2. Fetch current account info (equity, balance, etc.)
3. Check Layer 1: Equity floor violation
4. Check Layer 2: Daily drawdown % (if helper available)
5. Check Layer 3: Daily loss money (if helper available)
6. Check Layer 4: Max open positions (if helper available)
7. Check Layer 5: Risk per trade cap (if estimator provided)
8. If any check fails → return blocked status with reason
9. If all pass → execute wrapped orchestrator strategy
10. Return strategy result + equity_guard_meta

Returns:
dict - If blocked: {"status": "blocked_<reason>", "meta": {...}}
       If passed: {<strategy_result>, "equity_guard_meta": {...}}

Requirements (svc.sugar API):
- Required: ensure_connected, account_info
- Optional (stronger protection): daily_drawdown_pct, daily_pl_money,
            open_positions_count, est_risk_for_runner
"""

from __future__ import annotations
from typing import Callable, Optional, Iterable

async def run_with_equity_circuit_breaker(
    svc,
    runner_coro_factory: Callable[[], "object"],  # () -> coroutine
    *,
    # Hard equity floor (blocks if equity < min_equity)
    min_equity: Optional[float] = None,
    # Daily drawdown cap: blocks if daily_dd_pct <= -abs(max_daily_drawdown_pct)
    max_daily_drawdown_pct: Optional[float] = None,
    # Daily money loss cap: blocks if daily PnL <= -abs(max_daily_loss_money)
    max_daily_loss_money: Optional[float] = None,
    # Cap max open positions (global or per symbol if `symbol` provided)
    max_open_positions: Optional[int] = None,
    symbol: Optional[str] = None,
    # Risk-per-trade cap: blocks if upcoming trade risk% > given cap (best-effort)
    risk_per_trade_pct_cap: Optional[float] = None,
    # If we can estimate risk for the upcoming trade (optional hook)
    est_risk_for_runner: Optional[Callable[[], "object"]] = None,  # () -> float | coroutine returning float
    # Pass-through metadata (for logging/audit)
    reason_meta: Optional[dict] = None,
) -> dict:
    sugar = svc.sugar
    await sugar.ensure_connected()

    meta = {
        "min_equity": min_equity,
        "max_daily_drawdown_pct": max_daily_drawdown_pct,
        "max_daily_loss_money": max_daily_loss_money,
        "max_open_positions": max_open_positions,
        "symbol": symbol,
        "risk_per_trade_pct_cap": risk_per_trade_pct_cap,
    }
    if reason_meta:
        meta.update(reason_meta)

    # --- Base equity
    acc = await sugar.account_info()  # expect dict with at least 'equity'
    equity = float(acc.get("equity")) if "equity" in acc else None
    meta["equity_now"] = equity
    meta["account_info"] = acc

    # 1) Equity floor
    if min_equity is not None and equity is not None and equity < float(min_equity):
        return {"status": "blocked_min_equity", "meta": meta}

    # 2) Daily drawdown % (if helper exists)
    daily_dd_pct = None
    if hasattr(sugar, "daily_drawdown_pct"):
        try:
            daily_dd_pct = float(await sugar.daily_drawdown_pct())
        except Exception:
            daily_dd_pct = None
    meta["daily_drawdown_pct"] = daily_dd_pct

    if (max_daily_drawdown_pct is not None and
        daily_dd_pct is not None and
        daily_dd_pct <= -abs(float(max_daily_drawdown_pct))):
        return {"status": "blocked_daily_drawdown_pct", "meta": meta}

    # 3) Daily PnL money (if helper exists)
    daily_pl_money = None
    if hasattr(sugar, "daily_pl_money"):
        try:
            daily_pl_money = float(await sugar.daily_pl_money())
        except Exception:
            daily_pl_money = None
    meta["daily_pl_money"] = daily_pl_money

    if (max_daily_loss_money is not None and
        daily_pl_money is not None and
        daily_pl_money <= -abs(float(max_daily_loss_money))):
        return {"status": "blocked_daily_loss_money", "meta": meta}

    # 4) Max open positions (if helper exists)
    if max_open_positions is not None:
        open_cnt = None
        if hasattr(sugar, "open_positions_count"):
            try:
                open_cnt = int(await sugar.open_positions_count(symbol)) if symbol else int(await sugar.open_positions_count())
            except Exception:
                open_cnt = None
        meta["open_positions_count"] = open_cnt
        if open_cnt is not None and open_cnt >= int(max_open_positions):
            return {"status": "blocked_max_open_positions", "meta": meta}

    # 5) Risk-per-trade cap (best-effort)
    if risk_per_trade_pct_cap is not None:
        est_risk = None
        if est_risk_for_runner is not None:
            r = est_risk_for_runner()
            # coroutine-friendly
            if hasattr(r, "__await__"):
                try:
                    r = await r
                except Exception:
                    r = None
            try:
                est_risk = float(r) if r is not None else None
            except Exception:
                est_risk = None
        meta["estimated_trade_risk_pct"] = est_risk
        if est_risk is not None and est_risk > float(risk_per_trade_pct_cap):
            return {"status": "blocked_risk_per_trade_cap", "meta": meta}

    # Passed all checks -> run the target orchestrator
    res = await runner_coro_factory()
    if isinstance(res, dict):
        res = {**res, "equity_guard_meta": meta}
    return res

"""
Example of launch

1) Before an OCO-Straddle — do not trade if equity < $2,000, daily DD ≤ −3%, or daily loss ≤ −$150

from Strategy.orchestrator.equity_circuit_breaker import run_with_equity_circuit_breaker
from Strategy.orchestrator.oco_straddle import run_oco_straddle
from Strategy.presets.strategy import MarketEURUSD
from Strategy.presets.risk import Balanced

result = await run_with_equity_circuit_breaker(
    svc,
    runner_coro_factory=lambda: run_oco_straddle(
        svc, MarketEURUSD, Balanced, offset_pips=10
    ),
    min_equity=2000.0,
    max_daily_drawdown_pct=3.0,     # block at -3% or worse
    max_daily_loss_money=150.0,     # block at -$150 or worse
)

══════════════════════════════════════════════════════════════════════════════════════════

2) Before Bracket + Trailing — no more than 3 open positions per symbol and trade risk ≤ 1%

from Strategy.orchestrator.equity_circuit_breaker import run_with_equity_circuit_breaker
from Strategy.orchestrator.bracket_trailing_activation import run_bracket_with_trailing_activation
from Strategy.presets.strategy import MarketEURUSD
from Strategy.presets.risk import Balanced

res = await run_with_equity_circuit_breaker(
    svc,
    runner_coro_factory=lambda: run_bracket_with_trailing_activation(
        svc, MarketEURUSD, Balanced,
        side="buy",
        activate_trailing_at_pips=12.0,
        trailing_distance_pips=6.0
    ),
    symbol=MarketEURUSD.symbol,
    max_open_positions=3,
    risk_per_trade_pct_cap=1.0,
    est_risk_for_runner=lambda: Balanced.risk_percent,  # simple estimate
)


"""