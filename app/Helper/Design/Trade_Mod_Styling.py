# app/Helper/Design/Trade_Mod_Styling.py
# Styling for MT4Service_Trade_mod - intermediate level between Low-Level and Sugar

from __future__ import annotations
import os
import sys
from typing import Any, Sequence

# ── Colors & UTF-8 Support ──────────────────────────────────────────────────
USE_COLOR = True
USE_UNICODE_BOXES = True

try:
    import colorama  # type: ignore
    colorama.just_fix_windows_console()
    if sys.platform == "win32":
        try:
            if hasattr(sys.stdout, 'reconfigure'):
                sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            USE_UNICODE_BOXES = False
except Exception:
    pass

if os.getenv("NO_COLOR"):
    USE_COLOR = False

def _c(s: str) -> str:
    return s if USE_COLOR else ""

# ANSI codes
RESET = _c("\x1b[0m")
BOLD = _c("\x1b[1m")
DIM = _c("\x1b[2m")
FG_GREEN = _c("\x1b[32m")
FG_RED = _c("\x1b[31m")
FG_YELLOW = _c("\x1b[33m")
FG_CYAN = _c("\x1b[36m")
FG_MAGENTA = _c("\x1b[35m")
FG_GRAY = _c("\x1b[90m")

# Box drawing
if USE_UNICODE_BOXES:
    BOX_TL = "╔"  # top-left
    BOX_TR = "╗"  # top-right
    BOX_BL = "╚"  # bottom-left
    BOX_BR = "╝"  # bottom-right
    BOX_H  = "═"  # horizontal
    BOX_V  = "║"  # vertical
    BOX_LT = "╟"  # left T
    BOX_RT = "╢"  # right T
    BOX_CROSS = "╬"  # cross
else:
    BOX_TL = "+"
    BOX_TR = "+"
    BOX_BL = "+"
    BOX_BR = "+"
    BOX_H  = "="
    BOX_V  = "|"
    BOX_LT = "+"
    BOX_RT = "+"
    BOX_CROSS = "+"

# ── Helper Functions ────────────────────────────────────────────────────────
def show_defaults(defaults: dict) -> None:
    """Display trade defaults configuration."""
    width = 62
    print(f"\n{BOX_TL}{BOX_H * (width - 2)}{BOX_TR}")
    print(f"{BOX_V} {BOLD}TRADE DEFAULTS{RESET}{' ' * (width - 17)}{BOX_V}")
    print(f"{BOX_LT}{BOX_H * (width - 2)}{BOX_RT}")

    magic = defaults.get("magic", "Not set")
    deviation = defaults.get("deviation_pips", "Not set")
    comment = defaults.get("comment", "Not set")

    print(f"{BOX_V} {FG_CYAN}Magic Number:{RESET} {magic:<46}{BOX_V}")
    print(f"{BOX_V} {FG_CYAN}Deviation (pips):{RESET} {deviation:<42}{BOX_V}")
    print(f"{BOX_V} {FG_CYAN}Comment:{RESET} {comment:<50}{BOX_V}")
    print(f"{BOX_BL}{BOX_H * (width - 2)}{BOX_BR}")

def show_trade_result(operation: str, ticket: int, symbol: str = "", lots: float = 0.0, price: float = 0.0) -> None:
    """Display trade operation result."""
    width = 62
    print(f"\n{BOX_TL}{BOX_H * (width - 2)}{BOX_TR}")
    print(f"{BOX_V} {FG_GREEN}✓{RESET} {BOLD}{operation}{RESET}{' ' * (width - len(operation) - 6)}{BOX_V}")
    print(f"{BOX_LT}{BOX_H * (width - 2)}{BOX_RT}")
    print(f"{BOX_V} {FG_CYAN}Ticket:{RESET} #{FG_YELLOW}{ticket}{RESET}{' ' * (width - 10 - len(str(ticket)))}{BOX_V}")

    if symbol:
        print(f"{BOX_V} {FG_CYAN}Symbol:{RESET} {symbol}{' ' * (width - 10 - len(symbol))}{BOX_V}")
    if lots > 0:
        print(f"{BOX_V} {FG_CYAN}Lots:{RESET} {lots:.2f}{' ' * (width - 8 - len(f'{lots:.2f}'))}{BOX_V}")
    if price > 0:
        print(f"{BOX_V} {FG_CYAN}Price:{RESET} {price:.5f}{' ' * (width - 9 - len(f'{price:.5f}'))}{BOX_V}")

    print(f"{BOX_BL}{BOX_H * (width - 2)}{BOX_BR}")

