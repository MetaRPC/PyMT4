# 🏗️ Architecture & Data Flow

*A practical map of how our Python SDK, gRPC services, and the MT4 terminal talk to each other — with just enough clarity to keep your margin level above 100%.*

---

## 🗺️ Big Picture

```
┌───────────────────────────────────────────────┐
│                 MT4 Terminal                  │
│      (broker login, quotes, trades)           │
└───────────────────────────────────────────────┘
                      │ local/IPC
                      ▼
┌───────────────────────────────────────────────┐
│      mt4_term_api.* (gRPC server)             │
│      Services: MarketQuota, Trade, Account... │
└───────────────────────────────────────────────┘
                      │ gRPC
                      ▼
┌───────────────────────────────────────────────┐
│      Python SDK (MetaRpcMT4)                  │
│      MT4Account (package/MetaRpcMT4/...)      │
│      + generated pb2/pb2_grpc stubs           │
└───────────────────────────────────────────────┘
                      │ async/await
                      ▼
┌───────────────────────────────────────────────┐
│      Service Layer (app/)                     │
│      MT4Service, MT4Service_Trade_mod         │
│      Connection mgmt, retry logic, hooks      │
└───────────────────────────────────────────────┘
                      │ async/await
                      ▼
┌───────────────────────────────────────────────┐
│      Sugar API (app/MT4Sugar.py)              │
│      Pip-based ops, auto-calculations         │
│      User-friendly wrappers                   │
└───────────────────────────────────────────────┘
                      │ async/await
                      ▼
┌───────────────────────────────────────────────┐
│      Strategy Layer (Strategy/)               │
│      Orchestrators: market_one_shot, etc.     │
│      Presets: Balanced, MarketEURUSD, etc.    │
└───────────────────────────────────────────────┘
                      │ async/await
                      ▼
┌───────────────────────────────────────────────┐
│      Your App / Examples                      │
│      (examples/, main*.py)                    │
└───────────────────────────────────────────────┘

```

**You write**: high‑level `await run_market_one_shot(...)` or `await sugar.buy_market(...)` calls.
**Sugar does**: pip↔price conversion, lot calculation, parameter validation.
**Service does**: connection management, retries, hooks, rate limiting.
**SDK does**: request building, metadata, deadlines, retries, unwraps `.reply.data`.
**Server does**: talks to the real MT4 terminal and executes.

---

## ⚙️ Main Components (by folders)

### 🔩 SDK & gRPC contracts (client side)

* `package/MetaRpcMT4/mt4_account.py` — **MT4Account** wrappers (public API).
* `package/MetaRpcMT4/mt4_term_api_*.py` — **pb2** messages (requests/replies/enums).
* `package/MetaRpcMT4/mt4_term_api_*_pb2_grpc.py` — **stubs** (client bindings).
* `package/MetaRpcMT4/mrpc_mt4_error_pb2.py` — errors/retcodes mapping.

### 🧠 Service layer (app/)

* `app/MT4Service.py` — core service wrapper, connection management. 🔌
* `app/MT4Service_Trade_mod.py` — trading operations wrapper. ☢️
* `app/MT4Sugar.py` — high-level sugar API with pip-based operations. 🍬
* `app/Helper/config.py` — settings loader (appsettings.json + env). ⚙️
* `app/Helper/hooks.py` — event hooks system (pre/post operations). 🪝
* `app/Helper/patch_mt4_account.py` — compatibility patches for MT4 quirks. 🧩
* `app/Helper/rate_limit.py` — API rate limiting protection. 🛡️
* `app/Helper/errors.py` — custom exceptions and error handling. 🚨

### 🎭 Strategy layer (Strategy/)

* `Strategy/orchestrator/*.py` — 13 ready-to-use trading scenarios.
* `Strategy/presets/risk.py` — 5 basic risk profiles (Conservative, Balanced, etc.).
* `Strategy/presets/risk_atr.py` — 3 ATR-based adaptive risk profiles.
* `Strategy/presets/risk_profiles.py` — symbol+style combinations.
* `Strategy/presets/risk_session.py` — session-based risk management.
* `Strategy/presets/strategy_symbols.py` — 30+ pre-configured symbols.

### 📚 Documentation & Examples

* `docs/MT4Account/**` — low-level API specs & overviews.
* `docs/MT4Sugar/**` — sugar API method documentation.
* `docs/Strategy/**` — orchestrators & presets guides.
* `examples/**` — runnable demo scripts.
* `main*.py` — entry point demos.

