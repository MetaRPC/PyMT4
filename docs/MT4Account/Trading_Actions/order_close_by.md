# ✅ Close by Opposite Position — `order_close_by`

> **Request:** close one **open position** using an **opposite position** on the **same symbol** (MT4 *Close By* operation).
> This reduces commissions/swaps vs two separate closes and can net residual volume automatically.

**Source files (SDK):**

* `MetaRpcMT4/mt4_account.py` — method `order_close_by(...)`
* `MetaRpcMT4/mt4_term_api_trading_helper_pb2.py` — `OrderCloseBy*` messages (request/reply/data)

### RPC

* **Service:** `mt4_term_api.TradingHelper`
* **Method:** `OrderCloseBy(OrderCloseByRequest) → OrderCloseByReply`
* **Low‑level client:** `TradingHelperStub.OrderCloseBy(request, metadata, timeout)`
* **SDK wrapper:**

  ```python
  MT4Account.order_close_by(
      ticket_to_close: int,
      opposite_ticket_closing_by: int,
      deadline: datetime | None = None,
      cancellation_event: asyncio.Event | None = None,
  ) -> trading_helper_pb2.OrderCloseByData
  ```

**Request message:** `OrderCloseByRequest { ticket_to_close, opposite_ticket_closing_by }`
**Reply message:** `OrderCloseByReply { data: OrderCloseByData }`

---

### 🔗 Code Examples

```python
# 1) Close a BUY by an opposite SELL on the same symbol
await acct.order_close_by(
    ticket_to_close=buy_ticket,
    opposite_ticket_closing_by=sell_ticket,
)

# 2) After close-by, reconcile residuals (if volumes differed)
od = await acct.opened_orders()
# If one side had bigger lots, you'll still see a reduced position remaining
```

---

### Method Signature

```python
async def order_close_by(
    self,
    ticket_to_close: int,
    opposite_ticket_closing_by: int,
    deadline: datetime | None = None,
    cancellation_event: asyncio.Event | None = None,
) -> trading_helper_pb2.OrderCloseByData
```

---

## 💬 Just the essentials

* **What it is.** MT4 "Close By": match two opposite positions on the **same symbol**; broker nets them and closes both (or leaves a residual).
* **Why.** Save commissions/swaps vs closing both separately; perform clean netting operations on hedge accounts.
* **Volumes.** If volumes differ, the **smaller** is closed against the **larger**; the remainder stays open.

---

## 🔽 Input

| Parameter                    | Type           | Description                                                   |                                       |
| ---------------------------- | -------------- | ------------------------------------------------------------- | ------------------------------------- |
| `ticket_to_close`            | `int`          | Ticket of the position you consider the primary close target. |                                       |
| `opposite_ticket_closing_by` | `int`          | Ticket of the opposite position used to close by.             |                                       |
| `deadline`                   | `datetime      | None`                                                         | Absolute per‑call deadline.           |
| `cancellation_event`         | `asyncio.Event | None`                                                         | Cooperative cancel for retry wrapper. |

> The wrapper does **not** accept `lots`/`slippage` — the server nets the volumes directly according to MT4 rules.

---

## ⬆️ Output

### Payload: `OrderCloseByData`

Concrete fields vary by pb build. Common ones:

| Field                 | Proto Type                   | Description                                            |
| --------------------- | ---------------------------- | ------------------------------------------------------ |
| `order_was_closed_by` | `bool?`                      | Operation result flag.                                 |
| `close_price_first`   | `double?`                    | Close price applied to the first ticket (if reported). |
| `close_price_second`  | `double?`                    | Close price for the opposite ticket (if reported).     |
| `lots_closed`         | `double?`                    | Net lots closed (min of two volumes).                  |
| `date_time`           | `google.protobuf.Timestamp?` | Server timestamp of the operation.                     |

> Check your `mt4_term_api_trading_helper_pb2.py` for the authoritative schema.

---

## 🧱 Related enums (from pb)

This RPC **does not use method‑specific enums**.

---

### 🎯 Purpose

Use this method to:

* Net two hedge positions efficiently (BUY vs SELL on the same symbol).
* Reduce costs when de‑hedging grids or martingale legs.
* Keep audit trails cleaner (single *close by* event instead of two closes).

### 🧩 Notes & Tips

* Works on **hedge accounts**; not applicable to netting/FIFO modes.
* Ensure **same symbol** and **opposite sides**; broker will reject otherwise.
* After reconnection, pull `opened_orders()` to verify that any residual was handled correctly.
* If you need explicit partials on a single position, use `order_close_delete(...)` instead.

**See also:**
`order_close_delete(...)` — partial/full close or delete pending.
`opened_orders(...)` — snapshot to verify residuals.
`on_trade(...)` — stream to observe the resulting trade events.

---

## Usage Snippets

### 1) Find an opposite ticket by symbol

```python
od = await acct.opened_orders()
# suppose we want to close BUY by any SELL on the same symbol
buy = next(o for o in od.items if o.order_type == ORDER_TYPE_BUY)
sell = next(o for o in od.items if o.symbol == buy.symbol and o.order_type == ORDER_TYPE_SELL)
await acct.order_close_by(buy.ticket, sell.ticket)
```

### 2) Post‑check residual position

```python
after = await acct.opened_orders()
left = [o for o in after.items if o.symbol == buy.symbol]
# If any remain, volumes were unequal; update your UI or risk accordingly
```
