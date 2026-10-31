# Orders History

> Closed (historical) orders over a time range, with paging and a sort mode — your trade log.

**API Information:**

* **Low-level API:** `MT4Account.orders_history(...)` (defined in `package/MetaRpcMT4/mt4_account.py`)
* **gRPC service:** `mt4_term_api.AccountHelper`
* **RPC:** `OrdersHistory(OrdersHistoryRequest) -> OrdersHistoryReply`
* **Payload:** `OrdersHistoryData`

## 💬 Just the essentials

* **What it is.** The list of closed orders in a time window, each with open/close price & time and realized profit.
* **Why you need it.** Reporting, P/L analysis, win-rate stats, strategy validation.
* **When to use.** After sessions, or any time you audit what actually happened.

---

## 🎯 Purpose

* Closed orders over a date range
* Open/close price, open/close time, realized profit per order
* Pagination for large histories (`total_count`, `next_page_token`)
* Choose the sort order

---

## Method Signature

```python
async def orders_history(
    self,
    sort_mode: EnumOrderHistorySortType = EnumOrderHistorySortType.HISTORY_SORT_BY_CLOSE_TIME_DESC,
    from_time: Optional[datetime] = None,
    to_time: Optional[datetime] = None,
    page_number: Optional[int] = None,
    items_per_page: Optional[int] = None,
    deadline: Optional[datetime] = None,
    cancellation_event: Optional[asyncio.Event] = None,
)
```

**Request message (key fields):**

```protobuf
message OrdersHistoryRequest {
  EnumOrderHistorySortType input_sort_mode = 1;
  Timestamp input_from = 2;        // start of window
  Timestamp input_to = 4;          // end of window
  int32 page_number = 6;
  int32 items_per_page = 7;
  // ... input_from_utc / input_to_utc / page_token / page_size
}
```

**Payload message:**

```protobuf
message OrdersHistoryData {
  repeated HistoryOrderInfo orders_info = 1;
  int32 total_count = 2;
  string next_page_token = 3;
}

message HistoryOrderInfo {
  string symbol = 11;
  int32 ticket = 13;
  OpenedOrderType order_type = 15;
  double lots = 5;
  double open_price = 7;
  double close_price = 21;
  double profit = 8;
  double swap = 10;
  double commision = 2;
  int32 magic_number = 6;
  string comment = 1;
  Timestamp open_time = 17;    // (+ open_time_utc)
  Timestamp close_time = 19;   // (+ close_time_utc)
  // ... stop_loss, take_profit, expiration_time, account_login
}
```

---

## 🔽 Input

| Parameter | Type | Description |
|-----------|------|-------------|
| `sort_mode` | `EnumOrderHistorySortType` | Sort order; default `HISTORY_SORT_BY_CLOSE_TIME_DESC`. |
| `from_time` | datetime, optional | Start of the window (UTC). |
| `to_time` | datetime, optional | End of the window (UTC). |
| `page_number` | int, optional | Zero-based page index. |
| `items_per_page` | int, optional | Page size. |
| `deadline` | datetime, optional | Absolute UTC deadline for the gRPC call. |
| `cancellation_event` | asyncio.Event, optional | Set to abort the request. |

---

## ⬆️ Output — `OrdersHistoryData`

| Field | Python Type | Description |
|-------|-------------|-------------|
| `orders_info` | `list[HistoryOrderInfo]` | The closed orders for this page |
| `total_count` | `int` | Total orders matching the query (across pages) |
| `next_page_token` | `str` | Token/cursor for the next page (if paging by token) |

Each `HistoryOrderInfo` (adds close fields to the open-order shape):

| Field | Python Type | Description |
|-------|-------------|-------------|
| `ticket` | `int` | Order ticket |
| `symbol` | `str` | Symbol |
| `order_type` | `OpenedOrderType` (`int`) | Operation (`OO_OP_*`) |
| `lots` | `float` | Volume |
| `open_price` / `close_price` | `float` | Entry / exit price |
| `profit` | `float` | Realized profit (excl. swap/commission) |
| `swap` / `commision` | `float` | Costs (note proto spelling `commision`) |
| `open_time` / `close_time` (+ `_utc`) | `datetime` | Entry / exit time |
| `magic_number` | `int` | Expert/magic id |
| `comment` | `str` | Order comment |

---

## 🧱 Related enums (from proto)

### `EnumOrderHistorySortType` — input `sort_mode`

