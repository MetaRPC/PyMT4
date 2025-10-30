# main_streams.py - MT4 STREAMS DEMO (on_symbol_tick, on_trade)
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
from app.Helper.Design.Stream_Styling import (
    header,
    RateMeter,
    fmt_tick,
    fmt_trade,
    subscribe_banner,
    stream_summary,
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

async def bounded_stream(agen, *, max_seconds: float = 5.0, max_events: int = 10, printer=None) -> list:
    """Reads the async generator no longer than max_seconds and no more than max_events."""
    out = []
    start = asyncio.get_event_loop().time()

    async def stream_reader():
        try:
            async for item in agen:
                out.append(item)
                if printer:
                    printer(item)
                if len(out) >= max_events:
                    break
                if (asyncio.get_event_loop().time() - start) >= max_seconds:
                    break
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"[stream aborted] {e}")

    try:
        await asyncio.wait_for(stream_reader(), timeout=max_seconds)
    except asyncio.TimeoutError:
        pass

    return out


# ══════════════════════════════
# region WIRING  🔌                                                         
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

# ═════════════════════════
#  region STREAMS
# ═════════════════════════
async def run_streams_demo(svc: MT4Service, conf: dict) -> None:
    """STREAMS Demonstration: on_symbol_tick, on_trade"""
    demo = conf.get("demo", {})
    symbol: str = demo.get("symbol", "EURUSD")

    # 1) on_symbol_tick - stream ticks by symbol
    header("TICK STREAM", "📊")
    subscribe_banner("ticks", symbol, 5.0, 10)

    rate_meter = RateMeter()

    def tick_printer(e):
        try:
            # Extract symbol_tick if it exists (nested structure)
            tick_data = e
            if hasattr(e, "symbol_tick"):
                tick_data = e.symbol_tick
            elif isinstance(e, dict) and "symbol_tick" in e:
                tick_data = e["symbol_tick"]

            # Use the styled formatter
            rate_meter.hit()
            print(fmt_tick(tick_data))
            sys.stdout.flush()
        except Exception as ex:
            print(f"  {FG_RD}[tick parse error]: {ex}{RESET}")
            print(f"  raw: {e}")
            sys.stdout.flush()

    ticks = await bounded_stream(
        svc.on_symbol_tick(symbol),
        max_seconds=5.0,
        max_events=10,
        printer=tick_printer,
    )
    final_rate = rate_meter.hit() if ticks else 0.0
    stream_summary("TICKS", len(ticks), final_rate)

    # 2) on_trade - streaming of trading events
    header("TRADE STREAM", "💼")
    subscribe_banner("trade events", "all symbols", 5.0, 10)
    print(f"  {FG_YL}Note:{RESET} Events will appear when orders are opened/modified/closed\n")

    trade_rate_meter = RateMeter()

    def trade_printer(e):
        try:
            # Extract trade data if nested
            trade_data = e
            if hasattr(e, "trade_transaction"):
                trade_data = e.trade_transaction
            elif isinstance(e, dict) and "trade_transaction" in e:
                trade_data = e["trade_transaction"]

            # Use the styled formatter
            trade_rate_meter.hit()
            print(fmt_trade(trade_data))
            sys.stdout.flush()
        except Exception as ex:
            print(f"  {FG_RD}[trade parse error]: {ex}{RESET}")
            print(f"  raw: {e}")
            sys.stdout.flush()

    trades = await bounded_stream(
        svc.on_trade(),
        max_seconds=5.0,
        max_events=10,
        printer=trade_printer,
    )
    trade_final_rate = trade_rate_meter.hit() if trades else 0.0
    stream_summary("TRADE EVENTS", len(trades), trade_final_rate)

    # 3) on_opened_orders_tickets - open order ticket stream
    header("OPENED ORDERS TICKETS STREAM", "🎫")
    subscribe_banner("order tickets", "all", 5.0, 10)
    print(f"  {FG_YL}Note:{RESET} Monitors list of open order tickets\n")

    tickets_rate_meter = RateMeter()

    def tickets_printer(e):
        try:
            tickets_rate_meter.hit()
            if hasattr(e, "position_tickets"):
                tickets_list = list(e.position_tickets) if e.position_tickets else []
                pending_list = list(e.pending_tickets) if hasattr(e, "pending_tickets") and e.pending_tickets else []
                print(f"  {FG_CY}[Tickets]{RESET} Positions: {FG_GN}{len(tickets_list)}{RESET}, Pending: {FG_YL}{len(pending_list)}{RESET}")
                if tickets_list[:3]:
                    print(f"    → {tickets_list[:3]}")
            else:
                print(f"  {FG_CY}[Tickets]{RESET} {e}")
            sys.stdout.flush()
        except Exception as ex:
            print(f"  {FG_RD}[tickets parse error]: {ex}{RESET}")
            sys.stdout.flush()

    tickets_data = await bounded_stream(
        svc.on_opened_orders_tickets(pull_interval_milliseconds=500),
        max_seconds=5.0,
        max_events=10,
        printer=tickets_printer,
    )
    tickets_final_rate = tickets_rate_meter.hit() if tickets_data else 0.0
    stream_summary("ORDER TICKETS", len(tickets_data), tickets_final_rate)

    # 4) on_opened_orders_profit - profit stream on open orders
    header("OPENED ORDERS PROFIT STREAM", "💰")
    subscribe_banner("profit updates", "all", 5.0, 10)
    print(f"  {FG_YL}Note:{RESET} Real-time profit/loss updates\n")

    profit_rate_meter = RateMeter()

    def profit_printer(e):
        try:
            profit_rate_meter.hit()
            if hasattr(e, "account_info"):
                acc = e.account_info
                profit = getattr(acc, "profit", 0.0)
                equity = getattr(acc, "equity", 0.0)
                balance = getattr(acc, "balance", 0.0)
                margin_level = getattr(acc, "margin_level", 0.0)
                color = FG_GN if profit >= 0 else FG_RD
                print(f"  {FG_CY}[Account]{RESET} Balance: {FG_GN}{balance:.2f}{RESET} │ Equity: {FG_CY}{equity:.2f}{RESET} │ P/L: {color}{profit:.2f}{RESET} │ ML: {margin_level:.2f}%")

                # Show count of updated positions
                if hasattr(e, "opened_orders_with_profit_updated"):
                    count = len(list(e.opened_orders_with_profit_updated))
                    print(f"    → Updated {count} positions")
            else:
                print(f"  {FG_CY}[Profit]{RESET} {e}")
            sys.stdout.flush()
        except Exception as ex:
            print(f"  {FG_RD}[profit parse error]: {ex}{RESET}")
            sys.stdout.flush()

    profit_data = await bounded_stream(
        svc.on_opened_orders_profit(timer_period_milliseconds=1000),
        max_seconds=5.0,
        max_events=10,
        printer=profit_printer,
    )
    profit_final_rate = profit_rate_meter.hit() if profit_data else 0.0
    stream_summary("PROFIT UPDATES", len(profit_data), profit_final_rate)

    print(f"\n{BOLD}{FG_GN}[STREAMS DEMO FINISHED]{RESET}")

