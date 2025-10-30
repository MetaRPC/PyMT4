# examples/Orchestrator_demo.py
# -*- coding: utf-8 -*-
"""
ORCHESTRATOR DEMONSTRATION - Strategy orchestrators in action

This script demonstrates how to use strategy orchestrators that combine:
- Strategy presets (symbol, entry method, magic number)
- Risk presets (risk %, SL/TP in pips, trailing stop, breakeven)
- Market conditions guards (spread, session time)

Orchestrators shown:
1) market_one_shot - Simple market order with auto management
2) pending_bracket - Pending order with bracket management
3) spread_guard - Market order only if spread is acceptable
4) session_guard - Trade only during specified time windows

Each orchestrator encapsulates a complete trading scenario.
"""

import os
import sys
import asyncio
import json
from pathlib import Path
from datetime import datetime

# ---- Path bootstrap ----
REPO_ROOT = Path(__file__).resolve().parent.parent
PKG = REPO_ROOT / "package"
APP = REPO_ROOT / "app"
STRATEGY = REPO_ROOT / "Strategy"

for p in [str(PKG), str(APP), str(REPO_ROOT), str(STRATEGY)]:
    if p not in sys.path:
        sys.path.insert(0, p)

# ---- Imports ----
from MetaRpcMT4.mt4_account import MT4Account
from app.MT4Service import MT4Service

# Strategy presets
from Strategy.presets.strategy import StrategyPreset, MarketEURUSD, LimitEURUSD
from Strategy.presets.risk import RiskPreset, Conservative, Balanced, Aggressive, Scalper

# Orchestrators
from Strategy.orchestrator.market_one_shot import run_market_one_shot
from Strategy.orchestrator.pending_bracket import run_pending_bracket
from Strategy.orchestrator.spread_guard import market_with_spread_guard


def load_settings(path: str = "appsettings.json") -> dict:
    """Load settings from appsettings.json"""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def hdr(title: str) -> None:
    """Print section header"""
    print(f"\n{'=' * 80}")
    print(f"{title}")
    print(f"{'=' * 80}")


def show_result(title: str, result: dict) -> None:
    """Pretty print orchestrator result"""
    print(f"\n[{title}]")
    if isinstance(result, dict):
        for key, val in result.items():
            if key == "snapshot":
                print(f"  {key}: <diagnostic snapshot>")
            elif key == "subscriptions":
                print(f"  {key}: {list(val.keys()) if val else 'none'}")
            else:
                print(f"  {key}: {val}")
    else:
        print(f"  Result: {result}")


