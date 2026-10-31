# Trade Events Stream

> A live async stream of trade events — orders opened, updated and removed.

**API Information:**

* **Low-level API:** `MT4Account.on_trade(...)` (defined in `package/MetaRpcMT4/mt4_account.py`)
* **gRPC service:** `mt4_term_api.SubscriptionService`
* **RPC:** `OnTrade(OnTradeRequest) -> stream of OnTradeReply`
* **Payload:** `OnTradeData`

## 💬 Just the essentials

* **What it is.** An async generator that fires whenever an order's lifecycle changes — new, modified, closed/removed.
* **Why you need it.** To react instantly to order activity (monitors, copiers, dashboards) instead of polling.
* **When to use.** Any event-driven logic around orders. Drive it with a `cancellation_event`.

---

## 🎯 Purpose

* New / updated / removed order events
* Per-order operation type (`SUB_OP_*`)
* Event group type (profit vs update)
* Account snapshot alongside each event

---

## Method Signature

```python
async def on_trade(
    self,
    cancellation_event: Optional[asyncio.Event] = None,
)
```

**Request message:**

```protobuf
message OnTradeRequest {}
```

**Payload message:**

```protobuf
message OnTradeData {
  MT4_SUB_ENUM_EVENT_GROUP_TYPE type = 1;
  OnTadeEventData event_data = 2;
  OnEventAccountInfo account_info = 3;
  string terminal_instance_guid_id = 4;
}

message OnTadeEventData {
  repeated OnTradeOrderInfo new_orders = 1;
  repeated OnTradeUpdatedOrderInfo updated_orders = 2;   // each has previous / current
  repeated OnTradeOrderInfo removed_orders = 3;
  repeated OnTradeOrderInfo new_history_orders = 4;
}

message OnTradeOrderInfo {
  int32 ticket = 2;
  string symbol = 16;
  double lots = 8;
  double open_price = 10;
  double stop_loss = 14;
  double take_profit = 17;
  double order_profit = 13;
  SUB_ORDER_OPERATION_TYPE type = 18;
  // ... is_history, comment, magic_number, close_price, close_time
}
```

---

## 🔽 Input

| Parameter | Type | Description |
|-----------|------|-------------|
| `cancellation_event` | asyncio.Event, optional | Set to stop the stream. |

---

## ⬆️ Output — async generator of `OnTradeData`

| Field | Python Type | Description |
|-------|-------------|-------------|
| `type` | `MT4_SUB_ENUM_EVENT_GROUP_TYPE` | Event group (profit vs update) |
| `event_data.new_orders` | `list[OnTradeOrderInfo]` | Newly opened/placed orders |
| `event_data.updated_orders` | `list[OnTradeUpdatedOrderInfo]` | Changed orders (`.previous` / `.current`) |
| `event_data.removed_orders` | `list[OnTradeOrderInfo]` | Closed / deleted orders |
| `event_data.new_history_orders` | `list[OnTradeOrderInfo]` | Orders that moved to history |

Each `OnTradeOrderInfo` carries `ticket`, `symbol`, `lots`, `open_price`, `stop_loss`, `take_profit`, `order_profit`, and `type` (`SUB_ORDER_OPERATION_TYPE`).

---

## 🧱 Related enums (from proto)

### `MT4_SUB_ENUM_EVENT_GROUP_TYPE` — field `type`

| Constant | Value | Meaning |
|----------|-------|---------|
| `OrderProfit` | 0 | Profit-update group |
| `OrderUpdate` | 1 | Order lifecycle change |

### `SUB_ORDER_OPERATION_TYPE` — order `type`

| Constant | Value | Meaning |
|----------|-------|---------|
| `SUB_OP_BUY` | 0 | Market buy |
| `SUB_OP_SELL` | 1 | Market sell |
| `SUB_OP_BUYLIMIT` | 2 | Buy limit |
| `SUB_OP_SELLLIMIT` | 3 | Sell limit |
| `SUB_OP_BUYSTOP` | 4 | Buy stop |
| `SUB_OP_SELLSTOP` | 5 | Sell stop |

> Access via `subscriptions_pb2.SUB_ORDER_OPERATION_TYPE.SUB_OP_BUY` and
> `subscriptions_pb2.MT4_SUB_ENUM_EVENT_GROUP_TYPE.OrderUpdate`.

---

