"""
═══════════════════════════════════════════════════════════════════════════════
 FILE: 17_usercode.py - USER CODE SANDBOX

 PURPOSE:
   A ready-wired playground: the connection is already established, so you
   just drop your own trading logic in and run it.

 🎯 WHO SHOULD USE THIS:
   • Anyone trying a quick idea against a live-connected account
   • Learning the three API levels side by side
   • Prototyping before moving code into a real strategy

 📚 WHAT THIS DEMO COVERS:
   When run_user_code() runs you get three ready objects:
      • account - low-level gRPC client  (MT4Account)
      • service - typed facade           (MT4Service)
      • sugar   - high-level helpers      (MT4Sugar)
   It ships three commented examples (balance / quote / market order) plus a
   harmless default that just prints the current EURUSD quote.
   Everything is async — remember to `await`.

 🔄 API LEVELS:
   LOW-LEVEL  (MT4Account) - account, raw gRPC calls
   MID-LEVEL  (MT4Service) - service, typed facade
   HIGH-LEVEL (MT4Sugar)   - sugar, one-liner helpers

 🚀 HOW TO RUN:
   cd examples
   python main.py usercode         (or select [17] from the menu)

 ⚠️  NOTE: the default run only READS a quote. The commented market-order
   example sends a REAL 0.01 order — uncomment it on a DEMO account only.
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
    print_success, print_info, print_if_error, fatal,
)
from app.MT4Service import MT4Service


# region USER SANDBOX
# ═══════════════════════════════════════════════════════════════════════════════
# 1. USER SANDBOX
# ═══════════════════════════════════════════════════════════════════════════════
async def run_user_code(account, service, sugar):
    """Write your code here. `account`, `service`, `sugar` are ready to use."""

    # ───────────────────────────────────────────────────────────────
    # 1.1  Ready-to-uncomment snippets
    #      Three starters at each API level — uncomment one to try it:
    #        • Example 1: account balance via Sugar
    #        • Example 2: a quote via Service
    #        • Example 3: open + close a market order via Sugar
    #      ⚠️  Example 3 sends a REAL 0.01 order (DEMO only).
    # ───────────────────────────────────────────────────────────────

    # --- a few ready-to-uncomment examples -----------------------------------

    # Example 1: account balance (Sugar)
    # bal = await sugar.balance if hasattr(sugar, "balance") else None
    # print("Balance:", bal)

    # Example 2: a quote (Service)
    # q = await service.quote("EURUSD")
    # print(f"EURUSD: Bid={q.bid:.5f} Ask={q.ask:.5f}")

    # Example 3: open + close a market order (Sugar) — DEMO ONLY
    # ticket = await sugar.buy_market("EURUSD", lots=0.01)
    # print("opened", ticket)
    # await sugar.close(ticket)

    # ───────────────────────────────────────────────────────────────
    # 1.2  YOUR CODE HERE
    #      Replace the default below with your own logic. The default is
    #      read-only: it just prints the latest EURUSD quote.
    # ───────────────────────────────────────────────────────────────

    # =========================================================================
    # YOUR CODE HERE
    # =========================================================================

    # A harmless default so the sandbox shows something on first run:
    q = await service.quote("EURUSD")
    print_info(f"sandbox ready — EURUSD Bid={q.bid:.5f} Ask={q.ask:.5f}")
    print_info("edit examples/5_usercode/17_usercode.py and add your logic")

    # =========================================================================
# endregion


# region ENTRYPOINT
# ═══════════════════════════════════════════════════════════════════════════════
# 2. ENTRYPOINT - connect, hand over the three objects, disconnect
# ═══════════════════════════════════════════════════════════════════════════════
async def main():
    print("\n" + "=" * 78)
    print("USER CODE SANDBOX")
    print("=" * 78)
    try:
        config = load_settings()
    except Exception as e:
        fatal(e, "Failed to load settings")

    account = await create_and_connect_mt4(config)
    service = MT4Service(account)
    sugar = service.sugar
    try:
        await run_user_code(account, service, sugar)
    except Exception as e:
        print_if_error(e, "user code")
    finally:
        await service.disconnect()
        print_success("Disconnected")
# endregion


if __name__ == "__main__":
    asyncio.run(main())