---

## 🔀 Data Flow (Unary Request)

### Example: Buy market order with Sugar API

```python
# 1. Your code
await sugar.buy_market("EURUSD", lots=0.1, sl_pips=20, tp_pips=40)

# 2. Sugar API (MT4Sugar.py)
# - Validates parameters
# - Converts pips to price (20 pips → 0.0020 for EURUSD)
# - Builds order request
# - Calls MT4Service_Trade_mod

# 3. Service Layer (MT4Service_Trade_mod.py)
# - Checks rate limits
# - Fires pre-operation hooks
# - Calls MT4Service.order_send()
# - Handles retries on failure
# - Fires post-operation hooks

# 4. Core Service (MT4Service.py)
# - Ensures connection alive
# - Adds metadata (login, session)
# - Sets timeout/deadline
# - Calls MT4Account.order_send()

# 5. SDK (package/MetaRpcMT4/mt4_account.py)
# - Builds gRPC Request protobuf
# - Calls stub: ServiceStub.OrderSend(request, metadata, timeout)
# - Waits for Reply
# - Unwraps reply.data
# - Returns order ticket

# 6. gRPC Server (mt4_term_api)
# - Receives request
# - Calls MT4 terminal functions
# - Executes order
# - Returns Reply with ticket/retcode

# 7. Result flows back through layers
# - SDK unwraps reply
# - Service processes hooks
# - Sugar returns clean result
# - Your code gets ticket number
```

---

## 🔄 Data Flow (Streaming)

Streams keep a channel open and push events. Use **cancellation\_event** and keep handlers **non‑blocking**.

### Example: Stream live ticks

```python
import asyncio

stop_event = asyncio.Event()

# 1. Your code subscribes
async for tick in sugar.on_symbol_tick(["EURUSD", "GBPUSD"], cancellation_event=stop_event):
    print(f"{tick.symbol}: {tick.bid}/{tick.ask}")

    if should_stop():
        stop_event.set()  # Signal to close stream

# 2. Sugar API
# - Validates symbols
# - Calls MT4Service.on_symbol_tick()

# 3. Service Layer
# - Ensures connection
# - Calls MT4Account.on_symbol_tick()
# - Monitors cancellation_event

# 4. SDK
# - Opens streaming gRPC channel
# - Yields events as they arrive
# - Closes on cancellation_event.set()

# 5. Server
# - Subscribes to terminal tick events
# - Streams ticks for requested symbols
# - Closes on client disconnect
```

Common streams:

* `on_symbol_tick` — live ticks per symbol. 📈
* `on_trade` — trade execution events (orders filled, positions changed). 💼
* `on_opened_orders_tickets` — stream of open ticket IDs. 🎫
* `on_opened_orders_profit` — stream of profit updates. 💰

Links: [Streams Overview](./MT4Account/Streams/Streams_Overview.md)

---

## 🧩 Layer Responsibilities

### Layer 1: Strategy Orchestrators 🎭
**What:** Complete trading workflows (market_one_shot, pending_bracket, spread_guard, etc.)

**Responsibilities:**
- Combine multiple operations into scenarios
- Implement trading logic (guards, timeouts, automation)
- Use presets for configuration
- Handle complex flows (wait for fill, activate trailing, etc.)

**Example:**
```python
from Strategy.orchestrator.market_one_shot import run_market_one_shot
from Strategy.presets import MarketEURUSD, Balanced

result = await run_market_one_shot(svc, MarketEURUSD, Balanced)
```

### Layer 2: Presets ⚙️
**What:** Reusable configurations (MarketEURUSD, Balanced, Conservative, etc.)

**Responsibilities:**
- Define WHAT to trade (symbol, entry type, magic number)
- Define HOW MUCH to risk (%, SL, TP, trailing)
- Provide consistent configurations
- Enable mixing and matching

**Example:**
```python
from Strategy.presets import MarketEURUSD, Balanced

strategy = MarketEURUSD  # WHAT: EURUSD, market entry
risk = Balanced          # HOW MUCH: 1% risk, 20 pip SL, 40 pip TP
```

### Layer 3: Sugar API 🍬
**What:** High-level convenience methods (buy_market, modify_sl_tp_by_pips, etc.)

**Responsibilities:**
- Pip↔price conversions
- Auto lot calculation by risk %
- Symbol info caching
- User-friendly parameter names
- Input validation

