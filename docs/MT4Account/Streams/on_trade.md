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

| Field                       | Proto Type             | Description                                        |
| --------------------------- | ---------------------- | -------------------------------------------------- |
| `type`                      | `enum`                 | Event type (0 = OrderProfit, 1 = OrderUpdate).     |
| `event_data`                | `OnTadeEventData`      | Trade event details (orders, updates, removals).   |
| `account_info`              | `OnEventAccountInfo`   | Account state snapshot (balance, equity, etc.).    |
| `terminal_instance_guid_id` | `string`               | Terminal instance identifier.                      |

### Nested: `OnTadeEventData`

| Field                | Type                       | Description                          |
| -------------------- | -------------------------- | ------------------------------------ |
| `new_orders`         | `OnTradeOrderInfo`         | Newly created orders/positions.      |
| `updated_orders`     | `OnTradeUpdatedOrderInfo`  | Modified orders (previous/current).  |
| `removed_orders`     | `OnTradeOrderInfo`         | Closed/deleted orders.               |
| `new_history_orders` | `OnTradeOrderInfo`         | New historical orders.               |

### Nested: `OnTradeOrderInfo`

| Field          | Proto Type                  | Description                              |
| -------------- | --------------------------- | ---------------------------------------- |
| `index`        | `int32`                     | Order index.                             |
| `ticket`       | `int32`                     | Order/position ticket.                   |
| `is_history`   | `bool`                      | True if historical order.                |
| `symbol`       | `string`                    | Trading symbol.                          |
| `type`         | `enum`                      | Order type (SUB_OP_BUY, SUB_OP_SELL, etc.). |
| `lots`         | `double`                    | Volume in lots.                          |
| `open_price`   | `double`                    | Entry price.                             |
| `close_price`  | `double`                    | Exit price (if closed).                  |
| `stop_loss`    | `double`                    | Stop loss level.                         |
| `take_profit`  | `double`                    | Take profit level.                       |
| `open_time`    | `google.protobuf.Timestamp` | Order open time (UTC).                   |
| `close_time`   | `google.protobuf.Timestamp` | Order close time (UTC, if closed).       |
| `expiration`   | `google.protobuf.Timestamp` | Pending order expiration (if set).       |
| `magic_number` | `int32`                     | EA magic number.                         |
| `order_profit` | `double`                    | Current/realized profit.                 |
| `swap`         | `double`                    | Swap charged/credited.                   |
| `commission`   | `double`                    | Commission.                              |
| `comment`      | `string`                    | Order comment.                           |
| `account_login`| `int64`                     | Account login number.                    |

### Nested: `OnTradeUpdatedOrderInfo`

| Field      | Type              | Description                 |
| ---------- | ----------------- | --------------------------- |
| `previous` | `OnTradeOrderInfo`| Order state before update.  |
| `current`  | `OnTradeOrderInfo`| Order state after update.   |

### Nested: `OnEventAccountInfo`

| Field          | Proto Type | Description                     |
| -------------- | ---------- | ------------------------------- |
| `login`        | `int64`    | Account login number.           |
| `balance`      | `double`   | Account balance.                |
| `credit`       | `double`   | Credit amount.                  |
| `equity`       | `double`   | Current equity.                 |
| `margin`       | `double`   | Used margin.                    |
| `free_margin`  | `double`   | Free margin available.          |
| `profit`       | `double`   | Total floating profit.          |
| `margin_level` | `double`   | Margin level percentage.        |

> The SDK yields `reply.data` directly as `OnTradeData` with nested structures for different event types.

---

## 🧱 Related enums (from pb)

### Order Type (in `OnTradeOrderInfo.type`)

* `SUB_OP_BUY = 0` — Market buy position
* `SUB_OP_SELL = 1` — Market sell position
* `SUB_OP_BUYLIMIT = 2` — Buy limit pending order
* `SUB_OP_SELLLIMIT = 3` — Sell limit pending order
* `SUB_OP_BUYSTOP = 4` — Buy stop pending order
* `SUB_OP_SELLSTOP = 5` — Sell stop pending order

### Event Type (in `OnTradeData.type`)

* `OrderProfit = 0` — Profit/account state update
* `OrderUpdate = 1` — Order state change (new/updated/removed orders)

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
