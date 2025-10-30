# main_sugar.py - HIGH-LEVEL MT4 API DEMO (MT4Sugar wrapper)
from __future__ import annotations
import sys
from pathlib import Path

# Setup paths
ROOT = Path(__file__).resolve().parent
PKG = ROOT / "package"
APP = ROOT / "app"
for p in [str(PKG), str(APP), str(ROOT)]:
    if p not in sys.path:
        sys.path.insert(0, p)

import asyncio
import json
from typing import Any
from datetime import datetime

from MetaRpcMT4.mt4_account import MT4Account
from app.MT4Service import MT4Service
from app.Helper.Design.Sugar_Styling import (
    show_connectivity_status,
    show_symbol_info,
    show_risk_calc,
    show_exposure,
    show_order_result,
    show_positions_value,
    show_diagnostic_snapshot,
    BOLD, RESET, FG_CY, FG_GN, FG_YL, FG_RD
)

# ─── utils ────────────────────────────────────────────────────────────────────
def load_settings(path: str = "appsettings.json") -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def hdr(title: str) -> None:
    print(f"\n{FG_CY}{'=' * 76}")
    print(f"{BOLD}{title}{RESET}")
    print(f"{FG_CY}{'=' * 76}{RESET}")

def pp(title: str, obj: Any) -> None:
    import pprint
    print(title)
    pprint.PrettyPrinter(indent=2, width=100).pprint(obj)

# ══════════════════════════════
# region WIRING 
# ══════════════════════════════

def build_account(conf: dict) -> MT4Account:
    mt4 = conf["mt4"]

    import os
    user = int(os.getenv("MT4_LOGIN", mt4["login"]))
    password = os.getenv("MT4_PASSWORD", mt4["password"])
    grpc_server = os.getenv("GRPC_SERVER", conf.get("grpc", {}).get("server", "mt4.mrpc.pro:443"))

    print(f"\n{BOLD}[CONFIG]{RESET}")
    print(f"  {FG_CY}GRPC Server:{RESET} {grpc_server}")
    print(f"  {FG_CY}User:{RESET} {user}")
    print(f"  {FG_CY}Password:{RESET} {'*' * len(password)}")

    return MT4Account(user=user, password=password, grpc_server=grpc_server)

#endregion


