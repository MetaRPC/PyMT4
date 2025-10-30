# app/Helper/console_ui.py
# Terminal UI helpers for pretty printing MT4 data (colors, tables, sorting)


from __future__ import annotations
import os
import sys
from typing import Any, Iterable, Sequence

# ── Colors (with Windows support) ───────────────────────────────────────────
USE_COLOR = True
USE_UNICODE_BOXES = True

try:
    # On Windows, enable ANSI via colorama
    import colorama  # type: ignore
    colorama.just_fix_windows_console()
    # Check if we can use Unicode box characters on Windows
    if sys.platform == "win32":
        # Try to set console to UTF-8
        try:
            # For Windows 10+, set console code page to UTF-8
            if hasattr(sys.stdout, 'reconfigure'):
                sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            # Fall back to ASCII boxes if UTF-8 fails
            USE_UNICODE_BOXES = False
except Exception:
    # If colorama is not available, keep ANSI for *nix; allow disabling via ENV
    pass

if os.getenv("NO_COLOR"):
    USE_COLOR = False

def _c(code: str) -> str:
    return code if USE_COLOR else ""

RESET = _c("\x1b[0m")
BOLD  = _c("\x1b[1m")
DIM   = _c("\x1b[2m")

FG_GREEN = _c("\x1b[32m")
FG_RED   = _c("\x1b[31m")
FG_CYAN  = _c("\x1b[36m")
FG_YELLOW= _c("\x1b[33m")
FG_GRAY  = _c("\x1b[90m")

# Box drawing characters (with ASCII fallback)
if USE_UNICODE_BOXES:
    BOX_TL = "┌"  # top-left
    BOX_TR = "┐"  # top-right
    BOX_BL = "└"  # bottom-left
    BOX_BR = "┘"  # bottom-right
    BOX_H  = "─"  # horizontal
    BOX_V  = "│"  # vertical
    BOX_VR = "├"  # vertical-right
    BOX_VL = "┤"  # vertical-left
    BOX_VH = "┼"  # vertical-horizontal
else:
    BOX_TL = "+"
    BOX_TR = "+"
    BOX_BL = "+"
    BOX_BR = "+"
    BOX_H  = "-"
    BOX_V  = "|"
    BOX_VR = "+"
    BOX_VL = "+"
    BOX_VH = "+"

def color_num(x: float, pos=FG_GREEN, neg=FG_RED, zero=FG_GRAY) -> str:
    if x > 0:
        return pos
    if x < 0:
        return neg
    return zero

def fmt_money(x: float, currency: str | None = None) -> str:
    s = f"{x:,.2f}"
    return f"{s} {currency}" if currency else s

# ── Safe attribute/dict access ──────────────────────────────────────────────
def get(o: Any, name: str, default: Any = None) -> Any:
    if hasattr(o, name):
        return getattr(o, name)
    if isinstance(o, dict):
        return o.get(name, default)
    return default

# ── Account Summary ─────────────────────────────────────────────────────────
def show_account_summary(acc: Any) -> None:
    """
    Pretty account block with colors and quick PnL stats.
    """
    login     = int(get(acc, "account_login", 0))
    bal       = float(get(acc, "account_balance", 0.0))
    eq        = float(get(acc, "account_equity", 0.0))
    cur       = str(get(acc, "account_currency", ""))
    lev       = int(get(acc, "account_leverage", 0))
    broker    = str(get(acc, "account_company_name", ""))
    floating  = eq - bal
    dd_pct    = (floating / bal * 100) if bal else 0.0

    c = color_num(floating)
    print()
    print(f"{BOX_TL}{BOX_H} {BOLD}ACCOUNT SUMMARY{RESET} {BOX_H*44}{BOX_TR}")
    print(f"{BOX_V} Login     : {login:<51}{BOX_V}")
    print(f"{BOX_V} Broker    : {broker:<51}{BOX_V}")
    print(f"{BOX_V} Currency  : {cur:<51}{BOX_V}")
    print(f"{BOX_V} Leverage  : 1:{lev:<48}{BOX_V}")
    print(f"{BOX_V} Balance   : {fmt_money(bal, cur):<51}{BOX_V}")
    print(f"{BOX_V} Equity    : {fmt_money(eq, cur):<51}{BOX_V}")
    print(f"{BOX_V} Floating  : {c}{fmt_money(floating, cur)} ({dd_pct:+.2f}%){RESET}{' '*(51-len(fmt_money(floating, cur))-len(f'({dd_pct:+.2f}%)')-1)}{BOX_V}")
    print(f"{BOX_BL}{BOX_H*63}{BOX_BR}")

