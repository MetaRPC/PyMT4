"""
==============================================================================
 FILE: 15_pending_bracket.py - ORCHESTRATOR: Pending order + bracket

  ⚠️  Places a real 0.01 pending order on your DEMO account; cleaned up at the end.

 Strategy: "set your price and wait for the market to come to you" — place a
 limit order at a chosen price with automatic bracket (SL/TP) protection.

     result = await run_pending_bracket(service, strategy, risk, timeout_s=...)

 The limit sits below the market, so in a short demo it won't fill — we use a
 short timeout and then cancel it.

 HOW TO RUN:
   cd examples
   python main.py pending          (or select [15] from the menu)
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
from Strategy.orchestrator.pending_bracket import run_pending_bracket
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
    print("ORCHESTRATOR: Pending bracket")
    print("=" * 78)
    try:
        config = load_settings()
    except Exception as e:
        fatal(e, "Failed to load settings")

    account = await create_and_connect_mt4(config)
    service = MT4Service(account)
    sugar = service.sugar

    # place a BUY LIMIT ~30 pips below the market (won't fill during the demo)
    mid = await sugar.mid_price(SYMBOL)
    entry = round(mid - 0.0030, 5)
    strategy = StrategyPreset(symbol=SYMBOL, use_market=False, entry_price=entry, lots=0.01,
                              magic=781, deviation_pips=3.0, comment="pymt4 pending_bracket")
    risk = RiskPreset(risk_percent=1.0, sl_pips=25, tp_pips=50)

    try:
        print_step(1, "Run the orchestrator (BUY LIMIT + bracket)")
        print_info(f"limit @ {entry} (mid {mid:.5f}), 12s window")
        try:
            result = await run_pending_bracket(service, strategy, risk, timeout_s=12)
            print_success(f"orchestrator returned keys: {list(result.keys())}")
        except Exception as e:
            print_if_error(e, "run_pending_bracket")
    finally:
        print_step(2, "Cleanup")
        await _cleanup(service)
        print_success("pending cancelled / positions cleared")
        await service.disconnect()
        print_success("Disconnected")


if __name__ == "__main__":
    asyncio.run(main())
