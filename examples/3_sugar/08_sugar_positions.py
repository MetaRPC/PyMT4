"""
==============================================================================
 FILE: 08_sugar_positions.py - HIGH-LEVEL (MT4Sugar) - PART 3/3: POSITIONS & STREAMS

  ⚠️  Opens ONE small test order so the queries/streams have data; closes it.

 Covers the position/query side and the callback-based streams of MT4Sugar:
   - Queries:  exposure_summary, positions_value, orders_for_symbol,
               find_orders, diag_snapshot
   - Streams:  watch_ticks / watch_profit / watch_tickets /
               watch_opened_orders / watch_trades  (+ unwatch)

 Unlike the MT4Account/MT4Service streams (async generators), MT4Sugar streams
 take a callback and return a subscription id you later pass to unwatch().

 HOW TO RUN:
   cd examples
   python main.py sugar08          (or select [8] from the menu)
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
    print_step, print_method, print_success, print_info, print_if_error, fatal,
)
from app.MT4Service import MT4Service
from app.MT4Sugar import MT4Sugar

SYMBOL = "EURUSD"
LOT = 0.01


# =============================================================================
# REGION 1 - QUERIES
# =============================================================================
async def region_queries(sugar: MT4Sugar):
    print_step(1, "Queries (positions, exposure, diagnostics)")

    print_method("1.1", "sugar.exposure_summary()", "net exposure, grouped by symbol")
    try:
        exp = await sugar.exposure_summary(by_symbol=True)
        print(f"   {exp}")
    except Exception as e:
        print_if_error(e, "exposure_summary")

    print_method("1.2", "sugar.positions_value()", "total value of open positions")
    try:
        print(f"   positions_value(all) = {await sugar.positions_value()}")
    except Exception as e:
        print_if_error(e, "positions_value")

    print_method("1.3", "sugar.orders_for_symbol()", f"orders on {SYMBOL}")
    try:
        orders = await sugar.orders_for_symbol(SYMBOL)
        print(f"   {len(orders)} order(s) on {SYMBOL}")
    except Exception as e:
        print_if_error(e, "orders_for_symbol")

    print_method("1.4", "sugar.find_orders()", "filter orders (open market orders)")
    try:
        found = await sugar.find_orders(state="open")
        print(f"   found {len(found)} open order(s)")
    except Exception as e:
        print_if_error(e, "find_orders")

    print_method("1.5", "sugar.diag_snapshot()", "one-shot diagnostics snapshot")
    try:
        snap = await sugar.diag_snapshot()
        keys = list(snap.keys()) if isinstance(snap, dict) else type(snap).__name__
        print(f"   snapshot keys: {keys}")
    except Exception as e:
        print_if_error(e, "diag_snapshot")


# =============================================================================
# REGION 2 - WATCH STREAMS (callback-based)
# =============================================================================
async def _watch(sugar, start, label, seconds=8.0):
    """Start a callback watcher, collect for `seconds`, then unwatch."""
    hits = {"n": 0}

    def cb(*args):
        hits["n"] += 1

    try:
        sub = await start(cb)
    except Exception as e:
        print_if_error(e, label)
        return
    print_success(f"{label} subscribed -> {sub}")
    await asyncio.sleep(seconds)
    try:
        await sugar.unwatch(sub)
    except Exception as e:
        print_if_error(e, f"unwatch {label}")
    print_success(f"{label}: {hits['n']} callback(s), unwatched")


async def region_streams(sugar: MT4Sugar):
    print_step(2, "Watch streams (callbacks + unwatch)")

    print_method("2.1", "sugar.watch_ticks()", "callback per tick")
    await _watch(sugar, lambda cb: sugar.watch_ticks(SYMBOL, cb, throttle_ms=200), "watch_ticks", 8.0)

    print_method("2.2", "sugar.watch_profit()", "callback with periodic P&L")
    await _watch(sugar, lambda cb: sugar.watch_profit(cb, timer_period_ms=1000), "watch_profit", 6.0)

    print_method("2.3", "sugar.watch_tickets()", "callback with ticket snapshots")
    await _watch(sugar, lambda cb: sugar.watch_tickets(cb, pull_interval_ms=1000), "watch_tickets", 6.0)

    print_method("2.4", "sugar.watch_opened_orders()", "callback on opened-orders changes")
    await _watch(sugar, lambda cb: sugar.watch_opened_orders(cb), "watch_opened_orders", 5.0)

    print_method("2.5", "sugar.watch_trades()", "callback on trade events (we trigger one)")

    async def trigger():
        await asyncio.sleep(2.0)
        try:
            t = await sugar.buy_market(SYMBOL, lots=LOT)
            await asyncio.sleep(1.0)
            await sugar.close(t)
        except Exception:
            pass

    tr = asyncio.create_task(trigger())
    await _watch(sugar, lambda cb: sugar.watch_trades(cb), "watch_trades", 8.0)
    tr.cancel()


async def main():
    print("\n" + "=" * 78)
    print("HIGH-LEVEL: MT4Sugar - positions & streams")
    print("=" * 78)
    try:
        config = load_settings()
    except Exception as e:
        fatal(e, "Failed to load settings")

    account = await create_and_connect_mt4(config)
    sugar = MT4Sugar(MT4Service(account))
    sugar.set_defaults(symbol=SYMBOL, magic=777)

    test_ticket = None
    try:
        # open one test order so queries / profit / tickets streams have data
        try:
            test_ticket = await sugar.buy_market(SYMBOL, lots=LOT)
            print_success(f"test order opened: #{test_ticket}")
        except Exception as e:
            print_if_error(e, "test order")

        await region_queries(sugar)
        await region_streams(sugar)
    finally:
        if test_ticket:
            try:
                await sugar.close(test_ticket)
            except Exception:
                pass
        await sugar.disconnect()
        print_success("Disconnected")


if __name__ == "__main__":
    asyncio.run(main())
