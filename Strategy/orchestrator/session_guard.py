# -*- coding: utf-8 -*-
"""
Session Guard Orchestrator 🕐
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Purpose: Time-based trading window control - only trade during specific sessions.
         "Trade when the market is right, sleep when it's not" automation.

What Are Trading Sessions? 🌍
Financial markets operate 24/5 with distinct regional sessions:
- 🇯🇵 Tokyo (Asian): 00:00-08:00 GMT - Low volatility, range-bound
- 🇬🇧 London (European): 07:00-16:30 GMT - High liquidity, major moves
- 🇺🇸 New York (American): 12:00-21:00 GMT - Highest volume, trending
- 🇦🇺 Sydney (Pacific): 22:00-06:00 GMT - Quietest session

Overlap periods = highest liquidity + volatility (e.g., London+NY: 12:00-16:30)

Why Use Session Guards? ⚡
✓ Strategy-specific: Some strategies work better in specific sessions
✓ Volatility control: Avoid quiet Asian hours for breakout strategies
✓ Liquidity matching: Scalping needs high liquidity (London/NY)
✓ Cost efficiency: Lower spreads during active sessions
✓ Risk management: Avoid overnight gaps and weekend risk
✓ Automated scheduling: Bot knows when to trade/sleep

Perfect For:
🎯 Session-specific strategies (e.g., London breakout, NY reversal)
🎯 Avoiding low-liquidity periods (Asian session for EUR/USD)
🎯 Overlap trading (London+NY = max volume)
🎯 Weekend risk avoidance (Friday close protection)
🎯 News-time protection (block specific hours)
🎯 Automated bots (schedule trading times)

Visual Example - Multiple Windows:
  windows = [("08:00", "11:30"), ("13:00", "17:00")]

  00:00 ───────────────────── ❌ Blocked (outside windows)
  08:00 ═══════════════════╗
  11:30 ╚══════════════════  ✓ Window 1: Trade allowed
  12:00 ───────────────────── ❌ Blocked (lunch break)
  13:00 ═══════════════════╗
  17:00 ╚══════════════════  ✓ Window 2: Trade allowed
  18:00 ───────────────────── ❌ Blocked (after hours)

Features:
┌─────────────────────┬──────────────────────────────────────────────────┐
│ Multiple Windows    │ Define several trading periods per day           │
├─────────────────────┼──────────────────────────────────────────────────┤
│ Weekday Filter      │ Trade only on specific days (Mon-Fri by default) │
├─────────────────────┼──────────────────────────────────────────────────┤
│ Timezone Support    │ Server, UTC, or any timezone (e.g., London/NY)  │
├─────────────────────┼──────────────────────────────────────────────────┤
│ Window Inversion    │ enforce_windows=False → trade OUTSIDE windows   │
├─────────────────────┼──────────────────────────────────────────────────┤
│ Rollover Buffer     │ Optional swap-time avoidance within guard       │
├─────────────────────┼──────────────────────────────────────────────────┤
│ Overnight Windows   │ Support 22:00-03:00 cross-midnight windows      │
├─────────────────────┼──────────────────────────────────────────────────┤
│ Preset Sessions     │ Built-in SESSIONS dict (London, NewYork, etc.)  │
└─────────────────────┴──────────────────────────────────────────────────┘

Parameters:
- runner_coro_factory: Wrapped strategy to execute (if within session)
- windows: List of ("HH:MM", "HH:MM") time ranges
  Example: [("08:00", "11:30"), ("13:00", "17:00")]
- tz: Timezone to use:
    * "server" - Use broker's server time (recommended) 🏆
    * "Europe/London" - GMT/BST
    * "America/New_York" - Eastern Time
    * None - Local system time
- weekdays: Tuple of allowed days (0=Mon, 6=Sun)
  Default: (0,1,2,3,4) = Monday-Friday
  Example: (0,1,2) = Monday-Wednesday only
- enforce_windows:
    * True (default) - Trade INSIDE windows ✓
    * False - Trade OUTSIDE windows (inverted logic) ❌
- rollover_hhmm: Optional rollover time to avoid (e.g., "23:00")
- rollover_buffer_min: Minutes before/after rollover to block (default 0)
- reason_meta: Optional metadata for logging/auditing

Built-in Session Presets:
Use SESSIONS dict for common sessions (GMT times):
📍 SESSIONS["London"] = (("07:00", "16:30"),)
📍 SESSIONS["NewYork"] = (("12:00", "21:00"),)
📍 SESSIONS["Tokyo"] = (("00:00", "08:00"),)
📍 SESSIONS["Sydney"] = (("22:00", "06:00"),)  # overnight
📍 SESSIONS["LondonNYOver"] = (("07:00", "21:00"),)  # full overlap

Execution Flow:
1. Get current time in specified timezone
   - Prefer server time if tz="server" and available
   - Fall back to zoneinfo or local time
2. Check weekday filter (Mon-Fri by default)
3. Check if time is within any trading window
4. Check rollover buffer (if configured)
5. Combine all checks:
   - allowed = ok_weekday AND in_window AND not_in_rollover
   - If enforce_windows=False → invert in_window logic
6. If blocked → return skipped status
7. If allowed → execute wrapped strategy
8. Attach session_meta to result

Window Inversion Example:
🔄 enforce_windows=True: Trade 08:00-17:00 (normal)
🔄 enforce_windows=False: Trade 00:00-08:00 and 17:00-24:00 (inverse)

Overnight Windows:
🌙 ("22:00", "03:00") works correctly - crosses midnight
   - 22:00-23:59 ✓ allowed
   - 00:00-03:00 ✓ allowed
   - 03:01-21:59 ❌ blocked

Returns:
dict {
  "status": "skipped_by_session",  # If blocked
  "session_meta": {
    "tz": str,                      # Timezone used
    "now_iso": str,                 # Current time (ISO format)
    "windows": list,                # Configured windows
    "weekdays": list,               # Allowed weekdays
    "in_window": bool,              # Is current time in window?
    "ok_weekday": bool,             # Is current day allowed?
    "in_rollover_buffer": bool      # Is in rollover danger zone?
  }
}

OR (if allowed):
dict {
  <strategy_result>,                # Result from wrapped strategy
  "session_meta": {...}             # Session check metadata
}

Requirements (svc.sugar API):
- Optional: server_time() - Get broker's server time (sync or async)
- Falls back to system time if not available

Use Cases:
💡 London breakout strategy → windows=SESSIONS["London"]
💡 NY session only → windows=SESSIONS["NewYork"]
💡 Overlap trading → windows=SESSIONS["LondonNYOver"]
💡 Avoid Asian session → windows=SESSIONS["Tokyo"], enforce_windows=False
💡 Weekday only → weekdays=(0,1,2,3,4)
💡 Weekend only → weekdays=(5,6)

Combine with Other Guards:
🛡️ rollover_avoidance.py - Time-specific swap protection
🛡️ equity_circuit_breaker.py - Account protection
🛡️ dynamic_deviation_guard.py - Market condition adaptation
"""

