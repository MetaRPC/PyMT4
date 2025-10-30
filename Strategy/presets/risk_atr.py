# -*- coding: utf-8 -*-
"""
ATR-Driven Risk Presets 📊
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Purpose: Dynamic risk management that adapts to market volatility using ATR.
         "Let the market tell you how wide your stops should be" approach.

What is ATR? 📈
ATR (Average True Range) = Volatility indicator measuring average price movement
- Invented by J. Welles Wilder Jr. in 1978
- Measures how much a symbol typically moves in pips over N periods
- Higher ATR = more volatile (wider stops needed)
- Lower ATR = less volatile (tighter stops possible)

Example:
  EUR/USD ATR(14) = 12 pips → Symbol moves ~12 pips per day typically
  EUR/USD ATR(14) = 25 pips → High volatility period, moves ~25 pips per day

Why Use ATR for Risk Management? 🎯
✓ Adaptive: Stops adjust to current market conditions automatically
✓ Smart: Wider stops in volatile markets (avoid premature stop-outs)
✓ Efficient: Tighter stops in calm markets (better risk/reward)
✓ Universal: Works across all symbols and timeframes
✓ Scientific: Based on actual price movement, not guesswork
✓ Professional: Used by institutional traders worldwide

Problem with Fixed Stops:
❌ 15 pip stop on EUR/USD:
   - In calm market (ATR=8): Too wide, wasting capital
   - In volatile market (ATR=25): Too tight, gets stopped out easily

Solution with ATR Stops:
✅ Stop = 1.5 × ATR (adapts automatically):
   - Calm market (ATR=8): Stop = 12 pips (efficient)
   - Volatile market (ATR=25): Stop = 37 pips (safe)

Perfect For:
🎯 Volatile markets (crypto, gold, news events)
🎯 Multi-symbol strategies (each symbol has different volatility)
🎯 Multi-timeframe trading (H1 ATR ≠ D1 ATR)
🎯 Adaptive algorithms (respond to changing conditions)
🎯 Professional risk management (institutional approach)

Visual Example:
  Symbol: EUR/USD
  ATR(14) = 16 pips
  atr_mult = 1.5
  min_sl_pips = 10
  max_sl_pips = 30

  Calculation:
  1. Raw SL = ATR × mult = 16 × 1.5 = 24 pips
  2. Clamped = max(10, min(24, 30)) = 24 pips ✓
  3. TP = RR × SL = 2.0 × 24 = 48 pips
  4. BE trigger = 0.5 × SL = 12 pips
  5. Trailing = max(0.75 × 24, 6) = 18 pips

Features:
┌────────────────────────┬────────────────────────────────────────────────┐
│ Dynamic SL Calculation │ SL = atr_mult × ATR (adapts to volatility)    │
├────────────────────────┼────────────────────────────────────────────────┤
│ Safety Clamps          │ min_sl_pips / max_sl_pips prevent extremes    │
├────────────────────────┼────────────────────────────────────────────────┤
│ RR-Based TP            │ TP = rr × SL (maintain risk:reward ratio)     │
├────────────────────────┼────────────────────────────────────────────────┤
│ Adaptive BE/Trailing   │ Derived from SL (proportional to volatility)  │
├────────────────────────┼────────────────────────────────────────────────┤
│ Fallback Protection    │ Uses fallback_sl_pips if ATR unavailable      │
├────────────────────────┼────────────────────────────────────────────────┤
│ Ready-to-Use Presets   │ ATR_Scalper, ATR_Balanced, ATR_Swing          │
└────────────────────────┴────────────────────────────────────────────────┘

ATR Multiplier Guidelines:
📊 Scalping (1.0-1.2× ATR): Tight stops, quick exits
📊 Day trading (1.5-2.0× ATR): Balanced risk/reward
📊 Swing trading (2.0-3.0× ATR): Room for noise, hold longer

Ready-to-Use Presets:
🔹 ATR_Scalper:
   - SL = 1.0 × ATR, clamped [6..15 pips]
   - RR = 1.2 (TP = 1.2 × SL)
   - BE at 50% of SL, trailing = 70% of SL
   - Perfect for: High-frequency, major pairs

🔹 ATR_Balanced:
   - SL = 1.5 × ATR, clamped [10..30 pips]
   - RR = 2.0 (TP = 2 × SL)
   - BE at 50% of SL, trailing = 75% of SL
   - Perfect for: Day trading, most strategies

🔹 ATR_Swing:
   - SL = 2.0 × ATR, clamped [20..60 pips]
   - RR = 2.5 (TP = 2.5 × SL)
   - BE at 33% of SL, trailing = 50% of SL
   - Perfect for: Position trading, catching big moves

Parameters:
- symbol: Trading symbol (e.g., "EURUSD")
- atr_period: ATR calculation period (default 14)
- atr_mult: Multiplier for ATR (e.g., 1.5 = SL is 1.5× ATR)
- min_sl_pips: Minimum stop loss (safety floor)
- max_sl_pips: Maximum stop loss (safety ceiling)
- risk_percent: Risk per trade in % of equity (e.g., 1.0 = 1%)
- rr: Risk:Reward ratio (e.g., 2.0 = TP is 2× SL)
- be_trigger_frac: Fraction of SL to trigger breakeven (e.g., 0.5)
- be_plus_pips: Extra pips above breakeven (e.g., 2)
- trailing_frac: Fraction of SL for trailing distance (e.g., 0.75)
- trailing_min_pips: Minimum trailing distance (e.g., 6)
- fallback_sl_pips: Used if ATR calculation fails (default 15)

Returns:
RiskPreset with dynamically calculated:
- sl_pips: From ATR × mult (clamped)
- tp_pips: From RR × sl_pips
- be_trigger_pips: From be_trigger_frac × sl_pips
- be_plus_pips: As specified
- trailing_pips: From trailing_frac × sl_pips (min threshold)
- _atr_meta: Diagnostic info (ATR used, calculations, etc.)

Requirements (svc.sugar API):
- atr_pips(symbol, period): Get ATR in pips
- Falls back to fallback_sl_pips if unavailable

Usage Example:
rp = await atr_risk(
    svc, "EURUSD",
    atr_period=14,          # Standard ATR period
    atr_mult=1.5,           # SL = 1.5 × ATR
    min_sl_pips=8,          # At least 8 pips
    max_sl_pips=40,         # At most 40 pips
    risk_percent=1.0,       # Risk 1% per trade
    rr=2.0,                 # TP = 2 × SL
    be_trigger_frac=0.5,    # BE at 50% of SL
    be_plus_pips=2,         # +2 pips above BE
    trailing_frac=0.75,     # Trailing = 75% of SL
    trailing_min_pips=6     # Minimum 6 pips trailing
)

Pro Tips:
💡 Higher volatility → Use lower atr_mult (1.0-1.5×)
💡 Lower volatility → Can use higher atr_mult (2.0-3.0×)
💡 Always set safety clamps (min/max) to prevent extreme values
💡 Test different ATR periods (14 standard, 7 for faster, 21 for slower)
💡 Combine with session_guard for time-based filtering
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Callable

# Import your canonical RiskPreset type
from Strategy.presets.risk import RiskPreset


# --- Helpers -----------------------------------------------------------------

async def _get_atr_pips(
    svc,
    symbol: str,
    atr_period: int,
    fallback_calc: Optional[Callable[[str, int], float]] = None,
) -> float | None:
    """Best-effort ATR(pips) getter."""
    sugar = svc.sugar
    if hasattr(sugar, "atr_pips"):
        try:
            return float(await sugar.atr_pips(symbol, period=atr_period))
        except Exception:
            pass
    if fallback_calc:
        try:
            return float(fallback_calc(symbol, atr_period))
        except Exception:
            pass
    return None


def _clamp(x: float, lo: float | None, hi: float | None) -> float:
    if lo is not None:
        x = max(lo, x)
    if hi is not None:
        x = min(hi, x)
    return x


# --- Main factory ------------------------------------------------------------

async def atr_risk(
    svc,
    symbol: str,
    *,
    atr_period: int = 14,
    atr_mult: float = 1.5,
    min_sl_pips: float | None = None,
    max_sl_pips: float | None = None,
    # Risk % of equity per trade (used downstream by calc_lot_by_risk)
    risk_percent: float = 1.0,
    # Optional TP by risk-reward multiple (tp_pips = rr * sl_pips)
    rr: float | None = 2.0,
    # Optional auto-BE derived from SL (e.g., 0.5 * SL)
    be_trigger_frac: float | None = 0.5,
    be_plus_pips: float | None = 2.0,
    # Optional trailing distance derived from SL (e.g., 0.75 * SL)
    trailing_frac: float | None = 0.75,
    trailing_min_pips: float | None = 6.0,
    # Fallback if atr is unavailable
    fallback_sl_pips: float = 15.0,
    fallback_calc: Optional[Callable[[str, int], float]] = None,
) -> RiskPreset:
    """
    Build a RiskPreset with sl_pips computed from ATR. Everything else mirrors RiskPreset.
    """
    atr = await _get_atr_pips(svc, symbol, atr_period, fallback_calc=fallback_calc)
    if atr is None or atr <= 0:
        sl_pips = fallback_sl_pips
        atr_used = None
    else:
        sl_pips = atr * float(atr_mult)
        sl_pips = _clamp(sl_pips, min_sl_pips, max_sl_pips)
        atr_used = atr

    # Compute TP from RR if requested
    tp_pips = None
    if rr is not None and sl_pips is not None:
        try:
            tp_pips = float(rr) * float(sl_pips)
        except Exception:
            tp_pips = None

    # Compute BE trigger and trailing from fractions of SL
    be_trigger_pips = None
    trailing_pips = None

    if be_trigger_frac is not None:
        try:
            be_trigger_pips = float(be_trigger_frac) * float(sl_pips)
        except Exception:
            be_trigger_pips = None

    if trailing_frac is not None:
        try:
            trailing_val = max(float(trailing_frac) * float(sl_pips), float(trailing_min_pips or 0.0))
            trailing_pips = trailing_val
        except Exception:
            trailing_pips = None

    # Return a standard RiskPreset (works everywhere)
    rp = RiskPreset(
        risk_percent=float(risk_percent),
        sl_pips=float(sl_pips),
        tp_pips=float(tp_pips) if tp_pips is not None else None,
        be_trigger_pips=float(be_trigger_pips) if be_trigger_pips is not None else None,
        be_plus_pips=float(be_plus_pips) if be_plus_pips is not None else None,
        trailing_pips=float(trailing_pips) if trailing_pips is not None else None,
    )

    # Attach introspection attributes (not required, but handy for logging/diagnostics)
    # These extra attrs won't break dataclass; they're just dynamic attributes.
    setattr(rp, "_atr_meta", {
        "symbol": symbol,
        "atr_period": atr_period,
        "atr_used_pips": atr_used,
        "atr_mult": atr_mult,
        "min_sl_pips": min_sl_pips,
        "max_sl_pips": max_sl_pips,
        "rr": rr,
        "be_trigger_frac": be_trigger_frac,
        "trailing_frac": trailing_frac,
        "trailing_min_pips": trailing_min_pips,
        "fallback_sl_pips": fallback_sl_pips,
    })
    return rp


# --- Ready-to-use wrappers (opinionated presets) -----------------------------

async def ATR_Scalper(
    svc, symbol: str, *, atr_period: int = 14, risk_percent: float = 1.0
) -> RiskPreset:
    """
    Tight stop based on ATR (good for liquid majors):
    SL = clamp(1.0 * ATR, 6 .. 15)
    TP = 1.2 * SL, BE at 0.5 * SL, trailing max(SL * 0.7, 6)
    """
    return await atr_risk(
        svc, symbol,
        atr_period=atr_period,
        atr_mult=1.0,
        min_sl_pips=6, max_sl_pips=15,
        risk_percent=risk_percent,
        rr=1.2,
        be_trigger_frac=0.5, be_plus_pips=2,
        trailing_frac=0.7, trailing_min_pips=6,
    )


async def ATR_Balanced(
    svc, symbol: str, *, atr_period: int = 14, risk_percent: float = 1.0
) -> RiskPreset:
    """
    Balanced stop:
    SL = clamp(1.5 * ATR, 10 .. 30)
    TP = 2.0 * SL, BE at 0.5 * SL, trailing max(SL * 0.75, 6)
    """
    return await atr_risk(
        svc, symbol,
        atr_period=atr_period,
        atr_mult=1.5,
        min_sl_pips=10, max_sl_pips=30,
        risk_percent=risk_percent,
        rr=2.0,
        be_trigger_frac=0.5, be_plus_pips=2,
        trailing_frac=0.75, trailing_min_pips=6,
    )


async def ATR_Swing(
    svc, symbol: str, *, atr_period: int = 14, risk_percent: float = 1.0
) -> RiskPreset:
    """
    Wider stop for swing:
    SL = clamp(2.0 * ATR, 20 .. 60)
    TP = 2.5 * SL, BE at 0.33 * SL, trailing max(SL * 0.5, 10)
    """
    return await atr_risk(
        svc, symbol,
        atr_period=atr_period,
        atr_mult=2.0,
        min_sl_pips=20, max_sl_pips=60,
        risk_percent=risk_percent,
        rr=2.5,
        be_trigger_frac=1/3, be_plus_pips=2,
        trailing_frac=0.5, trailing_min_pips=10,
    )

"""
Example of launch

from Strategy.presets.strategy_symbols import MarketEURUSD, MarketXAUUSD
from Strategy.presets.risk_atr import atr_risk, ATR_Scalper, ATR_Balanced, ATR_Swing

# 1) Flexible preset for EURUSD(SL=k*ATR, TP=RR*SL)
rp1 = await atr_risk(
    svc, MarketEURUSD.symbol,
    atr_period=14, atr_mult=1.5,
    min_sl_pips=10, max_sl_pips=30,
    risk_percent=1.0, rr=2.0,
)

# 2) A ready-made "button" (Scalper) for gold
rp2 = await ATR_Scalper(svc, MarketXAUUSD.symbol, atr_period=14, risk_percent=0.75)

# 3) In an orchestrator (e.g., Market One-Shot)
from Strategy.orchestrator.market_one_shot import run_market_one_shot
res = await run_market_one_shot(svc, MarketEURUSD, rp1)

"""