# app/Helper/Design/Sugar_Styling.py
# Pretty boxes for high-level (sugar) calls. Thick borders + colors.

from __future__ import annotations
import os
import sys
from typing import Iterable, Any

USE_COLOR = True
USE_UNICODE_BOXES = True

try:
    import colorama  # type: ignore
    colorama.just_fix_windows_console()
    # Check if we can use Unicode box characters on Windows
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

def _c(s: str) -> str: return s if USE_COLOR else ""

RESET = _c("\x1b[0m")
BOLD  = _c("\x1b[1m")
DIM   = _c("\x1b[2m")
FG_GR = _c("\x1b[90m")
FG_GN = _c("\x1b[32m")
FG_RD = _c("\x1b[31m")
FG_CY = _c("\x1b[36m")
FG_YL = _c("\x1b[33m")
FG_MG = _c("\x1b[35m")  # magenta

# ── Thick box drawing characters ─────────────────────────────────────────────
if USE_UNICODE_BOXES:
    TL, TR, BL, BR, H, V = "┏", "┓", "┗", "┛", "━", "┃"
    VR, VL, VH = "┣", "┫", "╋"
else:
    TL, TR, BL, BR, H, V = "+", "+", "+", "+", "=", "|"
    VR, VL, VH = "+", "+", "+"

def _line(len_: int) -> str:
    return H * len_

def _pad(s: str, width: int) -> str:
    # left-align text to given width (safe for ANSI stripped strings)
    vis = len(strip_ansi(s))
    return s + " " * max(0, width - vis)

def strip_ansi(s: str) -> str:
    import re
    return re.sub(r"\x1b\[[0-9;]*m", "", s)

def color_num(x: float) -> str:
    return FG_GN if x >= 0 else FG_RD

def box(title: str, lines: Iterable[str], *, emoji: str = "", width: int | None = None) -> None:
    """Render a thick-bordered box with a title and content lines."""
    title_text = f"{BOLD}{emoji} {title}{RESET}" if emoji else f"{BOLD}{title}{RESET}"
    content = list(lines) if not isinstance(lines, str) else [lines]
    # compute width by the longest visible line among title & content
    base = [strip_ansi(title_text)] + [strip_ansi(s) for s in content]
    w = max(len(s) for s in base) + 2  # inner padding
    if width: w = max(w, width)

    print(f"{TL}{_line(w+2)}{TR}")
    print(f"{V} {_pad(title_text, w)} {V}")
    print(f"{V} {_pad(FG_GR + _line(w) + RESET, w)} {V}")
    for s in content:
        print(f"{V} {_pad(s, w)} {V}")
    print(f"{BL}{_line(w+2)}{BR}")

def kv(key: str, val: Any) -> str:
    return f"{FG_CY}{key}{RESET}: {val}"

def ok(text: str) -> str:
    return f"{FG_GN}✅ {text}{RESET}"

def fail(text: str) -> str:
    return f"{FG_RD}❌ {text}{RESET}"

def money(x: float, cur: str | None = None) -> str:
    s = f"{x:,.2f}"
    return f"{s} {cur}" if cur else s

def num(x: float, prec: int = 5) -> str:
    try:
        return f"{float(x):.{prec}f}"
    except Exception:
        return str(x)

def row(*cols: Any, sep: str = "  |  ") -> str:
    return sep.join(str(c) for c in cols)

# ══════════════════════════════════════════════════════════════════════════════
# SUGAR-SPECIFIC DISPLAY FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def show_connectivity_status(is_alive: bool, terminal_id: str = None) -> None:
    """Display connectivity status in a box."""
    status = f"{FG_GN}ONLINE{RESET}" if is_alive else f"{FG_RD}OFFLINE{RESET}"
    lines = [
        kv("Status", status),
    ]
    if terminal_id:
        lines.append(kv("Terminal ID", terminal_id[:36]))
    box("CONNECTIVITY", lines, emoji="🔗", width=60)

def show_symbol_info(symbol: str, digits: int, point: float, pip_size: float,
                     spread: float, mid: float, bid: float, ask: float) -> None:
    """Display symbol information in a box."""
    lines = [
        kv("Symbol", f"{BOLD}{symbol}{RESET}"),
        kv("Digits", digits),
        kv("Point", f"{point:.{digits}f}"),
        kv("Pip Size", f"{pip_size:.{digits}f}"),
        "",
        kv("Spread", f"{FG_YL}{spread:.1f} pips{RESET}"),
        kv("Mid Price", f"{mid:.5f}"),
        kv("Bid", f"{FG_CY}{bid:.5f}{RESET}"),
        kv("Ask", f"{FG_MG}{ask:.5f}{RESET}"),
    ]
    box("SYMBOL INFO & PRICING", lines, emoji="📊", width=60)

def show_risk_calc(symbol: str, risk_percent: float, stop_pips: float,
                   calc_lots: float, lots: float, cash_risk: float) -> None:
    """Display risk calculation in a box."""
    lines = [
        kv("Symbol", symbol),
        kv("Risk", f"{FG_YL}{risk_percent:.1f}%{RESET}"),
        kv("Stop Loss", f"{stop_pips:.1f} pips"),
        "",
        kv("Calculated Lots", f"{BOLD}{calc_lots:.2f}{RESET}"),
        kv("Test Lots", f"{lots:.2f}"),
        kv("Cash Risk", f"{FG_RD}${cash_risk:.2f}{RESET}"),
    ]
    box("RISK & LOT SIZING", lines, emoji="⚖️", width=60)