from __future__ import annotations
from dataclasses import asdict
from datetime import datetime, time, timedelta
from typing import Callable, Iterable, Tuple, Optional, Literal

try:
    from zoneinfo import ZoneInfo  # py3.9+
except Exception:  # pragma: no cover
    ZoneInfo = None  # type: ignore


TimeWindow = Tuple[str, str]  # ("HH:MM", "HH:MM")


def _parse_hhmm(x: str) -> time:
    hh, mm = x.split(":")
    return time(int(hh), int(mm), 0)


def _now_in_tz(tz: Optional[str], *, svc=None) -> datetime:
    """Get current time in a timezone:
    - tz="server": try svc.sugar.server_time() if available; fallback to UTC.
    - tz like "Europe/London": use zoneinfo.
    - tz=None: naive local time (not recommended for servers)."""
    if tz == "server" and svc is not None:
        # Prefer sugar's server time if available
        st = None
        try:
            if hasattr(svc, "sugar") and hasattr(svc.sugar, "server_time"):
                st = svc.sugar.server_time  # could be sync or async; handle both below
        except Exception:
            st = None
        if st:
            try:
                val = st()
                if hasattr(val, "__await__"):  # coroutine -> can't await here
                    # Caller path can't await; so fallback to local UTC.
                    pass
                else:
                    # Assume val is aware datetime in server tz or UTC
                    if isinstance(val, datetime):
                        return val
            except Exception:
                pass
    if tz and tz != "server" and ZoneInfo:
        return datetime.now(ZoneInfo(tz))
    # Fallback: local system time (naive) — acceptable for dev
    return datetime.now()


def _is_within_any_window(now: datetime, windows: Iterable[TimeWindow]) -> bool:
    tnow = now.timetz() if now.tzinfo else now.time()
    for start_s, end_s in windows:
        start, end = _parse_hhmm(start_s), _parse_hhmm(end_s)
        if start <= end:
            # Normal window, e.g. 08:00–17:00
            if start <= tnow <= end:
                return True
        else:
            # Overnight window, e.g. 22:00–03:00
            if tnow >= start or tnow <= end:
                return True
    return False


def _is_weekday_allowed(now: datetime, weekdays: Optional[Iterable[int]]) -> bool:
    if weekdays is None:
        return True
    # Python: Monday=0 ... Sunday=6
    return now.weekday() in set(weekdays)


