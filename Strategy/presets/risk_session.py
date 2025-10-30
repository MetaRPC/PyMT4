# -*- coding: utf-8 -*-
"""
Session-Based Risk Presets 🕐
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Purpose: Automatically adapt risk parameters based on current trading session.
         "Trade differently in different sessions - markets change by the hour" 🌍

What is Session-Based Risk? ⏰
Session-based risk = RiskPreset that changes based on time of day:
- Different SL/TP during Asian vs London vs NY sessions
- Auto-detection of current session (timezone-aware)
- Profiles tuned to session characteristics (liquidity, volatility)
- Works with server time OR any timezone

Why Use Session-Based Risk? ✓
✓ Session-aware: London needs different risk than Asian session
✓ Automatic: Detects session automatically (no manual switching)
✓ Volatility-matched: Tighter stops in calm Asia, wider in volatile NY
✓ Timezone-flexible: Works with broker server time or any timezone
✓ Profile system: "default" vs "aggressive" risk profiles
✓ Ready-to-use: Pre-tuned for each major trading session

Perfect For:
🎯 24/5 automated trading bots (adapt to each session)
🎯 Session-specific strategies (London breakout, NY momentum)
🎯 Multi-session trading (different risk per hour)
🎯 Volatility adaptation (sessions have different characteristics)
🎯 Global traders (work across timezones automatically)

Trading Sessions Explained:

🌏 Asian Session (00:00-08:00 GMT):
   - Characteristics: Quieter, range-bound, lower volume
   - Major pairs: USD/JPY, AUD/USD
   - Strategy fit: Range trading, mean reversion
   - Risk approach: Conservative (low volatility)

🌍 London Session (07:00-16:00 GMT):
   - Characteristics: High liquidity, major moves start
   - Major pairs: EUR/USD, GBP/USD, EUR/GBP
   - Strategy fit: Breakouts, trend following
   - Risk approach: Balanced (active but controlled)

🌎 New York Session (12:00-21:00 GMT):
   - Characteristics: Highest volume, news-driven
   - Major pairs: All USD pairs
   - Strategy fit: News trading, momentum
   - Risk approach: Balanced (high volume but volatile)

🔥 London+NY Overlap (12:00-16:00 GMT):
   - Characteristics: Maximum volume and volatility
   - Major pairs: EUR/USD, GBP/USD (most active)
   - Strategy fit: Scalping, momentum, breakouts
   - Risk approach: Momentum (tighter BE, faster profit lock)

Session Detection:

Auto-detection works by priority (first match wins):
1. Overlap (12:00-16:00) → if in overlap window
2. London (07:00-16:00) → if in London window
3. NewYork (12:00-21:00) → if in NY window
4. Asia → fallback for all other times

Visual Timeline (GMT):

00:00 ═══════════════════ Asian Session
07:00 ───────────────────┐
                          │ London Session
12:00 ═══════════════════╪═══════════════════ Overlap (hottest!)
                          │ NY Session
16:00 ───────────────────┘
21:00 ───────────────────────────────────────
00:00 ═══════════════════ Asian Session (cycle repeats)

Ready-to-Use Session Presets:

🔹 make_asia_conservative():
   - Risk: 0.5% (safest)
   - SL: 20 pips, TP: 30 pips
   - BE trigger: +10 pips
   - Trailing: Disabled (range-bound session)
   - Perfect for: Quiet Asian hours, range strategies

🔹 make_london_balanced():
   - Risk: 1.0% (standard)
   - SL: 18 pips, TP: 36 pips (RR=1:2)
   - BE trigger: +9 pips
   - Trailing: 8 pips (active management)
   - Perfect for: London breakouts, day trading

🔹 make_newyork_balanced():
   - Risk: 1.0% (standard)
   - SL: 20 pips, TP: 40 pips (RR=1:2)
   - BE trigger: +10 pips
   - Trailing: 10 pips (news volatility)
   - Perfect for: NY session momentum, news trading

🔹 make_overlap_momentum():
   - Risk: 1.25% (slightly higher)
   - SL: 16 pips, TP: 32 pips (tighter)
   - BE trigger: +8 pips (faster lock-in)
   - Trailing: 7 pips (active profit protection)
   - Perfect for: Overlap scalping, high-volume trades

Profile System:

Two built-in profiles for different risk appetites:

📊 "default" Profile (Conservative-Balanced):
   - Asia: Conservative (0.5% risk)
   - London: Balanced (1.0% risk)
   - NewYork: Balanced (1.0% risk)
   - Overlap: Momentum (1.25% risk)
   - Perfect for: Most traders, steady growth

📊 "aggressive" Profile (Higher Risk):
   - Asia: Scalper (0.75% risk, tighter stops)
   - London: Aggressive (1.5% risk)
   - NewYork: Aggressive (1.5% risk)
   - Overlap: Momentum (1.25% risk)
   - Perfect for: Experienced traders, smaller accounts

Auto-Selection Function:

session_risk_auto(svc, symbol, tz, profile) → RiskPreset

Parameters:
- svc: MT4Service instance
- symbol: Trading symbol (reserved for future tuning)
- tz: Timezone ("Europe/London", "America/New_York", "server")
- profile: "default" OR "aggressive"

Returns:
- RiskPreset configured for current session
- Includes _session_meta attribute (diagnostic info)

Timezone Options:

🌍 "Europe/London" - GMT/BST (most common for Forex)
🌎 "America/New_York" - EST/EDT (US traders)
🏢 "server" - Use broker's server time (recommended!)
🖥️ None - Local system time (dev/testing only)

Usage Patterns:

💡 Auto-Detection (recommended):
   from Strategy.presets.risk_session import session_risk_auto
   risk = await session_risk_auto(svc, "EURUSD", tz="Europe/London")
   result = await run_market_one_shot(svc, MarketEURUSD, risk)

💡 Server Time (best for production):
   risk = await session_risk_auto(svc, "XAUUSD", tz="server", profile="default")

💡 Aggressive Profile:
   risk = await session_risk_auto(svc, "GBPUSD", tz="Europe/London", profile="aggressive")

💡 Explicit Session (no auto-detection):
   from Strategy.presets.risk_session import make_london_balanced
   risk = make_london_balanced()
   # Always use London settings (no time check)

💡 Combined with Session Guard:
   from Strategy.orchestrator.session_guard import run_with_session_guard, SESSIONS
   from Strategy.presets.risk_session import session_risk_auto

   risk = await session_risk_auto(svc, "EURUSD", tz="Europe/London")
   result = await run_with_session_guard(
       svc,
       lambda: run_market_one_shot(svc, MarketEURUSD, risk),
       windows=SESSIONS["London"],
       tz="Europe/London"
   )

Session Metadata:

After calling session_risk_auto(), the returned RiskPreset includes:

risk._session_meta = {
    "session": "London",           # Detected session
    "now_iso": "2025-10-29T10:30:00+00:00",
    "tz": "Europe/London",         # Timezone used
    "profile": "default",          # Profile applied
    "windows": {...}               # Session time windows
}

Pro Tips:

💡 Use "server" timezone for production (matches broker)
💡 London+NY overlap = best liquidity (tightest spreads)
💡 Asian session = range trading (lower volatility)
💡 NY session = news trading (high volatility)
💡 Combine with session_guard for time-based filtering
💡 Test timezone settings (some brokers use GMT+2/+3)
💡 Symbol-specific tuning planned (e.g., gold needs wider SL)
💡 Use explicit presets (make_london_balanced) for fixed behavior

Session Characteristics Summary:

┌──────────┬────────────┬────────────┬─────────────┬──────────────┐
│ Session  │ Volatility │ Liquidity  │ Best Pairs  │ Risk Style   │
├──────────┼────────────┼────────────┼─────────────┼──────────────┤
│ Asian    │ Low        │ Low        │ JPY pairs   │ Conservative │
│ London   │ Medium-High│ High       │ EUR, GBP    │ Balanced     │
│ NewYork  │ High       │ Very High  │ All USD     │ Balanced     │
│ Overlap  │ Very High  │ Maximum    │ EUR/USD #1  │ Momentum     │
└──────────┴────────────┴────────────┴─────────────┴──────────────┘
"""

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, time
from typing import Optional, Tuple, Dict

