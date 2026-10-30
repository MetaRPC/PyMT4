"""
==============================================================================
 FILE: 01_general_operations.py - LOW-LEVEL READ OPERATIONS (MT4Account)

 Shows the read-only side of the low-level gRPC client MT4Account:
   - account_summary()        account balance / equity / currency / leverage
   - symbols()                list of all symbols on the server
   - quote() / quote_many()   current Bid/Ask for one or several symbols
   - symbol_params_many()     full contract specs for a symbol
   - tick_value_with_size()   tick value / size (for position sizing)
   - opened_orders()          currently open orders/positions
   - opened_orders_tickets()  just the ticket numbers (lightweight)
   - orders_history()         closed orders over a time range

 No trades are sent here - everything is read-only and safe on any account.

 HOW TO RUN:
   cd examples
   python main.py general         (or select [1] from the menu)
==============================================================================
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

    # ---- 1. Account summary -------------------------------------------------
    print_method("1", "account_summary()", "account balance, equity, currency")
    try:
        s = await account.account_summary()
        print(f"   Login:    {s.account_login}  ({s.account_company_name})")
        print(f"   Balance:  {s.account_balance:.2f} {s.account_currency}")
        print(f"   Equity:   {s.account_equity:.2f}   Credit: {s.account_credit:.2f}")
        print(f"   Leverage: 1:{s.account_leverage}")
    except Exception as e:
        print_if_error(e, "account_summary")

    # ---- 2. Symbols ---------------------------------------------------------
    print_method("2", "symbols()", "all symbols available on the server")
    try:
        data = await account.symbols()
        names = [i.symbol_name for i in data.SymbolNameInfos]
        print(f"   Total symbols: {len(names)}")
        print(f"   First 10: {', '.join(names[:10])}")
    except Exception as e:
        print_if_error(e, "symbols")

    # ---- 3. Single quote ----------------------------------------------------
    symbol = "EURUSD"
    print_method("3", "quote()", f"current Bid/Ask for {symbol}")
    try:
        q = await account.quote(symbol)
        print(f"   {q.symbol}: Bid={q.bid:.5f}  Ask={q.ask:.5f}  (H={q.high:.5f} L={q.low:.5f})")
    except Exception as e:
        print_if_error(e, "quote")

    # ---- 4. Many quotes -----------------------------------------------------
    print_method("4", "quote_many()", "Bid/Ask for several symbols at once")
    try:
        qm = await account.quote_many(["EURUSD", "GBPUSD", "USDJPY"])
        for q in qm.quotes:
            print(f"   {q.symbol}: Bid={q.bid:.5f}  Ask={q.ask:.5f}")
    except Exception as e:
        print_if_error(e, "quote_many")

    # ---- 5. Symbol parameters ----------------------------------------------
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

    # ---- 6. Tick value ------------------------------------------------------
    print_method("6", "tick_value_with_size()", "tick value/size for position sizing")
    try:
        tv = await account.tick_value_with_size(["EURUSD", "GBPUSD"])
        for i in tv.infos:
            print(f"   {i.symbolName}: tick_value={i.TradeTickValue} "
                  f"tick_size={i.TradeTickSize} contract={i.TradeContractSize}")
    except Exception as e:
        print_if_error(e, "tick_value_with_size")

    # ---- 7. Opened orders ---------------------------------------------------
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

    # ---- 8. Opened order tickets -------------------------------------------
    print_method("8", "opened_orders_tickets()", "just the ticket numbers")
    try:
        t = await account.opened_orders_tickets()
        print(f"   Tickets: {list(t.tickets)}")
    except Exception as e:
        print_if_error(e, "opened_orders_tickets")

    # ---- 9. Orders history --------------------------------------------------
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
