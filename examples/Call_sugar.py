# examples/Call_sugar.py
# -*- coding: utf-8 -*-
"""
SUGAR API DEMONSTRATION - High-level trading with MT4Sugar

Demonstrates a complete trading scenario:
1) Connect to MT4 server
2) Get symbol information & pricing
3) Calculate lot size based on risk
4) Open market order with SL/TP in pips
5) Modify SL/TP dynamically
6) Partially close position
7) Close remaining position
8) Check positions and exposure

This file shows the "sugar" (high-level) API which abstracts away
low-level details like price conversions, error handling, etc.
"""

import os
import sys
import asyncio
import json
from pathlib import Path

# ---- Path bootstrap ----
REPO_ROOT = Path(__file__).resolve().parent.parent
PKG = REPO_ROOT / "package"
APP = REPO_ROOT / "app"
for p in [str(PKG), str(APP), str(REPO_ROOT)]:
    if p not in sys.path:
        sys.path.insert(0, p)

# ---- Imports ----
from MetaRpcMT4.mt4_account import MT4Account
from app.MT4Service import MT4Service


def load_settings(path: str = "appsettings.json") -> dict:
    """Load settings from appsettings.json"""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def hdr(title: str) -> None:
    """Print section header"""
    print(f"\n{'=' * 80}")
    print(f"{title}")
    print(f"{'=' * 80}")


