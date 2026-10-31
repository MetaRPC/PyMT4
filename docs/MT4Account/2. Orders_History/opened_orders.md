# Opened Orders

> Every currently open order (market **and** pending) with full detail, in the sort order you choose.

**API Information:**

* **Low-level API:** `MT4Account.opened_orders(...)` (defined in `package/MetaRpcMT4/mt4_account.py`)
* **gRPC service:** `mt4_term_api.AccountHelper`
* **RPC:** `OpenedOrders(OpenedOrdersRequest) -> OpenedOrdersReply`
* **Payload:** `OpenedOrdersData`

## 💬 Just the essentials

* **What it is.** The full list of live orders on the account — market positions and resting pending orders — each with price, SL/TP, profit, magic and times.
* **Why you need it.** To inspect, manage, or close current exposure.
* **When to use.** Whenever you need order details. If you only need ticket numbers, use [opened_orders_tickets](opened_orders_tickets.md) (cheaper).

---

## 🎯 Purpose

* All open market & pending orders in one call
* Full per-order detail (price, SL/TP, profit, swap, magic)
* Choose the sort order
* Filter in your code by symbol / magic / side

---

## Method Signature

```python
async def opened_orders(
    self,
    sort_mode: EnumOpenedOrderSortType = EnumOpenedOrderSortType.SORT_BY_OPEN_TIME_ASC,
    deadline: Optional[datetime] = None,
    cancellation_event: Optional[asyncio.Event] = None,
)
```

**Request message:**

```protobuf
message OpenedOrdersRequest {
  EnumOpenedOrderSortType sort_type = 1;
}
```

**Payload message:**

```protobuf
message OpenedOrdersData {
  repeated OpenedOrderInfo order_infos = 1;
}

message OpenedOrderInfo {
  string comment = 1;
  double commision = 2;
  Timestamp expiration_time = 3;
  double lots = 4;
  int32 magic_number = 5;
  double open_price = 6;
  double profit = 7;
  double stop_loss = 8;
  double swap = 9;
  string symbol = 10;
  double take_profit = 11;
  int32 ticket = 12;
  int32 position_index = 13;
  OpenedOrderType order_type = 14;
  int32 sort_index = 15;
  Timestamp open_time = 16;
  int64 account_login = 17;
  Timestamp expiration_time_utc = 18;
  Timestamp open_time_utc = 19;
}
```

---

## 🔽 Input

| Parameter | Type | Description |
|-----------|------|-------------|
| `sort_mode` | `EnumOpenedOrderSortType` | Sort order; default `SORT_BY_OPEN_TIME_ASC`. |
| `deadline` | datetime, optional | Absolute UTC deadline for the gRPC call. |
| `cancellation_event` | asyncio.Event, optional | Set to abort the request. |

---

## ⬆️ Output — `OpenedOrdersData`

`order_infos` — a list of `OpenedOrderInfo`:

| Field | Python Type | Description |
|-------|-------------|-------------|
| `ticket` | `int` | Order ticket |
| `symbol` | `str` | Symbol |
| `order_type` | `OpenedOrderType` (`int`) | Operation (`OO_OP_*`) |
| `lots` | `float` | Volume |
| `open_price` | `float` | Open / pending price |
| `stop_loss` / `take_profit` | `float` | SL / TP price (0 if unset) |
| `profit` | `float` | Current floating profit |
| `swap` / `commision` | `float` | Swap / commission (note proto spelling `commision`) |
| `magic_number` | `int` | Expert/magic id |
| `comment` | `str` | Order comment |
| `open_time` / `_utc` | `datetime` | Open time (server / UTC) |
| `expiration_time` / `_utc` | `datetime` | Pending-order expiration |

---

## 🧱 Related enums (from proto)

### `EnumOpenedOrderSortType` — input `sort_mode`

| Constant | Value | Meaning |
|----------|-------|---------|
| `SORT_BY_OPEN_TIME_ASC` | 0 | By open time, ascending |
| `SORT_BY_OPEN_TIME_DESC` | 1 | By open time, descending |
| `SORT_BY_ORDER_TICKET_ID_ASC` | 2 | By ticket id, ascending |
| `SORT_BY_ORDER_TICKET_ID_DESC` | 3 | By ticket id, descending |

### `OpenedOrderType` — field `order_type`

| Constant | Value | Meaning |
|----------|-------|---------|
| `OO_OP_BUY` | 0 | Market buy |
| `OO_OP_SELL` | 1 | Market sell |
| `OO_OP_BUYLIMIT` | 2 | Buy limit (pending) |
| `OO_OP_SELLLIMIT` | 3 | Sell limit (pending) |
| `OO_OP_BUYSTOP` | 4 | Buy stop (pending) |
| `OO_OP_SELLSTOP` | 5 | Sell stop (pending) |
| `OO_OP_BALANCE` | 6 | Balance record (non-tradable) |
| `OO_OP_CREDIT` | 7 | Credit record (non-tradable) |

