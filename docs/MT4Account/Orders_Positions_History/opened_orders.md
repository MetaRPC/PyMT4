# ✅ Getting Opened Orders

> **Request:** retrieve the full list of currently opened **orders/positions** as a single payload (`OpenedOrdersData`).
> Filtering and sorting are applied server‑side.

**Source files (SDK):**

* `MetaRpcMT4/mt4_account.py` — method `opened_orders(...)`
* `MetaRpcMT4/mt4_term_api_account_helper_pb2.py` — `OpenedOrders*`, `EnumOpenedOrderSortType`, `OpenedOrderType`

### RPC

* **Service:** `mt4_term_api.AccountHelper`
* **Method:** `OpenedOrders(OpenedOrdersRequest) → OpenedOrdersReply`
* **Low‑level client:** `AccountHelperStub.OpenedOrders(request, metadata, timeout)`
* **SDK wrapper:** `MT4Account.opened_orders(sort_mode=EnumOpenedOrderSortType.SORT_BY_OPEN_TIME_ASC, deadline=None, cancellation_event=None) → OpenedOrdersData`

**Request message:** `OpenedOrdersRequest { sort_type: EnumOpenedOrderSortType }`
**Reply message:** `OpenedOrdersReply { data: OpenedOrdersData }`

---

### 🔗 Code Example

```python
# High-level: fetch + print a compact table
async def show_opened_orders(acct):
    od = await acct.opened_orders()
    for it in od.items:  # items: list[OpenedOrder]
        print(
            f"#{it.ticket} {it.symbol} {it.order_type} "
            f"lots={it.lots:.2f} open={it.open_price:.5f} "
            f"sl={it.stop_loss or 0:.5f} tp={it.take_profit or 0:.5f} "
            f"profit={it.profit:.2f}"
        )

# Low-level: raw proto payload
od = await acct.opened_orders()
# od: OpenedOrdersData
```

---

### Method Signature

```python
async def opened_orders(
    self,
    sort_mode: account_helper_pb2.EnumOpenedOrderSortType = account_helper_pb2.EnumOpenedOrderSortType.SORT_BY_OPEN_TIME_ASC,
    deadline: datetime | None = None,
    cancellation_event: asyncio.Event | None = None,
) -> account_helper_pb2.OpenedOrdersData
```

---

## 💬 Just the essentials

* **What it is.** A single RPC returning **all active positions** for the current account, already sorted server‑side.
* **Why.** UI/CLI listings, risk monitoring, quick portfolio P/L calculations.
* **Sorting.** Controlled by `sort_mode` (see enum below).

---

## 🔽 Input

| Parameter            | Type                      | Description                          |                                                    |
| -------------------- | ------------------------- | ------------------------------------ | -------------------------------------------------- |
| `sort_mode`          | `EnumOpenedOrderSortType` | Sorting mode to apply on the server. |                                                    |
| `deadline`           | `datetime                 | None`                                | Absolute per‑call deadline (converted to timeout). |
| `cancellation_event` | `asyncio.Event            | None`                                | Cooperative cancel for the retry wrapper.          |

**Note:** The SDK builds `OpenedOrdersRequest(sort_type=sort_mode)` and executes via `execute_with_reconnect(...)`.

---

## ⬆️ Output

### Payload: `OpenedOrdersData`

| Field         | Type              | Description                                      |
| ------------- | ----------------- | ------------------------------------------------ |
| `order_infos` | `OpenedOrderInfo[]` | Array of currently opened orders and positions. |

Each `OpenedOrderInfo` element contains:

| Field              | Proto Type                          | Description                              |
| ------------------ | ----------------------------------- | ---------------------------------------- |
| `ticket`           | `int32`                             | Unique ID of the order/position.         |
| `symbol`           | `string`                            | Symbol (e.g., `EURUSD`).                 |
| `order_type`       | `enum OpenedOrderType`              | Order type (BUY/SELL/LIMIT/STOP, etc.).  |
| `lots`             | `double`                            | Volume in lots.                          |
| `magic_number`     | `int32`                             | EA magic number.                         |
| `open_price`       | `double`                            | Entry price.                             |
| `profit`           | `double`                            | Current floating P/L.                    |
| `stop_loss`        | `double`                            | Current SL (0 if none).                  |
| `take_profit`      | `double`                            | Current TP (0 if none).                  |
| `swap`             | `double`                            | Accumulated swap.                        |
| `commision`        | `double`                            | Commission charged.                      |
| `comment`          | `string`                            | Order comment.                           |
| `position_index`   | `int32`                             | Terminal position index (if applicable). |
| `open_time`        | `google.protobuf.Timestamp`         | Position open time (UTC).                |
| `expiration_time`  | `google.protobuf.Timestamp`         | Pending order expiration (if set).       |
| `sort_index`       | `int32`                             | Sort index for the current sort mode.    |
| `account_login`    | `int64`                             | Account login number.                    |

