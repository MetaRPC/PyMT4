# ✅ Streaming Ticks — `on_symbol_tick`

> **Stream:** subscribe to **real‑time ticks** for one or more symbols.
> Yields `OnSymbolTickData` messages continuously until cancelled.

**Source files (SDK):**

* `MetaRpcMT4/mt4_account.py` — method `on_symbol_tick(symbols, cancellation_event=None)`
* `MetaRpcMT4/mt4_term_api_subscriptions_pb2.py` — `OnSymbolTick*` (request/reply/data)

### RPC

* **Service:** `mt4_term_api.Subscriptions`
* **Method (server‑streaming):** `OnSymbolTick(OnSymbolTickRequest) → stream OnSymbolTickReply`
* **Low‑level client:** `SubscriptionsStub.OnSymbolTick(request, metadata)` (async stream)
* **SDK wrapper:** `MT4Account.on_symbol_tick(symbols: list[str], cancellation_event=None) → AsyncIterator[OnSymbolTickData]`

**Request message:** `OnSymbolTickRequest { symbol_names: string[] }`
**Reply message:** `OnSymbolTickReply { data: OnSymbolTickData }` (streamed)

---

### 🔗 Code Example

```python
# Consume tick stream with graceful cancellation
import asyncio

async def consume_ticks(acct, symbols):
    cancel = asyncio.Event()

    async def stopper():
        await asyncio.sleep(10)   # demo: stop after 10s
        cancel.set()

    asyncio.create_task(stopper())

    async for msg in acct.on_symbol_tick(symbols, cancellation_event=cancel):
        tick = msg.symbol_tick  # OnSymbolMqlTickInfo
        print(f"{tick.symbol}: bid={tick.bid}, ask={tick.ask}, last={tick.last}, time={tick.time}")
```

---

### Method Signature

```python
async def on_symbol_tick(
    self,
    symbols: list[str],
    cancellation_event: asyncio.Event | None = None,
) -> AsyncIterator[subscriptions_pb2.OnSymbolTickData]
```

---

## 💬 Just the essentials

* **What it is.** A **server‑stream** of ticks for the requested symbols.
* **Why.** Drive live price tiles, trigger signal logic, or maintain in‑memory quote caches.
* **Stop policy.** Provide `cancellation_event` to terminate cooperatively; the wrapper handles reconnects.

---

## 🔽 Input

| Parameter            | Type           | Description              |                                       |
| -------------------- | -------------- | ------------------------ | ------------------------------------- |
| `symbols`            | `list[str]`    | Symbols to subscribe to. |                                       |
| `cancellation_event` | `asyncio.Event | None`                    | Signal to stop the stream gracefully. |

---

## ⬆️ Output (streamed)

### Message: `OnSymbolTickData`

| Field                       | Proto Type            | Description                          |
| --------------------------- | --------------------- | ------------------------------------ |
| `symbol_tick`               | `OnSymbolMqlTickInfo` | Tick information for the symbol.     |
| `terminal_instance_guid_id` | `string`              | Terminal instance identifier.        |

### Nested: `OnSymbolMqlTickInfo`

| Field      | Proto Type                  | Description                              |
| ---------- | --------------------------- | ---------------------------------------- |
| `symbol`   | `string`                    | Symbol name.                             |
| `time`     | `google.protobuf.Timestamp` | Tick server timestamp (UTC).             |
| `bid`      | `double`                    | Best bid price.                          |
| `ask`      | `double`                    | Best ask price.                          |
| `last`     | `double`                    | Last traded price (if broker supplies).  |
| `volume`   | `uint64`                    | Volume for the tick.                     |
| `time_msc` | `int64`                     | Tick timestamp in milliseconds.          |

---

## 🧱 Related enums (from pb)

This stream **does not use method‑specific enums**.

---

### 🎯 Purpose

Use this stream to:

* Keep **real‑time** UI tiles in sync.
* Update in‑memory caches backing `quote(...)` fallbacks.
* Fire **signals** (cross/threshold rules) without polling.

### 🧩 Notes & Tips

* The wrapper calls `execute_stream_with_reconnect(...)` → it will retry on transient network errors.
* Keep the symbol list compact for low latency; use `quote_many(...)` for snapshot refills.
* When back‑pressure grows, consider sampling or debouncing on the client side.

**See also:**
`quote(...)` / `quote_many(...)` — on‑demand snapshots.
`on_opened_orders_tickets(...)` — stream of position ticket changes.
`on_opened_orders_profit(...)` — stream of aggregated P/L.

---

## Usage Examples

### 1) Debounced UI updates

```python
from time import monotonic

last_ui = 0
DEBOUNCE = 0.25
async for t in acct.on_symbol_tick(["EURUSD","XAUUSD"]):
    now = monotonic()
    if now - last_ui >= DEBOUNCE:
        last_ui = now
        # push a UI snapshot assembled from latest tick per symbol
```

### 2) Maintain a live cache for mid/spread

```python
cache = {}
async for t in acct.on_symbol_tick(["EURUSD","GBPUSD"]):
    sym = getattr(t, 'symbol', getattr(t, 'symbolName', None))
    bid = getattr(t, 'bid', None)
    ask = getattr(t, 'ask', None)
    if sym and bid and ask:
        cache[sym] = {"mid": (bid+ask)/2, "bid": bid, "ask": ask}
```

### 3) Cooperative shutdown

```python
stop = asyncio.Event()
asyncio.get_event_loop().call_later(5.0, stop.set)
async for _ in acct.on_symbol_tick(["USDJPY"], cancellation_event=stop):
    pass
```
