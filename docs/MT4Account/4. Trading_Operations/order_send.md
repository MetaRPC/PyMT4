# Order Send

> Send a market or pending order — the low-level entry point for opening trades.

**API Information:**

* **Low-level API:** `MT4Account.order_send(...)` (defined in `package/MetaRpcMT4/mt4_account.py`)
* **gRPC service:** `mt4_term_api.TradingHelper`
* **RPC:** `OrderSend(OrderSendRequest) -> OrderSendReply`
* **Payload:** `OrderSendData`

## 💬 Just the essentials

* **What it is.** Opens a market order or places a pending order, with optional SL/TP, comment and magic.
* **Why you need it.** Full control over every order field at the lowest level.
* **When to use.** When you need raw control. For pips-based SL/TP, normalization and risk sizing, prefer MT4Sugar (`buy_market`, `buy_limit`, …) which wraps this.

---

## 🎯 Purpose

* Open market orders (BUY / SELL)
* Place pending orders (LIMIT / STOP)
* Attach SL / TP, comment and magic number
* Set slippage and pending-order expiration

---

## Method Signature

```python
async def order_send(
    self,
    symbol: str,
    operation_type: OrderSendOperationType,
    volume: float,
    price: Optional[float] = None,
    slippage: Optional[int] = None,
    stoploss: Optional[float] = None,
    takeprofit: Optional[float] = None,
    comment: Optional[str] = None,
    magic_number: Optional[int] = None,
    expiration: Optional[datetime] = None,
    deadline: Optional[datetime] = None,
    cancellation_event: Optional[asyncio.Event] = None,
)
```

**Request message:**

```protobuf
message OrderSendRequest {
  string symbol = 1;
  OrderSendOperationType operation_type = 2;
  double volume = 3;
  double price = 4;
  int32 slippage = 5;
  double stoploss = 6;
  double takeprofit = 7;
  string comment = 8;
  int32 magic_number = 9;
  Timestamp expiration = 10;      // (+ expiration_utc)
}
```

**Payload message:**

```protobuf
message OrderSendData {
  int32 ticket = 1;
  double volume = 2;
  double price = 3;
  Timestamp open_time = 4;
  Timestamp open_time_utc = 5;
}
```

---

## 🔽 Input

| Parameter | Type | Description |
|-----------|------|-------------|
| `symbol` | `str` | Symbol name. |
| `operation_type` | `OrderSendOperationType` | Buy/sell, market or pending (see enum). |
| `volume` | `float` | Lots. |
| `price` | float, optional | Entry price — **required for pending orders**; for market orders it can be omitted. |
| `slippage` | int, optional | Max slippage in points (market orders). |
| `stoploss` | float, optional | Stop-loss price (0 / omit for none). |
| `takeprofit` | float, optional | Take-profit price (0 / omit for none). |
| `comment` | str, optional | Order comment. |
| `magic_number` | int, optional | Expert/magic id to tag the order. |
| `expiration` | datetime, optional | Expiration for pending orders. |
| `deadline` | datetime, optional | Absolute UTC deadline for the gRPC call. |
| `cancellation_event` | asyncio.Event, optional | Set to abort the request. |

---

## ⬆️ Output — `OrderSendData`

| Field | Python Type | Description |
|-------|-------------|-------------|
| `ticket` | `int` | Ticket of the new order |
| `volume` | `float` | Filled/placed volume |
| `price` | `float` | Fill price (market) or pending price |
| `open_time` / `open_time_utc` | `datetime` | Open/placement time (server / UTC) |

> On failure the call raises `ApiExceptionMT4` — inspect `e.error.mql_error_int_code` / `e.error.mql_error_description` (see the [Return Codes Reference](../../All_Guides/RETURN_CODES_REFERENCE.md)).

---

## 🧱 Related enums (from proto)

### `OrderSendOperationType` — input `operation_type`

| Constant | Value | Meaning |
|----------|-------|---------|
| `OC_OP_BUY` | 0 | Market buy |
| `OC_OP_SELL` | 1 | Market sell |
| `OC_OP_BUYLIMIT` | 2 | Buy limit (pending, below price) |
| `OC_OP_SELLLIMIT` | 3 | Sell limit (pending, above price) |
| `OC_OP_BUYSTOP` | 4 | Buy stop (pending, above price) |
| `OC_OP_SELLSTOP` | 5 | Sell stop (pending, below price) |

> Access via `trading_helper_pb2.OrderSendOperationType.OC_OP_BUY`.

---

## 🧩 Notes & Tips

