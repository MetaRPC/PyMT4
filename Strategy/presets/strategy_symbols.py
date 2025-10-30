# -*- coding: utf-8 -*-
"""
Symbol-Aware Strategy Presets 🌍
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Purpose: Pre-configured strategy presets for specific symbols with tuned parameters.
         "Symbol-specific optimization - each instrument gets its own settings" 🎯

What is Symbol-Aware Preset? 📊
Symbol-aware preset = StrategyPreset tuned for a specific trading instrument:
- Optimized deviation_pips (slippage tolerance per symbol volatility)
- Unique magic numbers (organize orders by symbol)
- Symbol-specific comments (clear identification)
- Three entry types per symbol: Market, Limit, Breakout

Why Symbol-Specific Presets? ✓
✓ Volatility-aware: Gold needs wider deviation than EUR/USD
✓ Organization: Unique magic numbers per symbol (easy filtering)
✓ Convenience: Ready-to-use configs (no manual setup)
✓ Best practices: Industry-standard settings per instrument
✓ Clarity: Clear naming (MarketXAUUSD vs generic preset)

Perfect For:
🎯 Multi-symbol portfolios (trade 5+ instruments)
🎯 Symbol rotation strategies (switch between assets)
🎯 Volatility-aware execution (auto-tuned deviation)
🎯 Order organization (magic number ranges per symbol)
🎯 Quick deployment (one-line strategy setup)

Symbol Coverage:

💱 Forex Majors:  EUR/USD, GBP/USD, USD/JPY
💰 Precious Metals: XAU/USD (Gold), XAG/USD (Silver)
📈 Indices: US100 (Nasdaq), US500 (S&P 500), GER40 (DAX)
₿ Crypto: BTC/USD (Bitcoin)

Entry Type Variants (each symbol has 3):

🔹 Market{Symbol} - Instant market orders (Magic: X01)
🔹 Limit{Symbol}(price) - Patient limit orders (Magic: X02)
🔹 Breakout{Symbol} - Dynamic stop orders (Magic: X03)

Magic Number Organization:

🔢 770-779: EUR/USD  |  🔢 780-789: GBP/USD  |  🔢 790-799: USD/JPY
🔢 800-809: XAU/USD  |  🔢 810-819: XAG/USD
🔢 820-829: US100    |  🔢 830-839: US500    |  🔢 840-849: GER40
🔢 850-859: BTC/USD

Deviation Tuning by Volatility:

📊 Forex Majors: 2.0-2.5 pips (low-medium volatility)
📊 Precious Metals: 4.0-5.0 pips (high volatility)
📊 Indices: 6.0-12.0 pips (very high volatility)
📊 Crypto: 20.0 pips (extreme volatility)

Usage Examples:

💡 Market Order on Gold:
   from Strategy.presets.strategy_symbols import MarketXAUUSD
   result = await run_market_one_shot(svc, MarketXAUUSD, Balanced)

💡 Limit Order on EUR/USD:
   strategy = LimitEURUSD(1.10500)
   result = await run_market_one_shot(svc, strategy, Scalper)

💡 Multi-Symbol Portfolio:
   symbols = [MarketEURUSD, MarketGBPUSD, MarketXAUUSD]
   for strategy in symbols:
       result = await run_market_one_shot(svc, strategy, Balanced)

Pro Tips:

💡 Use symbol-specific presets for production trading
💡 Test deviation settings with your broker (can vary)
💡 Combine with ATR-based risk for volatility adaptation
💡 Limit orders save spread costs (better average price)
💡 Crypto needs much wider deviation (extreme volatility)
"""

from __future__ import annotations
from dataclasses import replace
from .strategy import StrategyPreset

# --- Helpers -----------------------------------------------------------------

def _mk_market(symbol: str, *, magic: int, deviation_pips: float, comment: str) -> StrategyPreset:
    """Market-entry preset with tuned deviation."""
    return StrategyPreset(
        symbol=symbol, use_market=True, entry_price=None, lots=None,
        magic=magic, deviation_pips=deviation_pips, comment=comment
    )

def _mk_limit(symbol: str, price: float, *, magic: int, deviation_pips: float, comment: str) -> StrategyPreset:
    """Limit-entry preset factory."""
    return StrategyPreset(
        symbol=symbol, use_market=False, entry_price=float(price), lots=None,
        magic=magic, deviation_pips=deviation_pips, comment=comment
    )

def _mk_breakout(symbol: str, *, magic: int, deviation_pips: float, comment: str) -> StrategyPreset:
    """
    Breakout preset (entry_price=None): orchestrator must compute price (e.g., mid + offset).
    We keep use_market=False to force a pending stop/limit type in the runner.
    """
    return StrategyPreset(
        symbol=symbol, use_market=False, entry_price=None, lots=None,
        magic=magic, deviation_pips=deviation_pips, comment=comment
    )

# --- EURUSD family ------------------------------------------------------------

MarketEURUSD  = _mk_market("EURUSD",  magic=771, deviation_pips=2.0, comment="Market EURUSD")
def LimitEURUSD(price: float) -> StrategyPreset:
    return _mk_limit("EURUSD", price, magic=772, deviation_pips=2.0, comment="Limit EURUSD")
BreakoutEURUSD = _mk_breakout("EURUSD", magic=773, deviation_pips=2.5, comment="Breakout EURUSD")

# --- GBPUSD -------------------------------------------------------------------

MarketGBPUSD  = _mk_market("GBPUSD",  magic=781, deviation_pips=2.5, comment="Market GBPUSD")
def LimitGBPUSD(price: float) -> StrategyPreset:
    return _mk_limit("GBPUSD", price, magic=782, deviation_pips=2.5, comment="Limit GBPUSD")
