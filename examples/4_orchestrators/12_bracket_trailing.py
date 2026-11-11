"""
═══════════════════════════════════════════════════════════════════════════════
 FILE: 12_bracket_trailing.py - ORCHESTRATOR: Bracket + Trailing Activation

 PURPOSE:
   Open a bracketed position (SL/TP) and leave it alone until it reaches a
   profit threshold; only then switch on a trailing stop. Entry protection
   first, trailing only once the trade is "paying for itself".

 🎯 WHO SHOULD USE THIS:
   • Traders who want a trailing stop that arms only in profit
   • Bots combining a fixed bracket with conditional trailing
   • Learning staged/conditional position management

 📚 WHAT THIS DEMO COVERS:

   ORCHESTRATOR:
      • run_bracket_with_trailing_activation(service, strategy, risk,
            side, activate_trailing_at_pips, trailing_distance_pips,
            poll_interval_s)
        -> market entry + bracket, then trailing once profit >= threshold;
           returns {ticket, activated, ...}

   INPUTS (Strategy/presets/):
      • StrategyPreset(symbol, use_market, entry_price, lots, magic,
                       deviation_pips, comment)          - what / where to enter
      • RiskPreset(risk_percent, sl_pips, tp_pips, trailing_pips, ...)  - risk

   STEPS:
      1. RUN     - run the orchestrator, capped at RUN_CAP_S seconds
                   (trailing usually won't activate within the demo window)
      2. CLEANUP - close positions and cancel pendings for the symbol

 🔄 API LEVELS:
   ORCHESTRATOR - THIS FILE: multi-step strategy built ON TOP of the stack
   HIGH-LEVEL  (MT4Sugar)   - one-liner trading used under the hood
   MID-LEVEL   (MT4Service) - handed to the orchestrator, which drives it
   LOW-LEVEL   (MT4Account) - raw gRPC client beneath the service

 🚀 HOW TO RUN:
   cd examples
   python main.py trailing         (or select [12] from the menu)

 ⚠️  WARNING: this demo OPENS A REAL 0.01 POSITION on your account!
   • Uses the minimum lot size (0.01)
   • Closes positions / cancels pendings at the end
   • Run on a DEMO account first
═══════════════════════════════════════════════════════════════════════════════
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
        # region RUN
        # ═══════════════════════════════════════════════════════════════
        # 1. RUN THE ORCHESTRATOR
        # ═══════════════════════════════════════════════════════════════
        #    run_bracket_with_trailing_activation(service, strategy, risk, ...)
        #    Opens a REAL bracketed position; arms a trailing stop only
        #    after +activate_trailing_at_pips. Capped at RUN_CAP_S for
        #    the demo (activation usually won't be reached in time).
        #    Returns: dict with ticket, activated.
        #    ⚠️  sends a REAL order.
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
        # endregion
    except Exception as e:
        print_if_error(e, "run_bracket_with_trailing_activation")
    finally:
        # region CLEANUP
        # ═══════════════════════════════════════════════════════════════
        # 2. CLEANUP
        # ═══════════════════════════════════════════════════════════════
        #    Close positions and cancel pendings for the symbol.
        #    Best-effort (_cleanup swallows errors), then disconnect.
        print_step(2, "Cleanup")
        await _cleanup(service)
        print_success("positions/pendings cleared")
        await service.disconnect()
        print_success("Disconnected")
        # endregion


if __name__ == "__main__":
    asyncio.run(main())
