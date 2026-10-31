# Symbol Tick Stream

> A live async stream of tick (bid/ask) updates for one or more symbols.

**API Information:**

* **Low-level API:** `MT4Account.on_symbol_tick(...)` (defined in `package/MetaRpcMT4/mt4_account.py`)
* **gRPC service:** `mt4_term_api.SubscriptionService`
* **RPC:** `OnSymbolTick(OnSymbolTickRequest) -> stream of OnSymbolTickReply`
* **Payload:** `OnSymbolTickData`

## 💬 Just the essentials

* **What it is.** An async generator that yields a tick every time the price of a subscribed symbol changes.
* **Why you need it.** To react to price in real time instead of polling [quote](../3. Symbols_Quotes/quote.md).
* **When to use.** Live strategies, dashboards, spread/price monitors. Always drive it with a `cancellation_event`.

---

## 🎯 Purpose

* Live bid/ask per symbol
* Subscribe to several symbols in one stream
* Clean stop via a cancellation event

---

## Method Signature

```python
async def on_symbol_tick(
    self,
    symbols: list[str],
    cancellation_event: Optional[asyncio.Event] = None,
)
```

**Request message:**

```protobuf
message OnSymbolTickRequest {
  repeated string symbol_names = 1;
}
```

**Payload message:**

```protobuf
message OnSymbolTickData {
  OnSymbolMqlTickInfo symbol_tick = 1;
  string terminal_instance_guid_id = 2;
}

message OnSymbolMqlTickInfo {
  Timestamp time = 1;
  Timestamp time_utc = 2;
  double bid = 3;
  double ask = 4;
  double last = 5;
  uint64 volume = 6;
  int64 time_msc = 7;
  int64 time_msc_utc = 8;
  string symbol = 9;
}
```

---

## 🔽 Input

| Parameter | Type | Description |
|-----------|------|-------------|
| `symbols` | `list[str]` | Symbols to subscribe to. |
| `cancellation_event` | asyncio.Event, optional | Set to stop the stream. |

---

## ⬆️ Output — async generator of `OnSymbolTickData`

Each item has `symbol_tick` (`OnSymbolMqlTickInfo`):

| Field | Python Type | Description |
|-------|-------------|-------------|
| `symbol` | `str` | Symbol |
| `bid` / `ask` | `float` | Current bid / ask |
| `last` | `float` | Last price (if provided) |
| `volume` | `int` | Tick volume |
| `time` / `time_utc` | `datetime` | Tick time (server / UTC) |

---

## 🧩 Notes & Tips

* **Consume with `async for`.** Each iteration is one tick for one of the subscribed symbols — check `tick.symbol` to tell them apart.
* **Always pass a `cancellation_event`** and `.set()` it to stop cleanly, otherwise the stream (and its reconnect loop) keeps running — see [gRPC Stream Management](../../All_Guides/GRPC_STREAM_MANAGEMENT.md).
* **Auto-reconnect.** Transient gRPC drops are retried under the hood; your `async for` keeps yielding across a reconnect.
* **No ticks on a closed market.** On weekends/holidays the stream stays open but yields nothing — use a timeout so you don't block forever.
* **For a one-shot price** use [quote](../3. Symbols_Quotes/quote.md); for several at once [quote_many](../3. Symbols_Quotes/quote_many.md).

---

## 🔗 Usage Examples

### 1) Stream N ticks then stop

```python
import asyncio

async def first_ticks(account, symbol="EURUSD", n=5):
    cancel = asyncio.Event()
    count = 0
    async for td in account.on_symbol_tick([symbol], cancellation_event=cancel):
        t = td.symbol_tick
        print(f"{t.symbol}: bid={t.bid:.5f} ask={t.ask:.5f}")
        count += 1
        if count >= n:
            cancel.set()
            break
```

### 2) Keep the latest price per symbol

Maintain a live snapshot dict you can read from elsewhere.

```python
import asyncio

async def live_prices(account, symbols, stop: asyncio.Event):
    latest = {}
    cancel = asyncio.Event()
    async def pump():
        async for td in account.on_symbol_tick(symbols, cancellation_event=cancel):
            t = td.symbol_tick
            latest[t.symbol] = (t.bid, t.ask)
    task = asyncio.create_task(pump())
    await stop.wait()          # run until the caller signals stop
    cancel.set()
    await asyncio.sleep(0.3)
    task.cancel()
    return latest
```

### 3) Alert on a price level

Stop the stream as soon as a target is hit.

```python
import asyncio

async def wait_for_price(account, symbol, target, above=True, timeout=60):
    cancel = asyncio.Event()
    async def watch():
        async for td in account.on_symbol_tick([symbol], cancellation_event=cancel):
            bid = td.symbol_tick.bid
            if (above and bid >= target) or (not above and bid <= target):
                print(f"{symbol} hit {target} (bid={bid:.5f})")
                cancel.set()
                return True
    try:
        return await asyncio.wait_for(watch(), timeout=timeout)
    except asyncio.TimeoutError:
        cancel.set()
        return False
```

---

## ⚠️ Pitfalls

* **No cancellation = leak.** Without a `cancellation_event` you set, the stream and its reconnect loop run forever.
* **Blocking on a quiet market.** Closed sessions yield no ticks — wrap consumption in `asyncio.wait_for`/`asyncio.timeout`.
* **Per-tick work must be fast.** Heavy processing inside the loop backs up the stream — offload to a queue/task.
* **Distinguish symbols.** With multiple symbols, always branch on `tick.symbol`.

---

## 🧪 Testing Suggestions

* **Market open.** Subscribing to a liquid symbol yields ticks within a second; `ask >= bid`.
* **Clean stop.** After `cancellation_event.set()` the `async for` exits promptly without leaking tasks.
* **Timeout path.** On a closed market, a `wait_for(..., timeout=5)` returns/raises rather than hanging.

---

## 📚 See also

* [Quote](../3. Symbols_Quotes/quote.md)
* [Trade Events Stream](on_trade.md)
* [gRPC Stream Management](../../All_Guides/GRPC_STREAM_MANAGEMENT.md)

* **Back to:** [Streaming Methods — Overview](Streaming_Methods.Overview.md) · [MT4Account — Master Overview](../MT4Account.Master.Overview.md)