try:
    from zoneinfo import ZoneInfo  # py>=3.9
except Exception:  # pragma: no cover
    ZoneInfo = None

from Strategy.presets.risk import RiskPreset


# --- Session windows (local to chosen TZ) ------------------------------------

# Windows are tuples of ("HH:MM", "HH:MM"). Adjust to your taste/broker.
SESSIONS: Dict[str, Tuple[str, str]] = {
    "Asia":    ("00:00", "08:00"),
    "London":  ("07:00", "16:00"),
    "NewYork": ("12:00", "21:00"),
    # Overlap of London & NY is approximately 12:00–16:00 London time,
    # but we'll allow a wider 11:30–16:30.
    "Overlap": ("11:30", "16:30"),
}


def _parse_hhmm(s: str) -> time:
    h, m = s.split(":")
    return time(int(h), int(m), 0)


def _now_in_tz(svc, tz: Optional[str]) -> datetime:
    """
    Best-effort current time:
    - tz=="server": use svc.sugar.server_time() if available (sync/async tolerated).
    - named tz: Europe/London, America/New_York, ...
    - None: local system time (dev only).
    """
    if tz == "server" and hasattr(svc, "sugar") and hasattr(svc.sugar, "server_time"):
        try:
            val = svc.sugar.server_time()
            if hasattr(val, "__await__"):
                # can't await in sync func; fall back to local if async
                pass
            else:
                if isinstance(val, datetime):
                    return val
        except Exception:
            pass
    if tz and tz != "server" and ZoneInfo:
        return datetime.now(ZoneInfo(tz))
    return datetime.now()


