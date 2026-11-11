"""
═══════════════════════════════════════════════════════════════════════════════
 FILE: 14_oco_straddle.py - ORCHESTRATOR: OCO Straddle (breakout)

 PURPOSE:
   Trade a bi-directional breakout: place a BUY STOP above and a SELL STOP
   below price; when one triggers, the other is cancelled (OCO = One-Cancels-
   the-Other). Catches a move in either direction without picking a side.

 🎯 WHO SHOULD USE THIS:
   • Traders playing breakouts around news / key levels
   • Bots that want "whichever way it breaks" entries with auto-cancel
   • Learning OCO (one-cancels-the-other) order management

 📚 WHAT THIS DEMO COVERS:

   ORCHESTRATOR:
      • run_oco_straddle(service, strategy, risk, offset_pips,
            timeout_s, risk_mode)
        -> places BUY STOP + SELL STOP offset_pips away; cancels the loser
           when one fills (or on timeout); returns a result dict

   INPUTS (Strategy/presets/):
      • StrategyPreset(symbol, use_market=False, lots, magic,
                       deviation_pips, comment)          - straddle base
      • RiskPreset(risk_percent, sl_pips, tp_pips)        - per-leg risk

   STEPS:
      1. RUN     - place the straddle, wait up to timeout_s
                   (no breakout is expected during the short demo window)
      2. CLEANUP - cancel the straddle and close any positions for the symbol

 🔄 API LEVELS:
   ORCHESTRATOR - THIS FILE: multi-step strategy built ON TOP of the stack
   HIGH-LEVEL  (MT4Sugar)   - one-liner trading used under the hood
   MID-LEVEL   (MT4Service) - handed to the orchestrator, which drives it
   LOW-LEVEL   (MT4Account) - raw gRPC client beneath the service

 🚀 HOW TO RUN:
   cd examples
   python main.py oco              (or select [14] from the menu)

 ⚠️  WARNING: this demo PLACES REAL 0.01 STOP ORDERS on your account!
   • Uses the minimum lot size (0.01) per leg
   • Cancels the straddle / closes positions at the end
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
        # region RUN
        # ═══════════════════════════════════════════════════════════════
        # 1. RUN THE ORCHESTRATOR
        # ═══════════════════════════════════════════════════════════════
        #    run_oco_straddle(service, strategy, risk, offset_pips, ...)
        #    Places a REAL BUY STOP + SELL STOP 10 pips out, 12s window;
        #    one fill cancels the other (OCO). No breakout expected in
        #    the demo.
        #    Returns: result dict.
        #    ⚠️  sends REAL stop orders.
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
        # endregion
    finally:
        # region CLEANUP
        # ═══════════════════════════════════════════════════════════════
        # 2. CLEANUP
        # ═══════════════════════════════════════════════════════════════
        #    Cancel the straddle and close any positions for the symbol.
        #    Best-effort (_cleanup swallows errors), then disconnect.
        print_step(2, "Cleanup")
        await _cleanup(service)
        print_success("straddle cancelled / positions cleared")
        await service.disconnect()
        print_success("Disconnected")
        # endregion


if __name__ == "__main__":
    asyncio.run(main())
