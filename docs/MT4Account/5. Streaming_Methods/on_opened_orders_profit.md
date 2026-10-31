# Open-Order Profit Stream

> A live P/L ticker for open orders, emitted on a timer — plus an account snapshot.

**API Information:**

* **Low-level API:** `MT4Account.on_opened_orders_profit(...)` (defined in `package/MetaRpcMT4/mt4_account.py`)
* **gRPC service:** `mt4_term_api.SubscriptionService`
* **RPC:** `OnOpenedOrdersProfit(OnOpenedOrdersProfitRequest) -> stream of OnOpenedOrdersProfitReply`
* **Payload:** `OnOpenedOrdersProfitData`

## 💬 Just the essentials

* **What it is.** Every `timer_period_milliseconds` it yields the current floating P/L of each open order.
* **Why you need it.** Real-time floating P/L without polling — risk dashboards, trailing/exit logic.
* **When to use.** Live P/L monitoring and profit-target automation. Drive it with a `cancellation_event`.

---

## 🎯 Purpose

* Per-order live profit
* Emission interval control
* Account snapshot alongside each update

---

## Method Signature

```python
async def on_opened_orders_profit(
    self,
    timer_period_milliseconds: int = 1000,
    cancellation_event: Optional[asyncio.Event] = None,
)
```

**Request message:**

```protobuf
message OnOpenedOrdersProfitRequest {
  int32 timerPeriodMilliseconds = 1;
}
```

**Payload message:**

```protobuf
message OnOpenedOrdersProfitData {
  MT4_SUB_ENUM_EVENT_GROUP_TYPE type = 1;
  repeated OnOpenedOrdersProfitOrderInfo opened_orders_with_profit_updated = 2;
  OnEventAccountInfo account_info = 3;
  string terminal_instance_guid_id = 4;
}

message OnOpenedOrdersProfitOrderInfo {
  int32 ticket = 2;
  string symbol = 15;
  double order_profit = 12;
  double lots = 7;
  double open_price = 9;
  double stop_loss = 13;
  double take_profit = 16;
  SUB_ORDER_OPERATION_TYPE type = 18;
  // ... comment, magic_number, swap, commission
}
```

---

## 🔽 Input

| Parameter | Type | Description |
|-----------|------|-------------|
| `timer_period_milliseconds` | `int` | How often updates are emitted. Default 1000. |
| `cancellation_event` | asyncio.Event, optional | Set to stop the stream. |

---

## ⬆️ Output — async generator of `OnOpenedOrdersProfitData`

| Field | Python Type | Description |
|-------|-------------|-------------|
| `type` | `MT4_SUB_ENUM_EVENT_GROUP_TYPE` | Event group |
| `opened_orders_with_profit_updated` | `list[OnOpenedOrdersProfitOrderInfo]` | Open orders with live P/L |

Each `OnOpenedOrdersProfitOrderInfo` carries `ticket`, `symbol`, `order_profit`, `lots`, `open_price`, `stop_loss`, `take_profit`, and `type` (`SUB_ORDER_OPERATION_TYPE`).

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
> `subscriptions_pb2.MT4_SUB_ENUM_EVENT_GROUP_TYPE.OrderProfit`.

---

## 🧩 Notes & Tips

* **Profit field is `order_profit`** (not `profit`) on these items.
* **Timer-driven.** Updates arrive on `timer_period_milliseconds`, independent of ticks — so you get P/L updates even between price changes.
* **Same operation enum as [on_trade](on_trade.md).** Order `type` is `SUB_ORDER_OPERATION_TYPE` (`SUB_OP_*`).
* **Works on a closed market** (it re-values current orders on a timer), though P/L won't move without price changes.
* **Always pass a `cancellation_event`** and `.set()` it to stop — see [gRPC Stream Management](../../All_Guides/GRPC_STREAM_MANAGEMENT.md).

---

## 🔗 Usage Examples

### 1) Live P/L per order

```python
async def live_pnl(account):
    async for ev in account.on_opened_orders_profit():
        for o in ev.opened_orders_with_profit_updated:
            print(f"#{o.ticket} {o.symbol} {o.order_profit:+.2f}")
```

### 2) Alert on total floating loss

Stop and alert when aggregate floating P/L breaches a limit.

```python
import asyncio

async def floating_guard(account, max_loss: float = -100.0):
    cancel = asyncio.Event()
    async for ev in account.on_opened_orders_profit(timer_period_milliseconds=2000,
                                                    cancellation_event=cancel):
        total = sum(o.order_profit for o in ev.opened_orders_with_profit_updated)
        print(f"floating: {total:+.2f}")
        if total <= max_loss:
            print(f"[ALERT] floating {total:.2f} <= {max_loss} — de-risk!")
            cancel.set()
            break
```

### 3) Close an order when it hits a profit target

Watch the stream and close the ticket once its profit reaches the target.

```python
import asyncio

async def take_profit_at(account, ticket: int, target: float):
    cancel = asyncio.Event()
    async for ev in account.on_opened_orders_profit(cancellation_event=cancel):
        for o in ev.opened_orders_with_profit_updated:
            if o.ticket == ticket and o.order_profit >= target:
                await account.order_close_delete(order_ticket=ticket)
                print(f"#{ticket} hit {target:.2f} -> closed")
                cancel.set()
                return
```

---

## ⚠️ Pitfalls

* **Field is `order_profit`.** Not `profit` — a common `AttributeError`.
* **No cancellation = leak.** Stop with a `cancellation_event` you `.set()`.
* **Acting inside the loop.** Closing/modifying from within the stream is fine, but keep per-tick work light.
* **Flat account.** With nothing open, `opened_orders_with_profit_updated` is empty.

---

## 🧪 Testing Suggestions

* **With open orders.** Each update lists your open tickets; `order_profit` moves with price.
* **Total.** Summed `order_profit` roughly matches `equity − balance` from [account_summary](../1. Account_Information/account_summary.md).
* **Clean stop.** `cancellation_event.set()` ends the loop without leaking tasks.

---

## 📚 See also

* [Opened Order Tickets Stream](on_opened_orders_tickets.md)
* [Trade Events Stream](on_trade.md)
* [Account Summary](../1. Account_Information/account_summary.md)
* [gRPC Stream Management](../../All_Guides/GRPC_STREAM_MANAGEMENT.md)

* **Back to:** [Streaming Methods — Overview](Streaming_Methods.Overview.md) · [MT4Account — Master Overview](../MT4Account.Master.Overview.md)