def _in_window(now: datetime, start_s: str, end_s: str) -> bool:
    t = now.timetz() if now.tzinfo else now.time()
    start, end = _parse_hhmm(start_s), _parse_hhmm(end_s)
    if start <= end:
        return start <= t <= end
    # overnight window
    return t >= start or t <= end


def detect_session(now: datetime) -> str:
    """
    Returns one of: "Overlap", "London", "NewYork", "Asia".
    Priority: Overlap > London > NewYork > Asia (first match wins).
    """
    # Priority ensures overlap beats london/ny
    if _in_window(now, *SESSIONS["Overlap"]):  # type: ignore[arg-type]
        return "Overlap"
    if _in_window(now, *SESSIONS["London"]):   # type: ignore[arg-type]
        return "London"
    if _in_window(now, *SESSIONS["NewYork"]):  # type: ignore[arg-type]
        return "NewYork"
    return "Asia"


# --- Opinionated risk profiles per session -----------------------------------
# You can tune these defaults (they are conservative-ish).

def make_asia_conservative() -> RiskPreset:
    # Quieter market on average → smaller risk%, wider SL than scalper, modest TP
    return RiskPreset(
        risk_percent=0.5,
        sl_pips=20,
        tp_pips=30,
        be_trigger_pips=10,  # move to BE after +10 pips
        be_plus_pips=2,
        trailing_pips=None,  # often not needed in Asia
    )


def make_london_balanced() -> RiskPreset:
    # Active session → normal risk, balanced SL/TP, enable trailing
    return RiskPreset(
        risk_percent=1.0,
        sl_pips=18,
        tp_pips=36,
        be_trigger_pips=9,
        be_plus_pips=2,
        trailing_pips=8,
    )


def make_newyork_balanced() -> RiskPreset:
    # Liquidity good, but news spikes → similar to London with slightly bigger SL
    return RiskPreset(
        risk_percent=1.0,
        sl_pips=20,
        tp_pips=40,
        be_trigger_pips=10,
        be_plus_pips=2,
        trailing_pips=10,
    )


