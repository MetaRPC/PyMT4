"""
==============================================================================
 FILE: 14_oco_straddle.py - ORCHESTRATOR: OCO Straddle (breakout)

  ⚠️  Places real 0.01 stop orders on your DEMO account; cleaned up at the end.

 Strategy: a bi-directional breakout. Place a BUY STOP above and a SELL STOP
 below the current price; when one triggers, the other is cancelled (OCO).

     result = await run_oco_straddle(service, strategy, risk,
                                     offset_pips=10, timeout_s=...)

 We use a short timeout so the demo doesn't wait for a real breakout.

 HOW TO RUN:
   cd examples
   python main.py oco              (or select [14] from the menu)
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
from Strategy.orchestrator.oco_straddle import run_oco_straddle
from Strategy.presets.strategy import StrategyPreset
from Strategy.presets.risk import RiskPreset

SYMBOL = "EURUSD"


async def _cleanup(service):
    sugar = service.sugar
    for fn in (lambda: sugar.close_all(symbol=SYMBOL), lambda: sugar.cancel_pendings(symbol=SYMBOL)):
        try:
            await fn()
        except Exception:
            pass


async def main():
    print("\n" + "=" * 78)
    print("ORCHESTRATOR: OCO Straddle (breakout)")
    print("=" * 78)
    try:
        config = load_settings()
    except Exception as e:
        fatal(e, "Failed to load settings")

    account = await create_and_connect_mt4(config)
    service = MT4Service(account)

    strategy = StrategyPreset(symbol=SYMBOL, use_market=False, lots=0.01,
                              magic=779, deviation_pips=3.0, comment="pymt4 oco_straddle")
    risk = RiskPreset(risk_percent=1.0, sl_pips=20, tp_pips=40)

    try:
        print_step(1, "Run the orchestrator (BUY STOP + SELL STOP straddle)")
        print_info("offset 10 pips, 12s window (no breakout expected in the demo)")
        try:
            result = await run_oco_straddle(
                service, strategy, risk,
                offset_pips=10.0, timeout_s=12, risk_mode="per_leg_full",
            )
            print_success(f"orchestrator returned keys: {list(result.keys())}")
        except Exception as e:
            print_if_error(e, "run_oco_straddle")
    finally:
        print_step(2, "Cleanup")
        await _cleanup(service)
        print_success("straddle cancelled / positions cleared")
        await service.disconnect()
        print_success("Disconnected")


if __name__ == "__main__":
    asyncio.run(main())
