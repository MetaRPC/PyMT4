# examples/Presets_demo.py
# -*- coding: utf-8 -*-
"""
PRESETS DEMONSTRATION - Reusable Strategy & Risk Configurations

Demonstrates all available preset types:

1. **Basic Risk Presets** (risk.py)
   - Conservative, Balanced, Aggressive, Scalper, Walker

2. **ATR-Based Risk** (risk_atr.py)
   - Dynamic SL/TP based on market volatility (ATR)
   - ATR_Scalper, ATR_Balanced, ATR_Swing

3. **Risk Profiles** (risk_profiles.py)
   - Scalper vs Swing trading profiles
   - Symbol-specific: ScalperEURUSD, SwingXAUUSD, etc.

4. **Session-Based Risk** (risk_session.py)
   - Auto-adjusts by trading session (Asia/London/NY/Overlap)
   - Timezone-aware

5. **Strategy Symbol Presets** (strategy_symbols.py)
   - Symbol-specific strategy configs
   - MarketEURUSD, LimitXAUUSD, BreakoutGBPUSD, etc.

Each preset is a ready-to-use configuration object that works
with any orchestrator.
"""

import os
import sys
import asyncio
import json
from pathlib import Path

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

# Basic presets
from Strategy.presets.risk import (
    RiskPreset, Conservative, Balanced, Aggressive, Scalper, Walker
)
from Strategy.presets.strategy import (
    StrategyPreset, MarketEURUSD, LimitEURUSD
)

# Advanced presets
from Strategy.presets.risk_atr import (
    atr_risk, ATR_Scalper, ATR_Balanced, ATR_Swing
)
from Strategy.presets.risk_profiles import (
    make_scalper_tight, make_swing_wide,
    ScalperEURUSD, ScalperXAUUSD, SwingEURUSD, SwingXAUUSD
)
from Strategy.presets.risk_session import (
    session_risk_auto,
    make_london_balanced, make_newyork_aggressive, make_asia_conservative
)
from Strategy.presets.strategy_symbols import (
    MarketGBPUSD, MarketXAUUSD, MarketBTCUSD,
    LimitGBPUSD, LimitXAUUSD,
    BreakoutEURUSD, BreakoutGBPUSD
)


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


def show_risk_preset(name: str, preset: RiskPreset, indent: str = "  ") -> None:
    """Pretty print risk preset"""
    print(f"\n{indent}[{name}]")
    print(f"{indent}  Risk: {preset.risk_percent}%")
    print(f"{indent}  SL: {preset.sl_pips} pips")
    print(f"{indent}  TP: {preset.tp_pips} pips" if preset.tp_pips else f"{indent}  TP: None")
    if preset.trailing_pips:
        print(f"{indent}  Trailing: {preset.trailing_pips} pips")
    if preset.be_trigger_pips:
        print(f"{indent}  Breakeven: trigger={preset.be_trigger_pips}p, plus={preset.be_plus_pips}p")

    # Show ATR meta if available
    if hasattr(preset, '_atr_meta'):
        meta = preset._atr_meta
        if meta.get('atr_used_pips'):
            print(f"{indent}  ATR: {meta['atr_used_pips']:.2f} pips (period={meta['atr_period']}, mult={meta['atr_mult']})")

    # Show session meta if available
    if hasattr(preset, '_session_meta'):
        meta = preset._session_meta
        print(f"{indent}  Session: {meta.get('session')} ({meta.get('tz')})")


def show_strategy_preset(name: str, preset: StrategyPreset, indent: str = "  ") -> None:
    """Pretty print strategy preset"""
    print(f"\n{indent}[{name}]")
    print(f"{indent}  Symbol: {preset.symbol}")
    print(f"{indent}  Type: {'Market' if preset.use_market else 'Pending'}")
    if preset.entry_price:
        print(f"{indent}  Entry: {preset.entry_price}")
    if preset.lots:
        print(f"{indent}  Lots: {preset.lots}")
    print(f"{indent}  Magic: {preset.magic}")
    print(f"{indent}  Deviation: {preset.deviation_pips} pips")
    if preset.comment:
        print(f"{indent}  Comment: '{preset.comment}'")


