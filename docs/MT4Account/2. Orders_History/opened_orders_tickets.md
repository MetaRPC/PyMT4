# Opened Order Tickets

> Just the ticket numbers of currently open orders — the cheapest way to poll "what's open now".

**API Information:**

* **Low-level API:** `MT4Account.opened_orders_tickets(...)` (defined in `package/MetaRpcMT4/mt4_account.py`)
* **gRPC service:** `mt4_term_api.AccountHelper`
* **RPC:** `OpenedOrdersTickets(OpenedOrdersTicketsRequest) -> OpenedOrdersTicketsReply`
* **Payload:** `OpenedOrdersTicketsData`

## 💬 Just the essentials

* **What it is.** A flat list of open ticket numbers — no prices, no profit, just ids.
* **Why you need it.** Minimal payload for high-frequency "is anything open / did it change?" checks.
* **When to use.** Polling loops. When you need the actual details, call [opened_orders](opened_orders.md).

---

## 🎯 Purpose

* Minimal payload — ticket ids only
* Cheap to call in a tight loop
* Pair with [opened_orders](opened_orders.md) to fetch detail only when something changed

---

## Method Signature

```python
async def opened_orders_tickets(
    self,
    deadline: Optional[datetime] = None,
    cancellation_event: Optional[asyncio.Event] = None,
)
```

**Request message:**

```protobuf
message OpenedOrdersTicketsRequest {
}
```

**Payload message:**

```protobuf
message OpenedOrdersTicketsData {
  repeated int32 tickets = 1;   // open order tickets (market + pending)
}
```

---

## 🔽 Input

| Parameter | Type | Description |
|-----------|------|-------------|
| `deadline` | datetime, optional | Absolute UTC deadline for the gRPC call. |
| `cancellation_event` | asyncio.Event, optional | Set to abort the request. |

---

## ⬆️ Output — `OpenedOrdersTicketsData`

| Field | Python Type | Description |
|-------|-------------|-------------|
| `tickets` | `list[int]` | Ticket numbers of all open orders (market + pending) |

---

## 🧩 Notes & Tips

* **One flat list.** Unlike the streaming [on_opened_orders_tickets](../5. Streaming_Methods/on_opened_orders_tickets.md) (which splits positions from pending), this returns a single `tickets` list covering both.
* **Set math is your friend.** Convert to a `set` to diff against a previous poll and spot what opened or closed.
* **Fetch detail on change only.** Poll this; when the set changes, call [opened_orders](opened_orders.md) once to get the new details — far cheaper than pulling full detail every tick.

---

## 🔗 Usage Examples

### 1) Is anything open?

A one-liner liveness/exposure check.

```python
async def has_open_orders(account) -> bool:
    data = await account.opened_orders_tickets()
    return len(data.tickets) > 0
```

### 2) Detect opened / closed between polls

Diff two snapshots to react only when the set of open orders changes.

```python
import asyncio

async def watch_changes(account, interval: float = 1.0):
    prev = set()
    while True:
        now = set((await account.opened_orders_tickets()).tickets)
        opened, closed = now - prev, prev - now
        if opened:
            print("opened:", sorted(opened))
        if closed:
            print("closed:", sorted(closed))
        prev = now
        await asyncio.sleep(interval)
```

### 3) Poll cheap, fetch detail on change

Only pull full order detail when the ticket set actually changes.

```python
async def refresh_on_change(account, prev_tickets: set[int]):
    now = set((await account.opened_orders_tickets()).tickets)
    if now != prev_tickets:
        details = await account.opened_orders()     # one detailed call, only when needed
        print(f"{len(details.order_infos)} open order(s) now")
        return now, details
    return now, None
```

---

## ⚠️ Pitfalls

* **Ids only.** No prices, SL/TP or profit here — don't try to make risk decisions from this call alone.
* **Market + pending mixed.** The list doesn't tell you which tickets are filled vs resting; use [opened_orders](opened_orders.md) for that.
* **Empty when flat.** No open orders → empty `tickets` list.

---

## 🧪 Testing Suggestions

* **Flat account.** `tickets` is empty.
* **After opening an order.** The new ticket appears in `tickets` and matches the ticket returned by [order_send](../4. Trading_Operations/order_send.md).
* **Diff logic.** Open then close an order across two polls and assert the change-detector reports it once as opened, once as closed.

---

## 📚 See also

* [Opened Orders](opened_orders.md)
* [Orders History](orders_history.md)
* [On Opened Orders Tickets (stream)](../5. Streaming_Methods/on_opened_orders_tickets.md)

* **Back to:** [Orders & History — Overview](Orders_History.Overview.md) · [MT4Account — Master Overview](../MT4Account.Master.Overview.md)
