"""
═══════════════════════════════════════════════════════════════════════════════
 FILE: 01_general_operations.py - LOW-LEVEL READ OPERATIONS (MT4Account)

 PURPOSE:
   Reference tour of the READ-ONLY side of the low-level gRPC client
   MT4Account: account, symbol, quote, order and analytics queries.
   No trades are sent here — safe to run on any account.

 🎯 WHO SHOULD USE THIS:
   • Anyone inspecting what the raw MT4Account API returns
   • Building dashboards / reporting on account and market data
   • Learning the low-level calls before wrapping them

 📚 WHAT THIS DEMO COVERS (5 regions):

   REGION 1: ACCOUNT INFO (1 method)
      • account_summary()            - balance / equity / currency / leverage

   REGION 2: SYMBOLS & QUOTES (5 methods)
      • symbols()                    - all symbols on the server
      • quote()                      - current Bid/Ask for one symbol
      • quote_many()                 - Bid/Ask for several symbols at once
      • symbol_params_many()         - full contract specs for a symbol
      • tick_value_with_size()       - tick value / size (position sizing)

   REGION 3: ORDERS & HISTORY (3 methods)
      • opened_orders()              - currently open orders / positions
      • opened_orders_tickets()      - just the ticket numbers (lightweight)
      • orders_history()             - closed orders over a time range

   REGION 4: SERVER & ANALYTICS (5 methods)
      • server_timezone()            - trade-server timezone / UTC offset
      • trade_stats()                - aggregated trade statistics
      • equity_history()             - equity-curve points
      • trade_unrealized_pl()        - per-open-order unrealized P/L extrema
      • trade_stats_equity_history() - stats + equity + trades in one call

   REGION 5: MARKET WATCH (1 method)
      • symbol_select()              - add / remove a symbol from Market Watch

 🔄 API LEVELS:
   LOW-LEVEL   (MT4Account) - THIS FILE: direct gRPC/protobuf calls
   MID-LEVEL   (MT4Service) - native Python types, less boilerplate
   HIGH-LEVEL  (MT4Sugar)   - one-liner helpers with smart defaults

 🚀 HOW TO RUN:
   cd examples
   python main.py general         (or select [1] from the menu)

 ℹ️  SAFE: this demo is read-only — it never sends an order.
═══════════════════════════════════════════════════════════════════════════════
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta

# Make examples/0_common importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "0_common"))

from demo_helpers import (
    load_settings,
    create_and_connect_mt4,
    print_step,
    print_method,
    print_success,
    print_if_error,
    fatal,
)


async def run(account):
    """Run the read-only tour against an already-connected MT4Account."""

    # region ACCOUNT INFO
    # ═══════════════════════════════════════════════════════════════════════
    # ACCOUNT INFO
    # ═══════════════════════════════════════════════════════════════════════

    # ───────────────────────────────────────────────────────────────
    # 1  account.account_summary()
    #      Full account snapshot in a single call.
    #      Returns: login, company, balance, equity, credit, leverage.
    # ───────────────────────────────────────────────────────────────
    print_method("1", "account_summary()", "account balance, equity, currency")
    try:
        s = await account.account_summary()
        print(f"   Login:    {s.account_login}  ({s.account_company_name})")
        print(f"   Balance:  {s.account_balance:.2f} {s.account_currency}")
        print(f"   Equity:   {s.account_equity:.2f}   Credit: {s.account_credit:.2f}")
        print(f"   Leverage: 1:{s.account_leverage}")
    except Exception as e:
        print_if_error(e, "account_summary")
    # endregion

    # region SYMBOLS & QUOTES
    # ═══════════════════════════════════════════════════════════════════════
    # SYMBOLS & QUOTES
    # ═══════════════════════════════════════════════════════════════════════

    # ───────────────────────────────────────────────────────────────
    # 2  account.symbols()
    #      List every symbol the server exposes.
    #      Returns: SymbolNameInfos (names).
    # ───────────────────────────────────────────────────────────────
    print_method("2", "symbols()", "all symbols available on the server")
    try:
        data = await account.symbols()
        names = [i.symbol_name for i in data.SymbolNameInfos]
        print(f"   Total symbols: {len(names)}")
        print(f"   First 10: {', '.join(names[:10])}")
    except Exception as e:
        print_if_error(e, "symbols")

    # ───────────────────────────────────────────────────────────────
    # 3  account.quote(symbol)
    #      Current Bid/Ask (+ High/Low) for one symbol.
    #      Returns: a single quote object.
    # ───────────────────────────────────────────────────────────────
    symbol = "EURUSD"
    print_method("3", "quote()", f"current Bid/Ask for {symbol}")
    try:
        q = await account.quote(symbol)
        print(f"   {q.symbol}: Bid={q.bid:.5f}  Ask={q.ask:.5f}  (H={q.high:.5f} L={q.low:.5f})")
    except Exception as e:
        print_if_error(e, "quote")

    # ───────────────────────────────────────────────────────────────
    # 4  account.quote_many([symbols])
    #      Bid/Ask for several symbols in one round-trip.
    #      Returns: quotes (list).
    # ───────────────────────────────────────────────────────────────
    print_method("4", "quote_many()", "Bid/Ask for several symbols at once")
    try:
        qm = await account.quote_many(["EURUSD", "GBPUSD", "USDJPY"])
        for q in qm.quotes:
            print(f"   {q.symbol}: Bid={q.bid:.5f}  Ask={q.ask:.5f}")
    except Exception as e:
        print_if_error(e, "quote_many")

    # ───────────────────────────────────────────────────────────────
    # 5  account.symbol_params_many(symbol_name=)
    #      Full contract specs: digits, point, spread, volume limits.
    #      Returns: symbol_infos (list).
    # ───────────────────────────────────────────────────────────────
    print_method("5", "symbol_params_many()", f"contract specs for {symbol}")
    try:
        sp = await account.symbol_params_many(symbol_name=symbol)
        if sp.symbol_infos:
            p = sp.symbol_infos[0]
            print(f"   {p.SymbolName}: Digits={p.Digits} Point={p.Point} Spread={p.SpreadFloat}")
            print(f"   Volume: min={p.VolumeMin} max={p.VolumeMax} step={p.VolumeStep}")
            print(f"   Contract size={p.TradeContractSize}  "
                  f"Currencies {p.CurrencyBase}/{p.CurrencyProfit}/{p.CurrencyMargin}")
    except Exception as e:
        print_if_error(e, "symbol_params_many")

    # ───────────────────────────────────────────────────────────────
    # 6  account.tick_value_with_size([symbols])
    #      Tick value / size / contract size for position sizing.
    #      Returns: infos (list, one per symbol).
    # ───────────────────────────────────────────────────────────────
    print_method("6", "tick_value_with_size()", "tick value/size for position sizing")
    try:
        tv = await account.tick_value_with_size(["EURUSD", "GBPUSD"])
        for i in tv.infos:
            print(f"   {i.symbolName}: tick_value={i.TradeTickValue} "
                  f"tick_size={i.TradeTickSize} contract={i.TradeContractSize}")
    except Exception as e:
        print_if_error(e, "tick_value_with_size")
    # endregion

    # region ORDERS & HISTORY
    # ═══════════════════════════════════════════════════════════════════════
    # ORDERS & HISTORY
    # ═══════════════════════════════════════════════════════════════════════

    # ───────────────────────────────────────────────────────────────
    # 7  account.opened_orders()
    #      Currently open orders / positions with full detail.
    #      Returns: order_infos (list).
    # ───────────────────────────────────────────────────────────────
    print_method("7", "opened_orders()", "currently open orders / positions")
    try:
        oo = await account.opened_orders()
        orders = oo.order_infos
        print(f"   Open orders: {len(orders)}")
        for o in orders[:5]:
            print(f"     #{o.ticket} {o.symbol} type={o.order_type} lots={o.lots} "
                  f"open={o.open_price:.5f} profit={o.profit:.2f}")
    except Exception as e:
        print_if_error(e, "opened_orders")

    # ───────────────────────────────────────────────────────────────
    # 8  account.opened_orders_tickets()
    #      Lightweight: only the open ticket numbers.
    #      Returns: tickets (list of ints).
    # ───────────────────────────────────────────────────────────────
    print_method("8", "opened_orders_tickets()", "just the ticket numbers")
    try:
        t = await account.opened_orders_tickets()
        print(f"   Tickets: {list(t.tickets)}")
    except Exception as e:
        print_if_error(e, "opened_orders_tickets")

    # ───────────────────────────────────────────────────────────────
    # 9  account.orders_history(from_time=, to_time=)
    #      Closed orders over a time range (here: last 7 days).
    #      Returns: orders_info (list) + total_count.
    # ───────────────────────────────────────────────────────────────
    print_method("9", "orders_history()", "closed orders over the last 7 days")
    try:
        hist = await account.orders_history(
            from_time=datetime.utcnow() - timedelta(days=7),
            to_time=datetime.utcnow(),
        )
        print(f"   History entries: {hist.total_count}")
        for o in hist.orders_info[:5]:
            print(f"     #{o.ticket} {o.symbol} lots={o.lots} "
                  f"close={o.close_price:.5f} profit={o.profit:.2f}")
    except Exception as e:
        print_if_error(e, "orders_history")
    # endregion

    # region SERVER & ANALYTICS
    # ═══════════════════════════════════════════════════════════════════════
    # SERVER & ANALYTICS
    # ═══════════════════════════════════════════════════════════════════════

    # ───────────────────────────────────────────────────────────────
    # 10  account.server_timezone()
    #      Trade-server timezone and UTC offset.
    #      Returns: server name + utc_offset_seconds.
    # ───────────────────────────────────────────────────────────────
    print_method("10", "server_timezone()", "trade-server timezone / UTC offset")
    try:
        tz = await account.server_timezone()
        print(f"   Server: {tz.server}  UTC offset: {tz.utc_offset_seconds}s")
    except Exception as e:
        print_if_error(e, "server_timezone")

    # ───────────────────────────────────────────────────────────────
    # 11  account.trade_stats()
    #      Aggregated trade statistics (profit factor, growth, markets).
    #      Returns: stats object.
    # ───────────────────────────────────────────────────────────────
    print_method("11", "trade_stats()", "aggregated trade statistics")
    try:
        st = await account.trade_stats()
        print(f"   profit_factor={st.profit_factor:.2f} growth%={st.growth_percent:.2f} "
              f"markets={len(st.markets)}")
    except Exception as e:
        print_if_error(e, "trade_stats")

    # ───────────────────────────────────────────────────────────────
    # 12  account.equity_history()
    #      Points of the account equity curve.
    #      Returns: points (list).
    # ───────────────────────────────────────────────────────────────
    print_method("12", "equity_history()", "equity-curve points")
    try:
        eq = await account.equity_history()
        print(f"   equity points: {len(eq.points)}")
    except Exception as e:
        print_if_error(e, "equity_history")

    # ───────────────────────────────────────────────────────────────
    # 13  account.trade_unrealized_pl()
    #      Per-open-order unrealized P/L extrema.
    #      Returns: extrema (list).
    # ───────────────────────────────────────────────────────────────
    print_method("13", "trade_unrealized_pl()", "per-open-order unrealized P/L extrema")
    try:
        upl = await account.trade_unrealized_pl()
        print(f"   extrema entries: {len(upl.extrema)}")
    except Exception as e:
        print_if_error(e, "trade_unrealized_pl")

    # ───────────────────────────────────────────────────────────────
    # 14  account.trade_stats_equity_history()
    #      Stats + equity points + trades, all in one call.
    #      Returns: charts / trades / open_trades.
    # ───────────────────────────────────────────────────────────────
    print_method("14", "trade_stats_equity_history()", "stats + equity points + trades in one call")
    try:
        sc = await account.trade_stats_equity_history()
        print(f"   charts={len(sc.charts)} trades={len(sc.trades)} open_trades={len(sc.open_trades)}")
    except Exception as e:
        print_if_error(e, "trade_stats_equity_history")
    # endregion

    # region MARKET WATCH
    # ═══════════════════════════════════════════════════════════════════════
    # MARKET WATCH
    # ═══════════════════════════════════════════════════════════════════════

    # ───────────────────────────────────────────────────────────────
    # 15  account.symbol_select(symbol, select)
    #      Add (or remove) a symbol from Market Watch.
    #      Returns: success flag.
    # ───────────────────────────────────────────────────────────────
    print_method("15", "symbol_select()", f"add {symbol} to Market Watch")
    try:
        sel = await account.symbol_select(symbol, True)
        print(f"   success: {sel.success}")
    except Exception as e:
        print_if_error(e, "symbol_select")
    # endregion


async def main():
    print("\n" + "=" * 78)
    print("LOW-LEVEL: GENERAL (READ-ONLY) OPERATIONS")
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
