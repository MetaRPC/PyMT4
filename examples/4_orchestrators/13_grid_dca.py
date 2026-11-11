"""
═══════════════════════════════════════════════════════════════════════════════
 FILE: 13_grid_dca.py - ORCHESTRATOR: Grid DCA with a common Stop Loss

 PURPOSE:
   Lay a Dollar-Cost-Averaging grid of limit orders spaced by step_pips and
   manage the whole ladder under ONE shared Stop Loss once legs start filling.
   Averages into a position instead of betting on a single entry.

 🎯 WHO SHOULD USE THIS:
   • Traders who scale into a level with multiple limit legs
   • Bots that average down/up under a single risk cap
   • Learning multi-leg (grid/DCA) position construction

 📚 WHAT THIS DEMO COVERS:

   ORCHESTRATOR:
      • run_grid_dca_common_sl(service, strategy, risk, side,
            steps, step_pips, risk_mode, risk_total_percent)
        -> places `steps` limit legs spaced by step_pips under a common SL;
           returns a result dict (ticket/leg info)

   INPUTS (Strategy/presets/):
      • StrategyPreset(symbol, use_market=False, lots, magic,
                       deviation_pips, comment)          - grid base (pending)
      • RiskPreset(risk_percent, sl_pips, tp_pips)        - shared risk envelope

   STEPS:
      1. RUN     - build the grid, capped at RUN_CAP_S seconds
                   (legs sit off-market and usually don't fill in the demo)
      2. CLEANUP - cancel the grid and close any positions for the symbol

 🔄 API LEVELS:
   ORCHESTRATOR - THIS FILE: multi-step strategy built ON TOP of the stack
   HIGH-LEVEL  (MT4Sugar)   - one-liner trading used under the hood
   MID-LEVEL   (MT4Service) - handed to the orchestrator, which drives it
   LOW-LEVEL   (MT4Account) - raw gRPC client beneath the service

 🚀 HOW TO RUN:
   cd examples
   python main.py grid             (or select [13] from the menu)

 ⚠️  WARNING: this demo PLACES REAL 0.01 PENDING ORDERS on your account!
   • Uses the minimum lot size (0.01) per leg
   • Cancels the grid / closes positions at the end
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
from Strategy.orchestrator.grid_dca_common_sl import run_grid_dca_common_sl
from Strategy.presets.strategy import StrategyPreset
from Strategy.presets.risk import RiskPreset

SYMBOL = "EURUSD"
RUN_CAP_S = 15


async def _cleanup(service):
    sugar = service.sugar
    for fn in (lambda: sugar.close_all(symbol=SYMBOL), lambda: sugar.cancel_pendings(symbol=SYMBOL)):
        try:
            await fn()
        except Exception:
            pass


async def main():
    print("\n" + "=" * 78)
    print("ORCHESTRATOR: Grid DCA (common SL)")
    print("=" * 78)
    try:
        config = load_settings()
    except Exception as e:
        fatal(e, "Failed to load settings")

    account = await create_and_connect_mt4(config)
    service = MT4Service(account)

    strategy = StrategyPreset(symbol=SYMBOL, use_market=False, lots=0.01,
                              magic=780, deviation_pips=3.0, comment="pymt4 grid_dca")
    risk = RiskPreset(risk_percent=1.0, sl_pips=60, tp_pips=None)

    try:
        # region RUN
        # ═══════════════════════════════════════════════════════════════
        # 1. RUN THE ORCHESTRATOR
        # ═══════════════════════════════════════════════════════════════
        #    run_grid_dca_common_sl(service, strategy, risk, side, ...)
        #    Places a REAL 3-leg BUY grid (10 pip spacing) under one
        #    shared SL. Capped at RUN_CAP_S for the demo (legs usually
        #    stay pending).
        #    Returns: result dict (leg/ticket info).
        #    ⚠️  sends REAL pending orders.
        print_step(1, "Run the orchestrator (3-leg BUY grid, 10 pip spacing)")
        try:
            result = await asyncio.wait_for(
                run_grid_dca_common_sl(
                    service, strategy, risk, side="buy",
                    steps=3, step_pips=10.0,
                    risk_mode="split_total", risk_total_percent=1.0,
                ),
                timeout=RUN_CAP_S,
            )
            print_success(f"orchestrator returned keys: {list(result.keys())}")
        except asyncio.TimeoutError:
            print_info("demo cap reached (grid waiting for fills) — cancelling the grid")
        # endregion
    except Exception as e:
        print_if_error(e, "run_grid_dca_common_sl")
    finally:
        # region CLEANUP
        # ═══════════════════════════════════════════════════════════════
        # 2. CLEANUP
        # ═══════════════════════════════════════════════════════════════
        #    Cancel the grid and close any positions for the symbol.
        #    Best-effort (_cleanup swallows errors), then disconnect.
        print_step(2, "Cleanup")
        await _cleanup(service)
        print_success("grid cancelled / positions cleared")
        await service.disconnect()
        print_success("Disconnected")
        # endregion


if __name__ == "__main__":
    asyncio.run(main())
