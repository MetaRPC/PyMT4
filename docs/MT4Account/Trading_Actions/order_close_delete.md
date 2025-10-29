# ✅ Closing / Deleting an Order — `order_close_delete`

> **Request:** close a **market position** (full or partial) or **delete a pending order** by ticket.
> Thin wrapper over TradingHelper RPC with deadline + cooperative cancellation.

**Source files (SDK):**

* `MetaRpcMT4/mt4_account.py` — method `order_close_delete(...)`
* `MetaRpcMT4/mt4_term_api_trading_helper_pb2.py` — `OrderCloseDelete*` messages

### RPC

* **Service:** `mt4_term_api.TradingHelper`
* **Method:** `OrderCloseDelete(OrderCloseDeleteRequest) → OrderCloseDeleteReply`
* **Low‑level client:** `TradingHelperStub.OrderCloseDelete(request, metadata, timeout)`
* **SDK wrapper:**

  ```python
  MT4Account.order_close_delete(
      order_ticket: int,
      lots: float | None = None,           # partial close for market positions
      closing_price: float | None = None,  # optional target price (market close)
      slippage: int | None = None,         # max deviation in points (market close)
      deadline: datetime | None = None,
      cancellation_event: asyncio.Event | None = None,
  ) -> trading_helper_pb2.OrderCloseDeleteData
  ```

**Request message:** `OrderCloseDeleteRequest { order_ticket, lots?, closing_price?, slippage?, comment? }`
**Reply message:** `OrderCloseDeleteReply { data: OrderCloseDeleteData }`

> Field names reflect your pb (`mt4_term_api_trading_helper_pb2.py`). Some builds expose `lots` as `volume`; `closing_price` may be optional/ignored for delete.

---

### 🔗 Code Examples

```python
# 1) Close a full market position by ticket
await acct.order_close_delete(order_ticket=123456)

# 2) Partial close 0.20 lots
await acct.order_close_delete(order_ticket=123456, lots=0.20)

# 3) Delete a pending order (no price/slippage needed)
await acct.order_close_delete(order_ticket=789012)

# 4) Close with tight slippage guard
await acct.order_close_delete(order_ticket=123456, slippage=10)
```

---

### Method Signature

```python
async def order_close_delete(
    self,
    order_ticket: int,
    lots: float | None = None,
    closing_price: float | None = None,
    slippage: int | None = None,
    deadline: datetime | None = None,
    cancellation_event: asyncio.Event | None = None,
) -> trading_helper_pb2.OrderCloseDeleteData
```

---

## 💬 Just the essentials

* **What it is.** A single call to **close** an open position (optionally **partially**) or **delete** a pending order.
* **Why.** Core action for exits, scaling out, or cancelling unfilled entries.
* **Deviation control.** `slippage` applies to market closes to avoid unfavorable fills.

---

## 🔽 Input

| Parameter            | Type           | Description             |                                                                 |
| -------------------- | -------------- | ----------------------- | --------------------------------------------------------------- |
| `order_ticket`       | `int`          | Ticket to close/delete. |                                                                 |
| `lots`               | `float         | None`                   | Partial close volume; omit to close **all**.                    |
| `closing_price`      | `float         | None`                   | Target close price (market); server may ignore if incompatible. |
| `slippage`           | `int           | None`                   | Max permitted deviation in **points** for market close.         |
| `deadline`           | `datetime      | None`                   | Absolute per‑call deadline.                                     |
| `cancellation_event` | `asyncio.Event | None`                   | Cooperative cancel for retry wrapper.                           |

---

## ⬆️ Output

### Payload: `OrderCloseDeleteData`

Common fields (exact list depends on pb build):

| Field               | Proto Type                   | Description                                    |
| ------------------- | ---------------------------- | ---------------------------------------------- |
| `order_was_closed`  | `bool?`                      | Whether a market position was closed.          |
| `order_was_deleted` | `bool?`                      | Whether a pending order was deleted.           |
| `close_price`       | `double?`                    | Executed close price (if available).           |
| `lots_closed`       | `double?`                    | Closed volume for partial exits.               |
| `close_time`        | `google.protobuf.Timestamp?` | Server timestamp of the close/delete.          |
| `comment`           | `string?`                    | Echoed/normalized comment (if request had it). |

> If your pb returns a single boolean, the action type (close vs delete) follows from the order type referenced by `order_ticket`.

---

## 🧱 Related enums (from pb)

This RPC **does not use method‑specific enums**.

---

### 🎯 Purpose

Use this method to:

* Exit positions fully or partially (scaling out).
* Cancel unfilled pending orders.
* Enforce slippage caps on market exits.

### 🧩 Notes & Tips

* For **partial close**, ensure `lots` respects `VolumeMin/Step` from `symbol_params_many(...)`.
* If you need to close one hedge position **by another**, use `order_close_by(...)` instead.
* On transient network errors, the wrapper retries; make handlers idempotent to avoid double UI updates.

**See also:**
`order_send(...)` — place new orders with SL/TP.
`order_modify(...)` — adjust SL/TP/expiration.
`order_close_by(...)` — close with an opposite position (hedge accounts).

---

## Usage Snippets

### 1) Scale‑out helper (50%)

```python
def half_volume(p):
    return max(p.VolumeMin, round(p.lots / 2 / p.VolumeStep) * p.VolumeStep)

pos = next(it for it in (await acct.opened_orders()).items if it.ticket == 123456)
p = (await acct.symbol_params_many(pos.symbol)).params_info[0]
await acct.order_close_delete(order_ticket=pos.ticket, lots=half_volume(p))
```

### 2) Close with guard rails

```python
# If spread is too wide, skip close and alert
q = await acct.quote("EURUSD")
spread_ok = getattr(q, 'spread', 0) <= 30
if spread_ok:
    await acct.order_close_delete(order_ticket=ticket, slippage=10)
```
