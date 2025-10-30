# Strategy/orchestrator/ladder_builder.py
"""
Ladder Builder Utility
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Purpose: Simple utility to build a ladder of limit orders below a starting price.
         Used for DCA (Dollar Cost Averaging) and grid trading strategies.

Concept:
Creates a series of BUY LIMIT orders at evenly spaced price levels below the
starting price. Each order is placed with identical lot size, SL, and TP.

Visual Example (BUY ladder):
  Start Price: 1.1000
  Steps: 3
  Step Pips: 10

  Order 1: 1.0990 (10 pips below)
  Order 2: 1.0980 (20 pips below)
  Order 3: 1.0970 (30 pips below)

Use Cases:
- DCA strategy: Average down during market dips
- Support level trading: Place orders at known support zones
- Grid trading: Build buy side of a grid
- Mean reversion: Catch price pullbacks

Parameters:
- symbol: Trading symbol (e.g., "EURUSD")
- start_price: Top of ladder (current price or resistance level)
- steps: Number of limit orders to place (e.g., 5)
- step_pips: Distance between each order in pips (e.g., 10)
- risk: RiskPreset containing risk_percent, sl_pips, tp_pips

Execution Flow:
1. Ensure connection and symbol availability
2. For each step (0 to steps-1):
   - Calculate order price: start_price - (step_pips × step_index)
   - Calculate lot size based on risk preset
   - Place BUY LIMIT with SL/TP
   - Add comment "DCA {i+1}/{steps}"
3. Return list of order tickets

Returns:
list[int] - Tickets of all placed limit orders

Requirements (svc.sugar API):
- ensure_connected, ensure_symbol: Connection management
- pips_to_price: Convert pips offset to price
- calc_lot_by_risk: Calculate lot size based on risk
- buy_limit: Place limit order with SL/TP

Note: Currently only supports BUY ladders (orders placed below start_price).
      For SELL ladders, modify step_pips sign to positive in the implementation.
"""

from Strategy.presets import RiskPreset

async def build_ladder_limits(svc, symbol: str, start_price: float, steps: int, step_pips: float, risk: RiskPreset):
    sugar = svc.sugar
    await sugar.ensure_connected(); await sugar.ensure_symbol(symbol)
    tickets = []
    for i in range(steps):
        price = await sugar.pips_to_price(symbol, start_price, -step_pips * i)  # below by "i" steps
        lots = await sugar.calc_lot_by_risk(symbol, risk_percent=risk.risk_percent, stop_pips=risk.sl_pips)
        t = await sugar.buy_limit(symbol=symbol, price=price, lots=lots, sl_pips=risk.sl_pips, tp_pips=risk.tp_pips, comment=f"DCA {i+1}/{steps}")
        tickets.append(t)
    return tickets
