"""
==============================================================================
 FILE: 12_bracket_trailing.py - ORCHESTRATOR: Bracket + Trailing Activation

  ⚠️  Opens a real 0.01 position on your DEMO account; cleaned up at the end.

 Strategy: open a position with a bracket (SL/TP), then once it reaches a
 profit threshold, switch on a trailing stop.

     result = await run_bracket_with_trailing_activation(
         service, strategy, risk, side="buy",
         activate_trailing_at_pips=..., trailing_distance_pips=...)

 In this short demo the position usually won't reach the activation threshold,
 so we cap the run and then close whatever was opened.

 HOW TO RUN:
   cd examples
   python main.py trailing         (or select [12] from the menu)
==============================================================================
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "0_common"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "package"))

from demo_helpers import (
    load_settings, create_and_connect_mt4,
    print_step, print_success, print_info, print_if_error, fatal,
)
from app.MT4Service import MT4Service
from Strategy.orchestrator.bracket_trailing_activation import run_bracket_with_trailing_activation
from Strategy.presets.strategy import StrategyPreset
from Strategy.presets.risk import RiskPreset

SYMBOL = "EURUSD"
RUN_CAP_S = 18


async def _cleanup(service):
    sugar = service.sugar
    try:
        await sugar.close_all(symbol=SYMBOL)
    except Exception:
        pass
    try:
        await sugar.cancel_pendings(symbol=SYMBOL)
    except Exception:
        pass


async def main():
    print("\n" + "=" * 78)
    print("ORCHESTRATOR: Bracket + Trailing Activation")
    print("=" * 78)
    try:
        config = load_settings()
    except Exception as e:
        fatal(e, "Failed to load settings")

    account = await create_and_connect_mt4(config)
    service = MT4Service(account)

    strategy = StrategyPreset(symbol=SYMBOL, use_market=True, lots=0.01,
                              magic=778, deviation_pips=3.0, comment="pymt4 bracket_trailing")
    risk = RiskPreset(risk_percent=1.0, sl_pips=40, tp_pips=120, trailing_pips=20)

    try:
        print_step(1, "Run the orchestrator (market entry + trailing-on-profit)")
        print_info(f"activate trailing at +8 pips, distance {risk.trailing_pips} pips; "
                   f"capped at {RUN_CAP_S}s for the demo")
        try:
            result = await asyncio.wait_for(
                run_bracket_with_trailing_activation(
                    service, strategy, risk, side="buy",
                    activate_trailing_at_pips=8.0,
                    trailing_distance_pips=risk.trailing_pips,
                    poll_interval_s=1.0,
                ),
                timeout=RUN_CAP_S,
            )
            print_success(f"orchestrator returned: { {k: result.get(k) for k in ('ticket', 'activated')} }")
        except asyncio.TimeoutError:
            print_info("demo cap reached before trailing activated — closing the position")
    except Exception as e:
        print_if_error(e, "run_bracket_with_trailing_activation")
    finally:
        print_step(2, "Cleanup")
        await _cleanup(service)
        print_success("positions/pendings cleared")
        await service.disconnect()
        print_success("Disconnected")


if __name__ == "__main__":
    asyncio.run(main())
