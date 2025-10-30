# -*- coding: utf-8 -*-
"""
Dynamic Deviation Guard Orchestrator
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Purpose: Wrapper orchestrator that computes market-adaptive slippage/deviation
         dynamically before executing any trading strategy.

Problem: Fixed deviation values don't adapt to:
         - Volatile market conditions (wide spreads, fast price movements)
         - Different symbols (EURUSD vs BTCUSD have different typical spreads)
         - Time of day (Asian session vs London/NY overlap)

Solution: Calculate deviation_pips dynamically based on current market conditions
          using spread, ATR (Average True Range), or both.

Deviation Sources:
┌─────────┬────────────────────────────────────────────────────────────────────┐
│ spread  │ deviation = spread_pips * spread_mult + spread_add                │
│         │ Use when: Fast-moving markets, scalping, tight spreads important  │
├─────────┼────────────────────────────────────────────────────────────────────┤
│ atr     │ deviation = atr_pips(period) * atr_mult + atr_add                 │
│         │ Use when: Volatility-based adjustment, swing trading              │
├─────────┼────────────────────────────────────────────────────────────────────┤
│ hybrid  │ Combine spread + ATR via 'max' (default) or 'sum'                 │
│         │ Use when: Best of both worlds - adapts to spread AND volatility   │
├─────────┼────────────────────────────────────────────────────────────────────┤
│ fixed   │ Force constant deviation regardless of market conditions          │
│         │ Use when: Testing, backtesting, or broker-specific requirements   │
└─────────┴────────────────────────────────────────────────────────────────────┘

Parameters:
- spread_mult, spread_add: Linear formula for spread-based deviation
- atr_period: ATR lookback period (default 14)
- atr_mult, atr_add: Linear formula for ATR-based deviation
- hybrid_mode: "max" (pick larger) or "sum" (add both components)
- min_dev, max_dev: Safety clamps (e.g., 0.5 to 5.0 pips)
- fallback_dev: Fallback value if calculations fail (default 2.0)
- post_round_to_01pip: Round final value to 0.1 pip granularity

Execution Flow:
1. Ensure connection and symbol availability
2. Measure current spread_pips and/or atr_pips based on source
3. Calculate deviation using configured formulas
4. Apply min/max clamps and optional rounding
5. Set deviation via sugar.set_defaults()
6. Execute wrapped orchestrator strategy
7. Return strategy result + dynamic_deviation_meta

Returns:
dict - Strategy result with additional 'dynamic_deviation_meta' containing:
       spread_pips, atr_pips, final_deviation_pips, formulas used, etc.

Requirements (svc.sugar API):
- ensure_connected, ensure_symbol: Connection management
- spread_pips: Get current spread in pips
- atr_pips: Get ATR in pips (optional, only for 'atr'/'hybrid' sources)
- set_defaults: Set deviation_pips before strategy execution
"""

from __future__ import annotations
from dataclasses import asdict
from typing import Callable, Optional, Literal

Source = Literal["spread", "atr", "hybrid", "fixed"]
HybridMode = Literal["max", "sum"]

DEFAULT_ATR_PERIOD = 14