---

## 🧱 Related enums (from pb)

### `EnumOpenedOrderSortType`

Sort modes for opened orders:

* `SORT_BY_OPEN_TIME_ASC = 0` — Sort by open time ascending
* `SORT_BY_OPEN_TIME_DESC = 1` — Sort by open time descending
* `SORT_BY_ORDER_TICKET_ID_ASC = 2` — Sort by ticket ID ascending
* `SORT_BY_ORDER_TICKET_ID_DESC = 3` — Sort by ticket ID descending

### `OpenedOrderType`

Order/position types:

* `OO_OP_BUY = 0` — Market buy position
* `OO_OP_SELL = 1` — Market sell position
* `OO_OP_BUYLIMIT = 3` — Buy limit pending order
* `OO_OP_BUYSTOP = 4` — Buy stop pending order
* `OO_OP_SELLLIMIT = 5` — Sell limit pending order
* `OO_OP_SELLSTOP = 6` — Sell stop pending order

> Use `account_helper_pb2.EnumOpenedOrderSortType.Name(value)` or `OpenedOrderType.Name(value)` to map numeric values → labels.

---

### 🎯 Purpose

Use this method to:

* Render real‑time position tables in your UI/CLI.
* Monitor risk and PnL across the portfolio.
* Filter/sort by ticket, symbol, or open time without client‑side re‑sorting.

### 🧩 Notes & Tips

* Uses `execute_with_reconnect(...)` → automatic retry on transient gRPC errors.
* Prefer a short timeout (3–5s) with retries for large books.
* Right after connect, allow a brief warm‑up while the terminal syncs positions.

**See also:**

* `OpenedOrdersTickets(...)` — tickets only.
* `on_opened_orders_tickets(...)` — streaming ticket updates.
* `on_opened_orders_profit(...)` — streaming aggregated P/L.
* `orders_history(...)` — closed orders.

---

## Usage Examples

### 1) Basic list

```python
od = await acct.opened_orders()
for it in od.order_infos:
    print(f"#{it.ticket} {it.symbol} lots={it.lots:.2f} PnL={it.profit:.2f}")
```

### 2) Sort by ticket (descending)

```python
from MetaRpcMT4 import mt4_term_api_account_helper_pb2 as account_pb2

od = await acct.opened_orders(
    sort_mode=account_pb2.EnumOpenedOrderSortType.SORT_BY_ORDER_TICKET_ID_DESC
)
```

### 3) Deadline + cancellation

```python
from datetime import datetime, timedelta, timezone
import asyncio

cancel_event = asyncio.Event()
od = await acct.opened_orders(
    deadline=datetime.now(timezone.utc) + timedelta(seconds=3),
    cancellation_event=cancel_event,
)
```

### 4) View‑model for UI

```python
from dataclasses import dataclass

@dataclass
class OpenedOrderView:
    ticket: int
    symbol: str
    order_type: int
    lots: float
    open_price: float
    sl: float
    tp: float
    profit: float

    @staticmethod
    def from_proto(p):
        return OpenedOrderView(
            ticket=int(p.ticket),
            symbol=str(p.symbol),
            order_type=int(p.order_type),
            lots=float(p.lots),
            open_price=float(p.open_price),
            sl=float(getattr(p, 'stop_loss', 0.0)),
            tp=float(getattr(p, 'take_profit', 0.0)),
            profit=float(p.profit),
        )

od = await acct.opened_orders()
rows = [OpenedOrderView.from_proto(p) for p in od.items]
```

---

## 🧪 What this teaches

* How to retrieve all open positions efficiently.
* How to apply server‑side sorting via `sort_mode`.
* How to make safe, responsive RPC calls using `deadline` and `cancellation_event`.
