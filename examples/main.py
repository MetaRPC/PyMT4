"""
==============================================================================
 PyMT4 examples - single entry point

 Run the interactive menu:
     cd examples
     python main.py

 Or run one example directly (by number or name):
     python main.py general      python main.py 1
     python main.py trading      python main.py 2
     python main.py streaming    python main.py 3

 Each example connects using examples/0_common/settings.json.
==============================================================================
"""

import asyncio
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "0_common"))
sys.path.insert(0, os.path.join(HERE, "..", "package"))

# Print UTF-8 regardless of the console code page (Windows consoles default to
# cp1251/cp866 and would crash on box-drawing characters otherwise).
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


# (number, [aliases], group, title, folder, filename)
REGISTRY = [
    (1,  ["general", "gen", "lowlevel01"],   "LOW-LEVEL (direct gRPC · MT4Account)", "General (read-only) operations", "1_lowlevel", "01_general_operations.py"),
    (2,  ["trading", "trade", "lowlevel02"],  "LOW-LEVEL (direct gRPC · MT4Account)", "Trading operations",            "1_lowlevel", "02_trading_operations.py"),
    (3,  ["streaming", "stream", "lowlevel03"],"LOW-LEVEL (direct gRPC · MT4Account)", "Streaming methods",            "1_lowlevel", "03_streaming_methods.py"),

    (4,  ["service", "service04"],             "MID-LEVEL (MT4Service)",               "Service — all methods",         "2_service",  "04_service_demo.py"),

    (6,  ["sugar", "basics", "sugar06"],       "HIGH-LEVEL (MT4Sugar)",                "Sugar basics",                  "3_sugar",    "06_sugar_basics.py"),
    (7,  ["sugar07", "sugartrading"],          "HIGH-LEVEL (MT4Sugar)",                "Sugar trading",                 "3_sugar",    "07_sugar_trading.py"),
    (8,  ["sugar08", "positions"],             "HIGH-LEVEL (MT4Sugar)",                "Sugar positions",               "3_sugar",    "08_sugar_positions.py"),

    (11, ["market", "orch11"],                 "ORCHESTRATORS (strategies)",           "Market one-shot",               "4_orchestrators", "11_market_one_shot.py"),
    (12, ["trailing", "orch12"],               "ORCHESTRATORS (strategies)",           "Bracket + trailing activation", "4_orchestrators", "12_bracket_trailing.py"),
    (13, ["grid", "dca", "orch13"],            "ORCHESTRATORS (strategies)",           "Grid DCA (common SL)",          "4_orchestrators", "13_grid_dca.py"),
    (14, ["oco", "straddle", "orch14"],        "ORCHESTRATORS (strategies)",           "OCO straddle (breakout)",       "4_orchestrators", "14_oco_straddle.py"),
    (15, ["pending", "orch15"],                "ORCHESTRATORS (strategies)",           "Pending bracket",               "4_orchestrators", "15_pending_bracket.py"),
    (16, ["presets", "preset"],                "PRESETS",                              "Strategy & risk presets",       "4_orchestrators", "16_presets.py"),

    (17, ["usercode", "user", "sandbox"],      "USER CODE",                            "Your sandbox",                  "5_usercode", "17_usercode.py"),

    (18, ["inspect", "protobuf"],              "TOOLS",                                "Protobuf inspector (offline)",  "0_common",   "16_protobuf_inspector.py"),
]


def _load(folder, filename):
    """Import an example module by path, or return None if it doesn't exist yet."""
    path = os.path.join(HERE, folder, filename)
    if not os.path.exists(path):
        return None
    name = f"{folder}.{filename[:-3]}".replace(".", "_")
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
        return mod
    except Exception as e:  # pragma: no cover - defensive
        print(f"  [WARN] failed to import {folder}/{filename}: {e}")
        return None


def _resolve(token):
    """Map a CLI token (number or alias) to a REGISTRY row."""
    token = str(token).strip().lower()
    for row in REGISTRY:
        num, aliases = row[0], row[1]
        if token == str(num) or token in aliases:
            return row
    return None


async def _run_row(row):
    num, aliases, group, title, folder, filename = row
    mod = _load(folder, filename)
    if mod is None:
        print(f"\n[!] '{title}' is not available yet ({folder}/{filename}).")
        return
    entry = (getattr(mod, "main", None) or getattr(mod, "run", None)
             or getattr(mod, "run_protobuf_inspector", None))
    if entry is None:
        print(f"\n[!] {folder}/{filename} has no entry point.")
        return
    result = entry()
    if asyncio.iscoroutine(result):
        await result


def print_menu():
    print()
    print("╔════════════════════════════════════════════════════════════════════╗")
    print("║                 PyMT4 — MetaTrader 4 gRPC examples                   ║")
    print("╚════════════════════════════════════════════════════════════════════╝")
    last_group = None
    for num, aliases, group, title, folder, filename in REGISTRY:
        if group != last_group:
            print(f"\n  {group}")
            last_group = group
        ready = os.path.exists(os.path.join(HERE, folder, filename))
        mark = "" if ready else "   (coming soon)"
        alias = aliases[0]
        print(f"    [{num:>2}] {title:<32} → python main.py {alias}{mark}")
    print("\n     [q] Quit")
    print()


async def interactive():
    while True:
        print_menu()
        try:
            choice = input("  Select: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if choice in ("q", "quit", "exit", "0"):
            break
        row = _resolve(choice)
        if row is None:
            print(f"\n[!] Unknown choice: {choice!r}")
            continue
        try:
            await _run_row(row)
        except KeyboardInterrupt:
            print("\n[!] interrupted")
        input("\n  Press Enter to return to the menu...")


async def main():
    args = sys.argv[1:]
    if not args:
        await interactive()
        return
    row = _resolve(args[0])
    if row is None:
        print(f"[!] Unknown example: {args[0]!r}\n")
        print_menu()
        return
    await _run_row(row)


if __name__ == "__main__":
    asyncio.run(main())