#endregion


# ════════════════════════════════════
# region ENTRY POINT  ▶️                                                  
# ════════════════════════════════════

async def amain() -> None:
    print(f"\n{BOLD}{FG_CY}{'='*76}")
    print(f"{'MT4 STREAMS API DEMO':^76}")
    print(f"{'='*76}{RESET}")

    conf = load_settings("appsettings.json")

    # build account
    acc = build_account(conf)

    import os
    base_symbol = conf["mt4"].get("base_symbol", "EURUSD")
    timeout_seconds = max(300, int(conf["mt4"].get("timeout_seconds", 120)))

    #PRIORITY 1: Direct connection via host:port from appsettings.json
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

    print(f"\n{BOLD}{FG_GN}[START STREAMS DEMO]{RESET} {datetime.now().isoformat(timespec='seconds')}")
    await run_streams_demo(svc, conf)
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
# python main_streams.py

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                    PROCESS MANAGEMENT CHEAT SHEET (Windows)                  ║
# ╠══════════════════════════════════════════════════════════════════════════════╣
# ║ Kill by PID (Process ID):                                                    ║
# ║   taskkill /F /PID <process_id>                                              ║
# ║   Example: taskkill /F /PID 12345                                            ║
# ╠──────────────────────────────────────────────────────────────────────────────╣
# ║ Kill all Python processes:                                                   ║
# ║   taskkill /F /IM python.exe                                                 ║
# ╠──────────────────────────────────────────────────────────────────────────────╣
# ║ Find Python processes:                                                       ║
# ║   tasklist | findstr python                                                  ║
# ║   (or PowerShell): Get-Process python                                        ║
# ╠──────────────────────────────────────────────────────────────────────────────╣
# ║ Graceful shutdown (without /F):                                              ║
# ║   taskkill /PID <process_id>                                                 ║
# ╠──────────────────────────────────────────────────────────────────────────────╣
# ║ PowerShell alternative:                                                      ║
# ║   Stop-Process -Id <process_id> -Force                                       ║
# ║   Stop-Process -Name python -Force                                           ║
# ╠──────────────────────────────────────────────────────────────────────────────╣
# ║ Interrupt running script:                                                    ║
# ║   Press Ctrl+C in the terminal window                                        ║
# ╠══════════════════════════════════════════════════════════════════════════════╣
# ║ Flags: /F = Force, /IM = Image Name, /PID = Process ID                       ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

