# ✅ Getting Opened Order Tickets

> **Request:** retrieve the list of **tickets for all currently opened orders/positions** as a lightweight payload (`OpenedOrdersTicketsData`).
> Fastest way to enumerate active tickets without pulling full order details.

**Source files (SDK):**

* `MetaRpcMT4/mt4_account.py` — method `opened_orders_tickets(...)`
* `MetaRpcMT4/mt4_term_api_account_helper_pb2.py` — `OpenedOrdersTickets*`

### RPC

* **Service:** `mt4_term_api.AccountHelper`
* **Method:** `OpenedOrdersTickets(OpenedOrdersTicketsRequest) → OpenedOrdersTicketsReply`
* **Low‑level client:** `AccountHelperStub.OpenedOrdersTickets(request, metadata, timeout)`
* **SDK wrapper:** `MT4Account.opened_orders_tickets(deadline=None, cancellation_event=None) → OpenedOrdersTicketsData`

**Request message:** `OpenedOrdersTicketsRequest {}`
**Reply message:** `OpenedOrdersTicketsReply { data: OpenedOrdersTicketsData }`

---

### 🔗 Code Example

```python
# Fetch just the ticket IDs (fast, minimal payload)
od = await acct.opened_orders_tickets()
print(list(od.tickets))  # [1234567, 1234568, ...]

# Use the tickets to drive detail fetches (e.g., order_modify/close)
for ticket in od.tickets:
    # your logic here (e.g., decide which tickets to close/modify)
    pass
```

---

### Method Signature

```python
async def opened_orders_tickets(
    self,
    deadline: datetime | None = None,
    cancellation_event: asyncio.Event | None = None,
) -> account_helper_pb2.OpenedOrdersTicketsData
```

---

## 💬 Just the essentials

* **What it is.** A minimal call that returns only the active **ticket IDs**.
* **Why.** Perfect for quick scans, batch operations, or streaming comparisons (`on_opened_orders_tickets`).
* **When to prefer.** Use this instead of `opened_orders()` when you only need identifiers, not full order data.

---

## 🔽 Input

No required parameters.

| Parameter            | Type           | Description |                                                    |
| -------------------- | -------------- | ----------- | -------------------------------------------------- |
| `deadline`           | `datetime      | None`       | Absolute per‑call deadline → converted to timeout. |
| `cancellation_event` | `asyncio.Event | None`       | Cooperative cancel for the retry loop.             |

---

## ⬆️ Output

### Payload: `OpenedOrdersTicketsData`

| Field     | Proto Type | Description                                |
| --------- | ---------- | ------------------------------------------ |
| `tickets` | `int32[]`  | List of ticket IDs for all open positions. |

> This message is intentionally minimal to keep the call fast and bandwidth‑light.

---

## 🧱 Related enums (from pb)

This RPC **does not define method‑specific enums**. (No sort/filter in request.)

---

### 🎯 Purpose

Use this method to:

* Drive bulk actions (close/modify) using ticket IDs.
* Implement cheap change‑detection by diffing the current ticket set against a cached set.
* Feed streaming consumers that subscribe to `on_opened_orders_tickets`.

### 🧩 Notes & Tips

* Wrapper uses `execute_with_reconnect(...)` for transient gRPC retries.
* For ultra‑low latency loops, keep a short timeout (e.g., 2–3s) and backoff on failures.
* Combine with `opened_orders()` only when you actually need full details for the selected tickets.

**See also:**
`opened_orders(...)` — full order details.
`on_opened_orders_tickets(...)` — stream ticket updates.
`order_modify(...)`, `order_close_delete(...)`, `order_close_by(...)` — actions by ticket.

---

## Usage Examples

### 1) Basic print

```python
od = await acct.opened_orders_tickets()
print(f"Active tickets: {len(od.tickets)} → {list(od.tickets)[:10]}")
```

### 2) Check if a specific ticket is still open

```python
od = await acct.opened_orders_tickets()
if 1234567 in od.tickets:
    print("Ticket 1234567 is still active")
```

### 3) Diff against a cached set

```python
prev = {111, 222, 333}
cur = set(await acct.opened_orders_tickets()).tickets  # or set(od.tickets)
opened_now = cur - prev
closed_now = prev - cur
```

### 4) Bulk‑close by rule

```python
from MetaRpcMT4 import mt4_term_api_trading_helper_pb2 as trade_pb2

od = await acct.opened_orders_tickets()
for t in od.tickets:
    # Example: close all tickets (WARNING: this is just a sketch!)
    # await acct.order_close_delete(order_ticket=t)
    pass
```