async def main():
    hdr("PRESETS DEMONSTRATION - All Available Configurations")
    print("\nShows all preset types and how to use them with orchestrators")

    # ========= 1) Load settings and connect =========
    settings = load_settings()

    if not settings or "mt4" not in settings:
        print("\nError: appsettings.json not found or invalid")
        print("Note: Some ATR-based presets require connection to MT4")
        print("\nShowing preset structures without live data...")
        show_presets_structure_only()
        return

    # Extract credentials
    user = int(os.getenv("MT4_LOGIN", settings["mt4"].get("login", 0)))
    password = os.getenv("MT4_PASSWORD", settings["mt4"].get("password", ""))
    server_name = os.getenv("MT4_SERVER", settings["mt4"].get("server_name"))
    grpc_server = os.getenv("GRPC_SERVER", settings.get("grpc", {}).get("server", "mt4.mrpc.pro:443"))
    base_symbol = settings["mt4"].get("base_symbol", "EURUSD")
    timeout_seconds = settings["mt4"].get("timeout_seconds", 180)
    access_list = settings["mt4"].get("access", [])

    print(f"\n[CONFIG]")
    print(f"  User: {user}")
    print(f"  Symbol: {base_symbol}")

    # ========= 2) Connect =========
    hdr("[1] CONNECTION")

    account = MT4Account(user=user, password=password, grpc_server=grpc_server)
    connected = False

    # Try connection (3-priority system)
    if access_list:
        print("\n[PRIORITY 1] Direct connection via host:port")
        for host_port in access_list[:1]:  # Try first one only
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

    if not connected and server_name:
        print("\n[PRIORITY 2] Connection by server name")
        try:
            await account.connect_by_server_name(
                server_name=server_name,
                base_chart_symbol=base_symbol,
                timeout_seconds=timeout_seconds,
            )
            print(f"  [OK] Connected via {server_name}")
            connected = True
        except Exception as e:
            print(f"  [FAIL] {e}")

    if not connected:
        print("\n[WARN] Could not connect. Showing static presets only.")
        show_presets_structure_only()
        return

    print(f"\n[CONNECTED] Terminal ID: {account.id}")

    # ========= 3) Create service =========
    svc = MT4Service(account)
    sugar = svc.sugar

    await sugar.ensure_connected()
    await sugar.ensure_symbol("EURUSD")

    # ========= 4) DEMONSTRATE ALL PRESET TYPES =========

    # --- 1. BASIC RISK PRESETS ---
    hdr("[2] BASIC RISK PRESETS (risk.py)")
    print("\nStatic, pre-configured risk profiles for quick use:")

    show_risk_preset("Conservative", Conservative)
    show_risk_preset("Balanced", Balanced)
    show_risk_preset("Aggressive", Aggressive)
    show_risk_preset("Scalper", Scalper)
    show_risk_preset("Walker", Walker)

    print("\n  Usage:")
    print("    from Strategy.presets.risk import Balanced")
    print("    result = await run_market_one_shot(svc, strategy, Balanced)")

    # --- 2. ATR-BASED RISK ---
    hdr("[3] ATR-BASED RISK PRESETS (risk_atr.py)")
    print("\nDynamic SL/TP based on market volatility (ATR):")

    # Try to get ATR-based presets (requires connection)
    try:
        print("\n  Attempting to calculate ATR-based presets for EURUSD...")

        atr_scalper = await ATR_Scalper(svc, "EURUSD", risk_percent=1.0)
        show_risk_preset("ATR_Scalper", atr_scalper)

        atr_balanced = await ATR_Balanced(svc, "EURUSD", risk_percent=1.0)
        show_risk_preset("ATR_Balanced", atr_balanced)

        atr_swing = await ATR_Swing(svc, "EURUSD", risk_percent=0.75)
        show_risk_preset("ATR_Swing", atr_swing)

        print("\n  Custom ATR preset:")
        custom_atr = await atr_risk(
            svc, "EURUSD",
            atr_period=14,
            atr_mult=1.5,
            min_sl_pips=10,
            max_sl_pips=30,
            risk_percent=1.0,
            rr=2.0,
            be_trigger_frac=0.5,
            trailing_frac=0.75
        )
        show_risk_preset("Custom ATR (1.5x ATR)", custom_atr)

    except Exception as e:
        print(f"\n  Note: ATR calculation failed: {e}")
        print("  (Sugar API may not have atr_pips() method implemented)")

    print("\n  Usage:")
    print("    from Strategy.presets.risk_atr import ATR_Balanced")
    print("    risk = await ATR_Balanced(svc, 'EURUSD', risk_percent=1.0)")
    print("    result = await run_market_one_shot(svc, strategy, risk)")

    # --- 3. RISK PROFILES ---
    hdr("[4] RISK PROFILES (risk_profiles.py)")
    print("\nScalper vs Swing trading profiles:")

    scalper_tight = make_scalper_tight(risk_percent=1.0)
    show_risk_preset("ScalperTight (generic)", scalper_tight)

    swing_wide = make_swing_wide(risk_percent=1.0)
    show_risk_preset("SwingWide (generic)", swing_wide)

    print("\n  Symbol-specific shortcuts:")
    show_risk_preset("ScalperEURUSD", ScalperEURUSD())
    show_risk_preset("ScalperXAUUSD", ScalperXAUUSD())
    show_risk_preset("SwingEURUSD", SwingEURUSD())
    show_risk_preset("SwingXAUUSD", SwingXAUUSD())

    print("\n  Usage:")
    print("    from Strategy.presets.risk_profiles import ScalperEURUSD")
    print("    result = await run_market_one_shot(svc, MarketEURUSD, ScalperEURUSD())")

    # --- 4. SESSION-BASED RISK ---
    hdr("[5] SESSION-BASED RISK (risk_session.py)")
    print("\nAuto-adjusts risk by trading session:")

    # Explicit presets
    show_risk_preset("London Balanced", make_london_balanced())
    show_risk_preset("New York Aggressive", make_newyork_aggressive())
    show_risk_preset("Asia Conservative", make_asia_conservative())

    # Auto-detection
    print("\n  Auto-detection by current time:")
    try:
        session_auto = await session_risk_auto(
            svc, "EURUSD",
            tz="Europe/London",
            profile="default"
        )
        show_risk_preset("Auto (Current Session)", session_auto)

        session_aggr = await session_risk_auto(
            svc, "EURUSD",
            tz="Europe/London",
            profile="aggressive"
        )
        show_risk_preset("Auto (Aggressive Profile)", session_aggr)

    except Exception as e:
        print(f"  Note: Session auto-detection failed: {e}")

    print("\n  Usage:")
    print("    from Strategy.presets.risk_session import session_risk_auto")
    print("    risk = await session_risk_auto(svc, 'EURUSD', tz='Europe/London')")
    print("    result = await run_market_one_shot(svc, strategy, risk)")

    # --- 5. STRATEGY SYMBOL PRESETS ---
    hdr("[6] STRATEGY SYMBOL PRESETS (strategy_symbols.py)")
    print("\nSymbol-specific strategy configurations:")

    print("\n  === Forex ===")
    show_strategy_preset("MarketEURUSD", MarketEURUSD)
    show_strategy_preset("MarketGBPUSD", MarketGBPUSD)

    print("\n  === Metals ===")
    show_strategy_preset("MarketXAUUSD", MarketXAUUSD)

    print("\n  === Crypto ===")
    show_strategy_preset("MarketBTCUSD", MarketBTCUSD)

    print("\n  === Pending Orders (factories) ===")
    current_price = await sugar.mid_price("GBPUSD")
    limit_gbp = LimitGBPUSD(current_price - 0.0010)
    show_strategy_preset("LimitGBPUSD(price)", limit_gbp)

    show_strategy_preset("BreakoutEURUSD", BreakoutEURUSD)

    print("\n  Usage:")
    print("    from Strategy.presets.strategy_symbols import MarketXAUUSD")
    print("    from Strategy.presets.risk import Balanced")
    print("    result = await run_market_one_shot(svc, MarketXAUUSD, Balanced)")

    # --- 6. COMBINING PRESETS ---
    hdr("[7] COMBINING PRESETS WITH ORCHESTRATORS")
    print("\nPresets + Orchestrators = Complete Trading Scenarios")

    print("\n  Example 1: Market + Static Risk")
    print("    from Strategy.orchestrator.market_one_shot import run_market_one_shot")
    print("    result = await run_market_one_shot(svc, MarketEURUSD, Balanced)")

    print("\n  Example 2: Pending + ATR Risk")
    print("    risk = await ATR_Balanced(svc, 'GBPUSD')")
    print("    price = await sugar.mid_price('GBPUSD') - (10 * pip_size)")
    print("    strategy = LimitGBPUSD(price)")
    print("    result = await run_pending_bracket(svc, strategy, risk)")

    print("\n  Example 3: Symbol + Session Risk + Spread Guard")
    print("    risk = await session_risk_auto(svc, 'EURUSD', tz='Europe/London')")
    print("    result = await market_with_spread_guard(")
    print("        svc, MarketEURUSD, risk, max_spread_pips=1.5")
    print("    )")

    print("\n  Example 4: Gold Swing with Profile")
    print("    result = await run_market_one_shot(svc, MarketXAUUSD, SwingXAUUSD())")

    # ========= Summary =========
    hdr("SUMMARY")

    print("\n✓ All preset types demonstrated!")
    print("\nPreset Categories:")
    print("  1. Basic Risk - 5 static profiles (Conservative → Aggressive)")
    print("  2. ATR Risk - 3 dynamic profiles based on volatility")
    print("  3. Risk Profiles - Scalper vs Swing, symbol-aware")
    print("  4. Session Risk - Auto-adjust by trading session")
    print("  5. Strategy Symbols - 30+ symbol-specific configs")

    print("\nKey Benefits:")
    print("  • Reusable configurations")
    print("  • Type-safe with dataclasses")
    print("  • Composable with any orchestrator")
    print("  • Mix & match strategy + risk presets")

    print("\nAll Symbols Available:")
    print("  Forex: EURUSD, GBPUSD, USDJPY")
    print("  Metals: XAUUSD, XAGUSD")
    print("  Indices: US100, US500, GER40")
    print("  Crypto: BTCUSD")

    print("\nAll Risk Types:")
    print("  Static: Conservative, Balanced, Aggressive, Scalper, Walker")
    print("  ATR: ATR_Scalper, ATR_Balanced, ATR_Swing")
    print("  Profile: ScalperEURUSD, SwingXAUUSD, etc.")
    print("  Session: Auto-detect by time (Asia/London/NY/Overlap)")

    print("\n" + "=" * 80)


