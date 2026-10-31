# Order Close / Delete

> Close a market order (fully or partially) or delete a pending order — one call for both.

**API Information:**

* **Low-level API:** `MT4Account.order_close_delete(...)` (defined in `package/MetaRpcMT4/mt4_account.py`)
* **gRPC service:** `mt4_term_api.TradingHelper`
* **RPC:** `OrderCloseDelete(OrderCloseDeleteRequest) -> OrderCloseDeleteReply`
* **Payload:** `OrderCloseDeleteData`

## 💬 Just the essentials

* **What it is.** Closes a filled market order (whole or part) or removes a resting pending order — the server picks the right action by order type.
* **Why you need it.** To exit positions, take partial profit, or cancel pendings.
* **When to use.** Taking profit/loss, scaling out, or cleanup. MT4Sugar's `close` / `close_all` / `cancel_pendings` wrap this.

---

## 🎯 Purpose

* Close a market order in full
* Partially close a market order (pass `lots`)
* Delete a pending order
* Learn which action happened via `mode`

---

## Method Signature

```python
async def order_close_delete(
    self,
    order_ticket: int,
    lots: Optional[float] = None,
    closing_price: Optional[float] = None,
    slippage: Optional[int] = None,
    deadline: Optional[datetime] = None,
    cancellation_event: Optional[asyncio.Event] = None,
)
```

**Request message:**

```protobuf
message OrderCloseDeleteRequest {
  int32 order_ticket = 1;
  double lots = 2;            // partial close volume; omit for full
  double closing_price = 3;   // market close price (optional)
  int32 slippage = 4;
}
```

**Payload message:**

```protobuf
message OrderCloseDeleteData {
  OrderCloseDeleteMode mode = 1;        // which action happened
  string history_order_comment = 2;
}
```

---

## 🔽 Input

| Parameter | Type | Description |
|-----------|------|-------------|
| `order_ticket` | `int` | Ticket to close or delete. |
| `lots` | float, optional | Lots to close (partial); omit to close in full. |
| `closing_price` | float, optional | Closing price for market orders. |
| `slippage` | int, optional | Max slippage in points. |
| `deadline` | datetime, optional | Absolute UTC deadline for the gRPC call. |
| `cancellation_event` | asyncio.Event, optional | Set to abort the request. |

---

## ⬆️ Output — `OrderCloseDeleteData`

| Field | Python Type | Description |
|-------|-------------|-------------|
| `mode` | `OrderCloseDeleteMode` (`int`) | Whether a market order was closed or a pending deleted |
| `history_order_comment` | `str` | Resulting history/close comment |

---

## 🧱 Related enums (from proto)

### `OrderCloseDeleteMode` — field `mode`

| Constant | Value | Meaning |
|----------|-------|---------|
| `OCD_MARKET_ORDER` | 0 | A market order was closed |
| `OCD_PENDING_ORDER` | 1 | A pending order was deleted |

> Access via `trading_helper_pb2.OrderCloseDeleteMode.OCD_MARKET_ORDER`.

---

## 🧩 Notes & Tips

* **One call, both actions.** You don't choose close-vs-delete — the server does it based on the order type and reports it in `mode`.
* **Partial close.** Pass `lots` smaller than the order's volume; the remainder stays open as a separate ticket.
* **Pending deletes ignore `lots`.** For a pending order the whole thing is removed.
* **Market must be open** to close a market order — a weekend/closed market raises `ERR_MARKET_CLOSED` (132).
* **Bulk exits.** For closing many orders use MT4Sugar's `close_all` / `cancel_pendings` rather than looping this by hand.

---

## 🔗 Usage Examples

### 1) Close an order in full

```python
async def close(account, ticket: int):
    res = await account.order_close_delete(order_ticket=ticket)
    kind = "closed market" if res.mode == 0 else "deleted pending"
    print(f"#{ticket}: {kind}")
    return res
```

### 2) Partial close (scale out)

Close half of a position, leaving the rest to run.

```python
async def close_half(account, ticket: int, lots: float):
    half = round(lots / 2, 2)
    await account.order_close_delete(order_ticket=ticket, lots=half)
    print(f"#{ticket}: closed {half} lot, rest left open")
```

### 3) Close everything on a symbol

Pull open orders, then close each matching ticket.

```python
async def close_symbol(account, symbol: str):
    data = await account.opened_orders()
    for o in data.order_infos:
        if o.symbol == symbol:
            try:
                await account.order_close_delete(order_ticket=o.ticket)
                print(f"closed #{o.ticket}")
            except Exception as e:
                print(f"#{o.ticket} failed: {e}")
```

---

## ⚠️ Pitfalls

* **Market closed.** Closing a market order when the session is closed raises `ERR_MARKET_CLOSED` (132) — pendings can still usually be deleted.
* **Partial close limits.** `lots` must respect the symbol's volume step and be ≤ the order's volume.
* **Exceptions, not codes.** Failures raise `ApiExceptionMT4`; wrap in `try/except`.
* **Already closed.** Closing a ticket that's gone raises — tolerate it in cleanup loops.

---

## 🧪 Testing Suggestions

* **Round-trip (market open).** [order_send](order_send.md) then `order_close_delete` → `mode == OCD_MARKET_ORDER`; the ticket leaves [opened_orders](../2. Orders_History/opened_orders.md).
* **Pending delete.** Place a pending order and delete it → `mode == OCD_PENDING_ORDER`.
* **Partial.** Close part of a 0.02 position and assert a 0.01 remainder stays open.

---

## 📚 See also

* [Order Send](order_send.md)
* [Order Modify](order_modify.md)
* [Order Close By](order_close_by.md)

* **Back to:** [Trading Operations — Overview](Trading_Operations.Overview.md) · [MT4Account — Master Overview](../MT4Account.Master.Overview.md)