def show_modify_result(ticket: int, sl: float = None, tp: float = None) -> None:
    """Display modification result."""
    width = 62
    print(f"\n{BOX_TL}{BOX_H * (width - 2)}{BOX_TR}")
    print(f"{BOX_V} {FG_GREEN}✓{RESET} {BOLD}ORDER MODIFIED{RESET}{' ' * (width - 18)}{BOX_V}")
    print(f"{BOX_LT}{BOX_H * (width - 2)}{BOX_RT}")
    print(f"{BOX_V} {FG_CYAN}Ticket:{RESET} #{FG_YELLOW}{ticket}{RESET}{' ' * (width - 10 - len(str(ticket)))}{BOX_V}")

    if sl is not None:
        print(f"{BOX_V} {FG_CYAN}Stop Loss:{RESET} {sl:.5f}{' ' * (width - 14 - len(f'{sl:.5f}'))}{BOX_V}")
    if tp is not None:
        print(f"{BOX_V} {FG_CYAN}Take Profit:{RESET} {tp:.5f}{' ' * (width - 16 - len(f'{tp:.5f}'))}{BOX_V}")

    print(f"{BOX_BL}{BOX_H * (width - 2)}{BOX_BR}")

def show_close_result(operation: str, ticket: int, lots: float = None) -> None:
    """Display close operation result."""
    width = 62
    print(f"\n{BOX_TL}{BOX_H * (width - 2)}{BOX_TR}")
    print(f"{BOX_V} {FG_GREEN}✓{RESET} {BOLD}{operation}{RESET}{' ' * (width - len(operation) - 6)}{BOX_V}")
    print(f"{BOX_LT}{BOX_H * (width - 2)}{BOX_RT}")
    print(f"{BOX_V} {FG_CYAN}Ticket:{RESET} #{FG_YELLOW}{ticket}{RESET}{' ' * (width - 10 - len(str(ticket)))}{BOX_V}")

    if lots is not None:
        print(f"{BOX_V} {FG_CYAN}Closed Lots:{RESET} {lots:.2f}{' ' * (width - 15 - len(f'{lots:.2f}'))}{BOX_V}")

    print(f"{BOX_BL}{BOX_H * (width - 2)}{BOX_BR}")

def show_positions_summary(positions: list) -> None:
    """Display current positions summary."""
    if not positions:
        print(f"\n{FG_GRAY}No open positions{RESET}")
        return

    width = 76
    print(f"\n{BOX_TL}{BOX_H * (width - 2)}{BOX_TR}")
    print(f"{BOX_V} {BOLD}CURRENT POSITIONS{RESET}{' ' * (width - 20)}{BOX_V}")
    print(f"{BOX_LT}{BOX_H * (width - 2)}{BOX_RT}")

    # Header
    header = f"{BOX_V}   Ticket   │ Symbol │  Lots  │    Price    │   Profit   {BOX_V}"
    print(header)
    print(f"{BOX_LT}{BOX_H * (width - 2)}{BOX_RT}")

    # Rows
    for pos in positions[:10]:  # Limit to 10 positions
        ticket = pos.get('Ticket', pos.get('ticket', '?'))
        symbol = pos.get('Symbol', pos.get('symbol', '?'))
        lots = float(pos.get('Lots', pos.get('lots', 0)))
        price = float(pos.get('OpenPrice', pos.get('open_price', 0)))
        profit = float(pos.get('Profit', pos.get('profit', 0)))

        profit_color = FG_GREEN if profit >= 0 else FG_RED
        row = f"{BOX_V}  {ticket:>9} │ {symbol:<6} │ {lots:>6.2f} │ {price:>11.5f} │ {profit_color}{profit:>10.2f}{RESET} {BOX_V}"
        print(row)

    print(f"{BOX_BL}{BOX_H * (width - 2)}{BOX_BR}")


"""
Styling functions for the intermediate level MT4Service_Trade_mod.
Uses double-line borders to visually differentiate from the Low_Level and Sugar styles.
show_defaults() — displays default settings (magic number, deviation, comment).
show_trade_result() — order opening/placing result with details (ticket, symbol, lots, price).
show_modify_result() — order modification result (SL/TP change).
show_close_result() — order closing result with closed volume information.
show_positions_summary() — table of current open positions (up to 10) with profit/loss.
Supports Unicode double lines with fallback to ASCII and color output via colorama for Windows.
"""
