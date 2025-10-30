# Strategy/orchestrator/cleanup.py
"""
Emergency Cleanup Orchestrator
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Purpose: Provides panic/emergency functions to quickly close all positions and
         cancel pending orders for a specific symbol or entire account.

Functions:
- panic_close_symbol: Emergency close all positions for a specific symbol

Use Cases:
- Market conditions changed dramatically (news event, flash crash)
- Strategy malfunction detected, need immediate exit
- End of trading session, force close all positions
- Risk management: stop losses not triggered, manual intervention needed

Parameters:
- symbol: Symbol to close (e.g., "EURUSD")
- only_profit: Optional filter - True: close only profitable positions
                                  False: close only losing positions
                                  None: close all positions regardless of P/L

Execution Flow:
1. Ensure connection is alive
2. Close all matching positions for the symbol (respecting only_profit filter)
3. Cancel all pending orders for the symbol
4. Return diagnostic snapshot with current account state

Returns:
dict - Diagnostic snapshot with account balance, equity, open positions, etc.

Requirements (svc.sugar API):
- ensure_connected: Verify connection is active
- close_all: Close positions (with optional profit filter)
- cancel_pendings: Cancel pending orders
- diag_snapshot: Get current account diagnostics
"""

async def panic_close_symbol(svc, symbol: str, only_profit: bool | None = None):
    sugar = svc.sugar
    await sugar.ensure_connected()
    await sugar.close_all(symbol=symbol, only_profit=only_profit)
    await sugar.cancel_pendings(symbol=symbol)
    return await sugar.diag_snapshot()