# ══════════════════════════════
# region SUGAR DEMO
# ══════════════════════════════
async def run_sugar_demo(svc: MT4Service, conf: dict) -> None:
    """Demonstration of HIGH-LEVEL (sugar) calls via MT4Sugar."""
    sugar = svc.sugar
    demo = conf.get("demo", {})
    symbol: str = demo.get("symbol", "EURUSD")

    # Setting up defaults for convenience
    sugar.set_defaults(symbol=symbol, magic=9002, deviation_pips=2.0)

    # 1) CONNECTIVITY & ACCOUNT
    hdr("[SUGAR] CONNECTIVITY & ACCOUNT")
    await sugar.ensure_connected()
    print(f"{FG_GN}✓{RESET} ensure_connected() -> OK")

    is_alive = await sugar.ping()
    # Get terminal ID from service
    terminal_id = svc._mt4_account.id if hasattr(svc, '_mt4_account') else None
    show_connectivity_status(is_alive, terminal_id)

    # 2) SYMBOL INFO & PRICING
    hdr("[SUGAR] SYMBOL INFO & PRICING")
    await sugar.ensure_symbol(symbol)
    print(f"{FG_GN}✓{RESET} ensure_symbol({symbol}) -> OK\n")

    digits = await sugar.digits(symbol)
    point = await sugar.point(symbol)
    pip_size = await sugar.pip_size(symbol)
    spread = await sugar.spread_pips(symbol)
    mid = await sugar.mid_price(symbol)
    last = await sugar.last_quote(symbol)

    show_symbol_info(
        symbol=symbol,
        digits=digits,
        point=point,
        pip_size=pip_size,
        spread=spread,
        mid=mid,
        bid=last['bid'],
        ask=last['ask']
    )

    # 3) RISK CALCULATION
    hdr("[SUGAR] RISK & LOT SIZING")
    stop_pips = 20.0
    risk_percent = 1.0
    calc_lots = await sugar.calc_lot_by_risk(symbol, risk_percent=risk_percent, stop_pips=stop_pips)
    cash_risk = await sugar.calc_cash_risk(symbol, lots=0.01, stop_pips=stop_pips)

    show_risk_calc(
        symbol=symbol,
        risk_percent=risk_percent,
        stop_pips=stop_pips,
        calc_lots=calc_lots,
        lots=0.01,
        cash_risk=cash_risk
    )

    # 4) EXPOSURE SUMMARY
    hdr("[SUGAR] EXPOSURE SUMMARY")
    exposure = await sugar.exposure_summary(by_symbol=True)
    show_exposure(exposure)

    # 5) SMART MARKET ORDER (BUY)
    hdr("[SUGAR] SMART ORDERS: buy_market / modify / close")
    ticket = await sugar.buy_market(
        symbol=symbol,
        lots=0.01,
        sl_pips=20.0,
        tp_pips=40.0,
        comment="Sugar-Demo",
    )
    show_order_result("BUY MARKET", ticket, symbol=symbol, lots=0.01, ok=True)

    # Wait a bit for order to appear
    await asyncio.sleep(1.0)

    # 6) MODIFY SL/TP by pips
    await sugar.modify_sl_tp_by_pips(ticket, sl_pips=15.0, tp_pips=50.0)
    print(f"{FG_GN}✓{RESET} Ticket #{FG_CY}{ticket}{RESET}: SL/TP modified (15/50 pips)")

    # 7) CLOSE ORDER
    await sugar.close(ticket)
    show_order_result("CLOSED", ticket, ok=True)

    # 8) FIND ORDERS
    hdr("[SUGAR] QUERY & FILTERS")
    orders = await sugar.find_orders(symbol=symbol, state="open")
    print(f"{FG_YL}Found {len(orders)} open orders for {symbol}{RESET}\n")

    positions = await sugar.positions_value(symbol=symbol)
    show_positions_value(positions)

    # 9) DIAGNOSTIC SNAPSHOT
    hdr("[SUGAR] DIAGNOSTICS")
    snapshot = await sugar.diag_snapshot()
    show_diagnostic_snapshot(snapshot)

    # 10) ADDITIONAL SUGAR METHODS
    hdr("[SUGAR] ADDITIONAL METHODS")

    # BUY LIMIT ORDER
    current_quote = await sugar.last_quote(symbol)
    limit_price = current_quote['bid'] - 0.0010  # 10 pips below current
    print(f"\n{FG_YL}Testing buy_limit at {limit_price:.5f}...{RESET}")
    try:
        limit_ticket = await sugar.buy_limit(
            symbol=symbol,
            price=limit_price,
            lots=0.01,
            sl_pips=15.0,
            tp_pips=30.0,
            comment="Sugar-Limit-Demo",
        )
        show_order_result("BUY LIMIT", limit_ticket, symbol=symbol, lots=0.01, price=limit_price, ok=True)

        # Cancel pending order
        await asyncio.sleep(0.5)
        await sugar.close(limit_ticket)
        show_order_result("CANCELLED", limit_ticket, ok=True)
    except Exception as e:
        print(f"{FG_RD}✗ buy_limit() -> Error: {e}{RESET}")

    # SELL MARKET
    print(f"\n{FG_YL}Testing sell_market...{RESET}")
    try:
        sell_ticket = await sugar.sell_market(
            symbol=symbol,
            lots=0.01,
            sl_pips=20.0,
            tp_pips=40.0,
            comment="Sugar-Sell-Demo",
        )
        show_order_result("SELL MARKET", sell_ticket, symbol=symbol, lots=0.01, ok=True)

        await asyncio.sleep(1.0)

        # Modify by price (absolute)
        current_quote = await sugar.last_quote(symbol)
        new_sl = current_quote['ask'] + 0.0015  # 15 pips above
        await sugar.modify_sl_tp_by_price(sell_ticket, sl_price=new_sl, tp_price=None)
        print(f"{FG_GN}✓{RESET} Ticket #{FG_CY}{sell_ticket}{RESET}: SL modified by price to {new_sl:.5f}")

        # Close
        await sugar.close(sell_ticket)
        show_order_result("CLOSED", sell_ticket, ok=True)
    except Exception as e:
        print(f"{FG_RD}✗ sell_market() -> Error: {e}{RESET}")

    # CLOSE ALL (demo - will close any remaining test orders)
    print(f"\n{FG_YL}Testing close_all with magic filter...{RESET}")
    try:
        await sugar.close_all(magic=9002)
        print(f"{FG_GN}✓{RESET} close_all(magic=9002) -> OK")
    except Exception as e:
        print(f"{FG_RD}✗ close_all() -> Error: {e}{RESET}")

    print(f"\n{BOLD}{FG_GN}[SUGAR DEMO FINISHED]{RESET}")

