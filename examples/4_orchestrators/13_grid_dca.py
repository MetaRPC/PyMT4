"""
==============================================================================
 FILE: 13_grid_dca.py - ORCHESTRATOR: Grid DCA with a common Stop Loss

  ⚠️  Places real 0.01 pending orders on your DEMO account; cleaned up at the end.

 Strategy: a Dollar-Cost-Averaging grid of limit orders spaced by `step_pips`,
 managed under one common Stop Loss once legs start filling.

     result = await run_grid_dca_common_sl(
         service, strategy, risk, side="buy",
         steps=3, step_pips=10, risk_mode="split_total", risk_total_percent=1.0)

 The limits sit away from the market, so in a short demo they usually don't
 fill — we cap the run and cancel the grid afterwards.

 HOW TO RUN:
   cd examples
   python main.py grid             (or select [13] from the menu)
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
    except Exception as e:
        print_if_error(e, "run_grid_dca_common_sl")
    finally:
        print_step(2, "Cleanup")
        await _cleanup(service)
        print_success("grid cancelled / positions cleared")
        await service.disconnect()
        print_success("Disconnected")


if __name__ == "__main__":
    asyncio.run(main())
