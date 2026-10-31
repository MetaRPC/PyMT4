# ENUMs Usage Reference - MT4Account (Python)

> ENUM presence lookup table for all MT4Account low-level methods.
> Every method, enum name and value count below is taken directly from the
> `MetaRpcMT4` protobuf definitions.

---

## ✅ Summary Statistics

| Method Group | With ENUMs | Total | Percentage |
|--------------|------------|-------|------------|
| **Account Information** | 1 | 1 | 100% |
| **Orders & History** | 2 | 3 | 67% |
| **Symbols & Quotes** | 2 | 6 | 33% |
| **Trading Operations** | 2 | 4 | 50% |
| **Streaming Methods** | 2 | 4 | 50% |
| **TOTAL** | **9** | **18** | **50%** |

> MT4 has a single order list (there is no positions/deals split as in MT5) and
> no Depth-of-Market, `order_check` or `order_calc_*` methods — those are MT5-only.

---

## 👤 1. Account Information (1 method)

### 1/1 methods use ENUMs (100%)

| Method | ENUMs Count | Description | Input ENUMs | Output ENUMs |
|--------|-------------|-------------|-------------|--------------|
| **account_summary** | **[In: 0, Out: 2]**<br>Total: 2 ENUMs | Get all account data in one call (RECOMMENDED) | - | `EnumAccountTradeMode` (3 values) - Account type: DEMO, CONTEST, REAL<br>`EnumAccountMarginMode` (3 values) - Margin calculation mode |

---

## 📋 2. Orders & History (3 methods)

### 2/3 methods use ENUMs (67%)

| Method | ENUMs Count | Description | Input ENUMs | Output ENUMs |
|--------|-------------|-------------|-------------|--------------|
| **opened_orders** | **[In: 1, Out: 1]**<br>Total: 2 ENUMs | Get all currently open orders (market + pending) | `EnumOpenedOrderSortType` (4 values) - Sort mode | `OpenedOrderType` (8 values) - Order operation: BUY, SELL, BUYLIMIT, SELLLIMIT, BUYSTOP, SELLSTOP, BALANCE, CREDIT |
| **opened_orders_tickets** | **[In: 0, Out: 0]**<br>Total: 0 ENUMs | Get only ticket numbers (lightweight) | - | - |
| **orders_history** | **[In: 1, Out: 1]**<br>Total: 2 ENUMs | Get historical (closed) orders with pagination | `EnumOrderHistorySortType` (6 values) - Sort mode | `OpenedOrderType` (8 values) - Order operation type |

---

## 📊 3. Symbols & Quotes (6 methods)

### 2/6 methods use ENUMs (33%)

| Method | ENUMs Count | Description | Input ENUMs | Output ENUMs |
|--------|-------------|-------------|-------------|--------------|
| **symbols** | **[In: 0, Out: 0]**<br>Total: 0 ENUMs | List all symbols available on the account | - | - |
| **quote** | **[In: 0, Out: 0]**<br>Total: 0 ENUMs | Get a single symbol quote (Bid/Ask) | - | - |
| **quote_many** | **[In: 0, Out: 0]**<br>Total: 0 ENUMs | Get quotes for several symbols at once | - | - |
| **quote_history** | **[In: 1, Out: 0]**<br>Total: 1 ENUM (9 values) | Get OHLC bar history for a symbol | `ENUM_QUOTE_HISTORY_TIMEFRAME` (9 values) - Timeframe: QH_PERIOD_M1…MN1 | - |
| **symbol_params_many** | **[In: 0, Out: 3]**<br>Total: 3 ENUMs | Get detailed parameters for multiple symbols | - | **3 ENUMs in SymbolParamsManyInfo:**<br>`SP_ENUM_TRADE_CALC_MODE` (3 values) - Margin calc mode<br>`SP_ENUM_SYMBOL_TRADE_MODE` (5 values) - Trade permission<br>`SP_ENUM_SYMBOL_TRADE_EXECUTION` (4 values) - Execution mode |
| **tick_value_with_size** | **[In: 0, Out: 0]**<br>Total: 0 ENUMs | Get tick value / tick size / contract size | - | - |

---

## 💰 4. Trading Operations (4 methods)

### 2/4 methods use ENUMs (50%)

| Method | ENUMs Count | Description | Input ENUMs | Output ENUMs |
|--------|-------------|-------------|-------------|--------------|
| **order_send** | **[In: 1, Out: 0]**<br>Total: 1 ENUM (6 values) | Send a market or pending order | `OrderSendOperationType` (6 values) - Operation: OC_OP_BUY, OC_OP_SELL, OC_OP_BUYLIMIT, OC_OP_SELLLIMIT, OC_OP_BUYSTOP, OC_OP_SELLSTOP | - |
| **order_modify** | **[In: 0, Out: 0]**<br>Total: 0 ENUMs | Modify SL/TP/price of an existing order | - | - |
| **order_close_delete** | **[In: 0, Out: 1]**<br>Total: 1 ENUM (2 values) | Close a market order or delete a pending one | - | `OrderCloseDeleteMode` (2 values): OCD_MARKET_ORDER, OCD_PENDING_ORDER |
| **order_close_by** | **[In: 0, Out: 0]**<br>Total: 0 ENUMs | Close an order by an opposite one | - | - |