async def main():
    hdr("MT4 SUGAR API DEMONSTRATION")
    print("\nThis script demonstrates high-level trading with MT4Sugar API")
    print("Features: smart orders, risk calculation, pip-based SL/TP, position management")

    # ========= 1) Load settings =========
    settings = load_settings()

    if settings and "mt4" in settings:
        user = int(os.getenv("MT4_LOGIN", settings["mt4"].get("login", 0)))
        password = os.getenv("MT4_PASSWORD", settings["mt4"].get("password", ""))
        server_name = os.getenv("MT4_SERVER", settings["mt4"].get("server_name"))
        grpc_server = os.getenv("GRPC_SERVER", settings.get("grpc", {}).get("server", "mt4.mrpc.pro:443"))
        base_symbol = settings["mt4"].get("base_symbol", "EURUSD")
        timeout_seconds = settings["mt4"].get("timeout_seconds", 180)
        access_list = settings["mt4"].get("access", [])
    else:
        print("\nNo appsettings.json found. Please provide environment variables:")
        print("  MT4_LOGIN, MT4_PASSWORD, MT4_SERVER (or MT4_HOST and MT4_PORT)")
        return

    # Demo parameters
    demo = settings.get("demo", {})
    symbol = os.getenv("SYMBOL", demo.get("symbol", "EURUSD"))
    test_lots = float(os.getenv("TEST_LOTS", demo.get("test_lots", 0.02)))
    risk_percent = float(os.getenv("RISK_PERCENT", 1.0))
    stop_pips = float(os.getenv("STOP_PIPS", 20.0))
    tp_pips = float(os.getenv("TP_PIPS", 40.0))
    magic = int(os.getenv("MAGIC", 888888))

    # Control flags
    enable_trading = os.getenv("ENABLE_TRADING", "0") == "1"

    print(f"\n[CONFIG]")
    print(f"  GRPC Server: {grpc_server}")
    print(f"  User: {user}")
    print(f"  Symbol: {symbol}")
    print(f"  Test Lots: {test_lots}")
    print(f"  Risk: {risk_percent}%")
    print(f"  Stop Loss: {stop_pips} pips")
    print(f"  Take Profit: {tp_pips} pips")
    print(f"  Magic: {magic}")
    print(f"  Trading Enabled: {enable_trading}")

    # ========= 2) Create MT4Account and connect =========
    hdr("[1] CONNECTION")

    account = MT4Account(user=user, password=password, grpc_server=grpc_server)
    connected = False

    # Try connection methods (same as Low_level_call.py)
    if access_list:
        print("\n[PRIORITY 1] Trying direct connection via host:port")
        for host_port in access_list:
            try:
                print(f"  Attempting: {host_port}")
                parts = host_port.split(":")
                host = parts[0]
                port = int(parts[1]) if len(parts) > 1 else 443

                await account.connect_by_host_port(
                    host=host,
                    port=port,
                    base_chart_symbol=base_symbol,
                    timeout_seconds=timeout_seconds,
                )
                print(f"  [OK] Connected to {host}:{port}")
                connected = True
                break
            except Exception as e:
                print(f"  [FAIL] {host_port}: {e}")
                continue

    if not connected and server_name:
        print("\n[PRIORITY 2] Trying connection by server name")
        print(f"  Server: {server_name}")
        try:
            await account.connect_by_server_name(
                server_name=server_name,
                base_chart_symbol=base_symbol,
                wait_for_terminal_is_alive=True,
                timeout_seconds=timeout_seconds,
            )
            print(f"  [OK] Connected via server name")
            connected = True
        except Exception as e:
            print(f"  [FAIL] {e}")

    if not connected:
        env_host = os.getenv("MT4_HOST")
        env_port = os.getenv("MT4_PORT")

        if env_host and env_port:
            print("\n[PRIORITY 3] Trying connection via environment variables")
            try:
                await account.connect_by_host_port(
                    host=env_host,
                    port=int(env_port),
                    base_chart_symbol=base_symbol,
                    timeout_seconds=timeout_seconds,
                )
                print(f"  [OK] Connected via env variables")
                connected = True
            except Exception as e:
                print(f"  [FAIL] {e}")

    if not connected:
        print("\n[ERROR] Failed to connect. Please check appsettings.json or env variables")
        return

    print(f"\n[CONNECTED] Terminal ID: {account.id}")

    # ========= 3) Create MT4Service and Sugar =========
    svc = MT4Service(account)
    sugar = svc.sugar

    # Set default parameters for Sugar
    sugar.set_defaults(
        symbol=symbol,
        magic=magic,
        deviation_pips=2.0,
        risk_percent=risk_percent
    )

    # ========= 4) Connectivity check =========
    hdr("[2] CONNECTIVITY & PING")

    await sugar.ensure_connected()
    print(f"✓ ensure_connected() -> OK")

    is_alive = await sugar.ping()
    print(f"✓ ping() -> {is_alive}")

    # ========= 5) Symbol information =========
    hdr("[3] SYMBOL INFORMATION")

    await sugar.ensure_symbol(symbol)
    print(f"✓ ensure_symbol({symbol}) -> OK\n")

    digits = await sugar.digits(symbol)
    point = await sugar.point(symbol)
    pip_size = await sugar.pip_size(symbol)
    spread = await sugar.spread_pips(symbol)
    mid = await sugar.mid_price(symbol)
    last_quote = await sugar.last_quote(symbol)

    print(f"Symbol: {symbol}")
    print(f"  Digits: {digits}")
    print(f"  Point: {point}")
    print(f"  Pip Size: {pip_size}")
    print(f"  Spread: {spread:.1f} pips")
    print(f"  Mid Price: {mid:.5f}")
    print(f"  Bid: {last_quote['bid']:.5f}")
    print(f"  Ask: {last_quote['ask']:.5f}")

    # ========= 6) Risk calculation =========
    hdr("[4] RISK CALCULATION")

    calc_lots = await sugar.calc_lot_by_risk(
        symbol=symbol,
        risk_percent=risk_percent,
        stop_pips=stop_pips
    )
    cash_risk = await sugar.calc_cash_risk(
        symbol=symbol,
        lots=test_lots,
        stop_pips=stop_pips
    )

    print(f"Risk Parameters:")
    print(f"  Risk %: {risk_percent}%")
    print(f"  Stop Loss: {stop_pips} pips")
    print(f"  Calculated Lots: {calc_lots:.2f}")
    print(f"\nFor {test_lots} lots with {stop_pips} pips SL:")
    print(f"  Cash Risk: ${cash_risk:.2f}")

    # ========= 7) Exposure summary =========
    hdr("[5] CURRENT EXPOSURE")

    exposure = await sugar.exposure_summary(by_symbol=True)
    print(f"Total Positions: {exposure.get('total_positions', 0)}")
    print(f"Total Volume: {exposure.get('total_volume', 0):.2f} lots")
    print(f"Total P&L: ${exposure.get('total_profit', 0):.2f}")

    by_symbol = exposure.get('by_symbol', {})
    if by_symbol:
        print(f"\nBy Symbol:")
        for sym, data in by_symbol.items():
            print(f"  {sym}: {data.get('net_lots', 0):.2f} lots, P&L: ${data.get('profit', 0):.2f}")

    # ========= 8) TRADING OPERATIONS =========
    hdr("[6] TRADING OPERATIONS")

    if not enable_trading:
        print("⚠️  Trading is DISABLED. Set ENABLE_TRADING=1 to enable real trading.\n")
        print("=== Syntax Examples ===\n")

        print("# BUY Market Order:")
        print("ticket = await sugar.buy_market(")
        print(f"    symbol='{symbol}',")
        print(f"    lots={test_lots},")
        print(f"    sl_pips={stop_pips},")
        print(f"    tp_pips={tp_pips},")
        print("    comment='Sugar demo',")
        print(")")

        print("\n# Modify SL/TP by pips:")
        print("await sugar.modify_sl_tp_by_pips(")
        print("    ticket=ticket,")
        print("    sl_pips=15.0,")
        print("    tp_pips=50.0,")
        print(")")

        print("\n# Partial close:")
        print("await sugar.close_partial(")
        print(f"    ticket=ticket, lots={test_lots/2}")
        print(")")

        print("\n# Close position:")
        print("await sugar.close(ticket)")

        print("\n# SELL Market Order:")
        print("ticket = await sugar.sell_market(")
        print(f"    symbol='{symbol}', lots={test_lots},")
        print(f"    sl_pips={stop_pips}, tp_pips={tp_pips}")
        print(")")

        print("\n# Pending Orders:")
        print("# BUY LIMIT")
        print("ticket = await sugar.buy_limit(")
        print(f"    symbol='{symbol}', price=1.0850,")
        print(f"    lots={test_lots}, sl_pips={stop_pips}, tp_pips={tp_pips}")
        print(")")

        print("\n# SELL STOP")
        print("ticket = await sugar.sell_stop(")
        print(f"    symbol='{symbol}', price=1.0850,")
        print(f"    lots={test_lots}, sl_pips={stop_pips}, tp_pips={tp_pips}")
        print(")")

    else:
        print("⚠️  TRADING IS ENABLED! Real orders will be placed!\n")

        # ===== BUY Market Order =====
        print(f"\n=== Opening BUY MARKET order ===")
        print(f"  Symbol: {symbol}")
        print(f"  Lots: {test_lots}")
        print(f"  SL: {stop_pips} pips")
        print(f"  TP: {tp_pips} pips")

        try:
            ticket = await sugar.buy_market(
                symbol=symbol,
                lots=test_lots,
                sl_pips=stop_pips,
                tp_pips=tp_pips,
                comment="Sugar-Demo BUY",
            )
            print(f"✓ Order opened successfully!")
            print(f"  Ticket: {ticket}")
        except Exception as e:
            print(f"✗ Failed to open order: {e}")
            ticket = None

        if ticket:
            # Wait a bit for order to register
            await asyncio.sleep(2)

            # ===== Modify SL/TP =====
            print(f"\n=== Modifying SL/TP ===")
            print(f"  New SL: 15 pips")
            print(f"  New TP: 50 pips")

            try:
                await sugar.modify_sl_tp_by_pips(
                    ticket=ticket,
                    sl_pips=15.0,
                    tp_pips=50.0,
                )
                print(f"✓ Order modified successfully!")
            except Exception as e:
                print(f"✗ Failed to modify: {e}")

            await asyncio.sleep(1)

            # ===== Partial Close =====
            print(f"\n=== Partial close (50%) ===")
            partial_lots = test_lots / 2

            try:
                await sugar.close_partial(
                    ticket=ticket,
                    lots=partial_lots
                )
                print(f"✓ Partially closed {partial_lots:.2f} lots")
            except Exception as e:
                print(f"✗ Failed to partially close: {e}")

            await asyncio.sleep(1)

            # ===== Full Close =====
            print(f"\n=== Closing remaining position ===")

            try:
                await sugar.close(ticket=ticket)
                print(f"✓ Position closed successfully!")
            except Exception as e:
                # After partial close, original ticket may be invalid
                print(f"Note: {e}")
                print(f"  (Original ticket may be invalid after partial close)")

        # ===== SELL Market Order =====
        print(f"\n=== Opening SELL MARKET order ===")

        try:
            ticket2 = await sugar.sell_market(
                symbol=symbol,
                lots=test_lots,
                sl_pips=stop_pips,
                tp_pips=tp_pips,
                comment="Sugar-Demo SELL",
            )
            print(f"✓ SELL order opened!")
            print(f"  Ticket: {ticket2}")

            await asyncio.sleep(1)

            # Close SELL order
            await sugar.close(ticket=ticket2)
            print(f"✓ SELL order closed!")

        except Exception as e:
            print(f"✗ SELL order failed: {e}")

        # ===== Pending Order Example =====
        print(f"\n=== Pending Order: BUY LIMIT ===")

        # Calculate price 10 pips below current
        current_bid = last_quote['bid']
        limit_price = current_bid - (10 * pip_size)

        try:
            ticket3 = await sugar.buy_limit(
                symbol=symbol,
                price=limit_price,
                lots=test_lots,
                sl_pips=stop_pips,
                tp_pips=tp_pips,
                comment="Sugar-Demo BUYLIMIT",
            )
            print(f"✓ BUY LIMIT placed!")
            print(f"  Ticket: {ticket3}")
            print(f"  Price: {limit_price:.5f}")

            await asyncio.sleep(1)

            # Delete pending order
            await sugar.close(ticket=ticket3)
            print(f"✓ Pending order deleted!")

        except Exception as e:
            print(f"✗ Pending order failed: {e}")

    # ========= 9) Final exposure check =========
    hdr("[7] FINAL POSITIONS CHECK")

    # Get opened orders via MT4Service
    opened = await svc.opened_orders()

    # Extract positions list from response
    if hasattr(opened, 'order_infos'):
        positions_list = list(opened.order_infos)
    elif hasattr(opened, 'orders'):
        positions_list = list(opened.orders)
    elif hasattr(opened, 'Orders'):
        positions_list = list(opened.Orders)
    elif isinstance(opened, list):
        positions_list = opened
    else:
        positions_list = []

    print(f"Open Positions: {len(positions_list)}")

    if positions_list:
        for pos in positions_list[:5]:  # Show first 5
            try:
                ticket = getattr(pos, 'ticket', getattr(pos, 'Ticket', 'N/A'))
                symbol = getattr(pos, 'symbol', getattr(pos, 'Symbol', 'N/A'))
                order_type = getattr(pos, 'order_type', getattr(pos, 'Type', 'N/A'))
                lots = getattr(pos, 'lots', getattr(pos, 'Lots', getattr(pos, 'volume', 0)))
                open_price = getattr(pos, 'open_price', getattr(pos, 'OpenPrice', getattr(pos, 'price_open', 0)))
                profit = getattr(pos, 'profit', getattr(pos, 'Profit', 0))

                print(f"\n  Ticket: {ticket}")
                print(f"  Symbol: {symbol}")
                print(f"  Type: {order_type}")
                print(f"  Lots: {lots:.2f}")
                print(f"  Open Price: {open_price:.5f}")
                print(f"  Profit: ${profit:.2f}")
            except Exception as e:
                print(f"\n  Position data: {pos}")

    # ========= Summary =========
    hdr("EXECUTION SUMMARY")

    print("\n✓ All Sugar API demonstrations completed!")
    print("\nAPI Methods Demonstrated:")
    print("  ✓ Connection & Ping:")
    print("    - ensure_connected(), ping()")
    print("  ✓ Symbol Information:")
    print("    - ensure_symbol(), digits(), point(), pip_size()")
    print("    - spread_pips(), mid_price(), last_quote()")
    print("  ✓ Risk Management:")
    print("    - calc_lot_by_risk(), calc_cash_risk()")
    print("  ✓ Exposure & Positions:")
    print("    - exposure_summary(), svc.opened_orders()")

    if enable_trading:
        print("  ✓ Trading (EXECUTED):")
        print("    - buy_market(), sell_market()")
        print("    - buy_limit(), sell_stop()")
        print("    - modify_sl_tp_by_pips()")
        print("    - close(), close_partial()")
    else:
        print("  ✓ Trading (syntax shown):")
        print("    - buy_market(), sell_market()")
        print("    - buy_limit(), sell_stop()")
        print("    - modify_sl_tp_by_pips()")
        print("    - close(), close_partial()")

    print("\n" + "=" * 80)
    print("To enable real trading:")
    print("  export ENABLE_TRADING=1")
    print("  python examples/Call_sugar.py")
    print("=" * 80)