* **Market vs pending.** `OC_OP_BUY`/`OC_OP_SELL` fill immediately (price optional); the `*LIMIT`/`*STOP` variants are pending and **require** `price`.
* **Absolute SL/TP prices.** `stoploss`/`takeprofit` are prices, not pip distances. Respect the symbol's `TradeStopsLevel` ([symbol_params_many](../3. Symbols_Quotes/symbol_params_many.md)) or you'll get `ERR_INVALID_STOPS` (130).
* **Normalize first.** Round `volume` to `VolumeStep` and prices to `Digits`; MT4Sugar does this automatically.
* **Tag with `magic_number`.** It's how you later identify "my" orders in [opened_orders](../2. Orders_History/opened_orders.md).
* **Returns a ticket** on success — there is no numeric `returned_code` (that's MT5); errors are exceptions.

---

## 🔗 Usage Examples

> ⚠️ These place **real orders on the connected (demo) account**. Use 0.01 lots and clean up.

### 1) Open a market BUY

```python
import MetaRpcMT4.mt4_term_api_trading_helper_pb2 as th

async def buy(account, symbol="EURUSD", lots=0.01):
    res = await account.order_send(symbol, th.OrderSendOperationType.OC_OP_BUY, lots)
    print(f"opened #{res.ticket} {res.volume} lot @ {res.price:.5f}")
    return res.ticket
```

### 2) Market SELL with SL/TP, comment and magic

```python
import MetaRpcMT4.mt4_term_api_trading_helper_pb2 as th

async def sell_with_stops(account, symbol="EURUSD", lots=0.01):
    q = await account.quote(symbol)
    sl = round(q.bid + 0.0020, 5)   # 20 pips above for a short
    tp = round(q.bid - 0.0030, 5)   # 30 pips below
    res = await account.order_send(
        symbol, th.OrderSendOperationType.OC_OP_SELL, lots,
        stoploss=sl, takeprofit=tp, comment="demo sell", magic_number=777,
    )
    print(f"opened #{res.ticket} SL={sl} TP={tp}")
    return res.ticket
```

### 3) Place a BUY LIMIT below the market

```python
import MetaRpcMT4.mt4_term_api_trading_helper_pb2 as th

async def buy_limit(account, symbol="EURUSD", lots=0.01):
    q = await account.quote(symbol)
    price = round(q.ask - 0.0030, 5)   # 30 pips below current ask
    res = await account.order_send(
        symbol, th.OrderSendOperationType.OC_OP_BUYLIMIT, lots, price=price,
    )
    print(f"placed BUY LIMIT #{res.ticket} @ {price}")
    return res.ticket
```

### 4) Robust send with error handling

```python
import MetaRpcMT4.mt4_term_api_trading_helper_pb2 as th
from MetaRpcMT4.mt4_account import ApiExceptionMT4
from MetaRpcMT4 import mrpc_mt4_error_pb2 as err

async def safe_buy(account, symbol="EURUSD", lots=0.01):
    try:
        res = await account.order_send(symbol, th.OrderSendOperationType.OC_OP_BUY, lots)
        return res.ticket
    except ApiExceptionMT4 as e:
        code = e.error.mql_error_int_code
        if code == err.MqlErrorCode.ERR_NOT_ENOUGH_MONEY:      # 134
            print("not enough money")
        elif code == err.MqlErrorCode.ERR_INVALID_STOPS:        # 130
            print("SL/TP too close to price")
        else:
            print(f"rejected: {e.error.mql_error_description} ({code})")
        return None
```

---

## ⚠️ Pitfalls

* **Pending orders need `price`.** Omitting it for a `*LIMIT`/`*STOP` order fails.
* **SL/TP are prices.** And must respect `TradeStopsLevel` — too-close stops raise `ERR_INVALID_STOPS` (130).
* **Un-normalized volume/price.** Values off the broker's step/digits are rejected (`ERR_INVALID_TRADE_VOLUME` 131 / `ERR_INVALID_PRICE` 129).
* **Rejections are exceptions**, not a return code — always wrap trading calls in `try/except ApiExceptionMT4`.
* **Clean up demos.** Close what you open with [order_close_delete](order_close_delete.md).

---

## 🧪 Testing Suggestions

* **Happy path (demo).** A 0.01 market BUY returns a positive `ticket`; the ticket appears in [opened_orders](../2. Orders_History/opened_orders.md).
* **Round-trip.** Open then [order_close_delete](order_close_delete.md) the ticket; it leaves `opened_orders`.
* **Failure path.** Send an oversized volume and assert `ApiExceptionMT4` with a sensible `mql_error_int_code`.

---

## 📚 See also

* [Order Modify](order_modify.md)
* [Order Close / Delete](order_close_delete.md)
* [Order Close By](order_close_by.md)
* [Opened Orders](../2. Orders_History/opened_orders.md)

* **Back to:** [Trading Operations — Overview](Trading_Operations.Overview.md) · [MT4Account — Master Overview](../MT4Account.Master.Overview.md)