def show_presets_structure_only():
    """Show preset structures without requiring connection"""
    hdr("PRESET STRUCTURES (No Connection)")

    print("\n=== Basic Risk Presets ===")
    show_risk_preset("Conservative", Conservative)
    show_risk_preset("Balanced", Balanced)
    show_risk_preset("Aggressive", Aggressive)

    print("\n=== Strategy Presets ===")
    show_strategy_preset("MarketEURUSD", MarketEURUSD)
    show_strategy_preset("MarketXAUUSD", MarketXAUUSD)

    print("\n=== Risk Profiles ===")
    show_risk_preset("ScalperEURUSD", ScalperEURUSD())
    show_risk_preset("SwingXAUUSD", SwingXAUUSD())

    print("\nNote: ATR and Session-based presets require live connection")


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
# python examples\Presets_demo.py

"""
╔══════════════════════════════════════════════════════════════════════════════╗
║ FILE examples/Presets_demo.py — Reusable Strategy & Risk Presets showcase    ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ Purpose:                                                                     ║
║   Demonstrate every preset family used with orchestrators:                   ║
║   - Static risk presets (Conservative…Walker)                                ║
║   - ATR-based dynamic risk (ATR_Scalper/Balanced/Swing + custom)             ║
║   - Risk profiles (Scalper/Swing, symbol-aware)                              ║
║   - Session-based risk (timezone-aware auto adjust)                          ║
║   - Strategy symbol presets (Market/Limit/Breakout for many symbols)         ║
║                                                                              ║
║ Step-by-step behavior:                                                       ║
║   1) Bootstraps import paths (package/, app/, Strategy/).                    ║
║   2) Loads appsettings.json (+ ENV overrides).                               ║
║   3) If settings missing → prints presets structure only (no connection).    ║
║   4) Else: creates MT4Account and connects (host:port → server_name).        ║
║   5) Builds MT4Service (+ sugar), ensures connectivity & EURUSD symbol.      ║
║   6) Shows ALL preset types with pretty printers:                            ║
║        • Basic risk (risk.py)                                                ║
║        • ATR risk (risk_atr.py; live ATR if available)                       ║
║        • Risk profiles (risk_profiles.py; generic & symbol-specific)         ║
║        • Session risk (risk_session.py; auto detect by tz)                   ║
║        • Strategy symbol presets (strategy_symbols.py; Market/Limit/Breakout)║
║   7) Prints “how to use with orchestrators” examples.                        ║
║   8) Summary of categories, symbols, and benefits.                           ║
║                                                                              ║
║ Public API / Entry Points:                                                   ║
║   - main() — full demo flow                                                  ║
║   - show_presets_structure_only() — offline listing                          ║
║   - load_settings(), hdr(), show_risk_preset(), show_strategy_preset()       ║
║                                                                              ║
║ Dependencies used in this file:                                              ║
║   - MetaRpcMT4.mt4_account.MT4Account                                        ║
║   - app.MT4Service.MT4Service  (uses svc.sugar)                              ║
║   - Strategy.presets.risk: RiskPreset, Conservative, Balanced, Aggressive,   ║
║       Scalper, Walker                                                        ║
║   - Strategy.presets.strategy: StrategyPreset, MarketEURUSD, LimitEURUSD     ║
║   - Strategy.presets.risk_atr: atr_risk, ATR_Scalper, ATR_Balanced, ATR_Swing║
║   - Strategy.presets.risk_profiles:                                          ║
║       make_scalper_tight, make_swing_wide,                                   ║
║       ScalperEURUSD, ScalperXAUUSD, SwingEURUSD, SwingXAUUSD                 ║
║   - Strategy.presets.risk_session: session_risk_auto,                        ║
║       make_london_balanced, make_newyork_aggressive, make_asia_conservative  ║
║   - Strategy.presets.strategy_symbols: Market/Limit/Breakout for FX/Metals/  ║
║       Indices/Crypto (e.g., MarketGBPUSD, MarketXAUUSD, MarketBTCUSD, …)     ║
║                                                                              ║
║ Config & ENV references:                                                     ║
║   - appsettings.json → mt4.login, mt4.password, mt4.server_name,             ║
║       mt4.base_symbol, mt4.timeout_seconds, mt4.access[], grpc.server        ║
║   - ENV → MT4_LOGIN, MT4_PASSWORD, MT4_SERVER, GRPC_SERVER                   ║
║            (optional) MT4_HOST/MT4_PORT                                      ║
║                                                                              ║
║ RPC used during demo (via Sugar/Service):                                    ║
║   - Connectivity: sugar.ensure_connected()                                   ║
║   - Symbols/pricing: sugar.ensure_symbol(), sugar.mid_price(), sugar.pip_size║
║   - ATR/session presets may call Sugar/price helpers internally if available.║
║                                                                              ║
║ Preset families covered:                                                     ║
║   - Basic Risk (static): Conservative, Balanced, Aggressive, Scalper, Walker ║
║   - ATR-Based (dynamic): ATR_Scalper, ATR_Balanced, ATR_Swing, atr_risk(...) ║
║   - Profiles: make_scalper_tight(), make_swing_wide(),                       ║
║               ScalperEURUSD/XAUUSD, SwingEURUSD/XAUUSD                       ║
║   - Session-Based: session_risk_auto(), London/NY/Asia shortcuts             ║
║   - Strategy Symbols: Market*/Limit* factories, Breakout* shortcuts          ║
╚══════════════════════════════════════════════════════════════════════════════╝

╔══════════════════════════════════════════════════════════════════════════════╗
║                          🧠 STRATEGY & RISK PRESET MATRIX                   ║
╠═══════════════╦══════════╦════════════════════════╦══════════════════════════╣
║ PRESET TYPE   ║ EXAMPLE  ║ WHAT IT CONTROLS       ║ BEST USE CASES           ║
╠═══════════════╬══════════╬════════════════════════╬══════════════════════════╣
║ STATIC RISK   ║          ║ • Fixed SL/TP in pips  ║ • Stable assets          ║
║ (risk.py)     ║ Balanced ║ • Risk % per trade     ║ • User-defined sizing    ║
║               ║          ║ • (optional) trailing  ║ • Quick prototyping      ║
╠───────────────╬──────────╬────────────────────────╬──────────────────────────╣
║ ATR RISK      ║ ATR_     ║ • SL/TP by volatility  ║ • High volatility FX     ║
║ (risk_atr.py) ║ Balanced ║ • ATR multipliers      ║ • Crypto, Gold           ║
║               ║          ║ • Dynamic RR           ║ • Trending markets       ║
╠───────────────╬──────────╬────────────────────────╬──────────────────────────╣
║ RISK PROFILE  ║ Scalper- ║ • Risk preset +        ║ • Symbol-specific        ║
║ (profiles)    ║ EURUSD   ║   symbol behavior      ║ • Aggressive entries     ║
║               ║          ║ • Tight spreads focus  ║ • Short holding time     ║
╠───────────────╬──────────╬────────────────────────╬──────────────────────────╣
║ SESSION RISK  ║ London   ║ • Auto SL/TP/risk by   ║ • Session traders        ║
║ (session)     ║ Balanced ║   sessions + timezone  ║ • Avoid rollover risk    ║
║               ║          ║ • Asia/London/NY rules ║ • Smart auto-adaptive    ║
╠═══════════════╩══════════╩════════════════════════╩══════════════════════════╣
║ STRATEGY TYPE               WHAT IT DEFINES              USED WHEN…          ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ MARKET STRATEGY             • Immediate entry             • Scalping         ║
║ (MarketEURUSD…)             • Lots / magic / comment      • Strong signals   ║
╠──────────────────────────────────────────────────────────────────────────────╣
║ LIMIT/STOP STRATEGY         • Pending price & deviation   • Pullbacks        ║
║ (LimitGBPUSD…)              • Pre-planned entries         • Breakout waits   ║
╠──────────────────────────────────────────────────────────────────────────────╣
║ BREAKOUT STRATEGY           • Entry rules baked in        • Momentum bursts  ║
║ (BreakoutEURUSD…)           • Often no fixed price        • News volatility  ║
╚══════════════════════════════════════════════════════════════════════════════╝


"""