def _in_rollover_buffer(now: datetime, rollover_hhmm: Optional[str], buffer_min: int) -> bool:
    """If rollover is '23:00', block [22:30..23:30] for buffer_min=30."""
    if not rollover_hhmm:
        return False
    r = _parse_hhmm(rollover_hhmm)
    # Normalize 'now' date with rollover time
    dt_roll = now.replace(hour=r.hour, minute=r.minute, second=0, microsecond=0)
    start = dt_roll - timedelta(minutes=buffer_min)
    end   = dt_roll + timedelta(minutes=buffer_min)
    return start <= now <= end


async def run_with_session_guard(
    svc,
    runner_coro_factory: Callable[[], "object"],  # () -> coroutine
    *,
    windows: Iterable[TimeWindow],
    tz: Optional[str] = None,  # e.g. "Europe/London", "America/New_York", or "server"
    weekdays: Optional[Iterable[int]] = (0, 1, 2, 3, 4),  # Mon..Fri by default
    enforce_windows: bool = True,   # if False -> invert: trade ONLY outside the windows
    rollover_hhmm: Optional[str] = None,  # e.g. "23:00"
    rollover_buffer_min: int = 0,   # +/- minutes around rollover_hhmm to avoid trading
    reason_meta: Optional[dict] = None,
) -> dict:
    """
    Returns:
        - if guard blocks: {"status":"skipped_by_session", ...}
        - else: result of runner + {"session_meta":{...}} merged.
    """
    # 1) Determine current time in requested TZ
    now = _now_in_tz(tz, svc=svc)

    # 2) Check weekday and time windows
    ok_weekday = _is_weekday_allowed(now, weekdays)
    in_window  = _is_within_any_window(now, windows)
    in_roll    = _in_rollover_buffer(now, rollover_hhmm, rollover_buffer_min)

    allowed = ok_weekday and (in_window if enforce_windows else not in_window) and (not in_roll)

    meta = {
        "tz": tz or "local",
        "now_iso": now.isoformat(),
        "windows": list(windows),
        "weekdays": list(weekdays) if weekdays is not None else None,
        "enforce_windows": enforce_windows,
        "in_window": in_window,
        "ok_weekday": ok_weekday,
        "rollover_hhmm": rollover_hhmm,
        "rollover_buffer_min": rollover_buffer_min,
        "in_rollover_buffer": in_roll,
    }
    if reason_meta:
        meta.update(reason_meta)

    if not allowed:
        return {"status": "skipped_by_session", "session_meta": meta}

    # 3) Run target orchestrator
    res = await runner_coro_factory()
    # attach meta for auditability
    if isinstance(res, dict):
        res = {**res, "session_meta": meta}
    return res


# --- Convenience presets ------------------------------------------------------

SESSIONS = {
    # Typical city sessions (approx, adjust to broker/server time if needed)
    "London":       (("07:00", "16:30"),),
    "NewYork":      (("12:00", "21:00"),),
    "Tokyo":        (("00:00", "08:00"),),
    "Sydney":       (("22:00", "06:00"),),  # overnight example
    "LondonNYOver": (("07:00", "21:00"),),
}

"""
Example of launch

OCO-Straddle only in the London session (London time), with protection against the swap hour:

from Strategy.orchestrator.session_guard import run_with_session_guard, SESSIONS
from Strategy.orchestrator.oco_straddle import run_oco_straddle
from Strategy.presets.risk import Balanced
from Strategy.presets.strategy import MarketEURUSD

# windows for London, tz="Europe/London"
result = await run_with_session_guard(
    svc,
    runner_coro_factory=lambda: run_oco_straddle(
        svc, MarketEURUSD, Balanced, offset_pips=10, max_spread_pips=2.0
    ),
windows=SESSIONS["London"],
tz="Europe/London",
weekdays=(0,1,2,3,4), # Mon-Fri
rollover_hhmm="23:00", # if the broker swap is at 23:00 server time
rollover_buffer_min=30, # no trading for ±30 minutes
)

══════════════════════════════════════════════════════════════════════════════════════════

Bracket + Trailing Activation — we trade ONLY OUTSIDE the American session (window inversion):

from Strategy.orchestrator.session_guard import run_with_session_guard, SESSIONS
from Strategy.orchestrator.bracket_trailing_activation import run_bracket_with_trailing_activation
from Strategy.presets.risk import Balanced
from Strategy.presets.strategy import MarketEURUSD

res = await run_with_session_guard(
    svc,
    runner_coro_factory=lambda: run_bracket_with_trailing_activation(
        svc, MarketEURUSD, Balanced,
        side="buy",
        activate_trailing_at_pips=12.0,
        trailing_distance_pips=6.0
    ),
    windows=SESSIONS["NewYork"],
    tz="America/New_York",
    enforce_windows=False,  # IMPORTANT: We trade ONLY OUTSIDE this window
)

"""