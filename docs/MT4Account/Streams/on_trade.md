# ✅ Streaming Trade Events — `on_trade`

> **Stream:** subscribe to **all trade‑related events** (orders, deals, positions) for the current account.
> Yields `OnTradeData` messages continuously until cancelled.

**Source files (SDK):**

* `MetaRpcMT4/mt4_account.py` — method `on_trade(cancellation_event=None)`
* `MetaRpcMT4/mt4_term_api_subscriptions_pb2.py` — `OnTrade*` (request/reply/data), enums

### RPC

* **Service:** `mt4_term_api.Subscriptions`
* **Method (server‑streaming):** `OnTrade(OnTradeRequest) → stream OnTradeReply`
* **Low‑level client:** `SubscriptionsStub.OnTrade(request, metadata)` (async stream)
* **SDK wrapper:** `MT4Account.on_trade(cancellation_event=None) → AsyncIterator[OnTradeData]`

**Request message:** `OnTradeRequest {}`
**Reply message:** `OnTradeReply { data: OnTradeData }` (streamed)

---

### 🔗 Code Example

```python
# Consume trade events and route by subtype
import asyncio

async def consume_trades(acct):
    stop = asyncio.Event()
    # example: stop after some time
    # asyncio.get_event_loop().call_later(15.0, stop.set)

    async for ev in acct.on_trade(cancellation_event=stop):
        # OnTradeData may wrap one of: order/deal/position/update blocks
        # Common fields (presence depends on subtype):
        acc  = getattr(ev, 'account_login', None)
        kind = getattr(ev, 'type', None)  # SUB_ORDER_OPERATION_TYPE enum value

        # Order info
        if hasattr(ev, 'order_ticket') or hasattr(ev, 'open_price'):
            sym = getattr(ev, 'symbol', None)
            ticket = getattr(ev, 'order_ticket', None)
            lots = getattr(ev, 'lots', None)
            print(f"ORDER event: {sym} ticket={ticket} lots={lots}")
            continue

        # Deal info (execution)
        if hasattr(ev, 'deal_ticket') or hasattr(ev, 'price'):
            sym = getattr(ev, 'symbol', None)
            price = getattr(ev, 'price', None)
            pnl = getattr(ev, 'order_profit', None)
            print(f"DEAL event: {sym} price={price} pnl={pnl}")
            continue

        # Position info (aggregation)
        if hasattr(ev, 'position_id'):
            sym = getattr(ev, 'symbol', None)
            swap = getattr(ev, 'swap', None)
            print(f"POSITION event: {sym} swap={swap}")
```

---

### Method Signature

```python
async def on_trade(
    self,
    cancellation_event: asyncio.Event | None = None,
) -> AsyncIterator[subscriptions_pb2.OnTradeData]
```

---

## 💬 Just the essentials

* **What it is.** A **unified trade event stream**: order placement/modification/close, executions (deals), and position updates.
* **Why.** Drive UI notifications, audit logs, position widgets, and reactive risk management.
* **Stop policy.** Pass `cancellation_event` to terminate cooperatively; the wrapper auto‑reconnects on transient errors.

---

## 🔽 Input

No request fields (server subscribes for the current account).

| Parameter            | Type           | Description |                                      |
| -------------------- | -------------- | ----------- | ------------------------------------ |
| `cancellation_event` | `asyncio.Event | None`       | Signal to stop the stream gracefully |

---

## ⬆️ Output (streamed)

### Message: `OnTradeData`

Depending on the subtype present, the message may expose these fields (names mirror pb):

| Field           | Proto Type                      | Notes                                              |
| --------------- | ------------------------------- | -------------------------------------------------- |
| `account_login` | `int64`                         | Account id for multi‑account setups.               |
| `symbol`        | `string`                        | Symbol (may appear as `symbolName` in some builds) |
| `order_ticket`  | `int32`                         | Order/position ticket (for order updates).         |
| `deal_ticket`   | `int32`                         | Execution ticket (for fills); if present.          |
| `type`          | `enum SUB_ORDER_OPERATION_TYPE` | Operation type (see enum below).                   |
| `lots`          | `double`                        | Volume in lots (if applicable).                    |
| `open_price`    | `double`                        | Order open price (if applicable).                  |
| `close_price`   | `double`                        | Close price (on closes).                           |
| `price`         | `double`                        | Execution price (for deals).                       |
| `stop_loss`     | `double`                        | SL value.                                          |
| `take_profit`   | `double`                        | TP value.                                          |
| `order_profit`  | `double`                        | Profit reported with the event (if any).           |
| `swap`          | `double`                        | Swap, when included.                               |
| `magic_number`  | `int32`                         | EA magic for robots.                               |
| `comment`       | `string`                        | Comment text.                                      |
| `close_time`    | `google.protobuf.Timestamp`     | Time of closing, if present.                       |
| `date_time`     | `google.protobuf.Timestamp`     | Event timestamp.                                   |

> The SDK yields `reply.data` directly; presence of fields depends on whether the event is an **order**, **deal**, **position**, or an **updated/removed order** block.

---

## 🧱 Related enums (from pb)

### `SUB_ORDER_OPERATION_TYPE`

Operation type values reported by the server, such as:

* `OP_OPEN` — order created/opened
* `OP_MODIFY` — order modified
* `OP_CLOSE` — order closed
* (exact set depends on pb; map via `SUB_ORDER_OPERATION_TYPE.Name(value)`).

### `MT4_SUB_ENUM_EVENT_GROUP_TYPE`

Internal event grouping used in the stream payload to distinguish blocks (orders/deals/positions).

---

### 🎯 Purpose

Use this stream to:

* Update **positions and orders** in real time without polling.
* Build **audit trails** and notify the user of fills/modifies/closes.
* Trigger **risk controls** on specific event types.

### 🧩 Notes & Tips

* Keep handlers idempotent — reconnections may resend the last event.
* If you only need price ticks, prefer `on_symbol_tick(...)`.
* For bulk state refresh after reconnect, combine with snapshots: `opened_orders(...)`, `orders_history(...)`.

**See also:**
`on_opened_orders_tickets(...)` — stream of ticket set changes.
`on_opened_orders_profit(...)` — stream of aggregated P/L updates.
`opened_orders(...)`, `orders_history(...)` — snapshot endpoints.

---

## Usage Examples

### 1) Route by operation type

```python
from MetaRpcMT4 import mt4_term_api_subscriptions_pb2 as sub_pb

async for ev in acct.on_trade():
    op = getattr(ev, 'type', None)
    if op is None:
        continue
    name = sub_pb.SUB_ORDER_OPERATION_TYPE.Name(op)
    if name.startswith('OP_OPEN'):
        ...  # created
    elif name.startswith('OP_MODIFY'):
        ...  # modified
    elif name.startswith('OP_CLOSE'):
        ...  # closed
```

### 2) Reconcile with snapshots after reconnect

```python
# After stream resumes, pull fresh snapshots to resync UI
od = await acct.opened_orders()
hist = await acct.orders_history()
```
