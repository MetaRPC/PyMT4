# Protobuf Inspector - Interactive Type Explorer

> **Interactive developer utility for exploring MT4 protobuf types, fields, enums, and data structures from the MT4 gRPC API**

---

## 🏛️ What This Tool Does

The Protobuf Inspector is an **interactive command-line tool** that helps you explore the structure of the MT4 gRPC API:

- Interactive search for types, fields, and enums
- Inspection of protobuf message structures
- Field-level discovery - find which types contain a specific field
- Field type discovery - find fields by their data type (double, string, enum, etc.)
- Enum value exploration - see all possible enum values
- Enum usage tracking - find where a specific enum is used
- Type browsing with filters
- JSON export - export type structures for documentation
- Statistics - field types, enum counts, comprehensive metrics

It is **offline** — it reads the generated `MetaRpcMT4` protobuf descriptors, so no MT4 connection is required.

---

## 🏁 Getting Started

### Running the Inspector

```bash
cd examples
python main.py inspect
```

You will see an interactive prompt:

```
===========================================================
MT4 PROTOBUF TYPES INSPECTOR
===========================================================

  Discovered 193 protobuf message types
  Discovered 18 enum types

  Type 'help' to see available commands
  Type 'list' to see all types
===========================================================

>
```

---

## 🧰 Available Commands

| Command | Description | Example |
|---------|-------------|---------|
| `list` or `ls` | Show all available protobuf types | `list` |
| `list --request` | Show only Request types | `list --request` |
| `list --reply` | Show only Reply types | `list --reply` |
| `<TypeName>` | Inspect a specific type structure | `OpenedOrderInfo` |
| `search <text>` or `find <text>` | Search for types containing text | `search Order` |
| `field <name>` | Find all types with a specific field | `field ticket` |
| `findtype <type>` | Find all fields of a specific type | `findtype double` |
| `enum <name>` | Show all enum values | `enum OrderSendOperationType` |
| `whereenum <name>` | Find where an enum is used | `whereenum OpenedOrderType` |
| `export <TypeName>` | Export a type structure to JSON | `export OrderSendData` |
| `stats` | Show detailed statistics | `stats` |
| `help` or `?` | Show help message | `help` |
| `exit` / `quit` / `q` | Exit the inspector | `exit` |

---

## Practical Examples

### Example 1: Inspect a type's fields

**Command:**
```
> OpenedOrderInfo
```

**Output:**
```
TYPE: OpenedOrderInfo
===========================================================
FIELDS (19):
-----------------------------------------------------------
  #  1 comment                        : string
  #  2 commision                      : double
  #  3 expiration_time                : Timestamp
  #  4 lots                           : double
  #  5 magic_number                   : int32
  #  6 open_price                     : double
  #  7 profit                         : double
  #  8 stop_loss                      : double
  #  9 swap                           : double
  # 10 symbol                         : string
  # 11 take_profit                    : double
  # 12 ticket                         : int32
  # 13 position_index                 : int32
  # 14 order_type                     : OpenedOrderType
  # 15 sort_index                     : int32
  # 16 open_time                      : Timestamp
  # 17 account_login                  : int64
  # 18 expiration_time_utc            : Timestamp
  # 19 open_time_utc                  : Timestamp
```

---

### Example 2: Find which types have the "ticket" field

**Command:**
```
> field ticket
```

**Output:**
```
EXACT MATCH: field 'ticket' found in:
-----------------------------------------------------------
    1. HistoryOrderInfo
    2. OnOpenedOrdersProfitOrderInfo
    3. OnTradeOrderInfo
    4. OpenedOrderInfo
    5. OrderSendData
    6. TradeHistoryItemData
    7. TradeUnrealizedExtremaData
```

---

### Example 3: See order operation enum values

MT4 has distinct order-operation enums for different contexts. The one used to
**send** an order:

**Command:**
```
> enum OrderSendOperationType
```

**Output:**
```
ENUM: OrderSendOperationType
===========================================================
  OC_OP_BUY                                = 0
  OC_OP_SELL                               = 1
  OC_OP_BUYLIMIT                           = 2
  OC_OP_SELLLIMIT                          = 3
  OC_OP_BUYSTOP                            = 4
  OC_OP_SELLSTOP                           = 5
```

The one reported back on **open / history** orders:

**Command:**
```
> enum OpenedOrderType
```

**Output:**
```
ENUM: OpenedOrderType
===========================================================
  OO_OP_BUY                                = 0
  OO_OP_SELL                               = 1
  OO_OP_BUYLIMIT                           = 2
  OO_OP_SELLLIMIT                          = 3
  OO_OP_BUYSTOP                            = 4
  OO_OP_SELLSTOP                           = 5
  OO_OP_BALANCE                            = 6
  OO_OP_CREDIT                             = 7
```

