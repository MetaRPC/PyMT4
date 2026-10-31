# Connection State Stream

> A live async stream of terminal connection-state changes.

**API Information:**

* **Low-level API:** `MT4Account.on_connect_state(...)` (defined in `package/MetaRpcMT4/mt4_account.py`)
* **gRPC service:** `mt4_term_api.Connection`
* **RPC:** `OnConnectState(OnConnectStateRequest) -> stream of OnConnectStateReply`
* **Payload:** `ConnectStateData`

## 💬 Just the essentials

* **What it is.** An async generator that yields the terminal's connection state — connected/alive flags, server and account, with a timestamp.
* **Why you need it.** To react to connectivity changes (drops, recoveries) for health monitoring and auto-recovery.
* **When to use.** Supervising a long-running bot. Drive it with a `cancellation_event`.

---

## 🎯 Purpose

* Connected / alive flags for the terminal session
* Server and account context
* Event timestamps and any error message

---

## Method Signature

```python
async def on_connect_state(
    self,
    terminal_ids: Optional[list[str]] = None,
    cancellation_event: Optional[asyncio.Event] = None,
)
```

**Request message:**

```protobuf
message OnConnectStateRequest {
  repeated string terminal_ids = 1;   // omit for the current session
}
```

**Payload message:**

```protobuf
message ConnectStateData {
  string id = 1;
  string state = 2;            // e.g. "Connected"
  bool is_connected = 3;
  bool is_alive = 4;
  bool api_is_alive = 5;
  string server = 6;
  uint64 account = 7;
  string error_message = 8;
  Timestamp timestamp = 9;
}
```

---

## 🔽 Input

| Parameter | Type | Description |
|-----------|------|-------------|
| `terminal_ids` | list[str], optional | Restrict to specific terminal ids; omit for the current session. |
| `cancellation_event` | asyncio.Event, optional | Set to stop the stream. |

---

## ⬆️ Output — async generator of `ConnectStateData`

| Field | Python Type | Description |
|-------|-------------|-------------|
| `state` | `str` | State label (e.g. `"Connected"`) |
| `is_connected` | `bool` | Session is connected to the server |
| `is_alive` | `bool` | Terminal is alive |
| `api_is_alive` | `bool` | API layer is alive |
| `server` | `str` | Server name |
| `account` | `int` | Account login |
| `error_message` | `str` | Error text, if any |
| `timestamp` | `datetime` | Event time |
| `id` | `str` | Terminal/session id |

---

## 🧩 Notes & Tips

* **`state` is a string**, not an enum — compare against labels like `"Connected"`, or rely on the `is_connected` / `is_alive` booleans.
* **Three liveness flags.** `is_connected` (to the broker), `is_alive` (terminal), `api_is_alive` (gateway) — a healthy session has all three true.
* **Check `error_message`** when a flag flips false — it carries the reason.
* **Works regardless of market hours** — it reports session health, not prices.
* **Always pass a `cancellation_event`** and `.set()` it to stop — see [gRPC Stream Management](../../All_Guides/GRPC_STREAM_MANAGEMENT.md).

---

## 🔗 Usage Examples

### 1) Watch connection state

```python
import asyncio

async def watch_state(account, stop: asyncio.Event):
    cancel = asyncio.Event()
    async def pump():
        async for ev in account.on_connect_state(cancellation_event=cancel):
            print(f"{ev.state} connected={ev.is_connected} alive={ev.is_alive} "
                  f"server={ev.server}")
    task = asyncio.create_task(pump())
    await stop.wait(); cancel.set(); await asyncio.sleep(0.3); task.cancel()
```

### 2) Wait until connected

Block until the session reports a healthy state (with a timeout).

```python
import asyncio

async def wait_connected(account, timeout=30) -> bool:
    cancel = asyncio.Event()
    async def watch():
        async for ev in account.on_connect_state(cancellation_event=cancel):
            if ev.is_connected and ev.is_alive:
                return True
    try:
        return await asyncio.wait_for(watch(), timeout=timeout)
    except asyncio.TimeoutError:
        cancel.set()
        return False
```

### 3) Alert on disconnect

Fire a callback the moment connectivity drops.

```python
import asyncio

async def on_disconnect(account, callback, stop: asyncio.Event):
    cancel = asyncio.Event()
    async def pump():
        async for ev in account.on_connect_state(cancellation_event=cancel):
            if not ev.is_connected or not ev.is_alive:
                callback(ev.state, ev.error_message)
    task = asyncio.create_task(pump())
    await stop.wait(); cancel.set(); await asyncio.sleep(0.3); task.cancel()
```

---

## ⚠️ Pitfalls

* **`state` is free-form text.** Prefer the boolean flags over string matching where possible.
* **No cancellation = leak.** Stop with a `cancellation_event` you `.set()`.
* **Events are sparse.** State is reported on change/heartbeat — don't expect a steady stream; use a timeout when waiting.

---

## 🧪 Testing Suggestions

* **Healthy session.** Shortly after connecting, an event has `state == "Connected"` with all three liveness flags true.
* **`wait_connected`.** Returns True on a live demo session within the timeout.
* **Clean stop.** `cancellation_event.set()` ends the loop without leaking tasks.

---

## 📚 See also

* [Trade Events Stream](on_trade.md)
* [Open-Order Profit Stream](on_opened_orders_profit.md)
* [gRPC Stream Management](../../All_Guides/GRPC_STREAM_MANAGEMENT.md)

* **Back to:** [Streaming Methods — Overview](Streaming_Methods.Overview.md) · [MT4Account — Master Overview](../MT4Account.Master.Overview.md)
