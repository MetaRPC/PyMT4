# -*- coding: utf-8 -*-
"""
Strategy Presets - Unified Import Surface 🎯
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Purpose: One-stop import hub for all trading presets - risk, strategy, profiles.
         "Import once, access everything" - clean and organized API surface.

What's Inside? 📦

This module re-exports everything from the presets package:

🎯 Base Types:
   - RiskPreset: Core risk configuration dataclass
   - StrategyPreset: Core strategy configuration dataclass

💰 Classic Risk Presets (risk.py):
   - Conservative, Balanced, Aggressive (simple fixed-pip presets)
   - Scalper, Walker (advanced with trailing/BE)

📋 Classic Strategy Presets (strategy.py):
   - MarketEURUSD (basic market order preset)
   - LimitEURUSD(price) (limit order factory)
   - BreakoutBuy(symbol, offset) (breakout factory)

🌍 Symbol-Aware Strategies (strategy_symbols.py):
   - Market/Limit/Breakout presets for: EUR/USD, GBP/USD, USD/JPY
   - Metals: XAU/USD (Gold), XAG/USD (Silver)
   - Indices: US100, US500, GER40
   - Crypto: BTC/USD
   - STRATEGY_REGISTRY: Quick lookup dict

📊 Risk Profiles (risk_profiles.py):
   - make_scalper_tight(), make_swing_wide() (style-based factories)
   - ScalperEURUSD, ScalperXAUUSD (symbol-specific scalpers)
   - SwingEURUSD, SwingXAUUSD (symbol-specific swing)

🕐 Session-Based Risk (risk_session.py):
   - session_risk_auto(svc, symbol, tz, profile) (auto-detection)
   - make_asia_conservative(), make_london_balanced()
   - make_newyork_balanced(), make_overlap_momentum()
   - make_london_aggressive(), make_newyork_aggressive(), make_asia_scalper()

📈 ATR-Driven Risk (risk_atr.py):
   - atr_risk(svc, symbol, multiplier, clamp_min, clamp_max) (dynamic)
   - ATR_Scalper, ATR_Balanced, ATR_Swing (ATR-based presets)

Why Use This Module? ✓
✓ Single import: from Strategy.presets import *
✓ Clean namespace: No deep imports needed
✓ Backward compatibility: Old imports still work
✓ Organized: Logical grouping of related presets
✓ Discoverable: See all available presets in __all__

Quick Start Examples:

💡 Simple Market Order:
   from Strategy.presets import MarketEURUSD, Balanced
   result = await run_market_one_shot(svc, MarketEURUSD, Balanced)

💡 Symbol-Specific with ATR Risk:
   from Strategy.presets import MarketXAUUSD, ATR_Balanced
   risk = await ATR_Balanced(svc, "XAUUSD")
   result = await run_market_one_shot(svc, MarketXAUUSD, risk)

💡 Session-Aware Trading:
   from Strategy.presets import MarketGBPUSD, session_risk_auto
   risk = await session_risk_auto(svc, "GBPUSD", tz="Europe/London")
   result = await run_market_one_shot(svc, MarketGBPUSD, risk)

💡 Scalper Setup:
   from Strategy.presets import MarketEURUSD, ScalperEURUSD
   risk = ScalperEURUSD()
   result = await run_market_one_shot(svc, MarketEURUSD, risk)

💡 Multi-Symbol Portfolio:
   from Strategy.presets import (
       MarketEURUSD, MarketGBPUSD, MarketXAUUSD, Balanced
   )
   for strategy in [MarketEURUSD, MarketGBPUSD, MarketXAUUSD]:
       result = await run_market_one_shot(svc, strategy, Balanced)

Import Patterns:

💡 Import Everything:
   from Strategy.presets import *
   # Now have access to all presets

💡 Import Specific Presets:
   from Strategy.presets import (
       MarketEURUSD, MarketXAUUSD,
       Balanced, Aggressive,
       ATR_Scalper, session_risk_auto
   )

💡 Import from Submodules (still works):
   from Strategy.presets.risk import Conservative
   from Strategy.presets.strategy_symbols import MarketGBPUSD
   from Strategy.presets.risk_atr import atr_risk

Preset Categories Summary:

┌──────────────────────┬────────────────────┬─────────────────┐
│ Category             │ Use Case           │ Key Presets     │
├──────────────────────┼────────────────────┼─────────────────┤
│ Classic Risk         │ Simple fixed-pip   │ Balanced        │
│ Symbol Strategies    │ Per-symbol tuning  │ MarketXAUUSD    │
│ Risk Profiles        │ Style-based        │ ScalperEURUSD   │
│ Session Risk         │ Time-aware         │ session_risk_auto│
│ ATR Risk             │ Volatility-adaptive│ ATR_Balanced    │
└──────────────────────┴────────────────────┴─────────────────┘

Architecture:

Strategy.presets/
├── __init__.py         ← You are here (unified imports)
├── risk.py             ← Base RiskPreset + Conservative/Balanced/Aggressive
├── strategy.py         ← Base StrategyPreset + MarketEURUSD
├── strategy_symbols.py ← Symbol-specific strategy presets
├── risk_profiles.py    ← Scalper/Swing style-based risk
├── risk_session.py     ← Session-aware dynamic risk
└── risk_atr.py         ← ATR-driven volatility-adaptive risk

Backward Compatibility:

All old imports continue to work:
✓ from Strategy.presets.risk import Balanced
✓ from Strategy.presets.strategy import MarketEURUSD
✓ from Strategy.presets.strategy_symbols import MarketXAUUSD

New unified imports also work:
✓ from Strategy.presets import Balanced
✓ from Strategy.presets import MarketEURUSD, MarketXAUUSD

Pro Tips:

💡 Use unified imports for cleaner code
💡 Combine risk + strategy presets for complete setup
💡 Mix and match: ATR risk + symbol strategy
💡 Session risk + symbol strategy for time-aware trading
💡 Check __all__ for complete list of available presets
"""