async def main():
    hdr("STRATEGY ORCHESTRATORS DEMONSTRATION")
    print("\nDemonstrates modular trading orchestrators:")
    print("  - Presets: Reusable strategy and risk configurations")
    print("  - Guards: Market condition filters (spread, session time)")
    print("  - Orchestrators: Complete trading scenarios")

    # ========= 1) Load settings and connect =========
    settings = load_settings()

    if not settings or "mt4" not in settings:
        print("\nError: appsettings.json not found or invalid")
        return

    # Extract credentials
    user = int(os.getenv("MT4_LOGIN", settings["mt4"].get("login", 0)))
    password = os.getenv("MT4_PASSWORD", settings["mt4"].get("password", ""))
    server_name = os.getenv("MT4_SERVER", settings["mt4"].get("server_name"))
    grpc_server = os.getenv("GRPC_SERVER", settings.get("grpc", {}).get("server", "mt4.mrpc.pro:443"))
    base_symbol = settings["mt4"].get("base_symbol", "EURUSD")
    timeout_seconds = settings["mt4"].get("timeout_seconds", 180)
    access_list = settings["mt4"].get("access", [])

    # Control flags
    enable_trading = os.getenv("ENABLE_TRADING", "0") == "1"
    demo_symbol = os.getenv("DEMO_SYMBOL", "EURUSD")

    print(f"\n[CONFIG]")
    print(f"  User: {user}")
    print(f"  Symbol: {demo_symbol}")
    print(f"  Trading: {'ENABLED' if enable_trading else 'DISABLED (dry run)'}")

    # ========= 2) Connect =========
    hdr("[1] CONNECTION")

    account = MT4Account(user=user, password=password, grpc_server=grpc_server)
    connected = False

    # Try connection (3-priority system)
    if access_list:
        print("\n[PRIORITY 1] Direct connection via host:port")
        for host_port in access_list:
            try:
                parts = host_port.split(":")
                host = parts[0]
                port = int(parts[1]) if len(parts) > 1 else 443
                await account.connect_by_host_port(
                    host=host, port=port,
                    base_chart_symbol=base_symbol,
                    timeout_seconds=timeout_seconds,
                )
                print(f"  [OK] Connected to {host}:{port}")
                connected = True
                break
            except Exception as e:
                print(f"  [FAIL] {host_port}: {e}")
                continue

    if not connected and server_name:
        print("\n[PRIORITY 2] Connection by server name")
        try:
            await account.connect_by_server_name(
                server_name=server_name,
                base_chart_symbol=base_symbol,
                wait_for_terminal_is_alive=True,
                timeout_seconds=timeout_seconds,
            )
            print(f"  [OK] Connected via {server_name}")
            connected = True
        except Exception as e:
            print(f"  [FAIL] {e}")

    if not connected:
        print("\n[ERROR] Failed to connect")
        return

    print(f"\n[CONNECTED] Terminal ID: {account.id}")

    # ========= 3) Create service =========
    svc = MT4Service(account)
    sugar = svc.sugar

    # ========= 4) Show available presets =========
    hdr("[2] AVAILABLE PRESETS")

    print("\n=== Strategy Presets ===")
    print("  MarketEURUSD:")
    print(f"    symbol={MarketEURUSD.symbol}, use_market={MarketEURUSD.use_market}")
    print(f"    magic={MarketEURUSD.magic}, comment='{MarketEURUSD.comment}'")

    print("\n  LimitEURUSD(price):")
    print("    Creates pending limit order at specified price")

    print("\n=== Risk Presets ===")
    print(f"  Conservative: risk={Conservative.risk_percent}%, SL={Conservative.sl_pips}p, TP={Conservative.tp_pips}p")
    print(f"  Balanced:     risk={Balanced.risk_percent}%, SL={Balanced.sl_pips}p, TP={Balanced.tp_pips}p")
    print(f"  Aggressive:   risk={Aggressive.risk_percent}%, SL={Aggressive.sl_pips}p, TP={Aggressive.tp_pips}p")
    print(f"  Scalper:      risk={Scalper.risk_percent}%, SL={Scalper.sl_pips}p, TP={Scalper.tp_pips}p, trailing={Scalper.trailing_pips}p")

    # ========= 5) ORCHESTRATOR DEMONSTRATIONS =========

    if not enable_trading:
        hdr("[3] ORCHESTRATOR DEMONSTRATIONS (DRY RUN)")
        print("\n⚠️  Trading is DISABLED. Showing syntax and structure only.\n")

        # Demo 1: Market One Shot
        print("=" * 80)
        print("[ORCHESTRATOR 1] market_one_shot")
        print("=" * 80)
        print("\nExecutes immediate market order with auto-management:")
        print("  - Opens market position")
        print("  - Sets up trailing stop (if configured)")
        print("  - Sets up auto-breakeven (if configured)")
        print("  - Returns diagnostic snapshot")

        print("\nUsage:")
        print("  strategy = MarketEURUSD")
        print("  risk = Balanced")
        print("  result = await run_market_one_shot(svc, strategy, risk)")
        print("\nReturns:")
        print("  {")
        print("    'ticket': 123456,")
        print("    'subscriptions': {'trailing': 'sub_id', 'auto_be': 'sub_id'},")
        print("    'filled': {'status': 'filled', 'ticket': 123456},")
        print("    'snapshot': <diagnostic data>")
        print("  }")

        # Demo 2: Pending Bracket
        print("\n" + "=" * 80)
        print("[ORCHESTRATOR 2] pending_bracket")
        print("=" * 80)
        print("\nPlaces pending order with bracket management:")
        print("  - Opens pending limit/stop order")
        print("  - Waits for fill (with timeout)")
        print("  - If filled: activates trailing stop & breakeven")
        print("  - If timeout: cancels pending order")

        print("\nUsage:")
        print("  current_price = await sugar.mid_price('EURUSD')")
        print("  pip_size = await sugar.pip_size('EURUSD')")
        print("  entry_price = current_price - (10 * pip_size)  # 10 pips below")
        print("  strategy = LimitEURUSD(price=entry_price)")
        print("  risk = Conservative")
        print("  result = await run_pending_bracket(svc, strategy, risk, timeout_s=900)")
        print("\nReturns (if filled):")
        print("  {")
        print("    'ticket': 123457,")
        print("    'filled': {'status': 'filled', ...},")
        print("    'subscriptions': {'trailing': 'sub_id'},")
        print("    'snapshot': <diagnostic data>")
        print("  }")
        print("\nReturns (if timeout):")
        print("  {")
        print("    'ticket': 123457,")
        print("    'status': 'cancelled_by_timeout'")
        print("  }")

        # Demo 3: Spread Guard
        print("\n" + "=" * 80)
        print("[ORCHESTRATOR 3] spread_guard")
        print("=" * 80)
        print("\nMarket order with spread protection:")
        print("  - Checks current spread")
        print("  - If spread > max_spread_pips: skips trade")
        print("  - If spread acceptable: executes market_one_shot")

        print("\nUsage:")
        print("  strategy = MarketEURUSD")
        print("  risk = Scalper")
        print("  result = await market_with_spread_guard(")
        print("      svc, strategy, risk,")
        print("      max_spread_pips=1.5  # Only trade if spread <= 1.5 pips")
        print("  )")
        print("\nReturns (if spread too high):")
        print("  {")
        print("    'status': 'skipped_due_to_spread',")
        print("    'spread_pips': 2.3")
        print("  }")
        print("\nReturns (if spread OK):")
        print("  <same as market_one_shot>")

        # Demo 4: Session Guard
        print("\n" + "=" * 80)
        print("[ORCHESTRATOR 4] session_guard")
        print("=" * 80)
        print("\nTime-based trading window protection:")
        print("  - Only trades during specified time windows")
        print("  - Supports multiple daily windows")
        print("  - Weekday filtering")
        print("  - Rollover buffer (avoid swap time)")

        print("\nUsage:")
        print("  from Strategy.orchestrator.session_guard import run_with_session_guard")
        print("")
        print("  # Define trading windows (HH:MM format)")
        print("  windows = [")
        print("      ('08:00', '11:30'),  # Morning session")
        print("      ('13:00', '17:00'),  # Afternoon session")
        print("  ]")
        print("")
        print("  # Wrap orchestrator in session guard")
        print("  async def my_strategy():")
        print("      strategy = MarketEURUSD")
        print("      risk = Balanced")
        print("      return await run_market_one_shot(svc, strategy, risk)")
        print("")
        print("  result = await run_with_session_guard(")
        print("      svc=svc,")
        print("      runner_coro_factory=my_strategy,")
        print("      windows=windows,")
        print("      tz='Europe/London',  # Timezone")
        print("      weekdays=[0,1,2,3,4],  # Mon-Fri only")
        print("      rollover_hhmm='23:00',  # Avoid rollover time")
        print("      rollover_buffer_min=30,  # +/- 30 min buffer")
        print("  )")
        print("\nReturns (if outside window):")
        print("  {")
        print("    'status': 'skipped_session_outside_window',")
        print("    'current_time': '07:45:00',")
        print("    'windows': [('08:00', '11:30'), ('13:00', '17:00')]")
        print("  }")
        print("\nReturns (if in rollover buffer):")
        print("  {")
        print("    'status': 'skipped_rollover_buffer',")
        print("    'current_time': '22:45:00'")
        print("  }")

    else:
        hdr("[3] EXECUTING ORCHESTRATORS (LIVE)")
        print("\n⚠️  TRADING IS ENABLED! Real orders will be placed!\n")

        # Create custom strategy for demo
        demo_strategy = StrategyPreset(
            symbol=demo_symbol,
            use_market=True,
            lots=0.01,  # Fixed small lot
            magic=999999,
            deviation_pips=2.0,
            comment="Orchestrator-Demo"
        )

        # Use conservative risk
        demo_risk = RiskPreset(
            risk_percent=0.5,
            sl_pips=15,
            tp_pips=30,
            trailing_pips=None,
            be_trigger_pips=None,
        )

        # Demo 1: Market One Shot
        print("\n" + "=" * 80)
        print("[DEMO 1] market_one_shot - Market order with auto-management")
        print("=" * 80)

        try:
            result1 = await run_market_one_shot(svc, demo_strategy, demo_risk)
            show_result("RESULT", result1)

            # Wait a bit before closing
            await asyncio.sleep(2)

            # Close the position
            if "ticket" in result1:
                await sugar.close(result1["ticket"])
                print(f"  ✓ Position closed: {result1['ticket']}")

        except Exception as e:
            print(f"  ✗ Error: {e}")

        await asyncio.sleep(1)

        # Demo 2: Pending Bracket
        print("\n" + "=" * 80)
        print("[DEMO 2] pending_bracket - Pending order with timeout")
        print("=" * 80)

        try:
            # Get current price and calculate entry 10 pips below
            current_mid = await sugar.mid_price(demo_symbol)
            pip_size = await sugar.pip_size(demo_symbol)
            entry_price = current_mid - (10 * pip_size)

            pending_strategy = StrategyPreset(
                symbol=demo_symbol,
                use_market=False,
                entry_price=entry_price,
                lots=0.01,
                magic=999998,
                deviation_pips=2.0,
                comment="Pending-Demo"
            )

            print(f"  Entry price: {entry_price:.5f} (current: {current_mid:.5f})")
            print(f"  Waiting 5 seconds for fill...")

            result2 = await run_pending_bracket(svc, pending_strategy, demo_risk, timeout_s=5)
            show_result("RESULT", result2)

            # If not filled, it's already cancelled by orchestrator
            if result2.get("status") == "cancelled_by_timeout":
                print("  ✓ Order cancelled due to timeout (as expected)")

        except Exception as e:
            print(f"  ✗ Error: {e}")

        await asyncio.sleep(1)

        # Demo 3: Spread Guard
        print("\n" + "=" * 80)
        print("[DEMO 3] spread_guard - Only trade if spread acceptable")
        print("=" * 80)

        try:
            # Check current spread
            current_spread = await sugar.spread_pips(demo_symbol)
            print(f"  Current spread: {current_spread:.2f} pips")
            print(f"  Max allowed: 1.5 pips")

            result3 = await market_with_spread_guard(
                svc, demo_strategy, demo_risk,
                max_spread_pips=1.5
            )
            show_result("RESULT", result3)

            # Close if opened
            if "ticket" in result3 and result3.get("status") != "skipped_due_to_spread":
                await asyncio.sleep(2)
                await sugar.close(result3["ticket"])
                print(f"  ✓ Position closed: {result3['ticket']}")
            elif result3.get("status") == "skipped_due_to_spread":
                print(f"  ✓ Trade skipped due to spread (as intended)")

        except Exception as e:
            print(f"  ✗ Error: {e}")

    # ========= Summary =========
    hdr("SUMMARY")

    print("\n✓ Orchestrator demonstrations completed!")
    print("\nOrchestrators Demonstrated:")
    print("  1. market_one_shot - Immediate market order with auto-management")
    print("  2. pending_bracket - Pending order with fill timeout & cancellation")
    print("  3. spread_guard - Market order with spread filter")
    print("  4. session_guard - Time window filter (syntax shown)")

    print("\nKey Concepts:")
    print("  • Presets: Reusable configurations (strategy + risk)")
    print("  • Guards: Market condition filters")
    print("  • Orchestrators: Complete trading scenarios")
    print("  • Composable: Guards wrap orchestrators")

    print("\nAvailable Orchestrators:")
    print("  - market_one_shot")
    print("  - pending_bracket")
    print("  - spread_guard")
    print("  - session_guard")
    print("  - oco_straddle")
    print("  - bracket_trailing_activation")
    print("  - equity_circuit_breaker")
    print("  - dynamic_deviation_guard")
    print("  - rollover_avoidance")
    print("  - kill_switch_review")
    print("  - grid_dca_common_sl")

    print("\n" + "=" * 80)
    print("To enable live trading:")
    print("  export ENABLE_TRADING=1")
    print("  python examples/Orchestrator_demo.py")
    print("=" * 80)


