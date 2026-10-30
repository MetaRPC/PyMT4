"""
==============================================================================
 FILE: 02_trading_operations.py - LOW-LEVEL TRADING (MT4Account)

  ⚠️  SENDS REAL ORDERS ON YOUR DEMO ACCOUNT.
      Use a demo account only. Everything opened here is closed again at the end.

 Shows the trading side of the low-level gRPC client MT4Account:
   - order_send()          open a market or pending order
   - order_modify()        change SL / TP (or price/expiration for pendings)
   - order_close_delete()  close a market order / delete a pending order
   - order_close_by()      close a position by an opposite one (hedging)

 Order operation types (trading_helper_pb2.OrderSendOperationType):
   OC_OP_BUY, OC_OP_SELL, OC_OP_BUYLIMIT, OC_OP_SELLLIMIT, OC_OP_BUYSTOP, OC_OP_SELLSTOP

 HOW TO RUN:
   cd examples
   python main.py trading          (or select [2] from the menu)
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
    print_step,
    print_method,
    print_success,
    print_warning,
    print_if_error,
    fatal,
)

import MetaRpcMT4.mt4_term_api_trading_helper_pb2 as trading_pb2

OP = trading_pb2.OrderSendOperationType
SYMBOL = "EURUSD"
VOLUME = 0.01


async def run(account):
    # ---- 1. Open a market BUY ----------------------------------------------
    print_method("1", "order_send()", f"open a market BUY {VOLUME} {SYMBOL}")
    ticket = None
    try:
        res = await account.order_send(
            symbol=SYMBOL,
            operation_type=OP.OC_OP_BUY,
            volume=VOLUME,
            comment="pymt4 demo",
        )
        ticket = res.ticket
        fill = res.price
        print_success(f"opened #{ticket}  filled @ {fill:.5f}  vol={res.volume}")
    except Exception as e:
        print_if_error(e, "order_send")
        return

    # ---- 2. Modify its SL / TP ---------------------------------------------
    print_method("2", "order_modify()", "set Stop Loss and Take Profit")
    try:
        sl = round(fill - 0.0050, 5)   # 50 pips below for a BUY
        tp = round(fill + 0.0050, 5)   # 50 pips above
        mod = await account.order_modify(
            order_ticket=ticket,
            new_stop_loss=sl,
            new_take_profit=tp,
        )
        print_success(f"modified #{ticket}: SL={sl} TP={tp}  (ok={mod.order_was_modified})")
    except Exception as e:
        print_if_error(e, "order_modify")

    # ---- 3. Close it --------------------------------------------------------
    print_method("3", "order_close_delete()", "close the market order")
    try:
        cl = await account.order_close_delete(order_ticket=ticket)
        print_success(f"closed #{ticket}  (mode={cl.mode})")
    except Exception as e:
        print_if_error(e, "order_close_delete")

    # ---- 4. order_close_by (close a position by an opposite one) ------------
    print_method("4", "order_close_by()", "open BUY + SELL, then close one by the other")
    buy_t = sell_t = None
    try:
        buy = await account.order_send(symbol=SYMBOL, operation_type=OP.OC_OP_BUY,
                                        volume=VOLUME, comment="pymt4 close_by buy")
        buy_t = buy.ticket
        sell = await account.order_send(symbol=SYMBOL, operation_type=OP.OC_OP_SELL,
                                         volume=VOLUME, comment="pymt4 close_by sell")
        sell_t = sell.ticket
        print_success(f"opened BUY #{buy_t} and SELL #{sell_t}")

        cb = await account.order_close_by(
            ticket_to_close=buy_t,
            opposite_ticket_closing_by=sell_t,
        )
        print_success(f"close_by done: close_price={cb.close_price:.5f} profit={cb.profit:.2f}")
        buy_t = sell_t = None  # both consumed by close_by
    except Exception as e:
        print_warning(f"order_close_by not available on this account: {e}")
        # cleanup: close whatever is still open
        for t in (buy_t, sell_t):
            if t:
                try:
                    await account.order_close_delete(order_ticket=t)
                    print_success(f"cleaned up #{t}")
                except Exception as ce:
                    print_if_error(ce, f"cleanup #{t}")


async def main():
    print("\n" + "=" * 78)
    print("LOW-LEVEL: TRADING OPERATIONS  (sends real orders on your demo)")
    print("=" * 78)
    try:
        config = load_settings()
    except Exception as e:
        fatal(e, "Failed to load settings")

    account = await create_and_connect_mt4(config)
    try:
        await run(account)
    finally:
        await account.disconnect()
        print_success("Disconnected")


if __name__ == "__main__":
    asyncio.run(main())