**Note:** There is also `SUB_ORDER_OPERATION_TYPE` (`SUB_OP_*`) used inside streaming
events. See [ENUMS Usage Reference](ENUMS_USAGE_REFERENCE.md).

---

### Example 4: Find all types related to "Order"

**Command:**
```
> search Order
```

**Output:**
```
FOUND 32 TYPES MATCHING 'Order':
-----------------------------------------------------------
    1. HistoryOrderInfo
    2. OnOpenedOrdersProfitData
    3. OnOpenedOrdersProfitOrderInfo
    ...
   11. OpenedOrderInfo
   12. OpenedOrdersData
   ...
   27. OrderSendData
   28. OrderSendReply
   29. OrderSendRequest
   30. OrdersHistoryData
   31. OrdersHistoryReply
   32. OrdersHistoryRequest
```

---

### Example 5: Show all available types

**Command:**
```
> list
```

**Output (grouped by category):**
```
AVAILABLE PROTOBUF TYPES (193)
-----------------------------------------------------------

[Request] (55 types):
    1. AccountSummaryRequest
    2. ConnectExRequest
    ...
   38. OrderSendRequest
   39. OrdersHistoryRequest
   ...

[Reply] (59 types):
    ...

[Data] (53 types):
    ...

[Info] (12 types):
    ...

[Other] (14 types):
    ...
```

---

### Example 6: Find where an enum is used

**Command:**
```
> whereenum OpenedOrderType
```

**Output:**
```
ENUM 'OpenedOrderType' USED IN (2 fields):
===========================================================

  HistoryOrderInfo:
    - order_type

  OpenedOrderInfo:
    - order_type
```

---

### Example 7: Export a type to JSON

**Command:**
```
> export OrderSendData
```

**Output:**
```json
{
  "type_name": "OrderSendData",
  "full_name": "mt4_term_api.OrderSendData",
  "fields": [
    { "number": 1, "name": "ticket",        "type": "int32",     "label": "optional" },
    { "number": 2, "name": "volume",        "type": "double",    "label": "optional" },
    { "number": 3, "name": "price",         "type": "double",    "label": "optional" },
    { "number": 4, "name": "open_time",     "type": "Timestamp", "label": "optional" },
    { "number": 5, "name": "open_time_utc", "type": "Timestamp", "label": "optional" }
  ]
}
```

---

### Example 8: Show statistics

**Command:**
```
> stats
```

**Output:**
```
PROTOBUF INSPECTOR STATISTICS
===========================================================

Message Types: 193 total
-----------------------------------------------------------
  Request         :  55 types
  Reply           :  59 types
  Data            :  53 types
  Info            :  12 types
  Other           :  14 types

Enum Types: 18 total
-----------------------------------------------------------
  Total enum values  : 99

  Top 5 largest enums:
    EnumOpenTerminalChartWithEaChatPeriod    :  22 values
    ENUM_QUOTE_HISTORY_TIMEFRAME             :   9 values
    OpenedOrderType                          :   8 values
    EnumOrderHistorySortType                 :   6 values
    OrderSendOperationType                   :   6 values

Field Types: 108 distinct types
-----------------------------------------------------------
  Top 10 most common field types:
    string               : 217 fields
    double               : 173 fields
    timestamp            :  73 fields
    int32                :  65 fields
    error                :  45 fields
    bool                 :  42 fields
    int64                :  38 fields
    uint64               :  16 fields
    uint32               :  13 fields
    ontradeorderinfo     :   5 fields

Total Fields: 816
===========================================================
```

---

## ℹ️ Coverage

When you run the inspector, it covers:

- **Message types:** 193 (all MetaRpcMT4 gRPC message types)
- **Enums:** 18 (99 enum values total)
- **Fields:** 816 across all types
- **Field types:** 108 distinct protobuf types

---

## Frequently Used Enums

| Enum Name | Description | Values |
|-----------|-------------|--------|
| `OrderSendOperationType` | Operation for `order_send` (`OC_OP_*`) | 6 |
| `OpenedOrderType` | Operation on open / history orders (`OO_OP_*`, incl. BALANCE/CREDIT) | 8 |
| `SUB_ORDER_OPERATION_TYPE` | Operation inside streaming events (`SUB_OP_*`) | 6 |
| `OrderCloseDeleteMode` | Close market vs delete pending (`OCD_*`) | 2 |
| `EnumOpenedOrderSortType` | Sort mode for `opened_orders` | 4 |
| `EnumOrderHistorySortType` | Sort mode for `orders_history` | 6 |
| `ENUM_QUOTE_HISTORY_TIMEFRAME` | Timeframe for `quote_history` | 9 |
| `EnumAccountTradeMode` | Account type: DEMO / CONTEST / REAL | 3 |
| `EnumAccountMarginMode` | Margin calculation mode | 3 |
| `SP_ENUM_SYMBOL_TRADE_MODE` | Symbol trade permission (from `symbol_params_many`) | 5 |
| `MT4_SUB_ENUM_EVENT_GROUP_TYPE` | Streaming event group (OrderProfit / OrderUpdate) | 2 |

