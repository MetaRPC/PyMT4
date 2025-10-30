# app/Helper/Design/Stream_Styling.py
# Pretty console UI for MT4 streams (ticks, trades): colors, rate meter, compact rows.

from __future__ import annotations
import os
import sys
import time
from typing import Any

# ── Colors ──────────────────────────────────────────────────────────────────
USE_COLOR = True
USE_UNICODE = True

try:
    import colorama  # type: ignore
    colorama.just_fix_windows_console()
    if sys.platform == "win32":
        try:
            if hasattr(sys.stdout, 'reconfigure'):
                sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            USE_UNICODE = False
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
FG_MG = _c("\x1b[35m")

# ── Utils ───────────────────────────────────────────────────────────────────
def get(o: Any, name: str, default: Any=None) -> Any:
    if hasattr(o, name): return getattr(o, name)
    if isinstance(o, dict): return o.get(name, default)
    return default

def header(title: str, emoji: str = "📡") -> None:
    """Print a styled header with emoji and separator line."""
    if USE_UNICODE:
        line = "─" * max(0, 64 - len(title) - len(emoji) - 2)
    else:
        line = "-" * max(0, 64 - len(title) - 2)
    emoji_str = emoji if USE_UNICODE else ""
    print(f"\n{BOLD}{FG_CY}{emoji_str} {title}{RESET} {FG_GR}{line}{RESET}")
    sys.stdout.flush()

# ── Rate meter (events/sec) ─────────────────────────────────────────────────
class RateMeter:
    """Rolling events/sec meter for streams."""
    def __init__(self, window: float = 3.0):
        self.win = window
        self.buf: list[float] = []

    def hit(self) -> float:
        now = time.monotonic()
        self.buf.append(now)
        cutoff = now - self.win
        while self.buf and self.buf[0] < cutoff:
            self.buf.pop(0)
        span = max(1e-9, (self.buf[-1] - self.buf[0]))
        rate = (len(self.buf)-1) / span if len(self.buf) > 1 else 0.0
        return rate

# ── Row renderers ───────────────────────────────────────────────────────────
def fmt_tick(e: Any) -> str:
    """Format tick event for display."""
    sym = str(get(e, "symbol", "?")).upper()
    bid = get(e, "bid", None)
    ask = get(e, "ask", None)
    time_obj = get(e, "time", None)

    # Handle time as protobuf object or string
    if time_obj and hasattr(time_obj, "seconds"):
        tm = f"{time_obj.seconds}"
    else:
        tm = str(time_obj) if time_obj else "?"

    if bid is None or ask is None:
        return f"  {FG_CY}●{RESET} {sym:8s} │ {FG_GR}bid=? ask=?{RESET}"

    bid_f = float(bid)
    ask_f = float(ask)
    spr = abs(ask_f - bid_f)

    # Color spread based on value
    spr_color = FG_GN if spr < 0.0001 else (FG_YL if spr < 0.0005 else FG_RD)

    return f"  {FG_CY}●{RESET} {BOLD}{sym:8s}{RESET} │ bid={FG_MG}{bid_f:.5f}{RESET} │ ask={FG_CY}{ask_f:.5f}{RESET} │ spread={spr_color}{spr:.5f}{RESET}"

def fmt_trade(e: Any) -> str:
    """Format trade event for display."""
    tk   = get(e, "order", get(e, "ticket", "?"))
    et   = get(e, "type", get(e, "event_type", "?"))
    sym  = str(get(e, "symbol", "?")).upper()
    lots = get(e, "volume", get(e, "lots", None))
    pft  = get(e, "profit", None)

    # Format type
    type_str = str(et).replace("TRADE_TRANSACTION_", "").replace("_", " ")

    # Color profit
    c = FG_GN if (isinstance(pft, (int,float)) and pft >= 0) else FG_RD

    # Build components
    lots_s = f" │ {float(lots):.2f} lots" if lots is not None else ""
    pft_s  = f" │ P/L: {c}{float(pft):+.2f}{RESET}" if pft is not None else ""

    return f"  {FG_YL}▶{RESET} #{BOLD}{tk}{RESET} │ {FG_CY}{type_str:20s}{RESET} │ {sym:8s}{lots_s}{pft_s}"

# ── Stream banners & summaries ──────────────────────────────────────────────
def subscribe_banner(kind: str, detail: str, limit_sec: float, limit_events: int):
    """Display subscription banner."""
    print(f"{DIM}► Subscribing to {FG_CY}{kind}{RESET}{DIM} ({detail})")
    print(f"  Waiting for {FG_YL}{limit_sec:.0f}s{RESET}{DIM} or {FG_YL}{limit_events}{RESET}{DIM} events...{RESET}")
    sys.stdout.flush()

def stream_summary(kind: str, n: int, rate: float):
    """Display stream completion summary."""
    rate_s = f"{FG_YL}{rate:.2f} ev/s{RESET}" if rate > 0 else f"{FG_GR}{rate:.2f} ev/s{RESET}"
    icon = "✓" if USE_UNICODE else "[OK]"
    print(f"\n{FG_GN}{icon}{RESET} {BOLD}Received {n} {kind.lower()}{RESET}  │  Rate: {rate_s}")
    sys.stdout.flush()


"""
Utilities for beautifully displaying MT4 streaming data (ticks, trades) in the console.
RateMeter — a class for measuring event rate (events/sec) with a 3-second sliding window.
fmt_tick() — formatting tick data with bid/ask/spread and spread color highlighting.
fmt_trade() — formatting trading events (order opening/closing) with profit/loss.
header() — beautiful section headers with emoji and a separator line.
subscribe_banner() and stream_summary() — subscription banners and stream summary statistics.
Supports Unicode characters with fallback to ASCII and color output with Windows support via colorama.
"""
