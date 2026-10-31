# PyMT4 Glossary

> Project-specific terms and concepts. This glossary covers PyMT4 architecture, components, and trading automation terminology used throughout the codebase.

---

## 🏗️ Architectural Terms

### Three-Tier Architecture

Core design pattern of PyMT4 with three abstraction levels:

- **Tier 1 (MT4Account):** Low-level gRPC communication with the MT4 terminal
- **Tier 2 (MT4Service):** Typed facade over MT4Account with convenience trade helpers
- **Tier 3 (MT4Sugar):** High-level one-liner API with ready-made patterns

---

### MT4Account

**🔹 Tier 1 - Low-Level API**

Base layer providing direct access to the MT4 terminal via the gRPC protocol.

**Key characteristics:**

- Raw gRPC calls to the MT4 terminal
- Built-in connection resilience with automatic reconnection (`execute_with_reconnect`)
- Works with protobuf Request/Response objects
- Full control, maximum complexity
- **18 core API methods** (account, orders, history, symbols/quotes, trading, streaming) plus connection & stream helpers
- Returns protobuf Data objects
- Session management via the terminal session GUID (`terminalInstanceGuid`)

**When to use:** Advanced users who need granular control, custom integrations, building custom wrappers.

**Location:** `package/MetaRpcMT4/mt4_account.py` (~1200 lines)

**Documentation:** [MT4Account API Reference](../MT4Account/MT4Account.Master.Overview.md)


---

### MT4Service
**🔸 Tier 2 - Typed Facade**

Middle layer providing simplified method signatures without proto boilerplate.

**Key characteristics:**

- Wraps **all 18 MT4Account operations** one-to-one (same names: `account_summary`, `opened_orders`, `orders_history`, `order_send`, `quote`, …)
- Adds convenience **trade helpers**: `buy_market` / `sell_market` / `buy_limit` / `sell_limit` / `buy_stop` / `sell_stop`, `close`, `close_by`, `close_partial`, `modify_sl_tp`
- `order_send_with_defaults` / `set_trade_defaults` for shared order defaults
- Exposes the high-level layer via the `service.sugar` property
- Primary purpose: architectural middleware layer that MT4Sugar is built on

**When to use:** Building custom strategies that need more control than Sugar but less boilerplate than MT4Account.

**Location:** `app/MT4Service.py` (~985 lines)

**Documentation:** [MT4Service Overview](../MT4Service/MT4Service.Overview.md)


---

### MT4Sugar
**🔺 Tier 3 - Convenience API**

High-level API for common trading operations.

**Key characteristics:**

- Async context-manager support (`async with MT4Sugar(service) as sugar`)
- Pips-first helpers (`sl_pips` / `tp_pips`, `pips_to_price`, `price_to_pips`)
- Unified order entry (`place_order`) with smart defaults (`set_defaults` / `with_defaults`)
- One-line operations and background watchers
- Type hints everywhere
- **~60 high-level methods**
- **Best starting point** for most use cases

**Key features:**

- `buy_market(symbol, lots=...)` - one line to open a market order
- `calc_lot_by_risk(symbol, risk_percent, stop_pips)` - automatic lot sizing by risk
- `buy_market(symbol, lots=..., sl_pips=..., tp_pips=...)` - open with SL/TP in pips
- `set_trailing_stop(ticket, distance_pips=...)` - server-side style trailing
- `close_all(symbol=...)` - bulk close / emergency exit

**When to use:** Rapid development, prototyping, simple strategies, quick scripts.

**Location:** `app/MT4Sugar.py` (~2230 lines)

**Documentation:** [MT4Sugar Reference](../MT4Sugar/MT4Sugar.Master.Overview.md)


---

## 🧩 Python-Specific Concepts

### Async/Await Pattern
Python's built-in asynchronous programming model.

**All methods in PyMT4 are async:**
```python
import asyncio
from MetaRpcMT4.mt4_account import MT4Account

async def main():
    # Create and connect
    account = MT4Account(user=user, password=password, grpc_server="mt4.mrpc.pro:443")
    await account.connect_by_server_name(server_name, base_chart_symbol="EURUSD", timeout_seconds=30)

    # Must use 'await' for all async operations
    summary = await account.account_summary()
    print(f"Balance: {summary.account_balance}")

    orders = await account.opened_orders()

    await account.channel.close()

# Run async function
asyncio.run(main())
```

**Why async?**