if __name__ == "__main__":
    # Set console encoding for Windows
    if sys.platform == 'win32':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except:
            pass

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()


# Command to run:
# python examples\Orchestrator_demo.py

"""
╔══════════════════════════════════════════════════════════════════════════════╗
║ FILE examples/Orchestrator_demo.py — Strategy Orchestrators demonstration    ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ Purpose:                                                                     ║
║   Demonstrate modular strategy orchestrators built on MT4Service/MT4Sugar:   ║
║   reusable presets (strategy/risk), guards (spread/session), and complete    ║
║   trading flows (market one-shot, pending bracket, guarded execution).       ║
║                                                                              ║
║ Step-by-step behavior:                                                       ║
║   1) Bootstrap import paths (package/, app/, Strategy/).                     ║
║   2) Load config (appsettings.json) + ENV overrides.                         ║
║   3) Connect MT4Account by priority (access[host:port] → server_name).       ║
║   4) Build MT4Service (+ sugar).                                             ║
║   5) Print available presets (Strategy & Risk).                              ║
║   6) If ENABLE_TRADING=0: show orchestrator usage/syntax & expected outputs. ║
║   7) If ENABLE_TRADING=1:                                                    ║
║        - market_one_shot: open → manage → (demo) close                       ║
║        - pending_bracket: place pending, wait (timeout demo), manage on fill ║
║        - spread_guard: trade only if spread ≤ threshold; otherwise skip      ║
║   8) Print final summary of orchestrators and key concepts.                  ║
║                                                                              ║
║ Public API / Entry Points:                                                   ║
║   - main() — orchestrates connection, presets, and selected orchestrators    ║
║   - load_settings(), hdr(), show_result() — helpers                          ║
║                                                                              ║
║ Dependencies used in this file:                                              ║
║   - MetaRpcMT4.mt4_account.MT4Account                                        ║
║   - app.MT4Service.MT4Service  (uses svc.sugar)                              ║
║   - Strategy.presets.strategy: StrategyPreset, MarketEURUSD, LimitEURUSD     ║
║   - Strategy.presets.risk: RiskPreset, Conservative, Balanced, Aggressive,   ║
║                             Scalper                                          ║
║   - Strategy.orchestrator:                                                   ║
║       market_one_shot.run_market_one_shot                                    ║
║       pending_bracket.run_pending_bracket                                    ║
║       spread_guard.market_with_spread_guard                                  ║
║       (# session_guard mentioned in docs, imported on demand in usage block) ║
║                                                                              ║
║ Config & ENV references:                                                     ║
║   - From appsettings.json: mt4.login, mt4.password, mt4.server_name,         ║
║       mt4.base_symbol, mt4.timeout_seconds, mt4.access[], grpc.server        ║
║   - ENV: MT4_LOGIN, MT4_PASSWORD, MT4_SERVER, GRPC_SERVER, ENABLE_TRADING,   ║
║           DEMO_SYMBOL                                                        ║
║                                                                              ║
║ RPC used via Service/Sugar (indirectly by orchestrators):                    ║
║   - Connectivity: ensure_connected, ping                                     ║
║   - Symbol/price: mid_price, pip_size, spread_pips                           ║
║   - Trading: buy_market / pending (via orchestrators), close                 ║
║   - Utilities: exposure/diagnostics (depending on orchestrator internals)    ║
║                                                                              ║
║ Orchestrators demonstrated:                                                  ║
║   - market_one_shot — immediate market order with auto-management            ║
║   - pending_bracket — pending order with timeout & bracket management        ║
║   - spread_guard — executes only if spread ≤ max_spread_pips                 ║
║   - session_guard — time-window guard (syntax example in comments)           ║
╚══════════════════════════════════════════════════════════════════════════════╝

"""