"""
==============================================================================
 FILE: 11_market_one_shot.py - ORCHESTRATOR: Market One-Shot

  ⚠️  Opens a real 0.01 position on your DEMO account, then closes it.

 Strategy: fast market entry with automatic management (SL/TP, optional
 trailing stop and auto break-even). The orchestrator is a plain async
 function that takes an MT4Service + a StrategyPreset + a RiskPreset:

     result = await run_market_one_shot(service, strategy, risk)

 Presets (Strategy/presets/):
   StrategyPreset(symbol, use_market, entry_price, lots, magic, deviation_pips, comment)
   RiskPreset(risk_percent, sl_pips, tp_pips, trailing_pips, be_trigger_pips, be_plus_pips)

 HOW TO RUN:
   cd examples
   python main.py market           (or select [11] from the menu)
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
from Strategy.orchestrator.market_one_shot import run_market_one_shot
from Strategy.presets.strategy import StrategyPreset
from Strategy.presets.risk import RiskPreset

SYMBOL = "EURUSD"


async def main():
    print("\n" + "=" * 78)
    print("ORCHESTRATOR: Market One-Shot")
    print("=" * 78)
    try:
        config = load_settings()
    except Exception as e:
        fatal(e, "Failed to load settings")

    account = await create_and_connect_mt4(config)
    service = MT4Service(account)

    # Configure the strategy (fixed 0.01 lot) and its risk envelope.
    strategy = StrategyPreset(
        symbol=SYMBOL, use_market=True, lots=0.01,
        magic=777, deviation_pips=3.0, comment="pymt4 market_one_shot",
    )
    risk = RiskPreset(
        risk_percent=1.0, sl_pips=30, tp_pips=60,
        trailing_pips=20, be_trigger_pips=20, be_plus_pips=1,
    )

    ticket = None
    try:
        print_step(1, "Run the orchestrator")
        print_info(f"buy_market {strategy.symbol} {strategy.lots} lot, "
                   f"SL {risk.sl_pips} / TP {risk.tp_pips} pips, trailing {risk.trailing_pips}")
        result = await run_market_one_shot(service, strategy, risk)
        ticket = result.get("ticket")
        print_success(f"opened ticket #{ticket}")
        print_info(f"subscriptions: {list(result.get('subscriptions', {}).keys())}  "
                   f"filled: {bool(result.get('filled'))}")

        # let it manage for a few seconds, then tear down
        await asyncio.sleep(3)
    except Exception as e:
        print_if_error(e, "run_market_one_shot")
    finally:
        print_step(2, "Cleanup")
        sugar = service.sugar
        # stop any trailing / auto-be subscriptions this run created
        try:
            for sub in (result.get("subscriptions", {}).values() if ticket else []):
                try:
                    await sugar.unwatch(sub)
                except Exception:
                    pass
        except Exception:
            pass
        if ticket:
            try:
                await sugar.close(ticket)
                print_success(f"closed #{ticket}")
            except Exception as e:
                print_if_error(e, "close")
        await service.disconnect()
        print_success("Disconnected")


if __name__ == "__main__":
    asyncio.run(main())
