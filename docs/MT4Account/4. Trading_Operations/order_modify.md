# Order Modify

> Change an existing order's SL, TP, pending price or expiration.

**API Information:**

* **Low-level API:** `MT4Account.order_modify(...)` (defined in `package/MetaRpcMT4/mt4_account.py`)
* **gRPC service:** `mt4_term_api.TradingHelper`
* **RPC:** `OrderModify(OrderModifyRequest) -> OrderModifyReply`
* **Payload:** `OrderModifyData`

## 💬 Just the essentials

* **What it is.** Updates SL/TP (and, for pending orders, the entry price / expiration) of an order that already exists.
* **Why you need it.** To manage live orders without closing them — trailing stops, breakeven, re-pricing pendings.
* **When to use.** Any time you adjust protection or a pending price. MT4Sugar's `modify_sl_tp_by_price` / `modify_sl_tp_by_pips` wrap this.

---

## 🎯 Purpose

* Change SL / TP on a live order
* Re-price a pending order
* Update a pending order's expiration

---

## Method Signature

```python
async def order_modify(
    self,
    order_ticket: int,
    new_price: Optional[float] = None,
    new_stop_loss: Optional[float] = None,
    new_take_profit: Optional[float] = None,
    new_expiration: Optional[datetime] = None,
    deadline: Optional[datetime] = None,
    cancellation_event: Optional[asyncio.Event] = None,
)
```

**Request message:**

```protobuf
message OrderModifyRequest {
  int32 order_ticket = 1;
  double new_price = 2;              // pending-order price
  double new_stop_loss = 3;
  double new_take_profit = 4;
  Timestamp new_expiration = 5;      // (+ new_expiration_utc)
}
```

**Payload message:**

```protobuf
message OrderModifyData {
  bool order_was_modified = 1;
}
```

---

## 🔽 Input

| Parameter | Type | Description |
|-----------|------|-------------|
| `order_ticket` | `int` | Ticket to modify. |
| `new_price` | float, optional | New pending-order price (ignored for filled market orders). |
| `new_stop_loss` | float, optional | New SL price. |
| `new_take_profit` | float, optional | New TP price. |
| `new_expiration` | datetime, optional | New expiration (pending orders). |
| `deadline` | datetime, optional | Absolute UTC deadline for the gRPC call. |
| `cancellation_event` | asyncio.Event, optional | Set to abort the request. |

---

## ⬆️ Output — `OrderModifyData`

| Field | Python Type | Description |
|-------|-------------|-------------|
| `order_was_modified` | `bool` | True if the change was applied |

> On failure the call raises `ApiExceptionMT4` — e.g. `ERR_INVALID_STOPS` (130) when SL/TP is too close, or `ERR_NO_RESULT`/`ERR_TRADE_MODIFY_DENIED` (145) when nothing changed or the order is too near market.

---

## 🧩 Notes & Tips

* **Prices, not pips.** `new_stop_loss` / `new_take_profit` are absolute prices — convert from pips yourself (or use MT4Sugar's `modify_sl_tp_by_pips`).
* **Pass only what changes.** Supply just the fields you want to update; leave the rest `None`.
* **Respect the stops level.** New SL/TP must be at least `TradeStopsLevel` points from price ([symbol_params_many](../3. Symbols_Quotes/symbol_params_many.md)).
* **Pending vs market.** `new_price`/`new_expiration` only make sense for pending orders; for filled market orders, modify SL/TP.
* **No-op is an error on some brokers.** Submitting unchanged values can raise rather than silently succeed — only call when something actually changes.

---

## 🔗 Usage Examples

### 1) Set SL and TP on an order

```python
async def set_stops(account, ticket: int, sl: float, tp: float) -> bool:
    res = await account.order_modify(ticket, new_stop_loss=sl, new_take_profit=tp)
    print("modified" if res.order_was_modified else "no change")
    return res.order_was_modified
```

### 2) Trail the stop (move SL only)

Raise the stop on a long as price advances — one trailing step.

```python
async def trail_stop(account, ticket: int, symbol: str, distance_pips: float = 20):
    q = await account.quote(symbol)
    info = (await account.symbol_params_many(symbol)).symbol_infos[0]
    pip = info.Point * (10 if info.Digits in (3, 5) else 1)
    new_sl = round(q.bid - distance_pips * pip, info.Digits)   # for a BUY
    await account.order_modify(ticket, new_stop_loss=new_sl)
    print(f"SL -> {new_sl}")
```

### 3) Re-price a pending order

Move a resting BUY LIMIT to a new level.

```python
async def reprice_pending(account, ticket: int, new_price: float):
    res = await account.order_modify(ticket, new_price=round(new_price, 5))
    return res.order_was_modified
```

---

## ⚠️ Pitfalls

* **Absolute prices.** SL/TP/price are prices, not distances — compute them before calling.
* **Too-close stops.** Violating `TradeStopsLevel` raises `ERR_INVALID_STOPS` (130).
* **No-change calls.** Re-submitting identical values may raise (`ERR_TRADE_MODIFY_DENIED` 145 / no result) — guard against it.
* **Exceptions, not codes.** Failures raise `ApiExceptionMT4`; wrap in `try/except`.

---

## 🧪 Testing Suggestions

* **Happy path (market open).** Modifying SL/TP of an open order returns `order_was_modified == True` and the new values show in [opened_orders](../2. Orders_History/opened_orders.md).
* **Too-close SL.** A stop inside `TradeStopsLevel` raises `ERR_INVALID_STOPS` (130).
* **No-op.** Re-applying the same SL/TP either returns False or raises — assert your code tolerates both.

---

## 📚 See also

* [Order Send](order_send.md)
* [Order Close / Delete](order_close_delete.md)
* [Opened Orders](../2. Orders_History/opened_orders.md)

* **Back to:** [Trading Operations — Overview](Trading_Operations.Overview.md) · [MT4Account — Master Overview](../MT4Account.Master.Overview.md)