---

## 📡 5. Streaming Methods (4 methods)

### 2/4 methods use ENUMs (50%)

| Method | ENUMs Count | Description | Input ENUMs | Output ENUMs |
|--------|-------------|-------------|-------------|--------------|
| **on_symbol_tick** | **[In: 0, Out: 0]**<br>Total: 0 ENUMs | Stream tick data (Bid/Ask updates) | - | - |
| **on_trade** | **[In: 0, Out: 2]**<br>Total: 2 ENUMs | Stream trade events (new/updated orders) | - | `MT4_SUB_ENUM_EVENT_GROUP_TYPE` (2 values) - Event group: OrderProfit, OrderUpdate<br>`SUB_ORDER_OPERATION_TYPE` (6 values) - Order operation in the event payload |
| **on_opened_orders_tickets** | **[In: 0, Out: 0]**<br>Total: 0 ENUMs | Stream ticket-list changes | - | - |
| **on_opened_orders_profit** | **[In: 0, Out: 2]**<br>Total: 2 ENUMs | Stream open-order P&L updates | - | `MT4_SUB_ENUM_EVENT_GROUP_TYPE` (2 values) - Event group<br>`SUB_ORDER_OPERATION_TYPE` (6 values) - Order operation in the payload |

---

## 🗂 All ENUM types at a glance

| ENUM | Values | Module | Used by |
|------|--------|--------|---------|
| `EnumAccountTradeMode` | 3 | `account_helper_pb2` | account_summary (out) |
| `EnumAccountMarginMode` | 3 | `account_helper_pb2` | account_summary (out) |
| `EnumOpenedOrderSortType` | 4 | `account_helper_pb2` | opened_orders (in) |
| `EnumOrderHistorySortType` | 6 | `account_helper_pb2` | orders_history (in) |
| `OpenedOrderType` | 8 | `account_helper_pb2` | opened_orders, orders_history (out) |
| `SP_ENUM_TRADE_CALC_MODE` | 3 | `account_helper_pb2` | symbol_params_many (out) |
| `SP_ENUM_SYMBOL_TRADE_MODE` | 5 | `account_helper_pb2` | symbol_params_many (out) |
| `SP_ENUM_SYMBOL_TRADE_EXECUTION` | 4 | `account_helper_pb2` | symbol_params_many (out) |
| `OrderSendOperationType` | 6 | `trading_helper_pb2` | order_send (in) |
| `OrderCloseDeleteMode` | 2 | `trading_helper_pb2` | order_close_delete (out) |
| `ENUM_QUOTE_HISTORY_TIMEFRAME` | 9 | `market_info_pb2` | quote_history (in) |
| `MT4_SUB_ENUM_EVENT_GROUP_TYPE` | 2 | `subscriptions_pb2` | on_trade, on_opened_orders_profit (out) |
| `SUB_ORDER_OPERATION_TYPE` | 6 | `subscriptions_pb2` | on_trade, on_opened_orders_profit (out) |

---

## Important Notes

### Python ENUM Access

Python accesses ENUMs through the `mt4_term_api_*` protobuf modules:

**Correct:**
```python
from MetaRpcMT4 import mt4_term_api_trading_helper_pb2 as trading_helper_pb2

# Using an ENUM value
op = trading_helper_pb2.OrderSendOperationType.OC_OP_BUY

from MetaRpcMT4 import mt4_term_api_account_helper_pb2 as account_helper_pb2
sort = account_helper_pb2.EnumOpenedOrderSortType.SORT_BY_OPEN_TIME_ASC
```

**Incorrect:**
```python
OC_OP_BUY  # NameError: name 'OC_OP_BUY' is not defined
```

### Special Cases

**1. Order operation enums come in three flavours.**
`OrderSendOperationType` (`OC_OP_*`, used to *send* an order), `OpenedOrderType`
(`OO_OP_*`, the type reported back on open/history orders) and
`SUB_ORDER_OPERATION_TYPE` (`SUB_OP_*`, used inside streaming events) describe the
same six operations but are distinct enum types — don't mix their value names.
`OpenedOrderType` has two extra non-tradable entries, `OO_OP_BALANCE` and
`OO_OP_CREDIT`, used for balance/credit history records.

**2. Returned codes are not ENUMs.**
Trade-operation return/error codes are plain integers, not typed enums. See the
[Return Codes Reference](RETURN_CODES_REFERENCE.md).

---

## See Also

- [MT4Account — API Reference](../MT4Account/MT4Account.Master.Overview.md)
- [Return Codes Reference](RETURN_CODES_REFERENCE.md)
- [Getting Started](GETTING_STARTED.md)