#endregion


# ══════════════════════════════
# region MAIN
# ══════════════════════════════

async def amain() -> None:
    print(f"\n{BOLD}{FG_CY}{'='*76}")
    print(f"{'MT4 HIGH-LEVEL (SUGAR) API DEMO':^76}")
    print(f"{'='*76}{RESET}")

    conf = load_settings("appsettings.json")

    # build account
    acc = build_account(conf)

    import os
    base_symbol = conf["mt4"].get("base_symbol", "EURUSD")
    timeout_seconds = max(300, int(conf["mt4"].get("timeout_seconds", 120)))

    # PRIORITY 1: Direct connection via host:port from appsettings.json
    access_list = conf["mt4"].get("access", [])
    connected = False

    if access_list:
        print(f"\n{BOLD}[PRIORITY 1]{RESET} Trying direct connection via host:port from appsettings.json")
        for host_port in access_list:
            try:
                print(f"  {FG_YL}Attempting:{RESET} {host_port}")
                parts = host_port.split(":")
                host = parts[0]
                port = int(parts[1]) if len(parts) > 1 else 443

                await acc.connect_by_host_port(
                    host=host,
                    port=port,
                    base_chart_symbol=base_symbol,
                    timeout_seconds=timeout_seconds,
                )
                print(f"  {FG_GN}[OK]{RESET} Connected to {host}:{port}")
                connected = True
                break
            except Exception as e:
                print(f"  {FG_RD}[FAIL]{RESET} {host_port}: {e}")
                continue

    # PRIORITY 2: Connect by server name (ConnectEx)
    if not connected:
        server_name = os.getenv("MT4_SERVER", conf["mt4"].get("server_name"))
        if server_name:
            print(f"\n[PRIORITY 2] Trying connection by server name")
            print(f"  Server: {server_name}")
            print(f"  Base Symbol: {base_symbol}")
            print(f"  Timeout: {timeout_seconds}s")

            try:
                await acc.connect_by_server_name(
                    server_name=server_name,
                    base_chart_symbol=base_symbol,
                    timeout_seconds=timeout_seconds,
                )
                print(f"  [OK] Connected via server name")
                connected = True
            except Exception as e:
                print(f"  [FAIL] Failed to connect by server name: {e}")

    # PRIORITY 3: Environment Variables (if nothing else works)
    if not connected:
        env_host = os.getenv("MT4_HOST")
        env_port = os.getenv("MT4_PORT")

        if env_host and env_port:
            print(f"\n[PRIORITY 3] Trying connection via environment variables")
            print(f"  Host: {env_host}")
            print(f"  Port: {env_port}")

            try:
                await acc.connect_by_host_port(
                    host=env_host,
                    port=int(env_port),
                    base_chart_symbol=base_symbol,
                    timeout_seconds=timeout_seconds,
                )
                print(f"  [OK] Connected via environment variables")
                connected = True
            except Exception as e:
                print(f"  [FAIL] Failed to connect via env: {e}")

    if not connected:
        raise RuntimeError("Failed to connect using all available methods (appsettings.json, server_name, .env)")

    print(f"\n{BOLD}{FG_GN}[CONNECTED]{RESET}")
    print(f"  {FG_CY}Terminal ID:{RESET} {acc.id}")

    svc = MT4Service(acc)

    print(f"\n{BOLD}{FG_GN}[START SUGAR DEMO]{RESET} {datetime.now().isoformat(timespec='seconds')}")
    await run_sugar_demo(svc, conf)
    print(f"\n{BOLD}{FG_GN}[ALL DONE]{RESET}")


