"""
==============================================================================
 FILE: 07_sugar_trading.py - HIGH-LEVEL (MT4Sugar) - PART 2/3: TRADING

  ⚠️  SENDS REAL 0.01 ORDERS ON YOUR DEMO ACCOUNT. Everything is cleaned up.

 Covers the trading side of MT4Sugar:
   - Market orders (buy/sell_market, place_order)
   - Pending orders (buy/sell_limit, buy/sell_stop) + cancel_pendings
   - Modify SL/TP (by pips and by price)
   - Close variants (close, close_partial, close_by, close_by_tickets,
                     close_by_breakeven, close_all)
   - Trailing & auto (set/unset_trailing_stop, auto_breakeven)
   - Waits (wait_filled, wait_closed)

 HOW TO RUN:
   cd examples
   python main.py sugar07          (or select [7] from the menu)
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


async def _safe_close(sugar, ticket):
    try:
        await sugar.close(ticket)
    except Exception:
        pass


# =============================================================================
# REGION 1 - MARKET ORDERS
# =============================================================================
async def region_market(sugar: MT4Sugar):
    print_step(1, "Market orders")

    print_method("1.1", "sugar.buy_market()", f"BUY {LOT} {SYMBOL} with SL/TP in pips")
    try:
        t = await sugar.buy_market(SYMBOL, lots=LOT, sl_pips=50, tp_pips=80)
        print_success(f"opened #{t}")
        await _safe_close(sugar, t)
        print_success(f"closed #{t}")
    except Exception as e:
        print_if_error(e, "buy_market")

    print_method("1.2", "sugar.sell_market()", f"SELL {LOT} {SYMBOL} (keyword-only)")
    try:
        t = await sugar.sell_market(symbol=SYMBOL, lots=LOT)
        print_success(f"opened #{t}"); await _safe_close(sugar, t); print_success(f"closed #{t}")
    except Exception as e:
        print_if_error(e, "sell_market")

    print_method("1.3", "sugar.place_order()", "generic order builder (market buy)")
    try:
        t = await sugar.place_order(side="buy", order_type="market", symbol=SYMBOL, lots=LOT)
        print_success(f"opened #{t}"); await _safe_close(sugar, t); print_success(f"closed #{t}")
    except Exception as e:
        print_if_error(e, "place_order")


# =============================================================================
# REGION 2 - PENDING ORDERS
# =============================================================================
async def region_pending(sugar: MT4Sugar):
    print_step(2, "Pending orders")
    mid = await sugar.mid_price(SYMBOL)

    specs = [
        ("2.1", "buy_limit",  sugar.buy_limit,  round(mid - 0.0100, 5)),
        ("2.2", "sell_limit", sugar.sell_limit, round(mid + 0.0100, 5)),
        ("2.3", "buy_stop",   sugar.buy_stop,   round(mid + 0.0100, 5)),
        ("2.4", "sell_stop",  sugar.sell_stop,  round(mid - 0.0100, 5)),
    ]
    placed = []
    for num, name, fn, price in specs:
        print_method(num, f"sugar.{name}()", f"place {name} @ {price} (keyword-only)")
        try:
            t = await fn(symbol=SYMBOL, price=price, lots=LOT)
            placed.append(t)
            print_success(f"placed #{t}")
        except Exception as e:
            print_if_error(e, name)

    print_method("2.5", "sugar.cancel_pendings()", "delete all pending orders")
    try:
        await sugar.cancel_pendings(symbol=SYMBOL)
        print_success(f"cancelled {len(placed)} pending(s)")
    except Exception as e:
        print_if_error(e, "cancel_pendings")


# =============================================================================
# REGION 3 - MODIFY SL/TP
# =============================================================================
async def region_modify(sugar: MT4Sugar):
    print_step(3, "Modify SL / TP")
    t = None
    try:
        t = await sugar.buy_market(SYMBOL, lots=LOT)
        print_method("3.1", "sugar.modify_sl_tp_by_pips()", "SL 60 / TP 90 pips")
        await sugar.modify_sl_tp_by_pips(t, sl_pips=60, tp_pips=90)
        print_success("modified by pips")

        print_method("3.2", "sugar.modify_sl_tp_by_price()", "SL/TP at explicit prices")
        q = await sugar.last_quote(SYMBOL)
        await sugar.modify_sl_tp_by_price(t, sl_price=round(q["bid"] - 0.0070, 5),
                                          tp_price=round(q["ask"] + 0.0070, 5))
        print_success("modified by price")
    except Exception as e:
        print_if_error(e, "modify")
    finally:
        if t:
            await _safe_close(sugar, t)
            print_success(f"closed #{t}")


# =============================================================================
# REGION 4 - CLOSE VARIANTS
# =============================================================================
async def region_close(sugar: MT4Sugar):
    print_step(4, "Close variants")

    print_method("4.1", "sugar.close_partial()", "open 0.02, close 0.01, then the rest")
    try:
        t = await sugar.buy_market(SYMBOL, lots=0.02)
        await sugar.close_partial(t, 0.01)
        print_success(f"#{t}: closed 0.01 partial")
        await _safe_close(sugar, t)
        print_success(f"#{t}: closed remainder")
    except Exception as e:
        print_if_error(e, "close_partial")

    print_method("4.2", "sugar.close_by()", "open BUY + SELL, close one by the other")
    try:
        b = await sugar.buy_market(SYMBOL, lots=LOT)
        s = await sugar.sell_market(symbol=SYMBOL, lots=LOT)
        await sugar.close_by(b, s)
        print_success(f"close_by(#{b}, #{s}) done")
    except Exception as e:
        print_if_error(e, "close_by")

    print_method("4.3", "sugar.close_by_tickets()", "same, via close_by_tickets()")
    try:
        b = await sugar.buy_market(SYMBOL, lots=LOT)
        s = await sugar.sell_market(symbol=SYMBOL, lots=LOT)
        await sugar.close_by_tickets(b, s)
        print_success(f"close_by_tickets(#{b}, #{s}) done")
    except Exception as e:
        print_if_error(e, "close_by_tickets")

    print_method("4.4", "sugar.close_by_breakeven()", "close a position once it's at break-even")
    be_t = None
    try:
        be_t = await sugar.buy_market(SYMBOL, lots=LOT)
        await sugar.close_by_breakeven(be_t, plus_pips=0.0)
        print_success(f"close_by_breakeven(#{be_t}) done")
        be_t = None
    except Exception as e:
        print_info(f"close_by_breakeven rejected (expected if not yet at break-even): "
                   f"{type(e).__name__}")
    finally:
        if be_t:
            await _safe_close(sugar, be_t)

    print_method("4.5", "sugar.close_all()", "open 2, then close them all by symbol")
    try:
        await sugar.buy_market(SYMBOL, lots=LOT)
        await sugar.buy_market(SYMBOL, lots=LOT)
        n = await sugar.close_all(symbol=SYMBOL)
        print_success(f"close_all(symbol={SYMBOL}) -> {n}")
    except Exception as e:
        print_if_error(e, "close_all")


# =============================================================================
# REGION 5 - TRAILING & AUTO
# =============================================================================
async def region_trailing(sugar: MT4Sugar):
    print_step(5, "Trailing stop & auto break-even")
    t = None
    try:
        t = await sugar.buy_market(SYMBOL, lots=LOT)

        print_method("5.1", "sugar.set_trailing_stop()", "start a trailing stop (bg task)")
        sub = await sugar.set_trailing_stop(t, distance_pips=20, step_pips=5)
        print_success(f"trailing started -> {sub}")
        await asyncio.sleep(2)

        print_method("5.2", "sugar.unset_trailing_stop()", "stop it")
        await sugar.unset_trailing_stop(sub)
        print_success("trailing stopped")

        print_method("5.3", "sugar.auto_breakeven()", "arm auto break-even")
        sub2 = await sugar.auto_breakeven(t, trigger_pips=20, plus_pips=1)
        print_success(f"auto_breakeven armed -> {sub2}")
        try:
            await sugar.unwatch(sub2)
        except Exception:
            pass
    except Exception as e:
        print_if_error(e, "trailing/auto")
    finally:
        if t:
            await _safe_close(sugar, t)
            print_success(f"closed #{t}")


# =============================================================================
# REGION 6 - WAITS
# =============================================================================
async def region_waits(sugar: MT4Sugar):
    print_step(6, "Waits")
    print_method("6.1", "sugar.wait_filled() / wait_closed()", "open market, wait, close, wait")
    try:
        t = await sugar.buy_market(SYMBOL, lots=LOT)
        filled = await sugar.wait_filled(t, timeout_s=5)
        print_success(f"wait_filled(#{t}) -> {filled}")
        await sugar.close(t)
        closed = await sugar.wait_closed(t, timeout_s=5)
        print_success(f"wait_closed(#{t}) -> {closed}")
    except Exception as e:
        print_if_error(e, "waits")


async def main():
    print("\n" + "=" * 78)
    print("HIGH-LEVEL: MT4Sugar - trading (sends real 0.01 orders)")
    print("=" * 78)
    try:
        config = load_settings()
    except Exception as e:
        fatal(e, "Failed to load settings")

    account = await create_and_connect_mt4(config)
    sugar = MT4Sugar(MT4Service(account))
    sugar.set_defaults(symbol=SYMBOL, magic=777, deviation_pips=5)
    try:
        await region_market(sugar)
        await region_pending(sugar)
        await region_modify(sugar)
        await region_close(sugar)
        await region_trailing(sugar)
        await region_waits(sugar)
    finally:
        await sugar.disconnect()
        print_success("Disconnected")


if __name__ == "__main__":
    asyncio.run(main())
