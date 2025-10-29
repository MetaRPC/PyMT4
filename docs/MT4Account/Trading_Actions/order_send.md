# ✅ Sending an Order — `order_send`

> **Request:** place a **market or pending order** on a given symbol.
> Wrapper around the TradingHelper RPC that accepts volume, optional price (for pending), SL/TP, slippage, comment, magic, and expiration.

**Source files (SDK):**

* `MetaRpcMT4/mt4_account.py` — method `order_send(...)`
* `MetaRpcMT4/mt4_term_api_trading_helper_pb2.py` — `OrderSend*` messages, `OrderSendOperationType` enum

### RPC

* **Service:** `mt4_term_api.TradingHelper`
* **Method:** `OrderSend(OrderSendRequest) → OrderSendReply`
* **Low‑level client:** `TradingHelperStub.OrderSend(request, metadata, timeout)`
* **SDK wrapper:**

  ```python
  MT4Account.order_send(
      symbol: str,
      operation_type: trading_helper_pb2.OrderSendOperationType,
      volume: float,
      price: float | None = None,
      slippage: int | None = None,
      stoploss: float | None = None,
      takeprofit: float | None = None,
      comment: str | None = None,
      magic_number: int | None = None,
      expiration: datetime | None = None,
      deadline: datetime | None = None,
      cancellation_event: asyncio.Event | None = None,
  ) -> trading_helper_pb2.OrderSendData
  ```

**Request message:** `OrderSendRequest { symbol, operation_type, volume, price?, slippage?, stoploss?, takeprofit?, comment?, magic_number?, expiration? }`
**Reply message:** `OrderSendReply { data: OrderSendData }`

---

### 🔗 Code Examples

```python
from MetaRpcMT4 import mt4_term_api_trading_helper_pb2 as trade_pb

# 1) Market BUY 0.10 with SL/TP
await acct.order_send(
    symbol="EURUSD",
    operation_type=trade_pb.OrderSendOperationType.OC_OP_BUY,  # BUY
    volume=0.10,
    stoploss=1.0820,
    takeprofit=1.0870,
    slippage=20,  # points
    comment="bot v1",
    magic_number=12345,
)

# 2) Pending SELL LIMIT with expiration
from datetime import datetime, timedelta, timezone
await acct.order_send(
    symbol="XAUUSD",
    operation_type=trade_pb.OrderSendOperationType.OC_OP_SELLLIMIT,
    volume=0.50,
    price=2365.0,
    stoploss=2378.0,
    takeprofit=2325.0,
    expiration=datetime.now(timezone.utc) + timedelta(hours=6),
    comment="grid#7",
)
```

---

### Method Signature

```python
async def order_send(
    self,
    symbol: str,
    operation_type: trading_helper_pb2.OrderSendOperationType,
    volume: float,
    price: float | None = None,
    slippage: int | None = None,
    stoploss: float | None = None,
    takeprofit: float | None = None,
    comment: str | None = None,
    magic_number: int | None = None,
    expiration: datetime | None = None,
    deadline: datetime | None = None,
    cancellation_event: asyncio.Event | None = None,
) -> trading_helper_pb2.OrderSendData
```

---

## 💬 Just the essentials

* **What it is.** A single call to place **market or pending** orders.
* **Why.** Primary entry‑point for strategy execution / manual actions.
* **Validation.** Always combine with `symbol_params_many(...)` to respect `VolumeMin/Max/Step`, `StopsLevel/FreezeLevel`, and with `quote(...)` for price sanity.

---

## 🔽 Input

| Parameter            | Type                     | Description                                                 |                                                        |
| -------------------- | ------------------------ | ----------------------------------------------------------- | ------------------------------------------------------ |
| `symbol`             | `str`                    | Target symbol (e.g., `EURUSD`).                             |                                                        |
| `operation_type`     | `OrderSendOperationType` | **BUY / SELL / BUYLIMIT / SELLLIMIT / BUYSTOP / SELLSTOP**. |                                                        |
| `volume`             | `float`                  | Lots to trade (see `VolumeMin/Max/Step`).                   |                                                        |
| `price`              | `float                   | None`                                                       | Entry price for **pending** orders; `None` for market. |
| `slippage`           | `int                     | None`                                                       | Max slippage in **points** for market orders.          |
| `stoploss`           | `float                   | None`                                                       | Initial SL.                                            |
| `takeprofit`         | `float                   | None`                                                       | Initial TP.                                            |
| `comment`            | `str                     | None`                                                       | User/system comment.                                   |
| `magic_number`       | `int                     | None`                                                       | EA magic for robots.                                   |
| `expiration`         | `datetime                | None`                                                       | Expiration for pending orders.                         |
| `deadline`           | `datetime                | None`                                                       | Absolute per‑call deadline.                            |
| `cancellation_event` | `asyncio.Event           | None`                                                       | Cooperative cancel for retry wrapper.                  |