## 🧩 Notes & Tips

* **Four buckets per event.** `event_data` splits changes into `new_orders`, `updated_orders`, `removed_orders`, `new_history_orders` — iterate the ones you care about.
* **Updates carry before/after.** Each `updated_orders` item has `.previous` and `.current` (both `OnTradeOrderInfo`) — diff them to see exactly what changed (e.g. SL/TP).
* **Order operation enum differs from trading.** Streaming uses `SUB_OP_*` (`SUB_ORDER_OPERATION_TYPE`), not the `OC_OP_*` used by [order_send](../4. Trading_Operations/order_send.md) — same operations, different enum.
* **Always pass a `cancellation_event`** and `.set()` it to stop — see [gRPC Stream Management](../../All_Guides/GRPC_STREAM_MANAGEMENT.md).
* **No events without activity.** If nothing trades, nothing yields — use a timeout when you expect it to be quiet.

---

## 🔗 Usage Examples

### 1) Log new orders

```python
import MetaRpcMT4.mt4_term_api_subscriptions_pb2 as sub

LABEL = {
    sub.SUB_ORDER_OPERATION_TYPE.SUB_OP_BUY: "BUY",   sub.SUB_ORDER_OPERATION_TYPE.SUB_OP_SELL: "SELL",
    sub.SUB_ORDER_OPERATION_TYPE.SUB_OP_BUYLIMIT: "BUY LIMIT",  sub.SUB_ORDER_OPERATION_TYPE.SUB_OP_SELLLIMIT: "SELL LIMIT",
    sub.SUB_ORDER_OPERATION_TYPE.SUB_OP_BUYSTOP: "BUY STOP",    sub.SUB_ORDER_OPERATION_TYPE.SUB_OP_SELLSTOP: "SELL STOP",
}

async def log_new_orders(account):
    async for ev in account.on_trade():
        for o in ev.event_data.new_orders:
            print(f"[NEW] {LABEL.get(o.type,'?')} #{o.ticket} {o.symbol} @ {o.open_price:.5f}")
```

### 2) Watch SL/TP changes

Use the `previous`/`current` pair to report exactly what moved.

```python
async def watch_modifications(account):
    async for ev in account.on_trade():
        for upd in ev.event_data.updated_orders:
            cur, prev = upd.current, upd.previous
            if (cur.stop_loss, cur.take_profit) != (prev.stop_loss, prev.take_profit):
                print(f"[MOD] #{cur.ticket} {cur.symbol} "
                      f"SL {prev.stop_loss:.5f}->{cur.stop_loss:.5f} "
                      f"TP {prev.take_profit:.5f}->{cur.take_profit:.5f}")
```

### 3) Fire a callback on any close

```python
import asyncio

async def on_close(account, callback, stop: asyncio.Event):
    cancel = asyncio.Event()
    async def pump():
        async for ev in account.on_trade(cancellation_event=cancel):
            for o in ev.event_data.removed_orders:
                callback(o)
    task = asyncio.create_task(pump())
    await stop.wait()
    cancel.set(); await asyncio.sleep(0.3); task.cancel()
```

---

## ⚠️ Pitfalls

* **Wrong enum.** Order operations here are `SUB_OP_*`, not `OC_OP_*` — mixing them silently mismatches.
* **No cancellation = leak.** Always stop the stream with a `cancellation_event` you `.set()`.
* **Quiet periods.** No trading activity → no events; don't block forever, use a timeout.
* **Updates need before/after.** Compare `previous` vs `current` rather than assuming what changed.

---

## 🧪 Testing Suggestions

* **Market open.** Open then close a 0.01 order while subscribed — you see it in `new_orders` then `removed_orders`.
* **Modification.** Change an order's SL and assert it appears in `updated_orders` with differing `previous`/`current`.
* **Clean stop.** `cancellation_event.set()` ends the `async for` without leaking tasks.

---

## 📚 See also

* [Symbol Tick Stream](on_symbol_tick.md)
* [Open-Order Profit Stream](on_opened_orders_profit.md)
* [Order Send](../4. Trading_Operations/order_send.md)
* [gRPC Stream Management](../../All_Guides/GRPC_STREAM_MANAGEMENT.md)

* **Back to:** [Streaming Methods — Overview](Streaming_Methods.Overview.md) · [MT4Account — Master Overview](../MT4Account.Master.Overview.md)