"""
╔══════════════════════════════════════════════════════════════════════════════╗
║ FILE main_streams.py — MT4 STREAMS DEMO (on_symbol_tick, on_trade)           ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ Purpose:                                                                     ║
║   Demonstrate streaming APIs for MT4: live tick feed per symbol and          ║
║   trade-event feed, with bounded consumption and formatted console output.   ║
║                                                                              ║
║ Step-by-step behavior:                                                       ║
║   1) Prepare PYTHONPATH (adds package/, app/, project root).                 ║
║   2) Load config (appsettings.json) + ENV overrides.                         ║
║   3) Create MT4Account(user, password, grpc_server).                         ║
║   4) Connect using priorities: appsettings host:port → server_name → ENV.    ║
║   5) Wrap account into MT4Service for async calls.                           ║
║   6) TICK stream: subscribe via svc.on_symbol_tick(symbol),                  ║
║      consume with bounded_stream(max_seconds=5, max_events=10),              ║
║      pretty-print each tick (fmt_tick) and measure rate (RateMeter).         ║
║   7) TRADE stream: subscribe via svc.on_trade(), same bounded consumption,   ║
║      pretty-print trade events (fmt_trade) and measure rate.                 ║
║   8) TICKETS stream: subscribe via svc.on_opened_orders_tickets(),           ║
║      monitor list of open order tickets with 500ms polling interval.         ║
║   9) PROFIT stream: subscribe via svc.on_opened_orders_profit(),             ║
║      real-time profit/loss updates with 1000ms timer period.                 ║
║  10) Print per-stream summary (stream_summary) and finish.                   ║
║                                                                              ║
║ Public API / Entry Points:                                                   ║
║   - amain() — main async entrypoint                                          ║
║   - run_streams_demo(svc, conf) — orchestrates tick & trade streams          ║
║   - build_account(conf) — construct MT4Account with ENV support              ║
║   - bounded_stream(agen, *, max_seconds, max_events, printer) — helper       ║
║                                                                              ║
║ Dependencies used in this file:                                              ║
║   - MetaRpcMT4.mt4_account.MT4Account                                        ║
║   - app.MT4Service.MT4Service                                                ║
║   - app.Helper.Design.Stream_Styling:                                        ║
║       header, RateMeter, fmt_tick, fmt_trade, subscribe_banner,              ║
║       stream_summary, BOLD/RESET/FG_*                                        ║
║                                                                              ║
║ Config & ENV references:                                                     ║
║   - appsettings.json → mt4.login, mt4.password, mt4.access[],                ║
║                         mt4.server_name, mt4.base_symbol, timeout            ║
║   - ENV → MT4_LOGIN, MT4_PASSWORD, GRPC_SERVER,                              ║
║            MT4_SERVER, MT4_HOST, MT4_PORT                                    ║
║                                                                              ║
║ RPC used during demo (streams):                                              ║
║   - svc.on_symbol_tick(symbol) — live tick feed for a single symbol          ║
║   - svc.on_trade() — live trade/transaction events (all symbols)             ║
║   - svc.on_opened_orders_tickets() — live list of opened order tickets       ║
║   - svc.on_opened_orders_profit() — real-time profit/loss updates            ║
╚══════════════════════════════════════════════════════════════════════════════╝

"""