# ── Quotes table ────────────────────────────────────────────────────────────
def show_quotes_table(quotes: Sequence[Any] | Any) -> None:
    """
    Render quotes for multiple symbols (bid/ask/spread).
    Quotes can be proto objects, dicts, or QuoteManyData object.
    """
    # Handle QuoteManyData or similar objects with quotes field
    if hasattr(quotes, "quotes"):
        quotes = quotes.quotes
    elif hasattr(quotes, "Quotes"):
        quotes = quotes.Quotes
    elif not isinstance(quotes, (list, tuple)):
        # Try to convert to list
        try:
            quotes = list(quotes)
        except TypeError:
            # Single quote object
            quotes = [quotes]

    print()
    print(f"{BOX_TL}{BOX_H} {BOLD}QUOTES{RESET} {BOX_H*56}{BOX_TR}")
    print(f"{BOX_V} Symbol {BOX_V}     Bid     {BOX_V}     Ask     {BOX_V}  Spread   {BOX_V}")
    print(f"{BOX_VR}{BOX_H*8}{BOX_VH}{BOX_H*13}{BOX_VH}{BOX_H*13}{BOX_VH}{BOX_H*11}{BOX_VL}")
    for q in quotes:
        sym  = str(get(q, "symbol", "")).upper()
        bid  = float(get(q, "bid", 0.0))
        ask  = float(get(q, "ask", 0.0))
        spr  = abs(ask - bid)
        print(f"{BOX_V} {sym:6s} {BOX_V} {bid:12.5f}{BOX_V} {ask:12.5f}{BOX_V} {spr:9.5f} {BOX_V}")
    print(f"{BOX_BL}{BOX_H*8}{BOX_H}{BOX_H*13}{BOX_H}{BOX_H*13}{BOX_H}{BOX_H*11}{BOX_BR}")

# ── Open positions table (sorted by Profit) ────────────────────────────────
def _iter_open_positions(opened_obj: Any) -> Iterable[Any]:
    if hasattr(opened_obj, "order_infos"):
        return opened_obj.order_infos
    if isinstance(opened_obj, dict) and "order_infos" in opened_obj:
        return opened_obj["order_infos"]
    if isinstance(opened_obj, list):
        return opened_obj
    return []

def show_positions_table(opened_obj: Any, *, top: int | None = None, reverse: bool = True) -> None:
    """
    Show opened positions sorted by profit.
    reverse=True -> highest profit first (descending).
    """
    items = list(_iter_open_positions(opened_obj))
    items.sort(key=lambda o: float(get(o, "profit", 0.0)), reverse=reverse)
    if top is not None:
        items = items[:top]

    print()
    print(f"{BOX_TL}{BOX_H} {BOLD}OPEN POSITIONS (sorted by profit){RESET} {BOX_H*27}{BOX_TR}")
    print(f"{BOX_V}   Ticket   {BOX_V} Symbol {BOX_V}  Lots  {BOX_V}    Price    {BOX_V}   Profit   {BOX_V}")
    print(f"{BOX_VR}{BOX_H*12}{BOX_VH}{BOX_H*8}{BOX_VH}{BOX_H*8}{BOX_VH}{BOX_H*13}{BOX_VH}{BOX_H*12}{BOX_VL}")
    for o in items:
        ticket = int(get(o, "ticket", 0))
        sym    = str(get(o, "symbol", "")).upper()
        lots   = float(get(o, "lots", 0.0))
        price  = float(get(o, "open_price", 0.0))
        profit = float(get(o, "profit", 0.0))
        c = color_num(profit)
        print(f"{BOX_V} {ticket:10d} {BOX_V} {sym:6s} {BOX_V} {lots:6.2f} {BOX_V} {price:11.5f} {BOX_V} {c}{profit:10.2f}{RESET} {BOX_V}")
    print(f"{BOX_BL}{BOX_H*12}{BOX_H}{BOX_H*8}{BOX_H}{BOX_H*8}{BOX_H}{BOX_H*13}{BOX_H}{BOX_H*12}{BOX_BR}")

