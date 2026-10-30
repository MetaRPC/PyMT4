"""
==============================================================================
 FILE: 03_streaming_methods.py - LOW-LEVEL STREAMING (MT4Account)

  ⚠️  Opens ONE small test order (0.01) so the P&L / tickets streams have
      something to show, then closes it at the end. Demo accounts only.

 Shows the real-time streams of the low-level gRPC client MT4Account.
 Every stream is an async generator consumed with `async for`; pass a
 cancellation_event (and/or wrap in asyncio.wait_for) to stop it cleanly.

   - on_symbol_tick()           live Bid/Ask ticks for symbols
   - on_opened_orders_profit()  periodic P&L of open orders + account snapshot
   - on_opened_orders_tickets() periodic list of open position / pending tickets
   - on_trade()                 fires on trade events (open/modify/close)

 HOW TO RUN:
   cd examples
   python main.py streaming        (or select [3] from the menu)
==============================================================================
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "0_common"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "package"))

from demo_helpers import (
    load_settings,
    create_and_connect_mt4,
    print_method,
    print_success,
    print_info,
    print_if_error,
    fatal,
)

import MetaRpcMT4.mt4_term_api_trading_helper_pb2 as trading_pb2

OP = trading_pb2.OrderSendOperationType


async def sample(stream, label, handle, valid=None, max_items=5, timeout=12.0):
    """Consume from `stream` until `max_items` valid items (or `timeout`).
    `valid(item)` filters out empty handshake frames; `handle(item)` prints."""
    cancel = asyncio.Event()
    count = 0

    async def _run():
        nonlocal count
        async for item in stream(cancel):
            if valid is not None and not valid(item):
                continue  # skip empty/handshake frame
            handle(item)
            count += 1
            if count >= max_items:
                break

    try:
        await asyncio.wait_for(_run(), timeout=timeout)
    except asyncio.TimeoutError:
        print_info(f"{label}: no data in {timeout:.0f}s — moving on")
    finally:
        cancel.set()
        await asyncio.sleep(0.3)
    if count:
        print_success(f"{label}: {count} update(s)")


async def run(account):
    # ---- 1. Symbol ticks ----------------------------------------------------
    print_method("1", "on_symbol_tick()", "live Bid/Ask ticks")

    await sample(
        lambda c: account.on_symbol_tick(symbols=["EURUSD", "GBPUSD", "XAUUSD", "BTCUSD"], cancellation_event=c),
        "on_symbol_tick",
        handle=lambda td: print(f"     {td.symbol_tick.symbol}: "
                                f"Bid={td.symbol_tick.bid:.5f} Ask={td.symbol_tick.ask:.5f}"),
        valid=lambda td: td.symbol_tick.symbol != "",
        max_items=6, timeout=15.0,
    )

    # ---- 2. Open orders P&L -------------------------------------------------
    print_method("2", "on_opened_orders_profit()", "periodic P&L + account snapshot")

    def on_profit(upd):
        a = upd.account_info
        orders = list(upd.opened_orders_with_profit_updated)
        print(f"     Account: equity={a.equity:.2f} profit={a.profit:.2f} "
              f"free_margin={a.free_margin:.2f} | open orders: {len(orders)}")
        for o in orders[:5]:
            print(f"       #{o.ticket} {o.symbol} lots={o.lots} profit={o.order_profit:.2f}")

    await sample(
        lambda c: account.on_opened_orders_profit(timer_period_milliseconds=1000, cancellation_event=c),
        "on_opened_orders_profit", on_profit,
        valid=lambda upd: upd.account_info.equity > 0,
        max_items=2, timeout=12.0,
    )

    # ---- 3. Open order tickets ---------------------------------------------
    print_method("3", "on_opened_orders_tickets()", "periodic ticket snapshot")

    await sample(
        lambda c: account.on_opened_orders_tickets(pull_interval_milliseconds=1000, cancellation_event=c),
        "on_opened_orders_tickets",
        handle=lambda t: print(f"     positions={list(t.position_tickets)}  "
                               f"pending={list(t.pending_order_tickets)}"),
        valid=lambda t: len(t.position_tickets) > 0 or len(t.pending_order_tickets) > 0,
        max_items=1, timeout=10.0,
    )

    # ---- 4. Trade events ----------------------------------------------------
    print_method("4", "on_trade()", "fires when an order opens / changes / closes")
    print_info("Firing a quick 0.01 trade in parallel so an event arrives...")

    def on_trade_evt(ev):
        e = ev.event_data
        print(f"     [TRADE] type={ev.type} new={len(e.new_orders)} "
              f"updated={len(e.updated_orders)} removed={len(e.removed_orders)}")

    async def trigger_trade():
        # give on_trade() a moment to subscribe, then open+close a tiny order
        await asyncio.sleep(2.0)
        try:
            r = await account.order_send(symbol="EURUSD", operation_type=OP.OC_OP_BUY,
                                         volume=0.01, comment="pymt4 on_trade demo")
            await asyncio.sleep(1.0)
            await account.order_close_delete(order_ticket=r.ticket)
        except Exception:
            pass

    trigger = asyncio.create_task(trigger_trade())
    await sample(
        lambda c: account.on_trade(cancellation_event=c),
        "on_trade", on_trade_evt,
        valid=lambda ev: (len(ev.event_data.new_orders) + len(ev.event_data.updated_orders)
                          + len(ev.event_data.removed_orders)) > 0,
        max_items=2, timeout=12.0,
    )
    trigger.cancel()


async def main():
    print("\n" + "=" * 78)
    print("LOW-LEVEL: STREAMING METHODS  (opens/closes one 0.01 test order)")
    print("=" * 78)
    try:
        config = load_settings()
    except Exception as e:
        fatal(e, "Failed to load settings")

    account = await create_and_connect_mt4(config)
    test_ticket = None
    try:
        # Open a small test order so the P&L / tickets / trade streams have data.
        try:
            r = await account.order_send(symbol=config["test_symbol"],
                                         operation_type=OP.OC_OP_BUY, volume=0.01,
                                         comment="pymt4 stream demo")
            test_ticket = r.ticket
            print_success(f"test order opened: #{test_ticket}")
        except Exception as e:
            print_if_error(e, "could not open test order (streams may be quiet)")

        await run(account)
    finally:
        if test_ticket:
            try:
                await account.order_close_delete(order_ticket=test_ticket)
            except Exception:
                pass
        await account.disconnect()
        print_success("Disconnected")


if __name__ == "__main__":
    asyncio.run(main())
