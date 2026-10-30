"""
==============================================================================
 FILE: 16_presets.py - STRATEGY & RISK PRESETS

 The orchestrators are driven by two small dataclasses from Strategy/presets/:

   StrategyPreset(symbol, use_market, entry_price, lots, magic, deviation_pips, comment)
   RiskPreset(risk_percent, sl_pips, tp_pips, trailing_pips, be_trigger_pips, be_plus_pips)

 You pass them straight into any orchestrator:

   result = await run_market_one_shot(service, strategy, risk)

 This file just builds and prints the ready-made presets and factories — no
 connection and no trading. Use them as-is or as templates for your own.

 HOW TO RUN:
   cd examples
   python main.py presets          (or select [16] from the menu)
==============================================================================
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

    # --- Strategy presets ---------------------------------------------------
    print_step(1, "Strategy presets (what / where to enter)")
    print_method("1.1", "ready-made", "Strategy/presets/strategy.py")
    show("MarketEURUSD", MarketEURUSD)
    show("LimitEURUSD(1.0900)", LimitEURUSD(1.0900))
    show("BreakoutBuy('EURUSD',10)", BreakoutBuy("EURUSD", 10.0))

    print_method("1.2", "per-symbol limit factories", "Strategy/presets/strategy_symbols.py")
    show("LimitGBPUSD(1.2600)", strategy_symbols.LimitGBPUSD(1.2600))
    show("LimitXAUUSD(3900.0)", strategy_symbols.LimitXAUUSD(3900.0))
    print_info(f"registry symbols: {list(strategy_symbols.REGISTRY.keys())}")

    print_method("1.3", "custom", "build your own StrategyPreset")
    show("custom", StrategyPreset(symbol="USDJPY", use_market=True, lots=0.02,
                                  magic=1234, deviation_pips=4.0, comment="my strategy"))

    # --- Risk presets -------------------------------------------------------
    print_step(2, "Risk presets (how much to risk / protect)")
    print_method("2.1", "ready-made", "Strategy/presets/risk.py")
    show("Conservative", Conservative)

    print_method("2.2", "profiles", "Strategy/presets/risk_profiles.py")
    show("ScalperEURUSD()", risk_profiles.ScalperEURUSD())
    show("SwingEURUSD()", risk_profiles.SwingEURUSD())

    print_method("2.3", "custom", "build your own RiskPreset")
    show("custom", RiskPreset(risk_percent=1.0, sl_pips=30, tp_pips=60,
                              trailing_pips=20, be_trigger_pips=20, be_plus_pips=1))

    print_step(3, "Use them")
    print_info("await run_market_one_shot(service, StrategyPreset(...), RiskPreset(...))")
    print_info("See orchestrators 11-15 for live examples.")


if __name__ == "__main__":
    asyncio.run(main())
