# Opened Order Tickets Stream

> A periodic stream of the live open ticket lists — positions and pending orders.

**API Information:**

* **Low-level API:** `MT4Account.on_opened_orders_tickets(...)` (defined in `package/MetaRpcMT4/mt4_account.py`)
* **gRPC service:** `mt4_term_api.SubscriptionService`
* **RPC:** `OnOpenedOrdersTickets(OnOpenedOrdersTicketsRequest) -> stream of OnOpenedOrdersTicketsReply`
* **Payload:** `OnOpenedOrdersTicketsData`

## 💬 Just the essentials

* **What it is.** A lightweight heartbeat: every `pull_interval_milliseconds` it yields the current lists of open position and pending-order tickets.
* **Why you need it.** Cheap "what's open now?" monitoring without pulling full order detail.
* **When to use.** Change detection and liveness. For full detail fetch [opened_orders](../2. Orders_History/opened_orders.md) when something changes.

---

## 🎯 Purpose

* Separate position and pending ticket lists
* Server-side sampling interval
* Minimal payload for monitoring loops

---

## Method Signature

```python
async def on_opened_orders_tickets(
    self,
    pull_interval_milliseconds: int = 500,
    cancellation_event: Optional[asyncio.Event] = None,
)
```

**Request message:**

```protobuf
message OnOpenedOrdersTicketsRequest {
  int32 pullIntervalMilliseconds = 1;
}
```

**Payload message:**

```protobuf
message OnOpenedOrdersTicketsData {
  repeated int32 position_tickets = 1;
  repeated int32 pending_order_tickets = 2;
  Timestamp server_time = 3;
  Timestamp server_time_utc = 4;
  string terminal_instance_guid_id = 5;
}
```

---

## 🔽 Input

| Parameter | Type | Description |
|-----------|------|-------------|
| `pull_interval_milliseconds` | `int` | How often the server samples the ticket lists. Default 500. |
| `cancellation_event` | asyncio.Event, optional | Set to stop the stream. |

---

## ⬆️ Output — async generator of `OnOpenedOrdersTicketsData`

| Field | Python Type | Description |
|-------|-------------|-------------|
| `position_tickets` | `list[int]` | Open position (market order) tickets |
| `pending_order_tickets` | `list[int]` | Pending order tickets |
| `server_time` / `server_time_utc` | `datetime` | Sample time (server / UTC) |

---

## 🧩 Notes & Tips

* **Positions and pendings are split here** — unlike the one-shot [opened_orders_tickets](../2. Orders_History/opened_orders_tickets.md), which returns a single flat list.
* **Tune `pull_interval_milliseconds`.** 500 ms is responsive; raise it (e.g. 2000) to reduce chatter for slow strategies.
* **Fetch detail on change.** When a ticket set changes, call [opened_orders](../2. Orders_History/opened_orders.md) once — don't stream full detail.
* **Always pass a `cancellation_event`** and `.set()` it to stop — see [gRPC Stream Management](../../All_Guides/GRPC_STREAM_MANAGEMENT.md).
* **This heartbeat works even on a closed market** (it samples current state, not ticks).

---

## 🔗 Usage Examples

### 1) Heartbeat of open tickets

```python
async def heartbeat(account):
    async for ev in account.on_opened_orders_tickets(pull_interval_milliseconds=1000):
        print(f"positions={list(ev.position_tickets)} pending={list(ev.pending_order_tickets)}")
```

### 2) Detect opened / closed positions

Diff successive samples and act only on change.

```python
import asyncio

async def watch_positions(account, stop: asyncio.Event):
    prev = set()
    cancel = asyncio.Event()
    async def pump():
        nonlocal prev
        async for ev in account.on_opened_orders_tickets(cancellation_event=cancel):
            now = set(ev.position_tickets)
            if now != prev:
                print("opened:", now - prev, "closed:", prev - now)
                prev = now
    task = asyncio.create_task(pump())
    await stop.wait(); cancel.set(); await asyncio.sleep(0.3); task.cancel()
```

### 3) React when a pending order appears

```python
import asyncio

async def wait_for_pending(account, timeout=30):
    cancel = asyncio.Event()
    async def watch():
        async for ev in account.on_opened_orders_tickets(cancellation_event=cancel):
            if ev.pending_order_tickets:
                return list(ev.pending_order_tickets)
    try:
        return await asyncio.wait_for(watch(), timeout=timeout)
    except asyncio.TimeoutError:
        cancel.set()
        return []
```

---

## ⚠️ Pitfalls

* **Ids only.** No prices/profit here — fetch [opened_orders](../2. Orders_History/opened_orders.md) for detail.
* **No cancellation = leak.** Stop with a `cancellation_event` you `.set()`.
* **Interval trade-off.** Too small a `pull_interval_milliseconds` is chatty; too large is laggy — tune to your needs.

---

## 🧪 Testing Suggestions

* **Existing orders.** With open orders, `position_tickets` matches the one-shot [opened_orders_tickets](../2. Orders_History/opened_orders_tickets.md).
* **Change detection.** Open then close an order and assert the diff reports it once opened, once closed.
* **Clean stop.** `cancellation_event.set()` ends the loop without leaking tasks.

---

## 📚 See also

* [Opened Order Tickets](../2. Orders_History/opened_orders_tickets.md)
* [Open-Order Profit Stream](on_opened_orders_profit.md)
* [gRPC Stream Management](../../All_Guides/GRPC_STREAM_MANAGEMENT.md)

* **Back to:** [Streaming Methods — Overview](Streaming_Methods.Overview.md) · [MT4Account — Master Overview](../MT4Account.Master.Overview.md)
