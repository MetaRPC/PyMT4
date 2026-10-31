# Order Close By

> Close an order by an opposite order on the same symbol — net a hedge in one operation.

**API Information:**

* **Low-level API:** `MT4Account.order_close_by(...)` (defined in `package/MetaRpcMT4/mt4_account.py`)
* **gRPC service:** `mt4_term_api.TradingHelper`
* **RPC:** `OrderCloseBy(OrderCloseByRequest) -> OrderCloseByReply`
* **Payload:** `OrderCloseByData`

## 💬 Just the essentials

* **What it is.** Closes one order using an opposite-direction order on the same symbol, netting them against each other.
* **Why you need it.** To unwind a hedge (a buy and a sell on the same symbol) in a single operation instead of closing each leg.
* **When to use.** When you hold opposite orders on one symbol and want to net them.

---

## 🎯 Purpose

* Close-by between two opposite tickets
* Net a hedge in one call
* Get the resulting close price / profit

---

## Method Signature

```python
async def order_close_by(
    self,
    ticket_to_close: int,
    opposite_ticket_closing_by: int,
    deadline: Optional[datetime] = None,
    cancellation_event: Optional[asyncio.Event] = None,
)
```

**Request message:**

```protobuf
message OrderCloseByRequest {
  int32 ticket_to_close = 1;
  int32 opposite_ticket_closing_by = 2;
}
```

**Payload message:**

```protobuf
message OrderCloseByData {
  double close_price = 1;
  double profit = 2;
  Timestamp close_time = 3;
  Timestamp close_time_utc = 4;
}
```

---

## 🔽 Input

| Parameter | Type | Description |
|-----------|------|-------------|
| `ticket_to_close` | `int` | The ticket to be closed. |
| `opposite_ticket_closing_by` | `int` | The opposite-direction ticket used to close it. |
| `deadline` | datetime, optional | Absolute UTC deadline for the gRPC call. |
| `cancellation_event` | asyncio.Event, optional | Set to abort the request. |

---

## ⬆️ Output — `OrderCloseByData`

| Field | Python Type | Description |
|-------|-------------|-------------|
| `close_price` | `float` | Price at which the close-by settled |
| `profit` | `float` | Realized profit from the operation |
| `close_time` / `close_time_utc` | `datetime` | Close time (server / UTC) |

---

## 🧩 Notes & Tips

* **Both legs must be opposite and same-symbol.** A BUY and a SELL on the same instrument; close-by nets them.
* **Order of tickets matters.** `ticket_to_close` is the one being closed; `opposite_ticket_closing_by` is the counter order.
* **Broker support varies.** Not all brokers allow close-by (and hedging must be permitted); unsupported setups raise `ApiExceptionMT4`.
* **Alternative:** close each leg independently with [order_close_delete](order_close_delete.md) if close-by isn't available.
* **Market must be open** — a closed session raises `ERR_MARKET_CLOSED` (132).

---

## 🔗 Usage Examples

### 1) Close one order by another

```python
async def close_by(account, ticket: int, opposite: int):
    res = await account.order_close_by(ticket_to_close=ticket,
                                       opposite_ticket_closing_by=opposite)
    print(f"closed #{ticket} by #{opposite}: profit={res.profit:+.2f} @ {res.close_price:.5f}")
    return res
```

### 2) Net a hedge on a symbol

Find a buy and a sell on the same symbol and close them against each other.

```python
import MetaRpcMT4.mt4_term_api_account_helper_pb2 as ah

async def net_hedge(account, symbol: str):
    data = await account.opened_orders()
    buys  = [o for o in data.order_infos if o.symbol == symbol and o.order_type == ah.OpenedOrderType.OO_OP_BUY]
    sells = [o for o in data.order_infos if o.symbol == symbol and o.order_type == ah.OpenedOrderType.OO_OP_SELL]
    if buys and sells:
        res = await account.order_close_by(ticket_to_close=buys[0].ticket,
                                            opposite_ticket_closing_by=sells[0].ticket)
        print(f"netted {symbol}: profit={res.profit:+.2f}")
        return res
    print(f"no opposite pair on {symbol}")
```

---

## ⚠️ Pitfalls

* **Must be a true opposite pair.** Same symbol, opposite directions — otherwise the call is rejected.
* **Hedging may be disabled.** Brokers that forbid hedging (or close-by) raise `ApiExceptionMT4`; fall back to [order_close_delete](order_close_delete.md).
* **Market closed.** Raises `ERR_MARKET_CLOSED` (132) on a closed session.
* **Exceptions, not codes.** Wrap in `try/except`.

---

## 🧪 Testing Suggestions

* **Happy path (market open, hedging allowed).** Open a BUY and a SELL 0.01 on one symbol, then `order_close_by` → both leave [opened_orders](../2. Orders_History/opened_orders.md).
* **Unsupported.** On a non-hedging broker, assert the call raises rather than silently doing nothing.
* **Result fields.** `close_price` and `close_time` are populated on success.

---

## 📚 See also

* [Order Send](order_send.md)
* [Order Close / Delete](order_close_delete.md)
* [Order Modify](order_modify.md)

* **Back to:** [Trading Operations — Overview](Trading_Operations.Overview.md) · [MT4Account — Master Overview](../MT4Account.Master.Overview.md)
