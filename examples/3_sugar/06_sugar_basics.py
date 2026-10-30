"""
==============================================================================
 FILE: 06_sugar_basics.py - HIGH-LEVEL (MT4Sugar) - PART 1/3: BASICS

 MT4Sugar is the high-level convenience API, built on MT4Service:

     service = MT4Service(account)
     sugar   = MT4Sugar(service)

 This file covers the read / compute helpers (no trades):
   - Connection & defaults    - Price math & normalization
   - Quotes & market data      - Risk sizing

 Trading lives in 07_sugar_trading.py; positions/streams in 08_sugar_positions.py.

 HOW TO RUN:
   cd examples
   python main.py sugar            (or select [6] from the menu)
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


# =============================================================================
# REGION 1 - CONNECTION & DEFAULTS
# =============================================================================
async def region_connection(sugar: MT4Sugar):
    print_step(1, "Connection & defaults")

    print_method("1.1", "sugar.ensure_connected() / ping()", "health check")
    try:
        await sugar.ensure_connected()
        await sugar.ping()
        print_success("connection is alive")
    except Exception as e:
        print_if_error(e, "ensure_connected/ping")

    print_method("1.2", "sugar.set_defaults() / get_default()", "set shared defaults")
    try:
        sugar.set_defaults(symbol=SYMBOL, magic=777, deviation_pips=5, risk_percent=1.0)
        print_success(f"default symbol={sugar.get_default('symbol')} "
                      f"magic={sugar.get_default('magic')} risk%={sugar.get_default('risk_percent')}")
    except Exception as e:
        print_if_error(e, "set_defaults")

    print_method("1.3", "sugar.ensure_symbol()", "select/preload a symbol")
    try:
        await sugar.ensure_symbol(SYMBOL)
        print_success(f"{SYMBOL} is ready")
    except Exception as e:
        print_if_error(e, "ensure_symbol")


# =============================================================================
# REGION 2 - PRICE MATH & NORMALIZATION
# =============================================================================
async def region_price_math(sugar: MT4Sugar):
    print_step(2, "Price math & normalization")

    print_method("2.1", "point / digits / pip_size / spread_pips / mid_price", "")
    try:
        print(f"   point={await sugar.point(SYMBOL)} digits={await sugar.digits(SYMBOL)} "
              f"pip_size={await sugar.pip_size(SYMBOL)}")
        print(f"   spread={await sugar.spread_pips(SYMBOL):.1f} pips  mid={await sugar.mid_price(SYMBOL):.5f}")
    except Exception as e:
        print_if_error(e, "price metrics")

    print_method("2.2", "pips_to_price / price_to_pips", "convert pips <-> price")
    try:
        p = await sugar.pips_to_price(SYMBOL, 20)
        back = await sugar.price_to_pips(SYMBOL, p)
        print(f"   20 pips = {p:.5f} price delta  ->  {back:.1f} pips")
    except Exception as e:
        print_if_error(e, "pip conversion")

    print_method("2.3", "normalize_price / normalize_lot", "round to broker precision")
    try:
        print(f"   normalize_price(1.123456789) = {await sugar.normalize_price(SYMBOL, 1.123456789)}")
        print(f"   normalize_lot(0.0234)        = {await sugar.normalize_lot(SYMBOL, 0.0234)}")
    except Exception as e:
        print_if_error(e, "normalize")


# =============================================================================
# REGION 3 - QUOTES & MARKET DATA
# =============================================================================
async def region_market_data(sugar: MT4Sugar):
    print_step(3, "Quotes & market data")

    print_method("3.1", "sugar.last_quote() / quotes()", "latest Bid/Ask")
    try:
        q = await sugar.last_quote(SYMBOL)
        print(f"   last_quote({SYMBOL}) -> {q}")
        many = await sugar.quotes([SYMBOL, "GBPUSD", "USDJPY"])
        print(f"   quotes([3 symbols]) -> {len(many)} quote(s)")
    except Exception as e:
        print_if_error(e, "quotes")

    print_method("3.2", "sugar.bars() / ticks()", "candles and raw ticks")
    try:
        bars = await sugar.bars(SYMBOL, "H1", count=5)
        last = bars[-1] if bars else None
        print(f"   bars({SYMBOL}, H1, 5) -> {len(bars)} bar(s)"
              + (f"; last close={last['close']:.5f}" if last else ""))
        tk = await sugar.ticks(SYMBOL, limit=5)
        print(f"   ticks({SYMBOL}, 5) -> {len(tk)} tick(s)")
    except Exception as e:
        print_if_error(e, "bars/ticks")

    print_method("3.3", "sugar.wait_price()", "wait until price crosses a level (3s cap)")
    try:
        mid = await sugar.mid_price(SYMBOL)
        hit = await sugar.wait_price(SYMBOL, target=mid - 0.0100, direction=">=", timeout_s=3)
        print(f"   wait_price(>= mid-100pips) -> {hit}")
    except Exception as e:
        print_if_error(e, "wait_price")


# =============================================================================
# REGION 4 - RISK SIZING
# =============================================================================
async def region_risk(sugar: MT4Sugar):
    print_step(4, "Risk sizing")

    print_method("4.1", "sugar.tick_value()", "money value of one tick")
    try:
        print(f"   tick_value({SYMBOL}, 1.0 lot) = {await sugar.tick_value(SYMBOL, 1.0)}")
    except Exception as e:
        print_if_error(e, "tick_value")

    print_method("4.2", "sugar.calc_lot_by_risk()", "lot size for a % risk and SL distance")
    try:
        lot = await sugar.calc_lot_by_risk(SYMBOL, risk_percent=1.0, stop_pips=20)
        print(f"   risk 1% with 20 pip SL -> {lot} lot")
    except Exception as e:
        print_if_error(e, "calc_lot_by_risk")

    print_method("4.3", "sugar.calc_cash_risk()", "cash at risk for a given lot/SL")
    try:
        cash = await sugar.calc_cash_risk(SYMBOL, lots=0.10, stop_pips=20)
        print(f"   0.10 lot, 20 pip SL -> {cash} at risk")
    except Exception as e:
        print_if_error(e, "calc_cash_risk")

    print_method("4.4", "sugar.breakeven_price()", "entry adjusted by commission/swap (price units)")
    try:
        be = sugar.breakeven_price(entry_price=1.10000, commission=0.00007, swap=-0.00002)
        print(f"   breakeven(entry 1.10000) = {be:.5f}")
    except Exception as e:
        print_if_error(e, "breakeven_price")


async def main():
    print("\n" + "=" * 78)
    print("HIGH-LEVEL: MT4Sugar - basics (prices, data, risk)")
    print("=" * 78)
    try:
        config = load_settings()
    except Exception as e:
        fatal(e, "Failed to load settings")

    account = await create_and_connect_mt4(config)
    sugar = MT4Sugar(MT4Service(account))
    try:
        await region_connection(sugar)
        await region_price_math(sugar)
        await region_market_data(sugar)
        await region_risk(sugar)
    finally:
        await sugar.disconnect()
        print_success("Disconnected")


if __name__ == "__main__":
    asyncio.run(main())
