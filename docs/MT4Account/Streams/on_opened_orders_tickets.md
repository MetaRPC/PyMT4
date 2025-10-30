# ✅ Streaming Opened Order Tickets

> **Stream:** subscribe to **real‑time updates of the set of opened order/position tickets**.
> Yields `OnOpenedOrdersTicketsData` messages continuously until cancelled.

**Source files (SDK):**

* `MetaRpcMT4/mt4_account.py` — method `on_opened_orders_tickets(cancellation_event=None)`
* `MetaRpcMT4/mt4_term_api_subscriptions_pb2.py` — `OnOpenedOrdersTickets*` (request/reply/data)

### RPC

* **Service:** `mt4_term_api.Subscriptions`
* **Method (server‑streaming):** `OnOpenedOrdersTickets(OnOpenedOrdersTicketsRequest) → stream OnOpenedOrdersTicketsReply`
* **Low‑level client:** `SubscriptionsStub.OnOpenedOrdersTickets(request, metadata)` (async stream)
* **SDK wrapper:** `MT4Account.on_opened_orders_tickets(cancellation_event=None) → AsyncIterator[OnOpenedOrdersTicketsData]`

**Request message:** `OnOpenedOrdersTicketsRequest { pull_interval_ms?: int32 }`
**Reply message:** `OnOpenedOrdersTicketsReply { data: OnOpenedOrdersTicketsData }` (streamed)

> `pull_interval_ms` (if present in your pb) controls the server‑side polling cadence for generating ticket snapshots.

---

### 🔗 Code Example

```python
# Consume ticket-set updates and diff against previous
import asyncio

async def watch_tickets(acct):
    stop = asyncio.Event()
    prev = set()

    async for msg in acct.on_opened_orders_tickets(cancellation_event=stop):
        data = msg  # OnOpenedOrdersTicketsData
        cur = set(getattr(data, 'tickets', []))
        opened = cur - prev
        closed = prev - cur
        if opened:
            print("Opened now:", sorted(opened))
        if closed:
            print("Closed now:", sorted(closed))
        prev = cur
```

---

### Method Signature

```python
async def on_opened_orders_tickets(
    self,
    cancellation_event: asyncio.Event | None = None,
) -> AsyncIterator[subscriptions_pb2.OnOpenedOrdersTicketsData]
```

---

## 💬 Just the essentials

* **What it is.** A **lightweight stream** that tells you when the ticket set changes (opens/closes) without sending full order details.
* **Why.** Trigger refreshes (e.g., refetch `opened_orders()`), drive notifications, or maintain a live set for risk logic.
* **Efficient.** Much cheaper than streaming full orders; perfect for UI badges and counters.

---

## 🔽 Input

No required parameters. (Some builds expose `pull_interval_ms`.)

| Parameter            | Type           | Description |                                       |
| -------------------- | -------------- | ----------- | ------------------------------------- |
| `cancellation_event` | `asyncio.Event | None`       | Signal to stop the stream gracefully. |

---

## ⬆️ Output (streamed)

### Message: `OnOpenedOrdersTicketsData`

| Field                       | Proto Type                  | Description                                        |
| --------------------------- | --------------------------- | -------------------------------------------------- |
| `position_tickets`          | `int32[]`                   | Array of current market position tickets.          |
| `pending_order_tickets`     | `int32[]`                   | Array of current pending order tickets.            |
| `server_time`               | `google.protobuf.Timestamp` | Server timestamp of this snapshot (UTC).           |
| `terminal_instance_guid_id` | `string`                    | Terminal instance identifier.                      |

---

## 🧱 Related enums (from pb)

This stream **does not use method‑specific enums**.

---

### 🎯 Purpose

Use this stream to:

* Detect **opens/closes** instantly and refresh detail views lazily.
* Maintain a **live set** for quick membership checks before modify/close actions.
* Drive **UI counters** (e.g., number of open positions).

### 🧩 Notes & Tips

* After reconnect, expect the **full current set** (not a delta). Diff against your cache.
* For full details (symbol, lots, P/L), call `opened_orders()` once a change is detected.
* Combine with `on_opened_orders_profit(...)` to update totals without pulling full lists.

**See also:**
`opened_orders_tickets(...)` — snapshot endpoint (single call).
`opened_orders(...)` — full opened orders with details.
`on_opened_orders_profit(...)` — stream aggregated P/L.

---

## Usage Examples

### 1) UI badge with count

```python
async for s in acct.on_opened_orders_tickets():
    count = len(getattr(s, 'tickets', []))
    print(f"Open positions: {count}")
```

### 2) Trigger snapshot refresh on change

```python
prev = set()
async for s in acct.on_opened_orders_tickets():
    cur = set(getattr(s, 'tickets', []))
    if cur != prev:
        details = await acct.opened_orders()
        # update UI list
    prev = cur
```