See [ENUMS Usage Reference](ENUMS_USAGE_REFERENCE.md) for which method uses which enum.

---

## Features

| Feature | Description |
|---------|-------------|
| **Case-insensitive search** | `search Order` = `search order` |
| **Partial field matching** | `field profit` finds `profit` and `take_profit` |
| **Type categorization** | Shows `[Request]`, `[Reply]`, `[Data]`, `[Info]`, `[Other]` tags |
| **Category filtering** | `list --request`, `list --reply` |
| **Field type search** | `findtype double` finds all double fields |
| **Enum usage tracking** | `whereenum <name>` shows where an enum is used |
| **JSON export** | `export <TypeName>` outputs structured JSON |
| **Detailed statistics** | `stats` shows comprehensive metrics |
| **Protobuf field numbers** | Shows field `#N` for each field |
| **Smart error messages** | Suggests alternatives when a type is not found |

---

## Implementation Details

The Protobuf Inspector uses Python reflection to:

1. Register all protobuf types at startup
2. Build in-memory indexes (field name → types, field type → fields, enum → usage)
3. Provide instant search and lookup
4. Export to JSON with complete metadata

**Source file:** `examples/0_common/16_protobuf_inspector.py`

**Modules scanned:**

- `mt4_term_api_account_helper_pb2`
- `mt4_term_api_trade_stats_pb2`
- `mt4_term_api_market_info_pb2`
- `mt4_term_api_admin_pb2`
- `mt4_term_api_trading_helper_pb2`
- `mt4_term_api_subscriptions_pb2` (streaming events)
- `mt4_term_api_charts_pb2` (chart / EA operations)
- `mt4_term_api_connection_pb2` (connection management)

---

## Technical Notes

- **No MT4 connection required** — purely offline; it inspects type definitions.
- **Instant search** — in-memory indexes for fast lookup.
- **Development only** — not intended for production use.
- **Python reflection** — uses the protobuf `DESCRIPTOR` API for introspection.
- **JSON export** — compatible with external documentation tools.

---

## When to Use This Tool

**Use the inspector when:**

- Learning the MT4 gRPC API structure
- Debugging "field not found" errors
- Exploring available protobuf types
- Looking up enum values
- Finding the correct request/response types for an API call
- Understanding message structures before writing code

**Don't use for:**

- Inspecting runtime data (use a debugger instead)
- Production code (this is a development tool)
- Testing API connectivity (use a demo connection instead)

---

## Quick Start Workflow

```bash
# 1. Start the inspector
cd examples
python main.py inspect

# 2. Browse what's available
> list

# 3. Search for what you need
> search Order

# 4. Inspect a type
> OpenedOrderInfo

# 5. Check enum values
> enum OrderSendOperationType

# 6. Find which types hold a field
> field ticket

# 7. Find fields by type
> findtype double

# 8. Check enum usage
> whereenum OpenedOrderType

# 9. Get detailed stats
> stats

# 10. Export to JSON
> export OrderSendData
```

---

## Troubleshooting

**Q: Type not found**

```
> PositionInfo
[!] Type 'PositionInfo' not found
```

**A:** That's an MT5-style name; it doesn't exist in MT4. Use `search` with a partial
name (e.g. `search Order`) to find the right MT4 type.

---

**Q: What's the difference between the `*Request`, `*Reply`, `*Data`, `*Info` types?**

- `*Request` — input for an API method (what you send)
- `*Reply` — the full response envelope (wraps `data` or `error`)
- `*Data` — the payload inside a reply (e.g. `OrderSendData`, `AccountSummaryData`)
- `*Info` — a structured record inside a payload (e.g. `OpenedOrderInfo`, `HistoryOrderInfo`)

---

**Q: Which fields are double vs int32?**

```
> findtype double    # prices, volumes, profits
> findtype int32     # tickets, magic numbers, indices
> findtype string    # symbols, comments
```

---

## Summary

The Protobuf Inspector is a handy first stop when working with the MT4 gRPC API. Use it to:

1. **Discover** available types and their structure
2. **Learn** message field names and types
3. **Debug** field-name and type issues
4. **Verify** enum values and usage
5. **Export** JSON documentation for your team

**Remember:** type `help` at any time for the command reference.

---

## Next Steps

- Run `python main.py inspect` and explore.
- Check [MT4Account API Reference](../MT4Account/MT4Account.Master.Overview.md) for the API documentation.
- See [ENUMS Usage Reference](ENUMS_USAGE_REFERENCE.md) for enum-to-method mapping.
- See [USERCODE_SANDBOX_GUIDE.md](USERCODE_SANDBOX_GUIDE.md) for coding examples.
