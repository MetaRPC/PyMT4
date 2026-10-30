"""
==============================================================================
 FILE: 17_usercode.py - YOUR SANDBOX

 Connection is already wired up — you just add your trading logic.
 When this runs you get three ready objects:

     account   low-level gRPC client   (MT4Account)
     service   typed facade            (MT4Service)
     sugar     high-level helpers      (MT4Sugar)

 Uncomment an example below, or write your own between the markers.
 Everything is async — remember to `await`.

 HOW TO RUN:
   cd examples
   python main.py usercode         (or select [17] from the menu)
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
    print_success, print_info, print_if_error, fatal,
)
from app.MT4Service import MT4Service


async def run_user_code(account, service, sugar):
    """Write your code here. `account`, `service`, `sugar` are ready to use."""

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

    # =========================================================================
    # YOUR CODE HERE
    # =========================================================================

    # A harmless default so the sandbox shows something on first run:
    q = await service.quote("EURUSD")
    print_info(f"sandbox ready — EURUSD Bid={q.bid:.5f} Ask={q.ask:.5f}")
    print_info("edit examples/5_usercode/17_usercode.py and add your logic")

    # =========================================================================


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


if __name__ == "__main__":
    asyncio.run(main())