# --- Base (keep old API) -----------------------------------------------------
from .risk import (
    RiskPreset,
    Conservative, Balanced, Aggressive, Scalper, Walker,
)
from .strategy import (
    StrategyPreset,
    MarketEURUSD, LimitEURUSD, BreakoutBuy,
)

# --- Symbol-aware strategies --------------------------------------------------
from .strategy_symbols import (
    # FX
    MarketGBPUSD, LimitGBPUSD, BreakoutGBPUSD,
    MarketUSDJPY, LimitUSDJPY, BreakoutUSDJPY,
    # Metals
    MarketXAUUSD, LimitXAUUSD, BreakoutXAUUSD,
    MarketXAGUSD, LimitXAGUSD, BreakoutXAGUSD,
    # Indices
    MarketUS100, LimitUS100, BreakoutUS100,
    MarketUS500, LimitUS500, BreakoutUS500,
    MarketGER40, LimitGER40, BreakoutGER40,
    # Crypto (if broker supports)
    MarketBTCUSD, LimitBTCUSD, BreakoutBTCUSD,
    # Quick registry
    REGISTRY as STRATEGY_REGISTRY,
)

# --- Risk profiles: Scalper Tight / Swing Wide --------------------------------
from .risk_profiles import (
    make_scalper_tight, make_swing_wide,
    ScalperEURUSD, ScalperXAUUSD, SwingEURUSD, SwingXAUUSD,
)

# --- Session-based risk -------------------------------------------------------
from .risk_session import (
    session_risk_auto,
    make_asia_conservative, make_london_balanced,
    make_newyork_balanced, make_overlap_momentum,
    make_london_aggressive, make_newyork_aggressive, make_asia_scalper,
)

# --- ATR-driven risk ----------------------------------------------------------
from .risk_atr import (
    atr_risk,
    ATR_Scalper, ATR_Balanced, ATR_Swing,
)

__all__ = [
    # Base types
    "RiskPreset", "StrategyPreset",

    # Classic risk presets
    "Conservative", "Balanced", "Aggressive", "Scalper", "Walker",

    # Classic strategy presets
    "MarketEURUSD", "LimitEURUSD", "BreakoutBuy",

    # Symbol-aware strategies (FX)
    "MarketGBPUSD", "LimitGBPUSD", "BreakoutGBPUSD",
    "MarketUSDJPY", "LimitUSDJPY", "BreakoutUSDJPY",

    # Metals
    "MarketXAUUSD", "LimitXAUUSD", "BreakoutXAUUSD",
    "MarketXAGUSD", "LimitXAGUSD", "BreakoutXAGUSD",

    # Indices
    "MarketUS100", "LimitUS100", "BreakoutUS100",
    "MarketUS500", "LimitUS500", "BreakoutUS500",
    "MarketGER40", "LimitGER40", "BreakoutGER40",

    # Crypto
    "MarketBTCUSD", "LimitBTCUSD", "BreakoutBTCUSD",

    # Registry
    "STRATEGY_REGISTRY",

    # Risk profiles (Scalper/Swing)
    "make_scalper_tight", "make_swing_wide",
    "ScalperEURUSD", "ScalperXAUUSD", "SwingEURUSD", "SwingXAUUSD",

    # Session-based risk
    "session_risk_auto",
    "make_asia_conservative", "make_london_balanced",
    "make_newyork_balanced", "make_overlap_momentum",
    "make_london_aggressive", "make_newyork_aggressive", "make_asia_scalper",

    # ATR-driven risk
    "atr_risk", "ATR_Scalper", "ATR_Balanced", "ATR_Swing",
]

