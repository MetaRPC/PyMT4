# Synchronous vs Asynchronous Methods - When to Use What (Python)

> Understanding the execution model in PyMT4: it is **async-first**, and how to drive it from scripts, notebooks and bots.

---

## 🎯 The short version

**PyMT4 is asynchronous end-to-end.** Every network method on `MT4Account`,
`MT4Service` and `MT4Sugar` is an `async def` and must be `await`-ed inside an
asyncio event loop. There are **no blocking synchronous network wrappers** — the only
non-async members are small local helpers (config setters like `set_defaults`,
pure calculations like `breakeven_price`).

So "sync vs async" in PyMT4 is really two practical questions:

1. **How do I run the event loop?** — `asyncio.run(...)` in a script, direct `await`
   in a notebook (Jupyter/IPython already runs a loop).
2. **Sequential or concurrent?** — plain `await` calls run one after another;
   `asyncio.gather` and `async for` streams run work concurrently.

---

## 🧭 Choosing a pattern

| Aspect | Sequential `await` | Concurrent (`gather` / streaming) |
|--------|--------------------|-----------------------------------|
| **Thread blocking** | Non-blocking (awaits yield the loop) | Non-blocking |
| **Throughput** | One operation at a time | Many operations / events in flight |
| **Real-time data** | ⚠️ Not ideal for continuous streams | ✅ Perfect for tick & trade streams |
| **Simplicity** | Simplest, linear to read | Needs care with ordering/cancellation |
| **Use for** | Scripts, notebooks, one-offs | Bots, multi-symbol trading, services |

---

## ▶️ Running from a script

Use `asyncio.run()` to start the loop, then `await` inside:

```python
import asyncio
from MetaRpcMT4.mt4_account import MT4Account

async def main():
    account = MT4Account(user=user, password=password, grpc_server=grpc_server)
    await account.connect_by_server_name(server_name, base_chart_symbol="EURUSD", timeout_seconds=30)
    summary = await account.account_summary()
    print(f"Balance: {summary.account_balance}, Equity: {summary.account_equity}")
    await account.channel.close()

asyncio.run(main())
```

## 📓 Running from a notebook (Jupyter / IPython)

A notebook already runs an event loop, so you `await` directly — **do not** call
`asyncio.run()` (it would error with "event loop is already running"):

```python
account = MT4Account(user=user, password=password, grpc_server=grpc_server)
await account.connect_by_server_name(server_name, base_chart_symbol="EURUSD", timeout_seconds=30)
summary = await account.account_summary()
print(summary.account_balance)
```

---

## 🚀 Concurrency patterns

### 1. Market data streaming

Ticks arrive continuously. Consume them with `async for` so your loop never blocks:

```python
cancel = asyncio.Event()
async for tick_data in account.on_symbol_tick(["EURUSD"], cancellation_event=cancel):
    tick = tick_data.symbol_tick
    print(f"{tick.symbol}: Bid={tick.bid:.5f} Ask={tick.ask:.5f}")
```

See [gRPC Stream Management](GRPC_STREAM_MANAGEMENT.md) for cancellation and cleanup.

### 2. Concurrent requests across symbols

Run independent calls at the same time with `asyncio.gather` instead of awaiting
them one by one:

```python
eur, gbp, usdjpy = await asyncio.gather(
    sugar.last_quote("EURUSD"),
    sugar.last_quote("GBPUSD"),
    sugar.last_quote("USDJPY"),
)
```

---

## 💡 Summary

- Everything that touches the network is `async` — always `await` it.
- In a **script**, wrap your code in `async def` and launch with `asyncio.run()`.
- In a **notebook**, `await` directly (the loop already exists).
- Reach for `asyncio.gather` and `async for` when you need concurrency or live streams.