async def run_with_dynamic_deviation(
    svc,
    runner_coro_factory: Callable[[], "object"],  # () -> coroutine
    *,
    symbol: str,
    source: Source = "hybrid",
    # Spread component
    spread_mult: float = 1.2,
    spread_add: float = 0.2,
    # ATR component
    atr_period: int = DEFAULT_ATR_PERIOD,
    atr_mult: float = 0.6,
    atr_add: float = 0.0,
    # Hybrid combiner
    hybrid_mode: HybridMode = "max",
    # Final clamps
    min_dev: Optional[float] = 0.5,
    max_dev: Optional[float] = 5.0,
    # Safety: fallback if sources fail
    fallback_dev: float = 2.0,
    # Optional: override after compute (e.g., round to tick)
    post_round_to_01pip: bool = True,
    # Attach meta
    reason_meta: Optional[dict] = None,
) -> dict:
    """
    Compute deviation_pips, set it via sugar.set_defaults, then run the scenario.
    Returns the scenario result with an extra 'dynamic_deviation_meta'.
    """
    sugar = svc.sugar
    await sugar.ensure_connected()
    await sugar.ensure_symbol(symbol)

    # --- Gather measurements
    spread_val = None
    atr_val = None

    try:
        spread_val = await sugar.spread_pips(symbol)
    except Exception:
        spread_val = None

    if source in ("atr", "hybrid"):
        if hasattr(sugar, "atr_pips"):
            try:
                atr_val = await sugar.atr_pips(symbol, period=atr_period)
            except Exception:
                atr_val = None

    # --- Compute components
    dev_from_spread = None
    dev_from_atr = None

    if spread_val is not None and source in ("spread", "hybrid"):
        dev_from_spread = spread_val * spread_mult + spread_add

    if atr_val is not None and source in ("atr", "hybrid"):
        dev_from_atr = atr_val * atr_mult + atr_add

    # --- Combine to final deviation
    deviation = None
    if source == "fixed":
        deviation = fallback_dev
    elif source == "spread":
        deviation = dev_from_spread
    elif source == "atr":
        deviation = dev_from_atr
    elif source == "hybrid":
        # default: max of the two signals; fallback to the one that exists
        vals = [v for v in (dev_from_spread, dev_from_atr) if v is not None]
        if vals:
            deviation = max(vals) if hybrid_mode == "max" else sum(vals)
        else:
            deviation = None

    # Fallback if none computed
    if deviation is None or not _is_finite_positive(deviation):
        deviation = fallback_dev

    # Clamp
    if min_dev is not None:
        deviation = max(min_dev, deviation)
    if max_dev is not None:
        deviation = min(max_dev, deviation)

    # Optional rounding to 0.1 pip granularity (adjust if you want 0.01)
    if post_round_to_01pip:
        deviation = round(float(deviation), 1)

    # Set default just-in-time
    sugar.set_defaults(symbol=symbol, deviation_pips=deviation)

    # Run the wrapped orchestrator
    res = await runner_coro_factory()

    meta = {
        "symbol": symbol,
        "source": source,
        "spread_pips": spread_val,
        "atr_period": atr_period if source in ("atr", "hybrid") else None,
        "atr_pips": atr_val,
        "spread_mult": spread_mult,
        "spread_add": spread_add,
        "atr_mult": atr_mult,
        "atr_add": atr_add,
        "hybrid_mode": hybrid_mode if source == "hybrid" else None,
        "min_dev": min_dev,
        "max_dev": max_dev,
        "fallback_dev": fallback_dev,
        "final_deviation_pips": deviation,
    }
    if reason_meta:
        meta.update(reason_meta)

    if isinstance(res, dict):
        res = {**res, "dynamic_deviation_meta": meta}
    return res


def _is_finite_positive(x) -> bool:
    try:
        return float(x) > 0.0
    except Exception:
        return False

"""
Example of launch

1) OCO-Straddle with hybrid deviation (max(spread-based, ATR-based))

from Strategy.orchestrator.dynamic_deviation_guard import run_with_dynamic_deviation
from Strategy.orchestrator.oco_straddle import run_oco_straddle
from Strategy.presets.strategy import MarketEURUSD
from Strategy.presets.risk import Balanced

result = await run_with_dynamic_deviation(
    svc,
    runner_coro_factory=lambda: run_oco_straddle(
        svc, MarketEURUSD, Balanced, offset_pips=10
    ),
    symbol=MarketEURUSD.symbol,
    source="hybrid",          # combine spread + ATR
    spread_mult=1.2,          # deviation >= 1.2 * spread + 0.2
    spread_add=0.2,
    atr_period=14,
    atr_mult=0.6,
    min_dev=0.6,
    max_dev=4.0,
)

══════════════════════════════════════════════════════════════════════════════════════════

2) Bracket + Trailing Activation — deviation only from the spread

from Strategy.orchestrator.dynamic_deviation_guard import run_with_dynamic_deviation
from Strategy.orchestrator.bracket_trailing_activation import run_bracket_with_trailing_activation
from Strategy.presets.strategy import MarketEURUSD
from Strategy.presets.risk import Balanced

res = await run_with_dynamic_deviation(
    svc,
    runner_coro_factory=lambda: run_bracket_with_trailing_activation(
        svc, MarketEURUSD, Balanced,
        side="buy",
        activate_trailing_at_pips=12.0,
        trailing_distance_pips=6.0
    ),
    symbol=MarketEURUSD.symbol,
    source="spread",          # only spread-based
    spread_mult=1.5,
    spread_add=0.1,
    min_dev=0.5,
    max_dev=3.0,
)


"""