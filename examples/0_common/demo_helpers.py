"""
Shared helpers for PyMT4 examples.

Provides:
  - load_settings()           - read examples/0_common/settings.json
  - create_and_connect_mt4()  - build MT4Account and connect to the terminal
  - small console print helpers (step / success / warning / info / error)

The helpers are self-contained so every example can just do:

    from demo_helpers import load_settings, create_and_connect_mt4, print_success
"""

import os
import sys
import json
from uuid import uuid4
from datetime import datetime, timedelta
from typing import Dict, Any

# Make the bundled MetaRpcMT4 package importable from anywhere under examples/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "package"))

# Print UTF-8 regardless of the console code page (Windows consoles default to
# cp1251/cp866 and would otherwise crash on box-drawing / arrow characters).
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from MetaRpcMT4.mt4_account import MT4Account  # noqa: E402

__all__ = [
    "load_settings",
    "create_and_connect_mt4",
    "print_separator",
    "print_step",
    "print_method",
    "print_success",
    "print_warning",
    "print_info",
    "print_error",
    "print_if_error",
    "fatal",
]

_SETTINGS = os.path.join(os.path.dirname(__file__), "settings.json")
_REQUIRED = ["user", "password", "grpc_server", "mt_cluster", "test_symbol"]

# A stable terminal id persisted between runs. Reusing the SAME id makes the
# gateway reuse ONE terminal instead of spawning a new one each run — which
# matters on a TRIAL key, where only one terminal per IP is allowed.
_TERMINAL_ID_FILE = os.path.join(os.path.dirname(__file__), ".terminal_id")


def _stable_terminal_id() -> str:
    try:
        if os.path.exists(_TERMINAL_ID_FILE):
            tid = open(_TERMINAL_ID_FILE, encoding="utf-8").read().strip()
            if tid:
                return tid
    except Exception:
        pass
    tid = str(uuid4())
    try:
        open(_TERMINAL_ID_FILE, "w", encoding="utf-8").write(tid)
    except Exception:
        pass
    return tid


def load_settings() -> Dict[str, Any]:
    """Load configuration from examples/0_common/settings.json.

    Required keys: user, password, grpc_server, mt_cluster, test_symbol.
    Optional: api_key (falls back to MRPC_API_KEY env, then "TRIAL"),
              test_volume (default 0.01).
    """
    if not os.path.exists(_SETTINGS):
        raise FileNotFoundError(
            f"Settings file not found: {_SETTINGS}\n"
            "Create settings.json with your MT4 demo credentials, e.g.:\n"
            '{\n'
            '  "user": 12345678,\n'
            '  "password": "your_password",\n'
            '  "grpc_server": "mt4.mrpc.pro:443",\n'
            '  "mt_cluster": "MetaQuotes-Demo",\n'
            '  "test_symbol": "EURUSD"\n'
            '}'
        )

    with open(_SETTINGS, "r", encoding="utf-8") as f:
        settings = json.load(f)

    missing = [k for k in _REQUIRED if k not in settings or settings[k] in ("", None)]
    if missing:
        raise ValueError(f"Missing required fields in settings.json: {', '.join(missing)}")

    # Env vars win so a live key / alternate gateway can be supplied without
    # editing settings.json (which ships pointing at production with TRIAL).
    settings["api_key"] = os.getenv("MRPC_API_KEY") or settings.get("api_key") or "TRIAL"
    settings["grpc_server"] = os.getenv("MRPC_GRPC_SERVER") or settings["grpc_server"]
    settings["test_volume"] = settings.get("test_volume", 0.01)
    return settings


async def create_and_connect_mt4(config: Dict[str, Any]) -> MT4Account:
    """Create an MT4Account and connect to the terminal via its broker server name.

    Returns a connected MT4Account. Raises on failure.
    """
    timeout_seconds = int(config.get("timeout_seconds", 120))

    account = MT4Account(
        user=int(config["user"]),
        password=config["password"],
        grpc_server=config["grpc_server"],
        id_=_stable_terminal_id(),  # reuse one terminal across runs (TRIAL = 1/IP)
        api_key=config["api_key"],
    )

    print("Connecting to MT4 server...")
    print(f"  User:        {config['user']}")
    print(f"  gRPC Server: {config['grpc_server']}")
    print(f"  MT Cluster:  {config['mt_cluster']}")
    print(f"  API Key:     {config['api_key']}")
    print()

    # The gRPC call deadline defaults to 30s; pass an explicit deadline so a
    # slow first terminal spin-up still succeeds.
    await account.connect_by_server_name(
        server_name=config["mt_cluster"],
        base_chart_symbol=config["test_symbol"],
        timeout_seconds=timeout_seconds,
        deadline=datetime.utcnow() + timedelta(seconds=timeout_seconds),
    )

    print_success(f"Connected (terminal id: {str(account.id)[:8]}…)")
    print()
    return account


# -----------------------------------------------------------------------------
# console helpers
# -----------------------------------------------------------------------------

def print_separator(title: str = "", char: str = "─"):
    if title:
        print(f"\n{title}")
    print(char * 59)


def print_step(step_num: int, title: str):
    print(f"\n\nSTEP {step_num}: {title}")
    print("═" * 59)


def print_method(method_num: str, method_name: str, description: str):
    print(f"\n{method_num}. {method_name} - {description}")


def print_success(msg: str):
    print(f"  [OK] {msg}")


def print_warning(msg: str):
    print(f"  [WARN] {msg}")


def print_info(msg: str):
    print(f"  [i] {msg}")


def print_error(error: Exception, context: str = ""):
    print(f"  [ERROR] {context + ': ' if context else ''}{error}")


def print_if_error(error: Exception, context: str = ""):
    if error:
        print_error(error, context)


def fatal(error: Exception, message: str):
    print(f"[FAIL] FATAL: {message}")
    if error:
        print(f"   Error: {error}")
        raise error
    raise RuntimeError(message)
