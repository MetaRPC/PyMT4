"""
==============================================================================
 FILE: 04_service_demo.py - MID-LEVEL (MT4Service) - ALL METHODS IN ONE TOUR

  ⚠️  Opens/closes a few 0.01 orders on your DEMO account (self-cleaning).

 MT4Service is a typed facade over MT4Account: same method names, constructed
 from an account, plus a .sugar bridge to the high-level MT4Sugar API.
 MT4ServiceTrade adds convenient, keyword-only trade helpers on top.

     service = MT4Service(account)
     trade   = MT4ServiceTrade(service)
     sugar   = service.sugar          # high-level helpers (see 3_sugar)

 This single file walks every region:
   - Account & Symbols     - Quotes
   - Orders (read)         - Trading (raw + helpers)
   - Streaming

 HOW TO RUN:
   cd examples
   python main.py service          (or select [4] from the menu)
==============================================================================
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta

# Need the repo root (for `app` and `package` packages) and 0_common on the path.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "0_common"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "package"))

from demo_helpers import (
    load_settings,
    create_and_connect_mt4,
    print_step,
    print_method,
    print_success,
    print_info,
    print_if_error,
    fatal,
)

from app.MT4Service import MT4Service, MT4ServiceTrade

SYMBOL = "EURUSD"


# =============================================================================
# REGION 1 - ACCOUNT & SYMBOLS
# =============================================================================
async def region_account_symbols(service: MT4Service):
    print_step(1, "Account & Symbols")

    print_method("1.1", "service.account_summary()", "balance / equity / currency")
    try:
        s = await service.account_summary()
        print(f"   {s.account_login} | {s.account_balance:.2f} {s.account_currency} "
              f"| equity {s.account_equity:.2f} | 1:{s.account_leverage}")
    except Exception as e:
        print_if_error(e, "account_summary")

    print_method("1.2", "service.symbols()", "all symbols on the server")
    try:
        data = await service.symbols()  # returns a list (of name-infos or a container)
        names = []
        for x in data:
            if hasattr(x, "symbol_name"):
                names.append(x.symbol_name)
            elif hasattr(x, "SymbolNameInfos"):
                names.extend(i.symbol_name for i in x.SymbolNameInfos)
        print(f"   {len(names)} symbols (e.g. {', '.join(names[:6])} ...)")
    except Exception as e:
        print_if_error(e, "symbols")

    print_method("1.3", "service.symbol_params_many()", f"contract specs for {SYMBOL}")
    try:
        sp = await service.symbol_params_many(SYMBOL)
        if sp.symbol_infos:
            p = sp.symbol_infos[0]
            print(f"   {p.SymbolName}: Digits={p.Digits} Point={p.Point} "
                  f"vol[{p.VolumeMin}..{p.VolumeMax}/{p.VolumeStep}]")
    except Exception as e:
        print_if_error(e, "symbol_params_many")

    print_method("1.4", "service.tick_value_with_size()", "tick value / size")
    try:
        tv = await service.tick_value_with_size(symbols=[SYMBOL, "GBPUSD"])
        for i in tv.infos:
            print(f"   {i.symbolName}: tick_value={i.TradeTickValue} contract={i.TradeContractSize}")
    except Exception as e:
        print_if_error(e, "tick_value_with_size")


# =============================================================================
# REGION 2 - QUOTES
# =============================================================================
async def region_quotes(service: MT4Service):
    print_step(2, "Quotes")

    print_method("2.1", "service.quote()", f"current Bid/Ask for {SYMBOL}")
    try:
        q = await service.quote(SYMBOL)
        print(f"   {q.symbol}: Bid={q.bid:.5f} Ask={q.ask:.5f}")
    except Exception as e:
        print_if_error(e, "quote")

    print_method("2.2", "service.quote_many()", "several symbols at once")
    try:
        qm = await service.quote_many([SYMBOL, "GBPUSD", "USDJPY"])
        for q in qm.quotes:
            print(f"   {q.symbol}: Bid={q.bid:.5f} Ask={q.ask:.5f}")
    except Exception as e:
        print_if_error(e, "quote_many")

    print_method("2.3", "service.quote_history()", "recent H1 candles")
    try:
        hist = await service.quote_history(SYMBOL, timeframe="H1", limit=5)
        bars = list(hist.historical_quotes)
        print(f"   got {len(bars)} H1 bar(s) for {SYMBOL}")
    except Exception as e:
        print_if_error(e, "quote_history")


# =============================================================================
# REGION 3 - ORDERS (READ)
# =============================================================================
async def region_orders_read(service: MT4Service):
    print_step(3, "Orders (read)")

    print_method("3.1", "service.opened_orders()", "currently open orders")
    try:
        oo = await service.opened_orders()
        print(f"   open orders: {len(oo.order_infos)}")
        for o in oo.order_infos[:5]:
            print(f"     #{o.ticket} {o.symbol} type={o.order_type} lots={o.lots} profit={o.profit:.2f}")
    except Exception as e:
        print_if_error(e, "opened_orders")

    print_method("3.2", "service.opened_orders_tickets()", "ticket numbers only")
    try:
        t = await service.opened_orders_tickets()
        print(f"   tickets: {list(t.tickets)}")
    except Exception as e:
        print_if_error(e, "opened_orders_tickets")

    print_method("3.3", "service.orders_history()", "closed orders (last 7 days)")
    try:
        hist = await service.orders_history(
            since=datetime.utcnow() - timedelta(days=7),
            until=datetime.utcnow(),
        )
        print(f"   history entries: {hist.total_count}")
    except Exception as e:
        print_if_error(e, "orders_history")


# =============================================================================
# REGION 4 - TRADING  (MT4ServiceTrade helpers + raw service.order_send)
# =============================================================================
async def region_trading(service: MT4Service):
    print_step(4, "Trading (sends real 0.01 orders, self-cleaning)")
    trade = MT4ServiceTrade(service)
    trade.set_trade_defaults(magic=777, deviation_pips=5, comment="pymt4 service")

    # --- market order via helper ---
    print_method("4.1", "trade.buy_market()", f"open BUY 0.01 {SYMBOL} (returns ticket)")
    ticket = None
    try:
        ticket = await trade.buy_market(symbol=SYMBOL, lots=0.01)
        print_success(f"opened #{ticket}")
    except Exception as e:
        print_if_error(e, "buy_market")

    # --- modify SL/TP via helper ---
    if ticket:
        print_method("4.2", "trade.modify_sl_tp()", "set SL/TP from current quote")
        try:
            q = await service.quote(SYMBOL)
            await trade.modify_sl_tp(ticket=ticket,
                                     sl_price=round(q.bid - 0.0050, 5),
                                     tp_price=round(q.ask + 0.0050, 5))
            print_success("SL/TP set")
        except Exception as e:
            print_if_error(e, "modify_sl_tp")

        print_method("4.3", "trade.close()", "close the market order")
        try:
            await trade.close(ticket=ticket)
            print_success(f"closed #{ticket}")
        except Exception as e:
            print_if_error(e, "close")

    # --- pending order via helper, then delete via raw service ---
    print_method("4.4", "trade.buy_limit() + service.order_close_delete()", "place & delete a pending")
    try:
        q = await service.quote(SYMBOL)
        pend = await trade.buy_limit(symbol=SYMBOL, price=round(q.bid - 0.0100, 5), lots=0.01)
        print_success(f"placed BUY_LIMIT #{pend}")
        await service.order_close_delete(ticket=pend)
        print_success(f"deleted pending #{pend}")
    except Exception as e:
        print_if_error(e, "pending order")

    # --- order_close_by: open BUY + SELL, then close one by the other --------
    print_method("4.5", "service.order_close_by()", "open BUY + SELL, close one by the other")
    try:
        b = await trade.buy_market(symbol=SYMBOL, lots=0.01)
        sll = await trade.sell_market(symbol=SYMBOL, lots=0.01)
        print_success(f"opened BUY #{b} and SELL #{sll}")
        cb = await service.order_close_by(b, sll)
        print_success(f"close_by: close_price={cb.close_price:.5f} profit={cb.profit:.2f}")
    except Exception as e:
        print_if_error(e, "order_close_by")


# =============================================================================
# REGION 5 - STREAMING  (brief sample; full streaming is in 1_lowlevel/03)
# =============================================================================
async def _sample(stream, label, handle, valid=None, max_items=4, timeout=12.0):
    """Consume up to max_items valid items from a service stream, then stop.
    (MT4Service streams don't take a cancellation_event — we just break.)"""
    n = 0

    async def _run():
        nonlocal n
        async for item in stream():
            if valid is not None and not valid(item):
                continue
            handle(item)
            n += 1
            if n >= max_items:
                break

    try:
        await asyncio.wait_for(_run(), timeout=timeout)
    except asyncio.TimeoutError:
        print_info(f"{label}: no data in {timeout:.0f}s")
    await asyncio.sleep(0.3)
    if n:
        print_success(f"{label}: {n} update(s)")


async def region_streaming(service: MT4Service):
    print_step(5, "Streaming (all four streams)")

    print_method("5.1", "service.on_symbol_tick()", "live Bid/Ask ticks")
    await _sample(
        lambda: service.on_symbol_tick(["EURUSD", "GBPUSD", "XAUUSD", "BTCUSD"]),
        "on_symbol_tick",
        lambda td: print(f"   {td.symbol_tick.symbol}: Bid={td.symbol_tick.bid:.5f} Ask={td.symbol_tick.ask:.5f}"),
        valid=lambda td: td.symbol_tick.symbol != "", max_items=4, timeout=15.0,
    )

    print_method("5.2", "service.on_opened_orders_profit()", "periodic P&L + account")
    await _sample(
        lambda: service.on_opened_orders_profit(timer_period_milliseconds=1000),
        "on_opened_orders_profit",
        lambda u: print(f"   equity={u.account_info.equity:.2f} profit={u.account_info.profit:.2f} "
                        f"| open orders: {len(u.opened_orders_with_profit_updated)}"),
        valid=lambda u: u.account_info.equity > 0, max_items=2, timeout=12.0,
    )

    print_method("5.3", "service.on_opened_orders_tickets()", "ticket snapshot")
    await _sample(
        lambda: service.on_opened_orders_tickets(pull_interval_milliseconds=1000),
        "on_opened_orders_tickets",
        lambda t: print(f"   positions={list(t.position_tickets)} pending={list(t.pending_order_tickets)}"),
        valid=lambda t: len(t.position_tickets) + len(t.pending_order_tickets) > 0, max_items=1, timeout=10.0,
    )

    print_method("5.4", "service.on_trade()", "fires on a trade event (we trigger one)")
    trade = MT4ServiceTrade(service)

    async def trigger():
        await asyncio.sleep(2.0)
        try:
            tk = await trade.buy_market(symbol=SYMBOL, lots=0.01)
            await asyncio.sleep(1.0)
            await trade.close(ticket=tk)
        except Exception:
            pass

    tr = asyncio.create_task(trigger())
    await _sample(
        lambda: service.on_trade(), "on_trade",
        lambda ev: print(f"   [TRADE] type={ev.type} new={len(ev.event_data.new_orders)} "
                         f"removed={len(ev.event_data.removed_orders)}"),
        valid=lambda ev: (len(ev.event_data.new_orders) + len(ev.event_data.updated_orders)
                          + len(ev.event_data.removed_orders)) > 0,
        max_items=2, timeout=12.0,
    )
    tr.cancel()


async def main():
    print("\n" + "=" * 78)
    print("MID-LEVEL: MT4Service - full tour")
    print("=" * 78)
    try:
        config = load_settings()
    except Exception as e:
        fatal(e, "Failed to load settings")

    account = await create_and_connect_mt4(config)
    service = MT4Service(account)
    try:
        await region_account_symbols(service)
        await region_quotes(service)
        await region_orders_read(service)
        await region_trading(service)
        await region_streaming(service)
    finally:
        await service.disconnect()
        print_success("Disconnected")


if __name__ == "__main__":
    asyncio.run(main())