**Example:**
```python
await sugar.buy_market("EURUSD", lots=0.1, sl_pips=20, tp_pips=40)
# Converts pips to prices, validates, calls service layer
```

### Layer 4: Service Wrappers 🔌
**What:** MT4Service, MT4Service_Trade_mod

**Responsibilities:**
- Connection management (connect, reconnect, ensure_connected)
- Rate limiting (prevent API throttling)
- Hook system (pre/post operation events)
- Retry logic (handle transient failures)
- Session management

**Example:**
```python
svc = MT4Service(...)
await svc.ensure_connected()
result = await svc.order_send(request)
```

### Layer 5: SDK (Low-level) 🔧
**What:** MT4Account (package/MetaRpcMT4/mt4_account.py)

**Responsibilities:**
- gRPC request/response building
- Protobuf serialization
- Metadata handling
- Timeout/deadline management
- Reply unwrapping

**Example:**
```python
from package.MetaRpcMT4.mt4_account import MT4Account

acct = MT4Account(...)
ticket = await acct.order_send(request)
```

---

## 🔌 Connection Management

### Connection Flow

```
1. Load config (appsettings.json or env)
   ↓
2. Create MT4Service instance
   ↓
3. Call ensure_connected()
   ↓
4. Try connect_by_server_name()
   ↓
5. If fails, try connect_by_host_port() for each host in "access" list
   ↓
6. If all fail, retry with backoff
   ↓
7. Connection established ✓
   ↓
8. Store session metadata
   ↓
9. Enable rate limiting
   ↓
10. Ready for operations
```

### Connection States

```
┌─────────────┐
│ Disconnected│
└─────────────┘
       │
       │ ensure_connected()
       ▼
┌─────────────┐
│ Connecting  │
└─────────────┘
       │
       │ success
       ▼
┌─────────────┐     transient error
│  Connected  │ ◄──────────────────┐
└─────────────┘                    │
       │                           │
       │ operation                 │
       ▼                           │
┌─────────────┐     auto-retry    │
│  Operating  │ ───────────────────┘
└─────────────┘
       │
       │ disconnect()
       ▼
┌─────────────┐
│ Disconnected│
└─────────────┘
```

---

## 🪝 Hook System

Hooks allow you to intercept operations at key points.

### Hook Types

```python
from app.Helper.hooks import HookManager

hooks = HookManager()

# Before operation
@hooks.before("order_send")
async def log_order(request):
    print(f"Sending order: {request.symbol} @ {request.volume}")

# After operation (success)
@hooks.after("order_send")
async def log_success(request, result):
    print(f"Order filled: ticket={result.ticket}")

# After operation (error)
@hooks.on_error("order_send")
async def log_error(request, error):
    print(f"Order failed: {error}")
```

### Common Hook Points

- `order_send` — before/after placing orders
- `order_modify` — before/after modifying orders
- `order_close` — before/after closing positions
- `connect` — before/after connection attempts
- `quote` — before/after fetching quotes

---

## 🛡️ Rate Limiting

Prevents overwhelming the MT4 terminal with requests.

### Configuration

```python
from app.Helper.rate_limit import RateLimiter

# Max 10 requests per second
limiter = RateLimiter(max_calls=10, period=1.0)

async def safe_operation():
    async with limiter:
        result = await svc.quote("EURUSD")
    return result
```

### Default Limits

- Market data: 20 req/sec
- Trading operations: 5 req/sec
- History queries: 10 req/sec

---

## 🧩 Compatibility Patches

MT4 has quirks. We patch them in `app/Helper/patch_mt4_account.py`.

### Common Patches

1. **Symbol params normalization** — some symbols return null/zero values
2. **Quote time conversion** — ensure UTC timestamps
3. **Tick size fallbacks** — calculate from digits when missing
4. **Spread calculation** — handle negative spreads
5. **Magic number validation** — ensure valid range

### How Patches Work

```python
# Before patch
result = await acct.symbol_params_many(["EURUSD"])
# result.point might be 0 or null

# After patch (automatic)
result = await svc.symbol_params_many(["EURUSD"])
# result.point is calculated from digits if missing
```

---

## 📊 Request/Response Examples

### Example 1: Get Quote

```python
# High-level (Sugar)
quote = await sugar.last_quote("EURUSD")
# Returns: QuoteData(symbol="EURUSD", bid=1.10000, ask=1.10020, time=...)

# Low-level (SDK)
from package.MetaRpcMT4 import mt4_term_api_market_quota_pb2 as mq_pb2

request = mq_pb2.QuoteRequest(symbol="EURUSD")
reply = await acct.quote(request)
# Returns: QuoteReply.data with bid/ask/time
```

