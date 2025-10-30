# -*- coding: utf-8 -*-
"""
Strategy Presets 📋
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Purpose: Core strategy configuration - reusable "strategy buttons" defining WHAT to trade.
         "Separate WHAT from HOW MUCH" - pairs with RiskPreset for complete setup.

What is StrategyPreset? 📊
StrategyPreset = Trading execution configuration:
- Symbol to trade (symbol)
- Entry method: market vs limit/stop (use_market, entry_price)
- Lot size override (lots)
- Order identification (magic, comment)
- Slippage tolerance (deviation_pips)

Think of it as: "Everything about EXECUTION in one place" 📦

Why Use Strategy Presets? ✓
✓ Clarity: Separates execution details from risk management
✓ Reusability: Same strategy config, different risk profiles
✓ Organization: Symbol-specific settings in one place
✓ Flexibility: Switch between market and limit entries easily
✓ Tracking: Magic numbers and comments identify orders

Perfect For:
🎯 Multi-symbol strategies (EURUSD, XAUUSD, etc.)
🎯 Different entry types (market, limit, stop)
🎯 Order identification (magic numbers per strategy)
🎯 Slippage control (deviation_pips per symbol)
🎯 Strategy naming (comment field)

Visual Hierarchy:
┌─────────────────────────────────────────────────────────────┐
│ StrategyPreset (Base Dataclass)                             │
├─────────────────────────────────────────────────────────────┤
│ • symbol: Trading symbol (e.g., "EURUSD")                   │
│ • use_market: True = market, False = pending [default=True] │
│ • entry_price: Price for limit/stop [optional]              │
│ • lots: Fixed lot size [optional, None = auto-calculate]    │
│ • magic: Order magic number [default=0]                     │
│ • deviation_pips: Max slippage in pips [default=2.0]        │
│ • comment: Order comment string [optional]                  │
└─────────────────────────────────────────────────────────────┘
         ↓ Ready-to-Use Presets ↓
┌────────────────┬──────────┬───────────┬───────┬─────────────┐
│ MarketEURUSD   │ Market   │ Magic=777 │ 2 pip │ PyMT4 Market│
├────────────────┼──────────┼───────────┼───────┼─────────────┤
│ LimitEURUSD(p) │ Limit    │ Magic=778 │ 2 pip │ PyMT4 Limit │
├────────────────┼──────────┼───────────┼───────┼─────────────┤
│ BreakoutBuy    │ Pending  │ Magic=779 │ 3 pip │ Breakout +X │
└────────────────┴──────────┴───────────┴───────┴─────────────┘

Ready-to-Use Presets Explained:

🔹 MarketEURUSD:
   - Entry: Instant market order (use_market=True)
   - Symbol: EURUSD
   - Magic: 777 (identifies these orders)
   - Deviation: 2 pips (standard slippage tolerance)
   - Comment: "PyMT4 Market"
   - Perfect for: Immediate entries, scalping, quick trades

🔹 LimitEURUSD(price: float):
   - Entry: Limit order at specified price (use_market=False)
   - Symbol: EURUSD
   - Magic: 778 (different from market orders)
   - Deviation: 2 pips
   - Comment: "PyMT4 Limit"
   - Perfect for: Precise entries, support/resistance, patience
   - Usage: LimitEURUSD(1.10500) → buy limit at 1.10500

🔹 BreakoutBuy(symbol: str, offset_pips: float):
   - Entry: Pending stop order (calculated by orchestrator)
   - Symbol: Configurable (default "EURUSD")
   - Magic: 779 (breakout-specific)
   - Deviation: 3 pips (wider for volatile breakouts)
   - Comment: "Breakout +{offset_pips} pips"
   - Perfect for: Breakout strategies, pending stops
   - Usage: BreakoutBuy("XAUUSD", 15.0) → gold breakout +15 pips

StrategyPreset Fields Explained:

📊 symbol (str):
   - Trading symbol name (must match MT4 broker symbols)
   - Examples: "EURUSD", "XAUUSD", "GBPJPY", "US500"
   - Case-sensitive (use broker's exact symbol name)
   - REQUIRED field

📊 use_market (bool):
   - True = Instant market order (buy/sell at current price)
   - False = Pending order (limit/stop at entry_price)
   - Default: True
   - Perfect for: True → scalping, False → patience

📊 entry_price (float | None):
   - Specific price for limit/stop orders
   - Example: 1.10500 for EUR/USD limit buy
   - Required when use_market=False (except for dynamic strategies)
   - None = orchestrator calculates price (e.g., breakouts)
   - Default: None

📊 lots (float | None):
   - Fixed lot size override
   - Example: 0.1 = always trade 0.1 lots
   - None = auto-calculate from risk_percent (recommended)
   - Default: None
   - Warning: Fixed lots ignore risk management!

📊 magic (int):
   - Order magic number for identification
   - Example: 777 = market orders, 778 = limit orders
   - Used by: MT4 to group/filter orders
   - Recommended: Unique per strategy type
   - Default: 0

📊 deviation_pips (float):
   - Maximum allowed slippage in pips
   - Example: 2.0 = accept up to 2 pips worse price
   - Higher values = more fills, worse average price
   - Lower values = fewer fills, better price
   - Default: 2.0
   - Adjust per symbol volatility (gold needs more)

📊 comment (str | None):
   - Order comment string (shows in MT4 terminal)
   - Example: "PyMT4 Market", "London Breakout"
   - Used for: Order identification, strategy tracking
   - Optional: None = no comment
   - Max length: Usually 31 characters (MT4 limit)

Market vs Pending Orders:

💡 Market Orders (use_market=True):
   ✓ Instant execution (filled immediately)
   ✓ No waiting for price
   ✓ Simple and fast
   ❌ Pays the spread immediately
   ❌ Potential slippage
   Perfect for: Scalping, quick entries, confirmed signals

💡 Pending Orders (use_market=False):
   ✓ Enter at exact price (no slippage)
   ✓ Can get better prices (buy cheaper, sell higher)
   ✓ Patient approach
   ❌ May never fill (price doesn't reach level)
   ❌ Requires entry_price calculation
   Perfect for: Limit orders, support/resistance, patience

Usage Patterns:

💡 Quick Start (use ready-made preset):
   from Strategy.presets.strategy import MarketEURUSD
   strategy = MarketEURUSD
   # Done! Pass to orchestrator with RiskPreset

💡 Limit Order (factory function):
   from Strategy.presets.strategy import LimitEURUSD
   strategy = LimitEURUSD(price=1.10500)
   # Buy limit at 1.10500

💡 Breakout Entry (orchestrator calculates price):
   from Strategy.presets.strategy import BreakoutBuy
   strategy = BreakoutBuy(symbol="XAUUSD", offset_pips=15.0)
   # Orchestrator will set entry_price = current_price + 15 pips

💡 Build from Scratch (full control):
   from Strategy.presets.strategy import StrategyPreset
   strategy = StrategyPreset(
       symbol="GBPJPY",
       use_market=True,
       lots=None,  # auto-calculate
       magic=888,
       deviation_pips=3.0,
       comment="Custom GBP/JPY"
   )

💡 Custom Symbol Market Order:
   from Strategy.presets.strategy import StrategyPreset
   strategy = StrategyPreset(symbol="XAUUSD", magic=801, deviation_pips=5.0)
   # Minimal setup: market order on gold with wider deviation

Combining with RiskPreset:

StrategyPreset (WHAT) + RiskPreset (HOW MUCH) = Complete Setup

from Strategy.presets.strategy import MarketEURUSD, LimitEURUSD
from Strategy.presets.risk import Balanced, Scalper
from Strategy.orchestrator.market_one_shot import run_market_one_shot

# Example 1: Market order with balanced risk
result = await run_market_one_shot(svc, MarketEURUSD, Balanced)

# Example 2: Limit order with scalper risk
strategy = LimitEURUSD(1.10500)
result = await run_market_one_shot(svc, strategy, Scalper)

Magic Number Convention:

Organize your strategies with magic number ranges:

🔢 700-799: EUR/USD strategies
   - 777: Market orders
   - 778: Limit orders
   - 779: Breakout orders

🔢 800-899: Gold (XAU/USD)
   - 801: Market orders
   - 802: Limit orders

🔢 900-999: Indices
   - 901: US500 market
   - 911: US100 market

Pro Tips:

💡 Always set unique magic numbers per strategy type
💡 Use None for lots (let risk management calculate)
💡 Adjust deviation_pips per symbol volatility:
   - Major pairs (EUR/USD): 2.0 pips
   - Gold (XAU/USD): 5.0 pips
   - Indices (US100): 10-15 pips
💡 Keep comments short and descriptive (31 char MT4 limit)
💡 Use symbol-specific presets (see strategy_symbols.py)
💡 Separate strategy configs from risk configs (better organization)
"""

from dataclasses import dataclass

@dataclass
class StrategyPreset:
    symbol: str
    use_market: bool = True
    entry_price: float | None = None
    lots: float | None = None
    magic: int = 0
    deviation_pips: float = 2.0
    comment: str | None = None

# Market (default)
MarketEURUSD = StrategyPreset(symbol="EURUSD", use_market=True, magic=777, deviation_pips=2.0, comment="PyMT4 Market")

# Limit – parameterized factory preset
def LimitEURUSD(price: float) -> StrategyPreset:
   return StrategyPreset(symbol="EURUSD", use_market=False, entry_price=price, magic=778, deviation_pips=2.0, comment="PyMT4 Limit")

# Breakout – the price will be calculated externally (by the orchestrator) from the current midpoint by an offset
def BreakoutBuy(symbol: str = "EURUSD", offset_pips: float = 10.0) -> StrategyPreset:
   # entry_price = None — calculated at startup by offset
    return StrategyPreset(symbol=symbol, use_market=False, entry_price=None, magic=779, deviation_pips=3.0, comment=f"Breakout +{offset_pips} pips")