if __name__ == "__main__":
    try:
        asyncio.run(amain())
    except KeyboardInterrupt:
        print(f"\n{FG_YL}[INTERRUPTED]{RESET}")
    except Exception as e:
        print(f"\n{BOLD}{FG_RD}[FATAL ERROR]{RESET} {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

 #endregion

# Command to run:
# python main_sugar.py

"""
╔══════════════════════════════════════════════════════════════════════════════╗
║ FILE main_sugar.py — HIGH-LEVEL MT4 API DEMO (MT4Sugar wrapper)              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ Purpose:                                                                     ║
║   Showcase high-level (“sugar”) helpers for MT4 via MT4Service.sugar:        ║
║   connectivity checks, symbol/pricing info, risk/lot sizing, smart orders,   ║
║   exposure snapshot, diagnostics, and convenient find/close utilities.       ║
║                                                                              ║
║ Step-by-step behavior:                                                       ║
║   1) Prepare PYTHONPATH (adds package/, app/, project root).                 ║
║   2) Load config (appsettings.json) + ENV overrides.                         ║
║   3) Create MT4Account(user, password, grpc_server).                         ║
║   4) Connect using priorities: appsettings host:port → server_name → ENV.    ║
║   5) Wrap account into MT4Service and use svc.sugar for high-level API.      ║
║   6) Connectivity & account: sugar.ensure_connected(), sugar.ping(),         ║
║      show_connectivity_status(…, terminal_id).                               ║
║   7) Symbol info & pricing: ensure_symbol, digits, point, pip_size,          ║
║      spread_pips, mid_price, last_quote → show_symbol_info().                ║
║   8) Risk & lot sizing: calc_lot_by_risk, calc_cash_risk → show_risk_calc(). ║
║   9) Exposure: exposure_summary(by_symbol=True) → show_exposure().           ║
║  10) Smart market order BUY → ticket, modify_sl_tp_by_pips, close,           ║
║      show_order_result for each step.                                        ║
║  11) Query helpers: find_orders(state="open"), positions_value → UI print.   ║
║  12) Diagnostics: diag_snapshot() → show_diagnostic_snapshot().              ║
║  13) Extra sugar ops: buy_limit (then cancel), sell_market →                 ║
║      modify_sl_tp_by_price → close; finally close_all(magic=9002).           ║
║                                                                              ║
║ Public API / Entry Points:                                                   ║
║   - amain() — main async entrypoint                                          ║
║   - run_sugar_demo(svc, conf) — orchestrates high-level (“sugar”) flow       ║
║   - build_account(conf) — construct MT4Account with ENV support              ║
║                                                                              ║
║ Dependencies used in this file:                                              ║
║   - MetaRpcMT4.mt4_account.MT4Account                                        ║
║   - app.MT4Service.MT4Service  (uses svc.sugar property)                     ║
║   - app.Helper.Design.Sugar_Styling:                                         ║
║       show_connectivity_status, show_symbol_info, show_risk_calc,            ║
║       show_exposure, show_order_result, show_positions_value,                ║
║       show_diagnostic_snapshot, BOLD/RESET/FG_*                              ║
║                                                                              ║
║ Config & ENV references:                                                     ║
║   - appsettings.json → mt4.login, mt4.password, mt4.access[],                ║
║                         mt4.server_name, mt4.base_symbol, timeout            ║
║   - ENV → MT4_LOGIN, MT4_PASSWORD, GRPC_SERVER,                              ║
║            MT4_SERVER, MT4_HOST, MT4_PORT                                    ║
║                                                                              ║
║ RPC used via Sugar during demo:                                              ║
║   - Connectivity: ensure_connected, ping                                     ║
║   - Symbol/price: ensure_symbol, digits, point, pip_size, spread_pips,       ║
║                   mid_price, last_quote                                      ║
║   - Risk/lot: calc_lot_by_risk, calc_cash_risk                               ║
║   - Orders: buy_market, buy_limit, sell_market,                              ║
║             modify_sl_tp_by_pips, modify_sl_tp_by_price, close, close_all    ║
║   - Queries/summary: find_orders, positions_value, exposure_summary,         ║
║                      diag_snapshot                                           ║
╚══════════════════════════════════════════════════════════════════════════════╝

"""