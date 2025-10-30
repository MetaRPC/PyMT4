# main_low_level.py — LOW-LEVEL MT4 API DEMO (MT4Service wrapper)
from __future__ import annotations
import sys
from pathlib import Path

# ─── PATHS & SYS.INIT ────────────────────────────────────────────────────────────────────                                             

ROOT = Path(__file__).resolve().parent
PKG = ROOT / "package"
APP = ROOT / "app"
for p in [str(PKG), str(APP), str(ROOT)]:
    if p not in sys.path:
        sys.path.insert(0, p)

# ─── IMPORTS ────────────────────────────────────────────────────────────────────                                                        

import asyncio
import json
from typing import Any
from datetime import datetime

from MetaRpcMT4.mt4_account import MT4Account
from app.MT4Service import MT4Service
from app.Helper.Design.Low_Level_Styling import (
    show_account_summary,
    show_quotes_table,
    show_positions_table,
    show_history_table,
    show_order_result,
    BOLD, RESET, FG_CYAN, FG_GREEN, FG_YELLOW, FG_RED
)

# ─── utils ────────────────────────────────────────────────────────────────────                                                        

def load_settings(path: str = "appsettings.json") -> dict:
    """Load JSON settings file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def hdr(title: str) -> None:
    """Pretty printed section header with color."""
    print(f"\n{FG_CYAN}{'=' * 76}")
    print(f"{BOLD}{title}{RESET}")
    print(f"{FG_CYAN}{'=' * 76}{RESET}")

def pp(title: str, obj: Any) -> None:
    """Pretty print helper for demo outputs."""
    import pprint
    print(title)
    pprint.PrettyPrinter(indent=2, width=100).pprint(obj)

# ══════════════════════════════
# region WIRING  🔌                                                         
# ══════════════════════════════

def build_low_level(conf: dict) -> MT4Account:
    """Create low-level MT4Account using settings and ENV overrides."""
    mt4 = conf["mt4"]

    # allow ENV overrides
    import os
    user = int(os.getenv("MT4_LOGIN", mt4["login"]))
    password = os.getenv("MT4_PASSWORD", mt4["password"])
    grpc_server = os.getenv("GRPC_SERVER", conf.get("grpc", {}).get("server", "mt4.mrpc.pro:443"))

    # important: exactly user/password/grpc_server
    print(f"\n{BOLD}[CONFIG]{RESET}")
    print(f"  {FG_CYAN}GRPC Server:{RESET} {grpc_server}")
    print(f"  {FG_CYAN}User:{RESET} {user}")
    print(f"  {FG_CYAN}Password:{RESET} {'*' * len(password)}")

    return MT4Account(user=user, password=password, grpc_server=grpc_server)
#endregion


# ═════════════════════════
#  region DEMO  🎯                                                           
# ═════════════════════════

async def run_low_level_demo(svc: MT4Service, conf: dict) -> None:
    demo = conf.get("demo", {})
    symbol: str = demo.get("symbol", "EURUSD")
    symbols: list[str] = demo.get("symbols", [symbol, "GBPUSD", "USDJPY"])

    # ── CONNECTIVITY 🔗 ─────────────────────────────────────────────
    hdr("[LOW] CONNECTIVITY")
    headers = svc.get_headers()
    print(f"{FG_YELLOW}Headers:{RESET}")
    pp("", headers)
    await svc.reconnect()
    print(f"{FG_GREEN}✓{RESET} reconnect() -> OK")

    # ── ACCOUNT SUMMARY 👤 ──────────────────────────────────────────
    hdr("[LOW] ACCOUNT SUMMARY")
    acc = await svc.account_summary()
    show_account_summary(acc)

    # ── SYMBOLS & QUOTES 📈 (read-only) ─────────────────────────────
    hdr("[LOW] SYMBOLS & QUOTES")
    syms = await svc.symbols(symbols)
    print(f"{FG_YELLOW}Available symbols:{RESET} {', '.join(symbols)}")
    sp = await svc.symbol_params_many([symbol])
    print(f"{FG_YELLOW}Symbol params for {symbol}:{RESET}")
    pp("", sp)
    q1 = await svc.quote(symbol)
    print(f"{FG_YELLOW}Single quote for {symbol}:{RESET}")
    pp("", q1)
    qn = await svc.quote_many(symbols)
    show_quotes_table(qn)

    # ── ORDERS & HISTORY 📜 (read-only) ─────────────────────────────
    hdr("[LOW] ORDERS (OPENED & HISTORY)")
    opened = await svc.opened_orders()
    show_positions_table(opened, top=10)
    try:
        hist = await svc.orders_history()
        show_history_table(hist, top=10)
    except Exception as e:
        print(f"{FG_YELLOW}orders_history() not available on this backend: {e}{RESET}")

    # ── TRADING 💼: market BUY → modify → close ─────────────────────
    hdr("[LOW] TRADING: order_send / order_modify / order_close_delete")

    # a) place market buy (minimal payload)
    order_payload = {
        "symbol": symbol,
        "side": "buy",
        "type": "market",
        "lots": 0.01,
        "comment": "LL-Demo",
        "magic": 9001,
        "deviation_pips": 2.0,
    }
    result = await svc.order_send(**order_payload)
    # order_send returns protobuf OrderSendData object
    if hasattr(result, "ticket"):
        ticket = int(result.ticket)
    elif hasattr(result, "Ticket"):
        ticket = int(result.Ticket)
    elif isinstance(result, dict):
        ticket = int(result.get("ticket") or result.get("Ticket") or result.get("order") or result.get("Order"))
    else:
        ticket = int(result)
    show_order_result(ticket, f"Market BUY opened on {symbol}, lots={order_payload['lots']}", ok=True)

    # helper: search order by ticket
    async def find_order(tk: int) -> Any | None:
        result = await svc.opened_orders()
        # opened_orders returns protobuf object with order_infos field
        if hasattr(result, "order_infos"):
            orders = result.order_infos
        else:
            orders = result if isinstance(result, list) else []

        for o in orders:
            # Handle both protobuf objects and dicts
            if hasattr(o, "ticket"):
                t = o.ticket
            elif hasattr(o, "Ticket"):
                t = o.Ticket
            elif isinstance(o, dict):
                t = o.get("ticket") or o.get("Ticket") or o.get("order") or o.get("Order")
            else:
                continue
            try:
                if int(t) == tk:
                    return o
            except Exception:
                pass
        return None

    # wait until it appears in opened (≤5s)
    import time
    t0 = time.monotonic()
    while time.monotonic() - t0 < 5.0:
        if await find_order(ticket):
            break
        await asyncio.sleep(0.2)

    # b) modify SL
    q = await svc.quote(symbol)
    # quote returns protobuf object with bid/ask fields
    bid = float(q.bid) if hasattr(q, "bid") else float(q.get("bid", 0))
    ask = float(q.ask) if hasattr(q, "ask") else float(q.get("ask", 0))
    mid = (bid + ask) / 2.0
    sl_price = mid - 0.0010
    await svc.order_modify(ticket=ticket, sl_price=sl_price, tp_price=None)
    show_order_result(ticket, f"Stop Loss modified to {sl_price:.5f}", ok=True)

    # c) close
    await svc.order_close_delete(ticket=ticket)
    show_order_result(ticket, "Closed successfully", ok=True)

    print(f"\n{BOLD}{FG_GREEN}[LOW-LEVEL DEMO FINISHED]{RESET}")
    print(f"{FG_YELLOW}Note:{RESET} For STREAMS demo (on_symbol_tick, on_trade), run main_streams.py")
    
#endregion


# ════════════════════════════════════
# region ENTRY POINT  ▶️                                                  
# ════════════════════════════════════

async def amain() -> None:
    print(f"\n{BOLD}{FG_CYAN}{'='*76}")
    print(f"{'MT4 LOW-LEVEL API DEMO':^76}")
    print(f"{'='*76}{RESET}")

    conf = load_settings("appsettings.json")

    # build account
    acc = build_low_level(conf)

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
                print(f"  {FG_YELLOW}Attempting:{RESET} {host_port}")
                parts = host_port.split(":")
                host = parts[0]
                port = int(parts[1]) if len(parts) > 1 else 443

                await acc.connect_by_host_port(
                    host=host,
                    port=port,
                    base_chart_symbol=base_symbol,
                    timeout_seconds=timeout_seconds,
                )
                print(f"  {FG_GREEN}[OK]{RESET} Connected to {host}:{port}")
                connected = True
                break
            except Exception as e:
                print(f"  {FG_RED}[FAIL]{RESET} {host_port}: {e}")
                continue

    # PRIORITY 2: Connect by server name (ConnectEx)
    if not connected:
        server_name = os.getenv("MT4_SERVER", conf["mt4"].get("server_name"))
        if server_name:
            print(f"\n{BOLD}[PRIORITY 2]{RESET} Trying connection by server name")
            print(f"  {FG_CYAN}Server:{RESET} {server_name}")
            print(f"  {FG_CYAN}Base Symbol:{RESET} {base_symbol}")
            print(f"  {FG_CYAN}Timeout:{RESET} {timeout_seconds}s")

            try:
                await acc.connect_by_server_name(
                    server_name=server_name,
                    base_chart_symbol=base_symbol,
                    timeout_seconds=timeout_seconds,
                )
                print(f"  {FG_GREEN}[OK]{RESET} Connected via server name")
                connected = True
            except Exception as e:
                print(f"  {FG_RED}[FAIL]{RESET} Failed to connect by server name: {e}")

    # PRIORITY 3: Environment variables fallback
    if not connected:
        env_host = os.getenv("MT4_HOST")
        env_port = os.getenv("MT4_PORT")

        if env_host and env_port:
            print(f"\n{BOLD}[PRIORITY 3]{RESET} Trying connection via environment variables")
            print(f"  {FG_CYAN}Host:{RESET} {env_host}")
            print(f"  {FG_CYAN}Port:{RESET} {env_port}")

            try:
                await acc.connect_by_host_port(
                    host=env_host,
                    port=int(env_port),
                    base_chart_symbol=base_symbol,
                    timeout_seconds=timeout_seconds,
                )
                print(f"  {FG_GREEN}[OK]{RESET} Connected via environment variables")
                connected = True
            except Exception as e:
                print(f"  {FG_RED}[FAIL]{RESET} Failed to connect via env: {e}")

    if not connected:
        raise RuntimeError(f"{FG_RED}Failed to connect using all available methods (appsettings.json, server_name, .env){RESET}")

    print(f"\n{BOLD}{FG_GREEN}[CONNECTED]{RESET}")
    print(f"  {FG_CYAN}Terminal ID:{RESET} {acc.id}")

    svc = MT4Service(acc)

    print(f"\n{BOLD}{FG_GREEN}[START LOW-LEVEL DEMO]{RESET} {datetime.now().isoformat(timespec='seconds')}")
    await run_low_level_demo(svc, conf)
    print(f"\n{BOLD}{FG_GREEN}[ALL DONE]{RESET}")


if __name__ == "__main__":
    try:
        asyncio.run(amain())
    except KeyboardInterrupt:
        print(f"\n{FG_YELLOW}[INTERRUPTED]{RESET}")
    except Exception as e:
        print(f"\n{BOLD}{FG_RED}[FATAL ERROR]{RESET} {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()


#endregion

# Command to run:
# python main_low_level.py

"""
╔══════════════════════════════════════════════════════════════════════════════╗
║ FILE main_low_level.py — LOW-LEVEL MT4 API DEMO (direct MT4Account control)  ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ Purpose:                                                                     ║
║   Demonstrate direct, raw MT4Account usage with manual connection handling   ║
║   and sequential low-level RPC operations with formatted output.             ║
║                                                                              ║
║ Step-by-step behavior:                                                       ║
║   1) Prepare PYTHONPATH (adds package/, app/, project root).                 ║
║   2) Load config (appsettings.json) + ENV overrides.                         ║
║   3) Create MT4Account(user, password, grpc_server).                         ║
║   4) Connect using priorities: appsettings host:port → server_name → ENV.    ║
║   5) Wrap account into MT4Service for async calls.                           ║
║   6) Demo workflow: reconnect → account_summary → symbols/quotes →           ║
║      opened_orders + orders_history → order_send → order_modify → close.     ║
║                                                                              ║
║ Public API / Entry Points:                                                   ║
║   - amain() — main async entrypoint                                          ║
║   - run_low_level_demo(svc, conf) — low-level call sequence                  ║
║   - build_low_level(conf) — construct MT4Account with ENV support            ║
║                                                                              ║
║ Dependencies used in this file:                                              ║
║   - MetaRpcMT4.mt4_account.MT4Account                                        ║
║   - app.MT4Service.MT4Service                                                ║
║   - app.Helper.Design.Low_Level_Styling.* (UI formatting helpers)            ║
║                                                                              ║
║ Config & ENV references:                                                     ║
║   - appsettings.json → mt4.login, mt4.password, mt4.access[],                ║
║                         mt4.server_name, mt4.base_symbol, timeout            ║
║   - ENV → MT4_LOGIN, MT4_PASSWORD, GRPC_SERVER,                              ║
║            MT4_SERVER, MT4_HOST, MT4_PORT                                    ║
║                                                                              ║
║ RPC used during demo:                                                        ║
║   - Read: account_summary, symbols, symbol_params_many,                      ║
║           quote, quote_many, opened_orders, orders_history                   ║
║   - Trading: order_send, order_modify, order_close_delete                    ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""