# -*- coding: utf-8 -*-
"""
PyMT4 - MetaTrader 4 gRPC Client Demonstration Runner
Entry point for running all PyMT4 examples.
"""

import sys
import os
import asyncio
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EXAMPLES_DIR = Path(__file__).resolve().parent

EXAMPLES = [
    {
        "id": "1",
        "name": "Low-level API Calls",
        "file": "Low_level_call.py",
        "desc": "Protobuf/MT4Account raw calls, quotes, history, streaming",
        "aliases": ["lowlevel", "low_level", "1"]
    },
    {
        "id": "2",
        "name": "High-level Sugar API",
        "file": "Call_sugar.py",
        "desc": "MT4Sugar convenient wrappers, risk calculation, pip SL/TP",
        "aliases": ["sugar", "2"]
    },
    {
        "id": "3",
        "name": "Strategy Orchestrators",
        "file": "Orchestrator_demo.py",
        "desc": "Automated order execution, trailing stops, bracket orders",
        "aliases": ["orchestrator", "orchestrators", "3"]
    },
    {
        "id": "4",
        "name": "Strategy & Risk Presets",
        "file": "Presets_demo.py",
        "desc": "Reusable risk profiles, ATR-based risk, session risk",
        "aliases": ["presets", "preset", "4"]
    }
]


def run_example(example_file: str) -> int:
    target = EXAMPLES_DIR / example_file
    print("\n" + "=" * 80)
    print(f"RUNNING: {example_file}")
    print("=" * 80 + "\n")
    proc = subprocess.run([sys.executable, str(target)], cwd=str(REPO_ROOT))
    return proc.returncode


def print_menu():
    print("=" * 80)
    print("PyMT4 - MetaTrader 4 gRPC Examples")
    print("=" * 80)
    for ex in EXAMPLES:
        print(f"  [{ex['id']}] {ex['name']} ({ex['file']})")
        print(f"      {ex['desc']}")
    print("  [A] Run All Examples sequentially")
    print("  [Q] Quit")
    print("=" * 80)


def main():
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower().strip()
        if arg in ["--all", "-a", "all", "a"]:
            for ex in EXAMPLES:
                code = run_example(ex["file"])
                if code != 0:
                    sys.exit(code)
            sys.exit(0)

        for ex in EXAMPLES:
            if arg in ex["aliases"] or arg == ex["file"].lower():
                code = run_example(ex["file"])
                sys.exit(code)

        print(f"Unknown example: {sys.argv[1]}")
        print("Usage: python main.py [1|2|3|4|all]")
        sys.exit(1)

    # Interactive mode or fallback
    if not sys.stdin.isatty():
        # Non-interactive environment, run all
        print("Non-interactive session detected: Running all examples...")
        for ex in EXAMPLES:
            code = run_example(ex["file"])
            if code != 0:
                sys.exit(code)
        sys.exit(0)

    print_menu()
    try:
        choice = input("Select an option: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        sys.exit(0)

    if choice in ["q", "quit", "exit"]:
        sys.exit(0)
    elif choice in ["a", "all"]:
        for ex in EXAMPLES:
            code = run_example(ex["file"])
            if code != 0:
                sys.exit(code)
    else:
        for ex in EXAMPLES:
            if choice == ex["id"] or choice in ex["aliases"]:
                code = run_example(ex["file"])
                sys.exit(code)
        print("Invalid selection.")
        sys.exit(1)


if __name__ == "__main__":
    main()