| Constant | Value | Meaning |
|----------|-------|---------|
| `HISTORY_SORT_BY_OPEN_TIME_ASC` | 0 | By open time, ascending |
| `HISTORY_SORT_BY_OPEN_TIME_DESC` | 1 | By open time, descending |
| `HISTORY_SORT_BY_CLOSE_TIME_ASC` | 2 | By close time, ascending |
| `HISTORY_SORT_BY_CLOSE_TIME_DESC` | 3 | By close time, descending (default) |
| `HISTORY_SORT_BY_ORDER_TICKET_ID_ASC` | 4 | By ticket id, ascending |
| `HISTORY_SORT_BY_ORDER_TICKET_ID_DESC` | 5 | By ticket id, descending |

> `order_type` uses the same `OpenedOrderType` (`OO_OP_*`) enum as [opened_orders](opened_orders.md).

---

## 🧩 Notes & Tips

* **Bound the window.** Pass both `from_time` and `to_time`; omitting them returns the default page of all history.
* **`total_count` drives paging.** It's the full match count — loop pages while `page_number * items_per_page < total_count`.
* **Net result per trade** is `profit + swap + commision` (costs are usually negative).
* **Balance/credit rows.** As with open orders, `OO_OP_BALANCE`/`OO_OP_CREDIT` can appear — skip them for trade stats.
* **Prefer [trade_stats](../1. Account_Information/trade_stats.md) for ratios.** It computes profit factor, win rate, drawdowns for you; use `orders_history` when you need the raw rows.

---

## 🔗 Usage Examples

### 1) Last 30 days — closed trades table

```python
from datetime import datetime, timedelta
import MetaRpcMT4.mt4_term_api_account_helper_pb2 as ah

async def recent_history(account, days: int = 30):
    end = datetime.utcnow()
    hist = await account.orders_history(from_time=end - timedelta(days=days), to_time=end)
    print(f"{hist.total_count} closed order(s) in {days}d")
    for o in hist.orders_info[:20]:
        side = "BUY" if o.order_type == ah.OpenedOrderType.OO_OP_BUY else "SELL"
        net = o.profit + o.swap + o.commision
        print(f"  #{o.ticket} {o.symbol:<8} {side:<4} {o.lots:.2f} "
              f"{o.open_price:.5f}->{o.close_price:.5f}  net={net:+.2f}")
```

### 2) Realized P/L and win rate for a window

```python
from datetime import datetime, timedelta

async def window_pnl(account, days: int = 7):
    end = datetime.utcnow()
    hist = await account.orders_history(from_time=end - timedelta(days=days), to_time=end)
    trades = [o for o in hist.orders_info]
    realized = sum(o.profit + o.swap + o.commision for o in trades)
    wins = sum(1 for o in trades if (o.profit + o.swap + o.commision) > 0)
    wr = wins / len(trades) * 100 if trades else 0.0
    print(f"{len(trades)} trades | realized {realized:+.2f} | win rate {wr:.1f}%")
    return realized
```

### 3) Page through a long history

Use `total_count` + `items_per_page` to walk every page.

```python
from datetime import datetime, timedelta

async def all_history(account, days: int = 365, page_size: int = 100):
    end = datetime.utcnow()
    start = end - timedelta(days=days)
    out, page = [], 0
    while True:
        res = await account.orders_history(
            from_time=start, to_time=end,
            page_number=page, items_per_page=page_size,
        )
        out.extend(res.orders_info)
        if (page + 1) * page_size >= res.total_count or not res.orders_info:
            break
        page += 1
    print(f"collected {len(out)} / {res.total_count} orders")
    return out
```

---

## ⚠️ Pitfalls

* **Costs are separate.** `profit` excludes `swap`/`commision` — add them for the true net.
* **Window required for meaningful results.** Without `from_time`/`to_time` you get the default page, not "everything".
* **Page bounds.** Stop when you've collected `total_count` (or a page comes back empty) to avoid an infinite loop.
* **Proto spelling:** `commision` (single s).

---

## 🧪 Testing Suggestions

* **Known window.** On a demo account with history, `len(orders_info) <= total_count` and timestamps fall inside `[from_time, to_time]`.
* **Round-trip.** Open then close an order, then query a window covering now — the ticket appears with a `close_time` and realized `profit`.
* **Paging.** With `items_per_page` smaller than `total_count`, concatenated pages equal the full set with no duplicates.

---

## 📚 See also

* [Opened Orders](opened_orders.md)
* [Opened Order Tickets](opened_orders_tickets.md)
* [Trade Statistics](../1. Account_Information/trade_stats.md)

* **Back to:** [Orders & History — Overview](Orders_History.Overview.md) · [MT4Account — Master Overview](../MT4Account.Master.Overview.md)