BreakoutGBPUSD = _mk_breakout("GBPUSD", magic=783, deviation_pips=3.0, comment="Breakout GBPUSD")

# --- USDJPY -------------------------------------------------------------------

MarketUSDJPY  = _mk_market("USDJPY",  magic=791, deviation_pips=2.0, comment="Market USDJPY")
def LimitUSDJPY(price: float) -> StrategyPreset:
    return _mk_limit("USDJPY", price, magic=792, deviation_pips=2.0, comment="Limit USDJPY")
BreakoutUSDJPY = _mk_breakout("USDJPY", magic=793, deviation_pips=2.5, comment="Breakout USDJPY")

# --- XAUUSD (Gold) ------------------------------------------------------------

MarketXAUUSD  = _mk_market("XAUUSD",  magic=801, deviation_pips=5.0, comment="Market XAUUSD")
def LimitXAUUSD(price: float) -> StrategyPreset:
    return _mk_limit("XAUUSD", price, magic=802, deviation_pips=5.0, comment="Limit XAUUSD")
BreakoutXAUUSD = _mk_breakout("XAUUSD", magic=803, deviation_pips=6.0, comment="Breakout XAUUSD")

# --- XAGUSD (Silver) ----------------------------------------------------------

MarketXAGUSD  = _mk_market("XAGUSD",  magic=811, deviation_pips=4.0, comment="Market XAGUSD")
def LimitXAGUSD(price: float) -> StrategyPreset:
    return _mk_limit("XAGUSD", price, magic=812, deviation_pips=4.0, comment="Limit XAGUSD")
BreakoutXAGUSD = _mk_breakout("XAGUSD", magic=813, deviation_pips=5.0, comment="Breakout XAGUSD")

# --- Indices (contract specs vary; adjust deviation to your broker) ----------

MarketUS100   = _mk_market("US100",   magic=821, deviation_pips=12.0, comment="Market US100")
def LimitUS100(price: float) -> StrategyPreset:
    return _mk_limit("US100", price, magic=822, deviation_pips=12.0, comment="Limit US100")
BreakoutUS100 = _mk_breakout("US100", magic=823, deviation_pips=15.0, comment="Breakout US100")

MarketUS500   = _mk_market("US500",   magic=831, deviation_pips=6.0, comment="Market US500")
def LimitUS500(price: float) -> StrategyPreset:
    return _mk_limit("US500", price, magic=832, deviation_pips=6.0, comment="Limit US500")
BreakoutUS500 = _mk_breakout("US500", magic=833, deviation_pips=8.0, comment="Breakout US500")

MarketGER40   = _mk_market("GER40",   magic=841, deviation_pips=8.0, comment="Market GER40")
def LimitGER40(price: float) -> StrategyPreset:
    return _mk_limit("GER40", price, magic=842, deviation_pips=8.0, comment="Limit GER40")
BreakoutGER40 = _mk_breakout("GER40", magic=843, deviation_pips=10.0, comment="Breakout GER40")

# --- Crypto (if supported by the broker) ----------------------------------

MarketBTCUSD  = _mk_market("BTCUSD",  magic=851, deviation_pips=20.0, comment="Market BTCUSD")
def LimitBTCUSD(price: float) -> StrategyPreset:
    return _mk_limit("BTCUSD", price, magic=852, deviation_pips=20.0, comment="Limit BTCUSD")
BreakoutBTCUSD = _mk_breakout("BTCUSD", magic=853, deviation_pips=25.0, comment="Breakout BTCUSD")

# --- Quick registry (optional) -----------------------------------------------

REGISTRY = {
    # FX
    "EURUSD:market": MarketEURUSD,
    "GBPUSD:market": MarketGBPUSD,
    "USDJPY:market": MarketUSDJPY,
    # Metals
    "XAUUSD:market": MarketXAUUSD,
    "XAGUSD:market": MarketXAGUSD,
    # Indices
    "US100:market":  MarketUS100,
    "US500:market":  MarketUS500,
    "GER40:market":  MarketGER40,
    # Crypto
    "BTCUSD:market": MarketBTCUSD,
}

__all__ = [
    # EURUSD
    "MarketEURUSD", "LimitEURUSD", "BreakoutEURUSD",
    # GBPUSD
    "MarketGBPUSD", "LimitGBPUSD", "BreakoutGBPUSD",
    # USDJPY
    "MarketUSDJPY", "LimitUSDJPY", "BreakoutUSDJPY",
    # XAUUSD
    "MarketXAUUSD", "LimitXAUUSD", "BreakoutXAUUSD",
    # XAGUSD
    "MarketXAGUSD", "LimitXAGUSD", "BreakoutXAGUSD",
    # Indices
    "MarketUS100", "LimitUS100", "BreakoutUS100",
    "MarketUS500", "LimitUS500", "BreakoutUS500",
    "MarketGER40", "LimitGER40", "BreakoutGER40",
    # Crypto
    "MarketBTCUSD", "LimitBTCUSD", "BreakoutBTCUSD",
    # Registry
    "REGISTRY",
]

"""
Example of launch

from Strategy.presets.strategy_symbols import (
    MarketXAUUSD, LimitXAUUSD, BreakoutXAUUSD,
    MarketGBPUSD, LimitGBPUSD,
    MarketUS100, LimitUS100,
)

sp1 = MarketXAUUSD
sp2 = LimitGBPUSD(1.25750)
sp3 = BreakoutXAUUSD   # The orchestrator will calculate the entry from the mid/offset

"""