- Non-blocking I/O for gRPC calls
- Better performance for multiple operations
- Can handle streaming data efficiently
- Standard Python pattern for network operations

**Documentation:** [Python asyncio](https://docs.python.org/3/library/asyncio.html)

---

### Dataclasses
Python's structured data containers.

**The Strategy layer uses `@dataclass` presets** for clean, typed configuration:
```python
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

@dataclass
class RiskPreset:
    risk_percent: float
    sl_pips: float
    tp_pips: float | None = None
    trailing_pips: float | None = None
    be_trigger_pips: float | None = None
    be_plus_pips: float | None = None
```

> Account data (`account_summary`) comes back as a **protobuf object**, not a dataclass.
> Access its typed fields directly:

```python
summary = await service.account_summary()
print(summary.account_balance)       # float
print(summary.account_equity)        # float
print(summary.account_margin_free)   # float
```

**Benefits of dataclasses:**

- Type hints for IDE autocomplete
- Clean attribute access (no dict keys)
- Automatic `__repr__` and `__eq__`

---

### Async Generators
Python's way to stream data asynchronously.

**Low-level streaming methods return async generators:**
```python
# Streaming returns an async generator
async for tick_data in account.on_symbol_tick(["EURUSD"]):
    tick = tick_data.symbol_tick
    print(f"Bid: {tick.bid}, Ask: {tick.ask}")

    # Can break anytime
    if some_condition:
        break

# Auto cleanup when loop exits
```

**Critical rules:**

- Use `async for` to consume data
- Generator auto-stops when you break
- No manual cleanup needed

**Example with timeout:**
```python
import asyncio

try:
    async for tick_data in account.on_symbol_tick(["EURUSD"]):
        tick = tick_data.symbol_tick
        await asyncio.wait_for(process_tick(tick), timeout=5.0)
except asyncio.TimeoutError:
    print("Processing timeout")
```

---

### Reading Account State
MT4Sugar does **not** expose balance/equity as properties. Account state comes from
`account_summary()` (via Service or Account), which returns a protobuf object:

```python
summary = await service.account_summary()

balance      = summary.account_balance
equity       = summary.account_equity
margin        = summary.account_margin
free_margin   = summary.account_margin_free
margin_level  = summary.account_margin_level
```

For live prices, use the Sugar quote helpers:

```python
q   = await sugar.last_quote("EURUSD")   # {"bid": ..., "ask": ..., "time": ...}
mid = await sugar.mid_price("EURUSD")    # (bid + ask) / 2
spr = await sugar.spread_pips("EURUSD")  # spread in pips
```

---

### Context Managers
Python's pattern for automatic resource cleanup.

**MT4Sugar supports `async with`:**
```python
account = MT4Account(
    user=12345678,
    password="password",
    grpc_server="mt4.mrpc.pro:443",
)

await account.connect_by_server_name(
    server_name="EGlobal-Demo",
    base_chart_symbol="EURUSD",
)

service = MT4Service(account)

# Use sugar with a context manager
async with MT4Sugar(service) as sugar:
    q = await sugar.last_quote("EURUSD")
    ticket = await sugar.buy_market("EURUSD", lots=0.01)

# Manual channel cleanup still recommended
await account.channel.close()
```

**Why context managers?**

- Cleaner code structure
- Standard Python pattern
- Scoped resource usage

**Important: Manual channel cleanup**

`account.channel` is the gRPC connection to the MT4 terminal. Call `await account.channel.close()` to:

- Close the persistent gRPC connection
- Release network resources
- Prevent connection leaks

**Recommended pattern with proper cleanup:**

```python
account = MT4Account(
    user=12345678,
    password="password",
    grpc_server="mt4.mrpc.pro:443",
)

try:
    await account.connect_by_server_name(
        server_name="EGlobal-Demo",
        base_chart_symbol="EURUSD",
    )

    service = MT4Service(account)
    sugar = service.sugar

    # Work here
    q = await sugar.last_quote("EURUSD")
    ticket = await sugar.buy_market("EURUSD", lots=0.01)

finally:
    await account.channel.close()  # Always cleanup
```

---

## 📦 Technical Concepts

### Normalization
Adjustment of trading parameters to broker requirements.

**What gets normalized:**

- **Volumes (lots):** Rounded to the broker's volume step (e.g., 0.01)
- **Prices:** Rounded to the symbol's digits/tick size (e.g., 5 decimals for EURUSD)

**In PyMT4:** MT4Sugar exposes explicit helpers so you don't have to guess:

```python
# Round a lot size to the broker's volume step
lots = await sugar.normalize_lot("EURUSD", 0.0234)   # -> 0.02

# Round a price to the symbol's digits
price = await sugar.normalize_price("EURUSD", 1.09876543)  # -> 1.09877

# Point / pip size for the symbol
point = await sugar.point("EURUSD")       # e.g. 0.00001 (5-digit broker)
pip   = await sugar.pip_size("EURUSD")    # e.g. 0.0001
```

> `buy_market` / `buy_limit` / … normalize lots and prices internally, so manual
> normalization is only needed for your own calculations.

---

### Risk-Based Lot Calculation
Calculate position size based on account risk rather than a fixed lot size.

**Methods (MT4Sugar):**

```python
# Lot size for a given % risk and SL distance in pips
lots = await sugar.calc_lot_by_risk("EURUSD", risk_percent=2.0, stop_pips=50)

# Open using the risk-based lot
ticket = await sugar.buy_market("EURUSD", lots=lots, sl_pips=50, tp_pips=100)

# Monetary risk for a given lot + SL distance
cash_risk = await sugar.calc_cash_risk("EURUSD", lots=0.10, stop_pips=50)
```

**Use case:** Consistent risk management across all trades.

---

### Points vs Pips
**Point:** Smallest price movement for a symbol (1 tick).

**Pip:** Traditional forex unit (0.0001 for most pairs).

**Relationship:**

- **5-digit brokers:** 1 pip = 10 points (EURUSD: 1.10000 → 1.10010 = 1 pip)
- **3-digit brokers:** 1 pip = 10 points (USDJPY: 110.000 → 110.010 = 1 pip)

**In PyMT4:** MT4Sugar is **pips-first** — convert with helpers instead of hand-math:

```python
# pip size / point size
pip   = await sugar.pip_size("EURUSD")              # 0.0001
point = await sugar.point("EURUSD")                 # 0.00001

# Convert pips <-> absolute price delta
delta = await sugar.pips_to_price("EURUSD", 20)     # 20 pips -> 0.0020
pips  = await sugar.price_to_pips("EURUSD", 0.0020) # 0.0020  -> 20 pips
```

---

### Pip-Based Order Entry
Open orders with SL/TP expressed in pips (familiar for forex traders).

**Methods (MT4Sugar):**

```python
# Market orders with SL/TP in pips
ticket = await sugar.buy_market("EURUSD", lots=0.01, sl_pips=20, tp_pips=30)
ticket = await sugar.sell_market("GBPUSD", lots=0.01, sl_pips=20, tp_pips=30)

# Pending orders: absolute price + SL/TP in pips
ask = (await sugar.last_quote("EURUSD"))["ask"]
ticket = await sugar.buy_limit("EURUSD", price=ask - 0.0020, lots=0.01, sl_pips=15, tp_pips=30)

bid = (await sugar.last_quote("EURUSD"))["bid"]
ticket = await sugar.sell_limit("EURUSD", price=bid + 0.0020, lots=0.01, sl_pips=15, tp_pips=30)
```

> You can also pass absolute `sl_price=` / `tp_price=` instead of the pip variants.

---

### Trailing Stop
Dynamic Stop Loss that follows price in the profit direction.

**In PyMT4:** MT4Sugar runs a background trailing worker for you:

```python
# Start trailing: keep SL ~20 pips behind price, update in 5-pip steps
await sugar.set_trailing_stop(ticket, distance_pips=20, step_pips=5)

# Stop trailing that ticket
await sugar.unset_trailing_stop(ticket)
```

**Use case:** Locking in profit on trending markets.

---

### Breakeven
Moving the Stop Loss to (or past) the entry price to eliminate risk.

**Methods (MT4Sugar):**
```python
# Compute a breakeven price from an entry price (sync helper — no await)
bp = sugar.breakeven_price(entry_price=1.10000, commission=0.0, swap=0.0)

# Auto-move SL to breakeven once the order is far enough in profit
await sugar.auto_breakeven(ticket, trigger_pips=40, plus_pips=1)

# Or move SL to an absolute price manually
await sugar.modify_sl_tp_by_price(ticket, sl_price=bp)
```

---

### Hedging
Opening an opposite order to lock in the current profit/loss level.

**Implementation:**
```python
# Main order
buy_ticket = await sugar.buy_market("EURUSD", lots=0.10)

# ... price moves against you ...

# Hedge
sell_ticket = await sugar.sell_market("EURUSD", lots=0.10)
```

**WARNING:** Not all brokers/regulations allow hedging. US brokers typically do not support it.

---

### Pending Order
Order that executes automatically when price reaches a specified level.

**Types:**

- **BUY LIMIT:** Buy at a price BELOW current (expect pullback, then up)
- **SELL LIMIT:** Sell at a price ABOVE current (expect rally, then down)
- **BUY STOP:** Buy at a price ABOVE current (breakout up)
- **SELL STOP:** Sell at a price BELOW current (breakout down)

**Methods (MT4Sugar):**
```python
# Buy limit without SL/TP
ticket = await sugar.buy_limit("EURUSD", price=1.09950, lots=0.01)

# Buy limit with SL/TP in pips
ticket = await sugar.buy_limit("EURUSD", price=1.09950, lots=0.01, sl_pips=15, tp_pips=30)

# Sell stop with absolute SL/TP
ticket = await sugar.sell_stop("EURUSD", price=1.09950, lots=0.01,
                               sl_price=1.10000, tp_price=1.09900)

# Cancel pending orders (optionally filtered by symbol/magic)
await sugar.cancel_pendings(symbol="EURUSD")
```

---

## 🔌 gRPC and Protocol Terms

### gRPC
High-performance RPC (Remote Procedure Call) framework using HTTP/2.

**In PyMT4:**

- The MT4Account tier sends gRPC requests to the MetaRPC gateway
- Request/Response pattern for all operations
- Async/await for non-blocking calls

**Connection setup:**
```python
account = MT4Account(
    user=12345678,
    password="password",
    grpc_server="mt4.mrpc.pro:443",
)

await account.connect_by_server_name(
    server_name="EGlobal-Demo",
    base_chart_symbol="EURUSD",
)
```

**Documentation:** [gRPC Python](https://grpc.io/docs/languages/python/)

---

### Protobuf
Protocol Buffers - Google's language-neutral data serialization format.

**In PyMT4:**

- All MT4Account methods use protobuf Request/Response messages
- Generated into the `MetaRpcMT4.mt4_term_api_*_pb2` modules
- Efficient binary serialization, type-safe message structures

**Example:**

```python
from MetaRpcMT4 import mt4_term_api_trading_helper_pb2 as trading_helper_pb2

# ENUM values live on the generated pb2 modules
op = trading_helper_pb2.OrderSendOperationType.OC_OP_BUY
```

> MT4Account returns protobuf Data objects. MT4Service and MT4Sugar unwrap the parts
> you usually need into plain Python types (float, int, dict, int ticket).

---

### Return Codes & Errors
How trade failures surface in PyMT4.

- **MT4Account** raises `ApiExceptionMT4` when the server returns an error, and
  `ConnectExceptionMT4` if you call a method before connecting.
- **MT4Sugar** raises `MT4Error` subclasses (`OrderRejected`, `ModifyRejected`,
  `ConnectivityError`, `RateLimitExceeded`) with structured details.
- Order helpers return the **ticket number** (`int`) on success.

**Example:**

```python
from MetaRpcMT4.mt4_account import ApiExceptionMT4
from app.Helper.errors import OrderRejected

try:
    ticket = await sugar.buy_market("EURUSD", lots=0.01)
    print(f"Trade successful! Ticket: {ticket}")
except OrderRejected as e:
    print(f"Order rejected: {e}")
except ApiExceptionMT4 as e:
    print(f"Server error: {e}")
```

**Documentation:** [Return Codes Reference](RETURN_CODES_REFERENCE.md)

---

### 📡 Streaming Pattern
Real-time data streams.

**Low-level (async generators on MT4Account):**
```python
# Stream tick data
async for tick_data in account.on_symbol_tick(["EURUSD"]):
    tick = tick_data.symbol_tick
    print(f"Bid: {tick.bid}, Ask: {tick.ask}")
    if should_stop:
        break  # auto cleanup

# Stream trade events
async for ev in account.on_trade():
    print(f"Type: {ev.type}")

# Stream open-order P&L updates
async for ev in account.on_opened_orders_profit():
    for o in ev.opened_orders_with_profit_updated:
        print(o)
```

**High-level (callback watchers on MT4Sugar):**
```python
# Register a callback; returns a watch id
def on_tick(t):
    print(t)

watch_id = await sugar.watch_ticks("EURUSD", on_tick)
# ... later ...
await sugar.unwatch(watch_id)
```

**With timeout (Python 3.11+):**
```python
import asyncio

async with asyncio.timeout(60):  # 60 seconds max
    async for tick_data in account.on_symbol_tick(["EURUSD"]):
        process(tick_data.symbol_tick)
```

**Documentation:** [gRPC Stream Management](GRPC_STREAM_MANAGEMENT.md)

---

## 🏛️ Trading Terms

### Basic Trading Terms

Core trading concepts that every trader must understand before working with MT4.

| Term | Description | Example / Details |
|------|-------------|-------------------|
| **Bid** | Price at which the broker **buys** from you (you **sell** at Bid) | EURUSD Bid: 1.10000 |
| **Ask** | Price at which the broker **sells** to you (you **buy** at Ask) | EURUSD Ask: 1.10002 |
| **Spread** | Difference between Ask and Bid (broker's commission) | Ask 1.10002 − Bid 1.10000 = 2 pips spread |
| **Long / Buy** | Opening a BUY order (profit when price goes up) | Buy EURUSD at 1.10000, close at 1.10050 = +50 pips |
| **Short / Sell** | Opening a SELL order (profit when price goes down) | Sell EURUSD at 1.10000, close at 1.09950 = +50 pips |
| **Order** | A trade on the account — market or pending (MT4 has a single order list) | BUY 0.1 lot EURUSD at 1.10000 |
| **Market Order** | Order that executes immediately at the current price | BUY EURUSD at current Ask price |
| **Pending Order** | Order that triggers automatically when price reaches a level | BUY LIMIT at 1.09950 |
| **Lot / Volume** | Position size (1 lot = 100,000 units of base currency) | 0.01 lot = 1,000 units (micro lot) |
| **Stop Loss (SL)** | Price level for automatic loss-limiting exit | SL at 1.09950 limits loss to 50 pips |
| **Take Profit (TP)** | Price level for automatic profit-taking exit | TP at 1.10050 locks in 50 pips profit |
| **Pip** | Standard unit of price movement (0.0001 for most forex) | EURUSD: 1.10000 → 1.10010 = 1 pip |
| **Point** | Smallest price movement (1 tick) | For 5-digit broker: 1 pip = 10 points |
| **Leverage** | Borrowed capital from the broker (e.g., 1:100) | With 1:100, control $100,000 with $1,000 margin |
| **Margin** | Funds locked as collateral for open orders | 1 lot EURUSD at 1:100 ≈ $1,000 margin |
| **Free Margin** | Available funds for opening new orders | Equity − Margin |
| **Balance** | Account funds without considering open orders | Initial deposit + closed trades P/L |
| **Equity** | Current account value (Balance ± floating P/L) | Balance $10,000 + Floating $500 = Equity $10,500 |
| **Floating P/L** | Unrealized profit/loss of open orders | Order currently +$50 (not yet closed) |
| **Margin Level** | Ratio of Equity to Margin (%) | Equity $10,500 / Margin $1,000 = 1050% |
| **Margin Call** | Warning when Margin Level drops below a threshold | Broker warns at 100% Margin Level |
| **Stop Out** | Forced closure when Margin Level is critically low | Broker closes orders at ~50% Margin Level |
| **Drawdown** | Decline from peak balance/equity | Peak $11,000 → $10,000 = $1,000 drawdown |
| **Slippage** | Difference between expected and executed price | Requested 1.10000, filled 1.10003 = 3 pts slippage |

**Critical for API usage:**

```python
# Prices
q   = await sugar.last_quote("EURUSD")   # {"bid": ..., "ask": ..., "time": ...}
mid = await sugar.mid_price("EURUSD")

# Account state
summary = await service.account_summary()
balance = summary.account_balance
equity  = summary.account_equity

# Open orders
buy_ticket  = await sugar.buy_market("EURUSD", lots=0.01)
sell_ticket = await sugar.sell_market("EURUSD", lots=0.01)

# Close order
await sugar.close(buy_ticket)

# Modify SL/TP (absolute prices)
await sugar.modify_sl_tp_by_price(buy_ticket, sl_price=1.09950, tp_price=1.10050)
```

---

### Risk Amount
Account amount you're willing to risk if the Stop Loss hits.

**Used in:**

```python
# Lot size for 2% risk with 50-pip SL
lots = await sugar.calc_lot_by_risk("EURUSD", risk_percent=2.0, stop_pips=50)

# Open with the risk-based lot
ticket = await sugar.buy_market("EURUSD", lots=lots, sl_pips=50, tp_pips=100)
```

---

### Grid Trading
Strategy placing multiple pending orders at equal intervals around current price.

**How it works:**

1. Place Buy Limit orders below current price (e.g., every 20 pips)
2. Place Sell Limit orders above current price (e.g., every 20 pips)
3. As price oscillates, orders trigger and close at TP
4. Works best in ranging markets

**Implementation:**
```python
grid_step_pips = 20
levels = 5

q   = await sugar.last_quote("EURUSD")
ask, bid = q["ask"], q["bid"]

for i in range(1, levels + 1):
    offset = await sugar.pips_to_price("EURUSD", i * grid_step_pips)

    # Buy Limit below Ask
    await sugar.buy_limit("EURUSD", price=ask - offset, lots=0.01, sl_pips=15, tp_pips=30)

    # Sell Limit above Bid
    await sugar.sell_limit("EURUSD", price=bid + offset, lots=0.01, sl_pips=15, tp_pips=30)
```

> The project ships a ready `grid_dca` orchestrator — see the Strategies docs.

**WARNING:** High volatility can trigger many orders, increasing exposure.

---

### Scalping
Fast strategy with small profits (5–25 pips) and tight stops (10–20 pips).

**Implementation:**
```python
# Scalp with 10-pip SL, 15-pip TP
ticket = await sugar.buy_market("EURUSD", lots=0.01, sl_pips=10, tp_pips=15)
```

---

### News Trading (OCO Straddle)
Placing stop orders on both sides of price before a major news event.

**Implementation:**
```python
q = await sugar.last_quote("EURUSD")
offset = await sugar.pips_to_price("EURUSD", 30)   # 30 pips

buy_ticket  = await sugar.buy_stop("EURUSD", price=q["ask"] + offset, lots=0.01)
sell_ticket = await sugar.sell_stop("EURUSD", price=q["bid"] - offset, lots=0.01)

# ... after one side triggers, remove the remaining pending order ...
await sugar.cancel_pendings(symbol="EURUSD")
```

> The project ships a ready `oco_straddle` orchestrator — see the Strategies docs.

**WARNING:** Slippage during news can trigger both orders.

---

### Volume Limits
Broker restrictions on order size (min / max / step).

**In PyMT4:** `normalize_lot` snaps any value into the broker's allowed range and step:

```python
lots = await sugar.normalize_lot("EURUSD", 0.0234)   # -> 0.02 (step 0.01)
```

The raw min/max/step come from `symbol_params_many` at the MT4Account level if you
need them explicitly.

---

## 🔑 Configuration Terms

### Settings File
The examples read connection settings from `examples/0_common/settings.json`:

```json
{
  "user": 12345678,
  "password": "YOUR_MT4_PASSWORD",
  "grpc_server": "mt4.mrpc.pro:443",
  "mt_cluster": "EGlobal-Demo",
  "test_symbol": "EURUSD",
  "test_volume": 0.01,
  "api_key": "TRIAL"
}
```

`examples/0_common/demo_helpers.py` loads this file and also honours two environment
variables that override the file when set:

```bash
MRPC_API_KEY=mrpc_live_...        # overrides api_key
MRPC_GRPC_SERVER=mt4.mrpc.pro:443 # overrides grpc_server
```

**Load in Python:**
```python
from demo_helpers import load_settings, create_and_connect_mt4

config  = load_settings()
account = await create_and_connect_mt4(config)
```

> **Never commit real credentials.** The committed `settings.json` ships with
> placeholders; `.terminal_id` is git-ignored.

---

## Cross-Component Terms

### Batch Operations
Executing an action across multiple orders at once.

**Methods (MT4Sugar):**
```python
# Close all open orders (optionally filtered)
await sugar.close_all()                    # everything
await sugar.close_all(symbol="EURUSD")     # by symbol
await sugar.close_all(only_profit=True)    # only profitable

# Cancel pending orders
await sugar.cancel_pendings(symbol="EURUSD")
```

**Use case:** Emergency exits, end-of-session cleanup, strategy resets.

---

### 📝 History Queries
Retrieving past orders for analysis.

**Low-level (MT4Account):**
```python
from datetime import datetime, timedelta
from MetaRpcMT4 import mt4_term_api_account_helper_pb2 as account_helper_pb2

to_time = datetime.utcnow()
from_time = to_time - timedelta(days=30)

history = await account.orders_history(
    sort_mode=account_helper_pb2.EnumOrderHistorySortType.HISTORY_SORT_BY_CLOSE_TIME_DESC,
    from_time=from_time,
    to_time=to_time,
    page_number=0,
    items_per_page=100,
)
```

**High-level (MT4Sugar):**
```python
closed = await sugar.find_orders(state="closed", symbol="EURUSD")
```

**Use case:** Performance analysis, trade logs, strategy validation.

---

### Educational Project

PyMT4 examples and helpers are educational materials and API demonstrations, NOT production trading systems.

**Implications:**

- Study the code and patterns ✅
- Modify for your needs ✅
- Test on demo accounts ✅
- Use as templates for your strategies ✅
- Don't use as-is with real money ❌
- Don't expect production-grade risk management ❌

**Remember:** These are educational examples, not battle-tested production systems.

---

## Python-Specific Patterns

### Exception Handling
Python's error-handling mechanism for API errors.

**Connection / API exceptions:**
```python
from MetaRpcMT4.mt4_account import ConnectExceptionMT4, ApiExceptionMT4

try:
    await account.connect_by_server_name(
        server_name="EGlobal-Demo",
        base_chart_symbol="EURUSD",
    )
except ConnectExceptionMT4 as e:
    print(f"Connection failed: {e}")
except ApiExceptionMT4 as e:
    print(f"API error: {e}")
```

**Trading-operation errors (Sugar layer):**
```python
from app.Helper.errors import MT4Error, OrderRejected

try:
    ticket = await sugar.buy_market("EURUSD", lots=0.01)
    print(f"Order opened: ticket {ticket}")
except OrderRejected as e:
    print(f"Order rejected: {e}")
except MT4Error as e:
    print(f"SDK error: {e}")
```

---

### Type Hints
Python's optional static typing for better IDE support.

**All PyMT4 code uses type hints:**
```python
from typing import Optional

async def buy_market(
    self,
    symbol: str | None = None,
    *,
    lots: float | None = None,
    sl_pips: float | None = None,
    tp_pips: float | None = None,
) -> int:
    """Open a BUY market order. Returns the ticket number."""
    ...
```

**Benefits:**

- IDE autocomplete
- Static type checking (mypy)
- Catch errors before runtime

---

### 🧱 Enums
Named constants for protobuf values.

**PyMT4 enums live on the generated `mt4_term_api_*_pb2` modules:**
```python
from MetaRpcMT4 import mt4_term_api_trading_helper_pb2 as trading_helper_pb2
from MetaRpcMT4 import mt4_term_api_account_helper_pb2 as account_helper_pb2

# Order operation (used by order_send)
op = trading_helper_pb2.OrderSendOperationType.OC_OP_BUY

# History sort mode
sort = account_helper_pb2.EnumOrderHistorySortType.HISTORY_SORT_BY_CLOSE_TIME_DESC
```

> At the Sugar level you rarely touch enums directly — you pass `"buy"` / `"sell"`,
> pip distances and prices, and the SDK maps them to the right enum values.

**Documentation:** [Enums Usage Reference](ENUMS_USAGE_REFERENCE.md)

---

## See Also

- **[MT4Account API Reference](../MT4Account/MT4Account.Master.Overview.md)** - Low-level API reference
- **[MT4Service Overview](../MT4Service/MT4Service.Overview.md)** - Typed facade API
- **[MT4Sugar Reference](../MT4Sugar/MT4Sugar.Master.Overview.md)** - High-level Sugar API
- **[gRPC Stream Management](GRPC_STREAM_MANAGEMENT.md)** - Guide to streaming subscriptions
- **[Return Codes Reference](RETURN_CODES_REFERENCE.md)** - Return codes reference
- **[User Code Sandbox Guide](USERCODE_SANDBOX_GUIDE.md)** - How to write custom code
- **[Your First Project](Your_First_Project.md)** - Setup and quick start guide
- **[Enums Usage Reference](ENUMS_USAGE_REFERENCE.md)** - All available enums
- **[Protobuf Inspector Guide](PROTOBUF_INSPECTOR_GUIDE.md)** - Explore protobuf types

---

"Trade safely, code cleanly, and may your async functions always await gracefully."