> In Python, access values via `account_helper_pb2.OpenedOrderType.OO_OP_BUY`.

---

## 🧩 Notes & Tips

* **Market and pending in one list.** `order_type` tells them apart: `OO_OP_BUY`/`OO_OP_SELL` are filled market orders; the `*LIMIT`/`*STOP` variants are resting pending orders.
* **Buy vs sell side.** Buy side = `OO_OP_BUY`, `OO_OP_BUYLIMIT`, `OO_OP_BUYSTOP`; the odd values (1,3,5) are the sell side.
* **`OO_OP_BALANCE` / `OO_OP_CREDIT`** are bookkeeping records, not tradable orders — skip them when summing exposure.
* **`profit` is floating** and excludes `swap`/`commision`; add them for the true carry cost.
* **Proto spelling:** the commission field is `commision` (single s) — use it as-is.
* **Lightweight alternative:** [opened_orders_tickets](opened_orders_tickets.md) returns just ticket numbers for fast polling.

---

## 🔗 Usage Examples

### 1) Open orders table

Print a readable snapshot of everything currently open.

```python
import MetaRpcMT4.mt4_term_api_account_helper_pb2 as ah

TYPE = {
    ah.OpenedOrderType.OO_OP_BUY: "BUY",   ah.OpenedOrderType.OO_OP_SELL: "SELL",
    ah.OpenedOrderType.OO_OP_BUYLIMIT: "BUY LIMIT",  ah.OpenedOrderType.OO_OP_SELLLIMIT: "SELL LIMIT",
    ah.OpenedOrderType.OO_OP_BUYSTOP: "BUY STOP",    ah.OpenedOrderType.OO_OP_SELLSTOP: "SELL STOP",
}

async def print_open(account):
    data = await account.opened_orders()
    print(f"{'Ticket':>10} {'Symbol':<8} {'Type':<10} {'Lots':>6} {'Price':>10} {'Profit':>10}")
    for o in data.order_infos:
        print(f"{o.ticket:>10} {o.symbol:<8} {TYPE.get(o.order_type,'?'):<10} "
              f"{o.lots:>6.2f} {o.open_price:>10.5f} {o.profit:>10.2f}")
    print(f"total floating: {sum(o.profit for o in data.order_infos):+.2f}")
```

### 2) Only my bot's orders

Filter by `magic_number` to isolate orders a given strategy opened.

```python
async def my_orders(account, magic: int):
    data = await account.opened_orders()
    mine = [o for o in data.order_infos if o.magic_number == magic]
    floating = sum(o.profit + o.swap + o.commision for o in mine)
    print(f"magic {magic}: {len(mine)} order(s), net {floating:+.2f}")
    return mine
```

### 3) Net exposure per symbol

Aggregate signed lots per symbol to see your real directional exposure (market orders only).

```python
import MetaRpcMT4.mt4_term_api_account_helper_pb2 as ah
from collections import defaultdict

BUY  = {ah.OpenedOrderType.OO_OP_BUY}
SELL = {ah.OpenedOrderType.OO_OP_SELL}

async def net_exposure(account):
    data = await account.opened_orders()
    net = defaultdict(float)
    for o in data.order_infos:
        if o.order_type in BUY:
            net[o.symbol] += o.lots
        elif o.order_type in SELL:
            net[o.symbol] -= o.lots
    for sym, lots in sorted(net.items()):
        side = "long" if lots > 0 else "short" if lots < 0 else "flat"
        print(f"{sym:<8} {lots:+.2f} lots ({side})")
    return dict(net)
```

---

## ⚠️ Pitfalls

* **Pending orders have no profit yet.** A `*LIMIT`/`*STOP` order isn't filled — its `profit` is 0; don't count it as exposure.
* **Skip balance/credit rows.** `OO_OP_BALANCE` / `OO_OP_CREDIT` appear here but aren't trades — exclude them from lot/exposure math.
* **SL/TP of 0 means "unset"**, not a price of zero.
* **Snapshot.** The list reflects the moment of the call; use [on_opened_orders_tickets](../5. Streaming_Methods/on_opened_orders_tickets.md) to react to changes live.

---

## 🧪 Testing Suggestions

* **Flat account.** `order_infos` is empty; the table prints a zero total without error.
* **With a market order open.** The new ticket appears with `order_type == OO_OP_BUY`/`OO_OP_SELL` and a sensible `open_price`.
* **Magic filter.** Open two orders with different magics and assert `my_orders()` returns only the matching one.

---

## 📚 See also

* [Opened Order Tickets](opened_orders_tickets.md)
* [Orders History](orders_history.md)
* [Order Send](../4. Trading_Operations/order_send.md)

* **Back to:** [Orders & History — Overview](Orders_History.Overview.md) · [MT4Account — Master Overview](../MT4Account.Master.Overview.md)
