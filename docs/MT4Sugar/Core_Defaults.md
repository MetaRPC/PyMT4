# Core & Defaults

## 🔌 `async ensure_connected()`

**What it does:** Ensures that the connection to the terminal is alive; automatically reconnects if lost.

**Used in:**

* Before any market operations (quotes, bars, orders).
* In long-running loops/workers to avoid silent disconnections.
* At the start of critical trading operations to guarantee connectivity.
* In scheduled tasks and background workers that run periodically.

**How it works:**

1. Checks if the current connection is active by attempting to get session headers
2. If connection is alive, returns immediately
3. If connection is lost, attempts to reconnect automatically
4. Emits a `on_reconnect` hook event when reconnection succeeds
5. Raises an error if reconnection fails

**Example 1: Basic usage before trading**

```python
# Ensure connection before any market calls
await sugar.ensure_connected()
price = await api.quote("EURUSD")
```

**Example 2: In a long-running trading loop**

```python
while True:
    # Guarantee connectivity at each iteration
    await sugar.ensure_connected()

    # Fetch market data
    quote = await sugar.last_quote("EURUSD")

    # Execute trading logic
    if quote["bid"] > target_price:
        await sugar.buy_market(lots=0.1, sl_pips=20)

    await asyncio.sleep(60)  # Wait 1 minute
```

**Example 3: Error handling with fallback**

```python
try:
    await sugar.ensure_connected()
    # Proceed with trading operations
    await sugar.buy_market("EURUSD", 0.1)
except ConnectivityError as e:
    logger.error(f"Failed to establish connection: {e}")
    # Notify admin or retry later
    await notify_admin("MT4 connection lost")
```

---

## 🔎 `get_default(key, fallback=None)`

**What it does:** Returns a stored default value by key (`symbol`, `magic`, `deviation_pips`, `risk_percent`, etc.).

**Used in:**

* When you need to read the current default for logic/logging.
* In wrappers where some parameters are auto-filled.
* For debugging and diagnostic purposes to verify current configuration.
* In multi-strategy applications to check active trading context.

**Available keys:**

* `symbol` - Default trading symbol (e.g., "EURUSD")
* `magic` - Magic number for order identification
* `deviation_pips` - Maximum allowed slippage in pips
* `slippage_pips` - Alternative name for deviation
* `risk_percent` - Default risk percentage per trade

**Example 1: Basic retrieval**

```python
magic = sugar.get_default("magic", fallback=1001)
print("Current magic:", magic)
```

**Example 2: Logging current configuration**

```python
def log_trading_config():
    """Log current Sugar API defaults for debugging"""
    config = {
        "symbol": sugar.get_default("symbol", "NOT_SET"),
        "magic": sugar.get_default("magic", "NOT_SET"),
        "deviation_pips": sugar.get_default("deviation_pips", 5),
        "risk_percent": sugar.get_default("risk_percent", 1.0),
    }
    logger.info(f"Trading config: {config}")
```

**Example 3: Conditional logic based on defaults**

```python
# Adjust strategy based on configured risk
risk_pct = sugar.get_default("risk_percent", fallback=1.0)

if risk_pct > 2.0:
    logger.warning("High risk mode activated!")
    # Use tighter stops
    stop_pips = 15
else:
    # Standard risk - wider stops
    stop_pips = 30
```

---

## 📡 `async ping()`

**What it does:** Lightweight connection health check. Returns `True/False`.

**Used in:**

* Monitoring, watchdog loops, readiness probes before executing critical actions.
* Together with `ensure_connected()` to quickly verify connectivity between operations.
* Health check endpoints in web APIs or monitoring systems.
* Pre-flight checks before executing expensive or critical operations.

**How it works:**

1. Attempts to get session headers (quick operation)
2. If successful, returns `True` immediately
3. If failed, attempts one reconnection attempt
4. Returns `True` if reconnection succeeds, `False` otherwise
5. Never raises exceptions - always returns boolean

