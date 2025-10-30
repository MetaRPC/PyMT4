# main_trade_mod.py — TRADE MOD API DEMO (MT4ServiceTrade shortcuts)
# Intermediate level: shortcuts + defaults + rate-limiting, NO pips/sugar
from __future__ import annotations
import sys
from pathlib import Path

# ─── PATHS & SYS.INIT  ───────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent
PKG = ROOT / "package"
APP = ROOT / "app"
for p in [str(PKG), str(APP), str(ROOT)]:
    if p not in sys.path:
        sys.path.insert(0, p)

# ─── IMPORTS  ────────────────────────────────────────────────────────────────────
import asyncio
import json
from typing import Any
from datetime import datetime

from MetaRpcMT4.mt4_account import MT4Account
from app.MT4Service import MT4Service
from app.MT4Service_Trade_mod import MT4ServiceTrade
from app.Helper.Design.Trade_Mod_Styling import (
    show_defaults,
    show_trade_result,
    show_modify_result,
    show_close_result,
    show_positions_summary,
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

# ══════════════════════════════
# region WIRING  🔌
# ══════════════════════════════

def build_account(conf: dict) -> MT4Account:
    """Create MT4Account using settings and ENV overrides."""
    mt4 = conf["mt4"]

    import os
    user = int(os.getenv("MT4_LOGIN", mt4["login"]))
    password = os.getenv("MT4_PASSWORD", mt4["password"])
    grpc_server = os.getenv("GRPC_SERVER", conf.get("grpc", {}).get("server", "mt4.mrpc.pro:443"))

    print(f"\n{BOLD}[CONFIG]{RESET}")
    print(f"  {FG_CYAN}GRPC Server:{RESET} {grpc_server}")
    print(f"  {FG_CYAN}User:{RESET} {user}")
    print(f"  {FG_CYAN}Password:{RESET} {'*' * len(password)}")

    return MT4Account(user=user, password=password, grpc_server=grpc_server)

#endregion

# ═════════════════════════
# region DEMO  🎯
# ═════════════════════════

async def run_trade_mod_demo(svc: MT4Service, conf: dict) -> None:
    """Демонстрация MT4ServiceTrade - промежуточный уровень с шорткатами."""

    demo = conf.get("demo", {})
    symbol: str = demo.get("symbol", "EURUSD")
    test_lots: float = demo.get("test_lots", 0.02)  # Changed from 0.01 to support partial close

    # Создаём Trade wrapper
    trade = MT4ServiceTrade(svc)

    # ── 1) Установка дефолтов ────────────────────────────────────────────────
    hdr("[TRADE_MOD] SET DEFAULTS")
    print(f"{FG_YELLOW}Setting trade defaults: magic=8001, deviation=2.0 pips, comment='TradeMod-Demo'{RESET}")

    trade.set_trade_defaults(
        magic=8001,
        deviation_pips=2.0,
        comment="TradeMod-Demo"
    )

    # Показываем установленные дефолты
    show_defaults(trade._defaults)

    # ── 2) Market Orders ──────────────────────────────────────────────────────
    hdr("[TRADE_MOD] MARKET ORDERS")
    print(f"{FG_YELLOW}Opening BUY MARKET order...{RESET}")

    # Получаем текущую цену для расчёта SL/TP
    quote = await svc.quote(symbol)
    ask = float(quote.ask)
    bid = float(quote.bid)

    # BUY market с абсолютными SL/TP
    sl_price = bid - 0.0015  # 15 пипсов ниже
    tp_price = bid + 0.0050  # 50 пипсов выше

    ticket1 = await trade.buy_market(
        symbol=symbol,
        lots=test_lots,
        sl=sl_price,
        tp=tp_price
    )
    show_trade_result("BUY MARKET OPENED", ticket1, symbol, test_lots, ask)

    # ── 3) Modify Order ───────────────────────────────────────────────────────
    hdr("[TRADE_MOD] MODIFY ORDER")
    print(f"{FG_YELLOW}Modifying Stop Loss to 10 pips...{RESET}")

    new_sl = bid - 0.0010  # 10 пипсов
    await trade.modify_sl_tp(ticket=ticket1, sl_price=new_sl)
    show_modify_result(ticket1, sl=new_sl)

    # ── 4) Pending Orders ─────────────────────────────────────────────────────
    hdr("[TRADE_MOD] PENDING ORDERS")
    print(f"{FG_YELLOW}Placing BUY LIMIT order...{RESET}")

    limit_price = bid - 0.0010  # 10 пипсов ниже текущей цены
    ticket2 = await trade.buy_limit(
        symbol=symbol,
        price=limit_price,
        lots=test_lots,
        sl=limit_price - 0.0015,
        tp=limit_price + 0.0050
    )
    show_trade_result("BUY LIMIT PLACED", ticket2, symbol, test_lots, limit_price)

    # ── 5) Close Pending Order ────────────────────────────────────────────────
    print(f"\n{FG_YELLOW}Closing pending BUY LIMIT order...{RESET}")
    await trade.close(ticket=ticket2)
    show_close_result("ORDER CANCELLED", ticket2)

    # ── 6) Partial Close ──────────────────────────────────────────────────────
    hdr("[TRADE_MOD] PARTIAL CLOSE")
    print(f"{FG_YELLOW}Closing half of the position...{RESET}")

    partial_lots = test_lots / 2
    await trade.close_partial(ticket=ticket1, lots=partial_lots)
    show_close_result("PARTIAL CLOSE", ticket1, partial_lots)

    # ── 7) Full Close ─────────────────────────────────────────────────────────
    print(f"\n{FG_YELLOW}Closing remaining position...{RESET}")
    try:
        await trade.close(ticket=ticket1)
        show_close_result("ORDER CLOSED", ticket1)
    except Exception:
        # After partial close, the original ticket may be invalid
        # The remaining position gets a new ticket number
        print(f"{FG_YELLOW}Note: Original ticket {ticket1} no longer valid after partial close{RESET}")
        print(f"{FG_YELLOW}(This is expected MT4 behavior - remaining position has new ticket){RESET}")

    # ── 8) SELL Market ────────────────────────────────────────────────────────
    hdr("[TRADE_MOD] SELL MARKET & CLOSE_BY")
    print(f"{FG_YELLOW}Opening SELL MARKET order...{RESET}")

    ticket3 = await trade.sell_market(
        symbol=symbol,
        lots=test_lots,
        sl=ask + 0.0015,
        tp=ask - 0.0050
    )
    show_trade_result("SELL MARKET OPENED", ticket3, symbol, test_lots, bid)

    print(f"\n{FG_YELLOW}Opening opposite BUY MARKET order...{RESET}")
    ticket4 = await trade.buy_market(
        symbol=symbol,
        lots=test_lots
    )
    show_trade_result("BUY MARKET OPENED", ticket4, symbol, test_lots, ask)

    # Close by opposite
    print(f"\n{FG_YELLOW}Closing tickets {ticket3} and {ticket4} by opposite...{RESET}")
    try:
        await trade.close_by(ticket_a=ticket3, ticket_b=ticket4)
        print(f"{FG_GREEN}✓ Orders closed by opposite{RESET}")
    except Exception as e:
        # If close_by is not supported, close individually
        print(f"{FG_YELLOW}close_by not supported, closing individually...{RESET}")
        await trade.close(ticket=ticket3)
        await trade.close(ticket=ticket4)
        print(f"{FG_GREEN}✓ Orders closed individually{RESET}")

    # ── 9) View Current Positions ─────────────────────────────────────────────
    hdr("[TRADE_MOD] CURRENT POSITIONS")
    positions = await svc.opened_orders()

    if hasattr(positions, 'order_infos'):
        positions_list = list(positions.order_infos)
    elif hasattr(positions, 'orders'):
        positions_list = list(positions.orders)
    elif hasattr(positions, 'Orders'):
        positions_list = list(positions.Orders)
    elif isinstance(positions, list):
        positions_list = positions
    else:
        positions_list = []

    # Convert protobuf to dict for display
    positions_dicts = []
    for pos in positions_list:
        if hasattr(pos, 'ticket'):
            positions_dicts.append({
                'Ticket': pos.ticket,
                'Symbol': pos.symbol,
                'Lots': pos.lots,
                'OpenPrice': pos.open_price,
                'Profit': pos.profit
            })
        elif hasattr(pos, 'Ticket'):
            positions_dicts.append({
                'Ticket': pos.Ticket,
                'Symbol': pos.Symbol,
                'Lots': pos.Lots,
                'OpenPrice': pos.OpenPrice,
                'Profit': pos.Profit
            })

    show_positions_summary(positions_dicts)

    print(f"\n{BOLD}{FG_GREEN}[TRADE_MOD DEMO FINISHED]{RESET}")

#endregion

# ══════════════════════════════
# region MAIN  🚀
# ══════════════════════════════

async def amain():
    print(f"{BOLD}{FG_CYAN}{'=' * 76}")
    print(f"                   MT4 TRADE MOD API DEMO                   ")
    print(f"{'=' * 76}{RESET}")

    conf = load_settings("appsettings.json")
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

    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    print(f"\n{BOLD}{FG_GREEN}[START TRADE_MOD DEMO]{RESET} {now}")

    await run_trade_mod_demo(svc, conf)

    print(f"\n{BOLD}{FG_GREEN}[ALL DONE]{RESET}")

if __name__ == "__main__":
    asyncio.run(amain())

#endregion

# 
