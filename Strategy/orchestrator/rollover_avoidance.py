# -*- coding: utf-8 -*-
"""
Rollover Avoidance Guard Orchestrator 🌙
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Purpose: Time-based protection that blocks trading during rollover (swap) periods.
         Avoids unpredictable spread widening and execution issues at day's end.

What is Rollover? 💱
Rollover (also called "swap") is the daily reset time when:
- Interest rates are applied to open positions
- Spreads often widen significantly (10x-50x normal)
- Liquidity temporarily drops
- Order execution becomes unpredictable
- Slippage can be extreme

Typical rollover time: 23:00 or 00:00 (server timezone)

Why Avoid Rollover? 🚫
❌ Spreads spike (normal 2 pips → 20+ pips)
❌ Slippage increases dramatically
❌ Orders may fill at worse prices
❌ SL/TP can be hit prematurely due to wide spreads
❌ Market becomes illiquid and unpredictable

Perfect For:
🎯 Intraday strategies (avoid holding overnight)
🎯 Scalping bots (sensitive to spreads)
🎯 News trading (rollovers often coincide with news)
🎯 Risk-averse traders (eliminate rollover risk)
🎯 Automated systems (avoid edge cases)

Visual Timeline Example:
  rollover_hhmm = "23:00"
  buffer_min = 30

  22:00 ─────────────────────────── Safe to trade ✓
  22:30 ───┐
            │ DANGER ZONE (blocked)  ← 30 min before
  23:00 ═══╪═══ ROLLOVER TIME       ← Exact rollover
            │ DANGER ZONE (blocked)  ← 30 min after
  23:30 ───┘
  00:00 ─────────────────────────── Safe to trade ✓

Features:
┌──────────────────────┬─────────────────────────────────────────────────┐
│ Time Window Block    │ Prevents execution in rollover ± buffer window  │
├──────────────────────┼─────────────────────────────────────────────────┤
│ Timezone Support     │ Server time, UTC, or any timezone (e.g. NY)     │
├──────────────────────┼─────────────────────────────────────────────────┤
│ Configurable Buffer  │ Adjust safety margin (default ±30 minutes)      │
├──────────────────────┼─────────────────────────────────────────────────┤
│ Server Time Sync     │ Prefers broker's server time (if available)     │
├──────────────────────┼─────────────────────────────────────────────────┤
│ Wrapper Design       │ Works with any orchestrator strategy            │
└──────────────────────┴─────────────────────────────────────────────────┘

Parameters:
- runner_coro_factory: Wrapped strategy function to execute (if safe)
- rollover_hhmm: Rollover time in "HH:MM" format (default "23:00")
- buffer_min: Safety margin in minutes before/after rollover (default 30)
- tz: Timezone to use:
    * "server" - Use broker's server time (recommended) 🏆
    * "America/New_York" - Eastern Time
    * "Europe/London" - GMT/BST
    * None - Local system time
- reason_meta: Optional metadata for logging/auditing

Timezone Examples:
🌍 Common broker server times:
  - GMT+2/+3 (Europe/London, most Forex brokers)
  - GMT+0 (Europe/London winter)
  - EST/EDT (America/New_York)

Execution Flow:
1. Get current time in specified timezone
   - Prefer server time if tz="server" and available
   - Fall back to zoneinfo or local time
2. Parse rollover time (e.g., "23:00")
3. Calculate danger zone:
   - start = rollover - buffer_min
   - end = rollover + buffer_min
4. Check if current time is in danger zone:
   - If YES → skip execution, return blocked status
   - If NO → execute wrapped strategy normally
5. Attach rollover_meta to result

Buffer Recommendations:
⏰ Conservative: 60 minutes (±60 min)
⏰ Standard: 30 minutes (±30 min) - recommended
⏰ Aggressive: 15 minutes (±15 min)

Returns:
dict {
  "status": "skipped_by_rollover",  # If blocked
  "meta": {
    "tz": str,                        # Timezone used
    "now_iso": str,                   # Current time (ISO format)
    "rollover_hhmm": str,             # Rollover time
    "buffer_min": int                 # Buffer in minutes
  }
}

OR (if allowed):
dict {
  <strategy_result>,                  # Result from wrapped strategy
  "rollover_meta": {...}              # Rollover check metadata
}

Requirements (svc.sugar API):
- Optional: server_time() - Get broker's server time (async or sync)
- Falls back to system time if not available

Safety Note:
✅ This is a TIME-BASED guard, not a spread-based guard
✅ For spread protection, also use max_spread_pips in your strategies
✅ Combine with equity_circuit_breaker for multi-layer protection
"""

from __future__ import annotations
from datetime import datetime, timedelta, time
from typing import Callable, Optional

try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None


def _parse_hhmm(hm: str) -> time:
    h, m = hm.split(":")
    return time(int(h), int(m))


async def run_with_rollover_avoidance(
    svc,
    runner_coro_factory: Callable[[], "object"],  # () -> coroutine
    *,
    rollover_hhmm: str = "23:00",
    buffer_min: int = 30,
    tz: Optional[str] = None,
    reason_meta: Optional[dict] = None,
) -> dict:
    """
    Args:
        rollover_hhmm: time of rollover (e.g. "23:00")
        buffer_min: +/- buffer in minutes
        tz: timezone ("Europe/London", "America/New_York", "server", or None for local)
    Returns:
        - {"status": "skipped_by_rollover", ...} if inside buffer
        - else: result of runner() + meta
    """
    now = await _now_in_tz(svc, tz)
    roll = _parse_hhmm(rollover_hhmm)
    roll_dt = now.replace(hour=roll.hour, minute=roll.minute, second=0, microsecond=0)

    start = roll_dt - timedelta(minutes=buffer_min)
    end   = roll_dt + timedelta(minutes=buffer_min)

    meta = {
        "tz": tz or "local",
        "now_iso": now.isoformat(),
        "rollover_hhmm": rollover_hhmm,
        "buffer_min": buffer_min,
    }
    if reason_meta:
        meta.update(reason_meta)

    if start <= now <= end:
        return {"status": "skipped_by_rollover", "meta": meta}

    res = await runner_coro_factory()
    if isinstance(res, dict):
        res = {**res, "rollover_meta": meta}
    return res


async def _now_in_tz(svc, tz: Optional[str]) -> datetime:
    """Best effort: use server_time async if available; else tz; else local."""
    # Prefer server-based time
    if tz == "server":
        if hasattr(svc, "sugar") and hasattr(svc.sugar, "server_time"):
            try:
                st = svc.sugar.server_time()
                # If server_time is async, await it
                if hasattr(st, "__await__"):
                    st = await st
                if isinstance(st, datetime):
                    return st
            except Exception:
                pass  # fallback below
    # Use zoneinfo
    if tz and tz != "server" and ZoneInfo:
        return datetime.now(ZoneInfo(tz))
    # Local naive
    return datetime.now()

"""
Example of launch

from Strategy.orchestrator.rollover_avoidance import run_with_rollover_avoidance
from Strategy.orchestrator.oco_straddle import run_oco_straddle
from Strategy.presets.risk import Balanced
from Strategy.presets.strategy import MarketEURUSD

result = await run_with_rollover_avoidance(
    svc,
    runner_coro_factory=lambda: run_oco_straddle(
        svc, MarketEURUSD, Balanced, offset_pips=10
    ),
rollover_hhmm="23:00", # broker rollover
buffer_min=45, # ±45 minutes
tz="server", # use terminal time
)

"""