**Example 1: Simple health check**

```python
# Health check between tasks
if not await sugar.ping():
    await sugar.ensure_connected()
```

**Example 2: Monitoring loop with alerting**

```python
async def health_monitor():
    """Monitor MT4 connection health every 30 seconds"""
    while True:
        is_healthy = await sugar.ping()

        if not is_healthy:
            logger.error("MT4 connection unhealthy!")
            await send_alert("MT4 connection down")
        else:
            logger.debug("MT4 connection OK")

        await asyncio.sleep(30)
```

**Example 3: Pre-flight check for critical operations**

```python
async def execute_large_order(symbol, lots):
    """Execute large order with pre-flight connectivity check"""

    # Pre-flight check
    if not await sugar.ping():
        raise RuntimeError("Cannot execute: MT4 connection unavailable")

    # Connection OK - proceed with order
    logger.info(f"Executing large order: {symbol} {lots} lots")
    return await sugar.buy_market(symbol, lots)
```

**Example 4: Web API health endpoint**

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/health/mt4")
async def mt4_health():
    """Health check endpoint for MT4 connectivity"""
    is_connected = await sugar.ping()
    return {
        "status": "healthy" if is_connected else "unhealthy",
        "service": "MT4",
        "connected": is_connected
    }
```

---

## 🧬 `set_defaults(symbol=None, magic=None, deviation_pips=None, slippage_pips=None, risk_percent=None)`

**What it does:** Sets human-friendly defaults that will be automatically injected into sugar calls.

**Used in:**

* Once during app/script startup.
* When switching trading contexts (different symbol, different `magic`, etc.).
* When changing trading strategies or risk profiles.
* In multi-strategy environments to isolate different trading contexts.

**Parameters:**

* `symbol` - Default trading symbol (e.g., "EURUSD", "GBPUSD")
* `magic` - Magic number for order identification (integer)
* `deviation_pips` - Maximum allowed price deviation/slippage in pips
* `slippage_pips` - Alternative parameter name for deviation
* `risk_percent` - Default risk percentage per trade (e.g., 1.0 = 1%)

**Important notes:**

* Only non-None values are applied - existing defaults remain unchanged
* All parameters are optional
* Defaults persist until explicitly changed again
* Context-specific overrides can be done with `with_defaults()`

**Example 1: App bootstrap configuration**

```python
# App bootstrap: configure sane defaults
sugar.set_defaults(
    symbol="EURUSD",
    magic=1001,
    deviation_pips=5,
    slippage_pips=3,
    risk_percent=1.0,
)
```

**Example 2: Switching trading contexts**

```python
# Trade EURUSD with conservative settings
sugar.set_defaults(
    symbol="EURUSD",
    magic=1001,
    risk_percent=0.5
)
await sugar.buy_market(lots=0.1)  # Uses EURUSD, magic=1001

# Switch to GBPUSD with aggressive settings
sugar.set_defaults(
    symbol="GBPUSD",
    magic=2002,
    risk_percent=2.0
)
await sugar.buy_market(lots=0.1)  # Uses GBPUSD, magic=2002
```

**Example 3: Strategy-specific configuration**

```python
class ScalpingStrategy:
    def __init__(self, sugar):
        self.sugar = sugar

        # Configure for scalping
        self.sugar.set_defaults(
            symbol="EURUSD",
            magic=5001,
            deviation_pips=2,  # Tight slippage for scalping
            risk_percent=0.5   # Conservative risk
        )

class SwingStrategy:
    def __init__(self, sugar):
        self.sugar = sugar

        # Configure for swing trading
        self.sugar.set_defaults(
            symbol="GBPUSD",
            magic=5002,
            deviation_pips=10,  # Allow wider slippage
            risk_percent=2.0    # Higher risk for swing trades
        )