> Price/SL/TP are **raw prices**; convert from points/pips with `Point` from `symbol_params_many(...)`.

---

## ⬆️ Output

### Payload: `OrderSendData`

Fields vary by integration; commonly returned:

| Field             | Proto Type                   | Description                                          |
| ----------------- | ---------------------------- | ---------------------------------------------------- |
| `ticket`          | `int32`                      | Ticket assigned to the newly created order/position. |
| `price`           | `double`                     | Executed/placed price (market or pending).           |
| `new_stop_loss`   | `double?`                    | Server‑normalized SL (if adjusted).                  |
| `new_take_profit` | `double?`                    | Server‑normalized TP (if adjusted).                  |
| `new_expiration`  | `google.protobuf.Timestamp?` | Server‑side expiration value (for pendings).         |
| `magic_number`    | `int32`                      | Echoed magic number.                                 |
| `comment`         | `string`                     | Echoed/normalized comment.                           |
| `date_time`       | `google.protobuf.Timestamp?` | Server timestamp.                                    |

> On error, the wrapper raises per `error_selector` in `execute_with_reconnect(...)`.

---

## 🧱 Related enums (from pb)

### `OrderSendOperationType`

Operation choices equal to MT4 order kinds (labels may differ by build):

* `OC_OP_BUY`
* `OC_OP_SELL`
* `OC_OP_BUYLIMIT`
* `OC_OP_SELLLIMIT`
* `OC_OP_BUYSTOP`
* `OC_OP_SELLSTOP`

> Map enum → label in UI via `trade_pb.OrderSendOperationType.Name(value)`.

---

### 🎯 Purpose

Use this method to:

* Place entries from strategies or UI.
* Create bracket orders with initial SL/TP.
* Populate audit logs with ticket/price outcomes.

### 🧩 Notes & Tips

* Respect **StopsLevel/FreezeLevel**: ensure `abs(entry - SL/TP) >= min_points * Point`.
* **Volume snapping:** clamp and snap to `[VolumeMin, VolumeMax]` by `VolumeStep`.
* Prefer absolute UTC times for `expiration`. Ensure it’s in the future relative to server time.
* For market orders, omit `price`; the server will fill at best available within `slippage`.

**See also:**
`order_modify(...)` — update SL/TP/expiration/price for pending.
`order_close_delete(...)` — close market positions / delete pendings.
`order_close_by(...)` — close one position by another (hedge accounts).

---

## Usage Snippets

### 1) Snap & validate volume

```python
p = (await acct.symbol_params_many("EURUSD")).params_info[0]

def snap_volume(vol, p):
    vol = max(p.VolumeMin, min(p.VolumeMax, vol))
    steps = round((vol - p.VolumeMin) / p.VolumeStep)
    return p.VolumeMin + steps * p.VolumeStep

v = snap_volume(0.27, p)
```

### 2) Ensure SL/TP distances

```python
q = await acct.quote("EURUSD")
p = (await acct.symbol_params_many("EURUSD")).params_info[0]
min_pts = max(p.StopsLevel, p.FreezeLevel)
min_delta = min_pts * p.Point

# Example for BUY pending
entry = q.ask - 10 * p.Point
sl = entry - 20 * p.Point
assert (entry - sl) >= min_delta
```

### 3) Market buy with tight slippage and comment

```python
from MetaRpcMT4 import mt4_term_api_trading_helper_pb2 as trade_pb
await acct.order_send(
    symbol="GBPUSD",
    operation_type=trade_pb.OrderSendOperationType.OC_OP_BUY,
    volume=0.20,
    slippage=10,
    comment="scalp#42",
)
```
