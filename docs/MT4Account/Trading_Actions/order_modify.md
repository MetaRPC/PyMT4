# ✅ Modifying an Order — `order_modify`

> **Request:** modify an existing **market position or pending order** — change price (for pendings), SL/TP, and/or expiration.
> Safe wrapper over TradingHelper RPC with deadline + cooperative cancellation.

**Source files (SDK):**

* `MetaRpcMT4/mt4_account.py` — method `order_modify(...)`
* `MetaRpcMT4/mt4_term_api_trading_helper_pb2.py` — `OrderModify*` messages

### RPC

* **Service:** `mt4_term_api.TradingHelper`
* **Method:** `OrderModify(OrderModifyRequest) → OrderModifyReply`
* **Low‑level client:** `TradingHelperStub.OrderModify(request, metadata, timeout)`
* **SDK wrapper:**

  ```python
  MT4Account.order_modify(
      order_ticket: int,
      new_price: float | None = None,
      new_stop_loss: float | None = None,
      new_take_profit: float | None = None,
      new_expiration: datetime | None = None,
      deadline: datetime | None = None,
      cancellation_event: asyncio.Event | None = None,
  ) -> trading_helper_pb2.OrderModifyData
  ```

**Request message:** `OrderModifyRequest { order_ticket, new_price?, new_stop_loss?, new_take_profit?, new_expiration? }`
**Reply message:** `OrderModifyReply { data: OrderModifyData }`

---

### 🔗 Code Examples

```python
# 1) Tighten SL and move TP on an existing position
await acct.order_modify(
    order_ticket=123456,
    new_stop_loss=1.0825,
    new_take_profit=1.0890,
)

# 2) Adjust pending order price and set expiration
from datetime import datetime, timedelta, timezone
await acct.order_modify(
    order_ticket=789012,
    new_price=1.0830,
    new_expiration=datetime.now(timezone.utc) + timedelta(hours=4),
)

# 3) Clear only the expiration (set a new future time)
await acct.order_modify(
    order_ticket=789012,
    new_expiration=datetime.now(timezone.utc) + timedelta(days=1),
)
```

---

### Method Signature

```python
async def order_modify(
    self,
    order_ticket: int,
    new_price: float | None = None,
    new_stop_loss: float | None = None,
    new_take_profit: float | None = None,
    new_expiration: datetime | None = None,
    deadline: datetime | None = None,
    cancellation_event: asyncio.Event | None = None,
) -> trading_helper_pb2.OrderModifyData
```

---

## 💬 Just the essentials

* **What it is.** Change **pending price**, **SL/TP**, and/or **expiration** on an existing ticket.
* **Why.** Manage risk, trail protection, or re‑price pending entries.
* **Selective updates.** Pass only the fields you want to change; others remain unchanged.

---

## 🔽 Input

| Parameter            | Type           | Description              |                                            |
| -------------------- | -------------- | ------------------------ | ------------------------------------------ |
| `order_ticket`       | `int`          | Target ticket to modify. |                                            |
| `new_price`          | `float         | None`                    | **Pending orders only** — new entry price. |
| `new_stop_loss`      | `float         | None`                    | New SL (raw price).                        |
| `new_take_profit`    | `float         | None`                    | New TP (raw price).                        |
| `new_expiration`     | `datetime      | None`                    | New expiration (UTC).                      |
| `deadline`           | `datetime      | None`                    | Absolute per‑call deadline.                |
| `cancellation_event` | `asyncio.Event | None`                    | Cooperative cancel for retry wrapper.      |

> Prices are **raw**; convert from points/pips with `Point` from `symbol_params_many(...)`.

---

## ⬆️ Output

### Payload: `OrderModifyData`

| Field                | Proto Type | Description                          |
| -------------------- | ---------- | ------------------------------------ |
| `order_was_modified` | `bool`     | Whether the server applied a change. |

> On error, the wrapper raises per `error_selector` inside `execute_with_reconnect(...)`.

---

## 🧱 Related enums (from pb)

This RPC **does not use method‑specific enums**.

---

### 🎯 Purpose

Use this method to:

* Trail SL/TP after breakouts.
* Re‑quote pending orders to new levels and extend expiry.
* Normalize SL/TP to broker‑approved grid (step) via server response.

### 🧩 Notes & Tips

* Always respect **StopsLevel/FreezeLevel** (`symbol_params_many`) when moving SL/TP.
  Example for BUY: `(new_price - new_stop_loss) ≥ StopsLevel * Point`.
* Ensure `new_price` is only used for **pending** orders; modifying market position price is not applicable.
* Use UTC for `new_expiration`; compare against `account_summary().server_time` if needed.
* For bulk updates, rate‑limit calls or stagger to avoid broker throttling.

**See also:**
`order_send(...)` — create orders.
`order_close_delete(...)` — close a market position / delete a pending order.
`order_close_by(...)` — close one position by another (hedge accounts).

---

## Usage Snippets

### 1) Guard SL against minimum distance

```python
p = (await acct.symbol_params_many("EURUSD")).params_info[0]
min_delta = max(p.StopsLevel, p.FreezeLevel) * p.Point
# For a BUY position at price `open_price`:
new_sl = open_price + (-30) * p.Point  # 30 pts below
assert (open_price - new_sl) >= min_delta
```

### 2) Extend a pending order expiration by 24h

```python
from datetime import datetime, timedelta, timezone
await acct.order_modify(
    order_ticket=ticket,
    new_expiration=datetime.now(timezone.utc) + timedelta(days=1),
)
```

### 3) Tighten TP only

```python
await acct.order_modify(order_ticket=ticket, new_take_profit=tp_new)
```