### Example 2: Place Market Order

```python
# High-level (Sugar)
ticket = await sugar.buy_market("EURUSD", lots=0.1, sl_pips=20, tp_pips=40)
# Sugar converts pips to prices, calls service

# Medium-level (Service)
result = await svc.order_send(
    symbol="EURUSD",
    order_type="market",
    volume=0.1,
    sl=1.09800,  # calculated from pips
    tp=1.10400,  # calculated from pips
)

# Low-level (SDK)
from package.MetaRpcMT4 import mt4_term_api_trading_action_pb2 as ta_pb2

request = ta_pb2.OrderSendRequest(
    symbol="EURUSD",
    order_type=ta_pb2.ORDER_TYPE_BUY,
    volume=0.1,
    sl=1.09800,
    tp=1.10400,
)
reply = await acct.order_send(request)
# Returns: OrderSendReply.data with ticket
```

---

## 🔍 Debugging Tips

### Enable Verbose Logging

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("MT4Service")
logger.setLevel(logging.DEBUG)
```

### Inspect gRPC Calls

```python
from app.Helper import grpc_debug

# Log all gRPC calls
grpc_debug.enable()

# Make calls
await svc.quote("EURUSD")
# Logs: Request, Reply, Duration

# Disable logging
grpc_debug.disable()
```

### Check Connection State

```python
is_connected = await svc.ping()
if not is_connected:
    await svc.ensure_connected()
```

### Monitor Rate Limits

```python
from app.Helper.rate_limit import get_limiter_stats

stats = get_limiter_stats()
print(f"Requests: {stats.calls} / {stats.limit}")
print(f"Window resets in: {stats.reset_in}s")
```

---

## 🎯 Performance Optimization

### 1. Cache Symbol Info

```python
# Bad: fetch every time
for i in range(100):
    digits = await sugar.digits("EURUSD")

# Good: cache once
digits = await sugar.digits("EURUSD")  # Automatically cached
for i in range(100):
    # Use cached value
    pass
```

### 2. Batch Quote Requests

```python
# Bad: one by one
quote1 = await sugar.last_quote("EURUSD")
quote2 = await sugar.last_quote("GBPUSD")

# Good: batch
quotes = await sugar.quotes(["EURUSD", "GBPUSD"])
```

### 3. Use Streams for Real-time Data

```python
# Bad: poll every second
while True:
    quote = await sugar.last_quote("EURUSD")
    await asyncio.sleep(1)

# Good: stream
async for tick in sugar.on_symbol_tick(["EURUSD"]):
    # Process tick immediately
    pass
```

### 4. Parallel Operations

```python
import asyncio

# Execute multiple operations in parallel
results = await asyncio.gather(
    sugar.last_quote("EURUSD"),
    sugar.last_quote("GBPUSD"),
    sugar.opened_orders(),
)
```

---

## 🧪 Testing Strategy

### Unit Tests (Mock SDK)

```python
from unittest.mock import AsyncMock

acct = AsyncMock()
acct.quote.return_value = QuoteReply(...)

svc = MT4Service(acct)
result = await svc.quote("EURUSD")
```

### Integration Tests (Demo Account)

```python
# Set ENABLE_TRADING=0 for safe testing
import os
os.environ["ENABLE_TRADING"] = "0"

# All trading operations will be simulated
await sugar.buy_market("EURUSD", lots=0.1)  # No real order
```

### Live Tests (Real Account)

```python
# Set ENABLE_TRADING=1 and use SMALL lots
os.environ["ENABLE_TRADING"] = "1"

# Real trading with minimal risk
await sugar.buy_market("EURUSD", lots=0.01, sl_pips=20, tp_pips=40)
```

---

## 📖 Related Documentation

* **[PROJECT_MAP.md](./PROJECT_MAP.md)** — Project structure and navigation
* **[MT4Account BASE](./MT4Account/BASE.md)** — Low-level API master overview
* **[MT4Sugar API](./MT4Sugar/)** — High-level API documentation
* **[Orchestrators Guide](./Strategy/All_about_orchestrator.md)** — Trading workflows
* **[Presets Guide](./Strategy/All_about_presets.md)** — Configuration presets

---

"May your architecture be solid, your data flow clean, and your trades profitable. 🏗️"
