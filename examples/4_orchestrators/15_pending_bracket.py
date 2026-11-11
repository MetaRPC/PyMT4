"""
═══════════════════════════════════════════════════════════════════════════════
 FILE: 15_pending_bracket.py - ORCHESTRATOR: Pending order + bracket

 PURPOSE:
   "Set your price and let the market come to you" — place a single limit
   order at a chosen price with automatic bracket (SL/TP) protection attached
   for when it fills.

 🎯 WHO SHOULD USE THIS:
   • Traders who work a specific entry level instead of chasing price
   • Bots that arm a protected pending order and wait
   • Learning pending-entry + bracket management

 📚 WHAT THIS DEMO COVERS:

   ORCHESTRATOR:
      • run_pending_bracket(service, strategy, risk, timeout_s)
        -> places a limit order (from strategy.entry_price) with SL/TP;
           waits up to timeout_s; returns a result dict

   INPUTS (Strategy/presets/):
      • StrategyPreset(symbol, use_market=False, entry_price, lots, magic,
                       deviation_pips, comment)          - the pending entry
      • RiskPreset(risk_percent, sl_pips, tp_pips)        - bracket protection

   STEPS:
      1. RUN     - place the BUY LIMIT ~30 pips below mid, 12s window
                   (it sits off-market and won't fill during the demo)
      2. CLEANUP - cancel the pending and close any positions for the symbol

 🔄 API LEVELS:
   ORCHESTRATOR - THIS FILE: multi-step strategy built ON TOP of the stack
   HIGH-LEVEL  (MT4Sugar)   - one-liner trading used under the hood
   MID-LEVEL   (MT4Service) - handed to the orchestrator, which drives it
   LOW-LEVEL   (MT4Account) - raw gRPC client beneath the service

 🚀 HOW TO RUN:
   cd examples
   python main.py pending          (or select [15] from the menu)

 ⚠️  WARNING: this demo PLACES A REAL 0.01 PENDING ORDER on your account!
   • Uses the minimum lot size (0.01)
   • Cancels the pending / closes positions at the end
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
        # region RUN
        # ═══════════════════════════════════════════════════════════════
        # 1. RUN THE ORCHESTRATOR
        # ═══════════════════════════════════════════════════════════════
        #    run_pending_bracket(service, strategy, risk, timeout_s=12)
        #    Places a REAL BUY LIMIT ~30 pips below mid with a bracket,
        #    then waits 12s. It sits off-market and won't fill in the demo.
        #    Returns: result dict.
        #    ⚠️  sends a REAL pending order.
        print_step(1, "Run the orchestrator (BUY LIMIT + bracket)")
        print_info(f"limit @ {entry} (mid {mid:.5f}), 12s window")
        try:
            result = await run_pending_bracket(service, strategy, risk, timeout_s=12)
            print_success(f"orchestrator returned keys: {list(result.keys())}")
        except Exception as e:
            print_if_error(e, "run_pending_bracket")
        # endregion
    finally:
        # region CLEANUP
        # ═══════════════════════════════════════════════════════════════
        # 2. CLEANUP
        # ═══════════════════════════════════════════════════════════════
        #    Cancel the pending and close any positions for the symbol.
        #    Best-effort (_cleanup swallows errors), then disconnect.
        print_step(2, "Cleanup")
        await _cleanup(service)
        print_success("pending cancelled / positions cleared")
        await service.disconnect()
        print_success("Disconnected")
        # endregion


if __name__ == "__main__":
    asyncio.run(main())
