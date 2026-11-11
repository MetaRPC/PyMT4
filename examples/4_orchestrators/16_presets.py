"""
═══════════════════════════════════════════════════════════════════════════════
 FILE: 16_presets.py - STRATEGY & RISK PRESETS

 PURPOSE:
   Show the two small dataclasses that drive every orchestrator and the
   ready-made presets / factories around them. This file only BUILDS and
   PRINTS presets — no connection, no trading.

 🎯 WHO SHOULD USE THIS:
   • Anyone wiring up orchestrators 11-15 and choosing inputs
   • Users who want ready-made presets or templates to copy
   • Learning how StrategyPreset / RiskPreset are shaped

 📚 WHAT THIS DEMO COVERS (3 steps):

   STEP 1: STRATEGY PRESETS - what / where to enter
      • ready-made         - MarketEURUSD, LimitEURUSD(), BreakoutBuy()
      • per-symbol limits  - strategy_symbols.LimitGBPUSD(), LimitXAUUSD(), REGISTRY
      • custom             - build your own StrategyPreset(...)

   STEP 2: RISK PRESETS - how much to risk / protect
      • ready-made         - Conservative
      • profiles           - risk_profiles.ScalperEURUSD(), SwingEURUSD()
      • custom             - build your own RiskPreset(...)

   STEP 3: USE THEM
      • pass StrategyPreset + RiskPreset straight into an orchestrator, e.g.
        run_market_one_shot(service, StrategyPreset(...), RiskPreset(...))

   The dataclasses (Strategy/presets/):
      StrategyPreset(symbol, use_market, entry_price, lots, magic,
                     deviation_pips, comment)
      RiskPreset(risk_percent, sl_pips, tp_pips, trailing_pips,
                 be_trigger_pips, be_plus_pips)

 🔄 API LEVELS:
   These presets are the INPUTS orchestrators consume; the orchestrators sit
   ON TOP of MT4Service > MT4Account. No API calls are made in this file.

 🚀 HOW TO RUN:
   cd examples
   python main.py presets          (or select [16] from the menu)

 ℹ️  SAFE: read-only — builds and prints presets, no connection, no orders.
═══════════════════════════════════════════════════════════════════════════════
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "0_common"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "package"))

from demo_helpers import print_step, print_method, print_info
from Strategy.presets.strategy import StrategyPreset, MarketEURUSD, LimitEURUSD, BreakoutBuy
from Strategy.presets.risk import RiskPreset, Conservative
from Strategy.presets import risk_profiles, strategy_symbols


def show(name, preset):
    print(f"   {name:<24} -> {preset}")


async def main():
    print("\n" + "=" * 78)
    print("STRATEGY & RISK PRESETS")
    print("=" * 78)

    # region STRATEGY PRESETS
    # ═══════════════════════════════════════════════════════════════════
    # 1. STRATEGY PRESETS - what / where to enter
    # ═══════════════════════════════════════════════════════════════════
    print_step(1, "Strategy presets (what / where to enter)")
    # ───────────────────────────────────────────────────────
    # 1.1  Ready-made presets (Strategy/presets/strategy.py)
    # ───────────────────────────────────────────────────────
    print_method("1.1", "ready-made", "Strategy/presets/strategy.py")
    show("MarketEURUSD", MarketEURUSD)
    show("LimitEURUSD(1.0900)", LimitEURUSD(1.0900))
    show("BreakoutBuy('EURUSD',10)", BreakoutBuy("EURUSD", 10.0))

    # ───────────────────────────────────────────────────────
    # 1.2  Per-symbol limit factories (strategy_symbols.py)
    # ───────────────────────────────────────────────────────
    print_method("1.2", "per-symbol limit factories", "Strategy/presets/strategy_symbols.py")
    show("LimitGBPUSD(1.2600)", strategy_symbols.LimitGBPUSD(1.2600))
    show("LimitXAUUSD(3900.0)", strategy_symbols.LimitXAUUSD(3900.0))
    print_info(f"registry symbols: {list(strategy_symbols.REGISTRY.keys())}")

    # ───────────────────────────────────────────────────────
    # 1.3  Custom — build your own StrategyPreset(...)
    # ───────────────────────────────────────────────────────
    print_method("1.3", "custom", "build your own StrategyPreset")
    show("custom", StrategyPreset(symbol="USDJPY", use_market=True, lots=0.02,
                                  magic=1234, deviation_pips=4.0, comment="my strategy"))

    # endregion

    # region RISK PRESETS
    # ═══════════════════════════════════════════════════════════════════
    # 2. RISK PRESETS - how much to risk / protect
    # ═══════════════════════════════════════════════════════════════════
    print_step(2, "Risk presets (how much to risk / protect)")
    # ───────────────────────────────────────────────────────
    # 2.1  Ready-made preset (Strategy/presets/risk.py)
    # ───────────────────────────────────────────────────────
    print_method("2.1", "ready-made", "Strategy/presets/risk.py")
    show("Conservative", Conservative)

    # ───────────────────────────────────────────────────────
    # 2.2  Profiles (Strategy/presets/risk_profiles.py)
    # ───────────────────────────────────────────────────────
    print_method("2.2", "profiles", "Strategy/presets/risk_profiles.py")
    show("ScalperEURUSD()", risk_profiles.ScalperEURUSD())
    show("SwingEURUSD()", risk_profiles.SwingEURUSD())

    # ───────────────────────────────────────────────────────
    # 2.3  Custom — build your own RiskPreset(...)
    # ───────────────────────────────────────────────────────
    print_method("2.3", "custom", "build your own RiskPreset")
    show("custom", RiskPreset(risk_percent=1.0, sl_pips=30, tp_pips=60,
                              trailing_pips=20, be_trigger_pips=20, be_plus_pips=1))

    # endregion

    # region USE THEM
    # ═══════════════════════════════════════════════════════════════════
    # 3. USE THEM
    # ═══════════════════════════════════════════════════════════════════
    #    Pass a StrategyPreset + a RiskPreset straight into any orchestrator.
    print_step(3, "Use them")
    print_info("await run_market_one_shot(service, StrategyPreset(...), RiskPreset(...))")
    print_info("See orchestrators 11-15 for live examples.")
    # endregion


if __name__ == "__main__":
    asyncio.run(main())