if __name__ == "__main__":
    # Set console encoding for Windows
    import sys
    if sys.platform == 'win32':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except:
            pass

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()


# Command to run:
# python examples\Call_sugar.py

"""
╔══════════════════════════════════════════════════════════════════════════════╗
║ FILE examples/Call_sugar.py — High-level MT4Sugar API trading demo           ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ Purpose:                                                                     ║
║   Demonstrate real-world usage of the MT4Sugar high-level API:               ║
║   auto-handling price formats, pip math, risk, smart order helpers,          ║
║   and safe execution flows with optional trading toggle.                     ║
║                                                                              ║
║ Step-by-step behavior:                                                       ║
║   1) Bootstraps local import paths (package/, app/).                         ║
║   2) Load config (appsettings.json) + ENV overrides.                         ║
║   3) Create MT4Account and connect using priority (host:port → server → ENV).║
║   4) Create MT4Service + sugar wrapper; set sugar defaults.                  ║
║   5) Connectivity & ping check.                                              ║
║   6) Symbol information & pricing summary.                                   ║
║   7) Risk calculation via pip-based parameters.                              ║
║   8) Exposure summary (by symbol).                                           ║
║   9) Trading operations (conditional):                                       ║
║        - buy_market, modify_sl_tp_by_pips,                                   ║
║          close_partial, close (full),                                        ║
║        - sell_market,                                                        ║
║        - buy_limit→close (pending cancel),                                   ║
║      (if ENABLE_TRADING=0 → print syntax only)                               ║
║  10) Final check using svc.opened_orders().                                  ║
║  11) Execution summary of demonstrated API.                                  ║
║                                                                              ║
║ Public API / Entry Points:                                                   ║
║   - main() — complete high-level trading scenario executor                   ║
║   - load_settings(), hdr() — helpers                                         ║
║                                                                              ║
║ Dependencies used in this file:                                              ║
║   - MetaRpcMT4.mt4_account.MT4Account                                        ║
║   - app.MT4Service.MT4Service  (using svc.sugar)                             ║
║                                                                              ║
║ Config & ENV references:                                                     ║
║   - User params: MT4_LOGIN, MT4_PASSWORD, MT4_SERVER                         ║
║   - Optional: MT4_HOST, MT4_PORT, GRPC_SERVER                                ║
║   - Trading params: SYMBOL, TEST_LOTS, RISK_PERCENT, STOP_PIPS, TP_PIPS,     ║
║                     MAGIC, ENABLE_TRADING                                    ║
║   - appsettings.json fallback for all fields                                 ║
║                                                                              ║
║ RPC used via Sugar:                                                          ║
║   - Connection: ensure_connected, ping                                       ║
║   - Symbol info: ensure_symbol, digits, point, pip_size, spread_pips,        ║
║                  mid_price, last_quote                                       ║
║   - Risk: calc_lot_by_risk, calc_cash_risk                                   ║
║   - Exposure: exposure_summary                                               ║
║   - Trading: buy_market, sell_market, buy_limit, sell_stop,                  ║
║              modify_sl_tp_by_pips, close, close_partial                      ║
║   - Query: svc.opened_orders                                                 ║
╚══════════════════════════════════════════════════════════════════════════════╝

"""