```

**Example 4: Partial updates**

```python
# Initial setup
sugar.set_defaults(
    symbol="EURUSD",
    magic=1001,
    risk_percent=1.0
)

# Later: only update risk, keep symbol and magic unchanged
sugar.set_defaults(risk_percent=2.0)

# symbol="EURUSD" and magic=1001 remain unchanged
```

---

## `with_defaults(**overrides)`

**What it does:** Temporarily override defaults in a limited context (within a code block).

**Used in:**

* Local scenarios: "for this section, trade GBPUSD with another magic."
* Tests/strategies where it's convenient to change context locally.
* Temporary context switches without affecting global configuration.
* Multi-symbol trading within a single strategy.

**Important notes:**

* Changes only affect code within the `with` block
* Original defaults are automatically restored when exiting the block
* Can override multiple parameters simultaneously
* Nested contexts are supported

**Example 1: Temporary symbol switch**

```python
# Global defaults: EURUSD
sugar.set_defaults(symbol="EURUSD", magic=1001)

# Temporarily switch trading context
with sugar.with_defaults(symbol="GBPUSD", magic=2002):
    # Inside this block calls will use these defaults
    await sugar.buy_market(lots=0.1)  # uses symbol=GBPUSD, magic=2002

# Outside — back to EURUSD with magic=1001
await sugar.buy_market(lots=0.1)  # uses symbol=EURUSD, magic=1001
```

**Example 2: Multi-symbol correlation trading**

```python
# Main strategy on EURUSD
sugar.set_defaults(symbol="EURUSD", magic=1001)

# Check correlation with GBPUSD
gbpusd_spread = None
with sugar.with_defaults(symbol="GBPUSD"):
    gbpusd_spread = await sugar.spread_pips()

# Check correlation with USDJPY
usdjpy_spread = None
with sugar.with_defaults(symbol="USDJPY"):
    usdjpy_spread = await sugar.spread_pips()

# Main symbol EURUSD still active
eurusd_spread = await sugar.spread_pips()  # Uses EURUSD

# Trade based on correlation
if eurusd_spread < 2.0 and gbpusd_spread < 3.0:
    await sugar.buy_market(lots=0.1)  # EURUSD
```

**Example 3: Risk-adjusted hedging**

```python
# Main position with standard risk
sugar.set_defaults(symbol="EURUSD", risk_percent=1.0)
ticket_main = await sugar.buy_market(lots=0.1)

# Hedge with lower risk
with sugar.with_defaults(symbol="EURUSD", risk_percent=0.5):
    lots_hedge = await sugar.calc_lot_by_risk(stop_pips=20)
    ticket_hedge = await sugar.sell_market(lots=lots_hedge)

# Back to standard risk for next trade
# risk_percent=1.0 restored automatically
```

**Example 4: Nested contexts**

```python
sugar.set_defaults(symbol="EURUSD", magic=1001, risk_percent=1.0)

with sugar.with_defaults(symbol="GBPUSD"):
    # GBPUSD, magic=1001, risk_percent=1.0
    await sugar.buy_market(lots=0.1)

    with sugar.with_defaults(risk_percent=2.0):
        # GBPUSD, magic=1001, risk_percent=2.0 (nested)
        lots = await sugar.calc_lot_by_risk(stop_pips=20)
        await sugar.buy_market(lots=lots)

    # Back to GBPUSD, magic=1001, risk_percent=1.0

# Back to EURUSD, magic=1001, risk_percent=1.0
```

**Example 5: Testing with different configurations**

```python
async def test_strategy_with_different_risks():
    """Test how strategy performs with different risk levels"""

    for risk_pct in [0.5, 1.0, 2.0, 3.0]:
        with sugar.with_defaults(risk_percent=risk_pct):
            lots = await sugar.calc_lot_by_risk(stop_pips=20)
            logger.info(f"Risk {risk_pct}% -> Lot size: {lots}")

    # Original risk_percent restored after loop
```