def make_overlap_momentum() -> RiskPreset:
    # The hottest hours → allow faster lock-in via BE and a tighter trailing
    return RiskPreset(
        risk_percent=1.25,
        sl_pips=16,
        tp_pips=32,
        be_trigger_pips=8,
        be_plus_pips=1,
        trailing_pips=7,
    )


# Optional: a slightly spicier profile set, selected via `profile="aggressive"`
def make_london_aggressive() -> RiskPreset:
    return RiskPreset(
        risk_percent=1.5,
        sl_pips=16,
        tp_pips=32,
        be_trigger_pips=8,
        be_plus_pips=1,
        trailing_pips=6,
    )


def make_newyork_aggressive() -> RiskPreset:
    return RiskPreset(
        risk_percent=1.5,
        sl_pips=18,
        tp_pips=36,
        be_trigger_pips=9,
        be_plus_pips=1,
        trailing_pips=7,
    )


def make_asia_scalper() -> RiskPreset:
    return RiskPreset(
        risk_percent=0.75,
        sl_pips=12,
        tp_pips=18,
        be_trigger_pips=6,
        be_plus_pips=1,
        trailing_pips=6,
    )


# --- Auto selector ------------------------------------------------------------

PROFILE_MAP_DEFAULT = {
    "Asia":    make_asia_conservative,
    "London":  make_london_balanced,
    "NewYork": make_newyork_balanced,
    "Overlap": make_overlap_momentum,
}

PROFILE_MAP_AGGR = {
    "Asia":    make_asia_scalper,
    "London":  make_london_aggressive,
    "NewYork": make_newyork_aggressive,
    "Overlap": make_overlap_momentum,  # still momentum, but pair with higher risk%
}

async def session_risk_auto(
    svc,
    symbol: str,                # reserved for future symbol-aware tuning
    *,
    tz: Optional[str] = "Europe/London",  # or "server" to use broker server time
    profile: str = "default",             # "default" | "aggressive"
) -> RiskPreset:
    """
    Choose a RiskPreset by current session in given TZ.
    """
    now = _now_in_tz(svc, tz)
    session = detect_session(now)

    if profile == "aggressive":
        factory = PROFILE_MAP_AGGR.get(session, make_london_balanced)
    else:
        factory = PROFILE_MAP_DEFAULT.get(session, make_london_balanced)

    rp = factory()

    # You can insert symbol-specific tweaks here (e.g., gold tends to need wider SL):
    # if symbol.upper() == "XAUUSD":
    #     rp.sl_pips = max(rp.sl_pips, 25)
    #     rp.tp_pips = int(rp.sl_pips * 2)

    # Attach meta (handy for logs)
    setattr(rp, "_session_meta", {
        "session": session,
        "now_iso": now.isoformat(),
        "tz": tz or "local",
        "profile": profile,
        "windows": SESSIONS,
    })
    return rp

"""
Example of launch

from Strategy.presets.risk_session import (
    session_risk_auto,
    make_london_balanced, make_newyork_aggressive,
)
# 1) Auto-selection by session (London time zone)
rp_auto = await session_risk_auto(svc, "EURUSD", tz="Europe/London", profile="default")

# 2) Same, but based on the broker's server time
rp_srv = await session_risk_auto(svc, "XAUUSD", tz="server", profile="aggressive")

# 3) Explicit preset (no autologic)
rp_fixed = make_newyork_aggressive()

══════════════════════════════════════════════════════════════════════════════════════════

Where to integrate this?

Into any orchestrator — like a regular RiskPreset:

from Strategy.presets.strategy_symbols import MarketEURUSD
from Strategy.presets.risk_session import session_risk_auto
from Strategy.orchestrator.market_one_shot import run_market_one_shot

rp = await session_risk_auto(svc, MarketEURUSD.symbol, tz="Europe/London", profile="default")
res = await run_market_one_shot(svc, MarketEURUSD, rp)

"""