def show_exposure(exposure: dict) -> None:
    """Display exposure summary in a box."""
    lines = []

    # Total exposure
    total = exposure.get("total", {})
    lines.append(f"{BOLD}TOTAL EXPOSURE:{RESET}")
    lines.append(kv("  Open Lots", f"{total.get('lots', 0):.2f}"))
    lines.append(kv("  Open Value", f"${total.get('value', 0):,.2f}"))
    lines.append(kv("  Floating P/L", f"{color_num(total.get('profit', 0))}${total.get('profit', 0):+,.2f}{RESET}"))
    lines.append("")

    # By symbol
    by_symbol = exposure.get("by_symbol", {})
    if by_symbol:
        lines.append(f"{BOLD}BY SYMBOL:{RESET}")
        for sym, data in list(by_symbol.items())[:5]:  # top 5
            profit = data.get('profit', 0)
            lines.append(f"  {FG_CY}{sym:8s}{RESET}: {data.get('lots', 0):5.2f} lots, P/L: {color_num(profit)}{profit:+8.2f}{RESET}")

    box("EXPOSURE SUMMARY", lines, emoji="💼", width=70)

def show_order_result(action: str, ticket: int, symbol: str = None,
                      lots: float = None, price: float = None, ok: bool = True) -> None:
    """Display order operation result."""
    mark = f"{FG_GN}✓{RESET}" if ok else f"{FG_RD}✗{RESET}"
    if not USE_UNICODE_BOXES:
        mark = f"{FG_GN}[OK]{RESET}" if ok else f"{FG_RD}[FAIL]{RESET}"

    parts = [f"{BOLD}{action.upper()}{RESET}"]
    if symbol:
        parts.append(f"{symbol}")
    if lots:
        parts.append(f"{lots:.2f} lots")
    if price:
        parts.append(f"@ {price:.5f}")

    print(f"{mark} Ticket #{FG_CY}{ticket}{RESET}: {' '.join(parts)}")

def show_positions_value(positions: dict) -> None:
    """Display positions value summary."""
    if not positions:
        print(f"{FG_GR}No positions to display{RESET}")
        return

    lines = []
    for sym, data in positions.items():
        # Handle both dict and numeric values
        if isinstance(data, dict):
            profit = data.get('profit', 0)
            lots = data.get('lots', 0)
        else:
            # If data is just a number (profit value)
            profit = float(data) if data else 0
            lots = 0
        lines.append(f"{FG_CY}{sym:8s}{RESET}: {lots:5.2f} lots, P/L: {color_num(profit)}{profit:+8.2f}{RESET}")

    box("POSITIONS VALUE", lines, emoji="📈", width=60)

def show_diagnostic_snapshot(snapshot: dict) -> None:
    """Display diagnostic snapshot in a box."""
    lines = []

    # Account info
    acc = snapshot.get("account", {})
    lines.append(f"{BOLD}ACCOUNT:{RESET}")
    lines.append(kv("  Balance", f"${acc.get('balance', 0):,.2f}"))
    lines.append(kv("  Equity", f"${acc.get('equity', 0):,.2f}"))
    lines.append(kv("  Margin Free", f"${acc.get('margin_free', 0):,.2f}"))
    lines.append("")

    # Exposure
    exp = snapshot.get("exposure", {}).get("total", {})
    lines.append(f"{BOLD}EXPOSURE:{RESET}")
    lines.append(kv("  Open Lots", f"{exp.get('lots', 0):.2f}"))
    lines.append(kv("  Floating P/L", f"{color_num(exp.get('profit', 0))}${exp.get('profit', 0):+,.2f}{RESET}"))
    lines.append("")

    # Orders count
    lines.append(kv("Open Orders", snapshot.get("open_orders_count", 0)))
    lines.append("")

    # Spreads
    spreads = snapshot.get("spreads", {})
    if spreads:
        lines.append(f"{BOLD}SPREADS:{RESET}")
        for sym, spread in list(spreads.items())[:5]:
            # Handle both numeric and dict spread values
            spread_val = float(spread) if not isinstance(spread, dict) else float(spread.get('pips', 0))
            lines.append(f"  {FG_CY}{sym:8s}{RESET}: {spread_val:.1f} pips")

    box("DIAGNOSTIC SNAPSHOT", lines, emoji="🔍", width=70)


"""
Functions for visually displaying high-level MT4Sugar operations in the console.
Uses thick borders to highlight important information.
box() is a universal function for drawing frames with a title and content.
show_connectivity_status() — terminal connection status, show_symbol_info() — symbol information.
show_risk_calc() — risk and lot size calculation, show_exposure() — open position summary.
show_order_result() — trade result (open/close), show_diagnostic_snapshot() — account diagnostics.
Supports Unicode frames with fallback to ASCII and color output via ANSI with Windows support.
"""