# ── Single order result line ────────────────────────────────────────────────
def show_order_result(ticket: int, text: str, ok: bool = True) -> None:
    if USE_UNICODE_BOXES:
        mark = f"{FG_GREEN}✓{RESET}" if ok else f"{FG_RED}✗{RESET}"
    else:
        mark = f"{FG_GREEN}[OK]{RESET}" if ok else f"{FG_RED}[FAIL]{RESET}"
    print(f"{mark} ORDER #{ticket}: {text}")

# ── History orders table ────────────────────────────────────────────────────
def _iter_history_orders(hist_obj: Any) -> Iterable[Any]:
    """Extract history orders from various response types."""
    if hasattr(hist_obj, "orders_info"):
        return hist_obj.orders_info
    elif isinstance(hist_obj, dict) and "orders_info" in hist_obj:
        return hist_obj["orders_info"]
    elif isinstance(hist_obj, list):
        return hist_obj
    return []

def show_history_table(hist_obj: Any, *, top: int | None = None) -> None:
    """
    Show closed/history orders with key details.
    Shows: ticket, symbol, lots, open/close prices, profit, close time
    """
    items = list(_iter_history_orders(hist_obj))
    if top is not None:
        items = items[:top]

    print()
    print(f"{BOX_TL}{BOX_H} {BOLD}HISTORY ORDERS{RESET} {BOX_H*87}{BOX_TR}")
    print(f"{BOX_V}   Ticket   {BOX_V} Symbol {BOX_V} Lots  {BOX_V}  Open Price  {BOX_V} Close Price {BOX_V}   Profit   {BOX_V} Comment        {BOX_V}")
    print(f"{BOX_VR}{BOX_H*12}{BOX_VH}{BOX_H*8}{BOX_VH}{BOX_H*7}{BOX_VH}{BOX_H*13}{BOX_VH}{BOX_H*13}{BOX_VH}{BOX_H*12}{BOX_VH}{BOX_H*16}{BOX_VL}")

    for o in items:
        ticket = int(get(o, "ticket", 0))
        sym    = str(get(o, "symbol", "N/A")).upper()
        lots   = float(get(o, "lots", 0.0))
        open_p = float(get(o, "open_price", 0.0))
        close_p= float(get(o, "close_price", 0.0))
        profit = float(get(o, "profit", 0.0))
        comment= str(get(o, "comment", ""))[:14]  # truncate to 14 chars

        c = color_num(profit)

        # Format prices based on symbol (crypto vs forex)
        if "BTC" in sym or "ETH" in sym:
            open_str = f"{open_p:11.2f}" if open_p else "     -     "
            close_str= f"{close_p:11.2f}" if close_p else "     -     "
        else:
            open_str = f"{open_p:11.5f}" if open_p else "     -     "
            close_str= f"{close_p:11.5f}" if close_p else "     -     "

        print(f"{BOX_V} {ticket:10d} {BOX_V} {sym:6s} {BOX_V} {lots:5.2f} {BOX_V} {open_str} {BOX_V} {close_str} {BOX_V} {c}{profit:10.2f}{RESET} {BOX_V} {comment:14s} {BOX_V}")

    print(f"{BOX_BL}{BOX_H*12}{BOX_H}{BOX_H*8}{BOX_H}{BOX_H*7}{BOX_H}{BOX_H*13}{BOX_H}{BOX_H*13}{BOX_H}{BOX_H*12}{BOX_H}{BOX_H*16}{BOX_BR}")

    if items:
        total_profit = sum(float(get(o, "profit", 0.0)) for o in items)
        c_total = color_num(total_profit)
        print(f"  {BOLD}Total shown:{RESET} {len(items)} orders, P/L: {c_total}{total_profit:+.2f}{RESET}")


"""
Low-level functions for beautiful MT4 data output to the console.
Supports color output (ANSI) with automatic adaptation for Windows via colorama.
Uses Unicode characters to draw tables with automatic fallback to ASCII.
Main functions: show_account_summary() — account information, show_quotes_table() — quotes,
show_positions_table() — open positions sorted by profit, show_history_table() — trade history.
Can automatically extract data from Protobuf objects, dictionaries, and lists.
Colors are configured using the NO_COLOR environment variable to disable color output.
"""
