# MT4Account — Master Overview

> One page to **orient fast**: what lives where, how to choose the right API, and jump links to every **overview** and **method spec** in this docs set.

---

## 🚦 Start here — Section Overviews

* **[Account\_Information — Overview](./Account_Information/account_summary.md)**
  Account balance/equity/margins, summary snapshot.

* **[Market\_Quota\_Symbols — Overview](./Market_quota_symbols/Market_Quota.Overview.md)**
  Quotes, symbols, ticks, bars history, symbol parameters, tick values.

* **[Orders\_Positions\_History — Overview](./Orders_Positions_History/Positions_History_Overview.md)**
  What's open now, tickets, order details.

* **[Trading\_Actions — Overview](./Trading_Actions/Trading_Actions_Overview.md)**
  Place/modify/close orders, close by opposite position.

* **[Streams — Overview](./Streams/Streams_Overview.md)**
  Live streams: ticks, trade events, tickets, profit snapshots.

---

## 🧭 How to pick an API

| If you need…                   | Go to…                   | Typical calls                                                                 |
| ------------------------------ | ------------------------ | ----------------------------------------------------------------------------- |
| Account snapshot               | Account\_Information     | `account_summary`                                                             |
| Quotes & market data           | Market\_Quota\_Symbols   | `quote`, `quote_many`, `quote_history`, `symbols`, `symbol_params_many`       |
| Live positions & tickets       | Orders.Positions.History | `opened_orders`, `opened_orders_tickets`                                      |
| Trading actions                | Trading\_Actions         | `order_send`, `order_modify`, `order_close_delete`, `order_close_by`         |
| Realtime updates               | Streams                  | `on_symbol_tick`, `on_trade`, `on_opened_orders_tickets`, `on_opened_orders_profit` |

---

## 🔌 Usage pattern (SDK wrappers)

Every method follows the same shape:

* **Service/Method (gRPC):** `Service.Method(Request) → Reply`
* **Low-level stub:** `ServiceStub.Method(request, metadata, timeout)`
* **SDK wrapper (what you call):** `await MT4Account.method_name(..., deadline=None, cancellation_event=None)`
* **Reply:** SDK returns **`.data`** payload (already unwrapped) unless otherwise noted.

Timestamps = **UTC** (`google.protobuf.Timestamp`). For long‑lived streams, pass a **`cancellation_event`**.

---

# 📚 Full Index · All Method Specs

---

## 📄 Account Information

* **Summary**
  – [account\_summary.md](./Account_Information/account_summary.md)

---

## 📊 Market · Quota · Symbols

* **Overview:** [Market\_Quota.Overview.md](./Market_quota_symbols/Market_Quota.Overview.md)

### Quotes

* [quote.md](./Market_quota_symbols/quote.md) — Single symbol quote (bid/ask/time)
* [quote\_many.md](./Market_quota_symbols/quote_many.md) — Multiple symbols quotes
* [quote\_history.md](./Market_quota_symbols/quote_history.md) — Historical bars/ticks

### Symbols Inventory

* [symbols.md](./Market_quota_symbols/symbols.md) — Available symbols list
* [symbol\_params\_many.md](./Market_quota_symbols/symbol_params_many.md) — Symbol properties (digits, point, spread, etc.)

### Pricing Utils

* [tick\_value\_with\_size.md](./Market_quota_symbols/tick_value_with_size.md) — Tick value/size for lot calculations

---

## 📦 Orders · Positions · History

* **Overview:** [Positions\_History\_Overview.md](./Orders_Positions_History/Positions_History_Overview.md)

### Live Now

* [opened\_orders.md](./Orders_Positions_History/opened_orders.md) — All open positions (full details)
* [opened\_orders\_tickets.md](./Orders_Positions_History/opened_orders_tickets.md) — Open positions tickets only

---

## 🛠 Trading Actions

* **Overview:** [Trading\_Actions\_Overview.md](./Trading_Actions/Trading_Actions_Overview.md)

### Placement & Lifecycle

* [order\_send.md](./Trading_Actions/order_send.md) — Place new order (market/limit/stop)
* [order\_modify.md](./Trading_Actions/order_modify.md) — Modify SL/TP/price
* [order\_close\_delete.md](./Trading_Actions/order_close_delete.md) — Close position or delete pending order

### Advanced

* [order\_close\_by.md](./Trading_Actions/order_close_by.md) — Close by opposite position

---

## 📡 Streams · Subscriptions

* **Overview:** [Streams\_Overview.md](./Streams/Streams_Overview.md)

### Price Updates

* [on\_symbol\_tick.md](./Streams/on_symbol_tick.md) — Real-time tick stream for symbols

### Trading Events

* [on\_trade.md](./Streams/on_trade.md) — Trade execution events

### Positions Snapshots

* [on\_opened\_orders\_tickets.md](./Streams/on_opened_orders_tickets.md) — Stream of open tickets
* [on\_opened\_orders\_profit.md](./Streams/on_opened_orders_profit.md) — Stream of profit updates

---

## 🎯 Quick Navigation by Use Case

| I want to... | Use this method |
|-------------|-----------------|
| Get current account balance/equity | [account\_summary](./Account_Information/account_summary.md) |
| Get current price for EURUSD | [quote](./Market_quota_symbols/quote.md) |
| Get prices for multiple symbols | [quote\_many](./Market_quota_symbols/quote_many.md) |
| Get historical bars/ticks | [quote\_history](./Market_quota_symbols/quote_history.md) |
| List available symbols | [symbols](./Market_quota_symbols/symbols.md) |
| Get symbol properties (digits, point, spread) | [symbol\_params\_many](./Market_quota_symbols/symbol_params_many.md) |
| Calculate tick value for lot sizing | [tick\_value\_with\_size](./Market_quota_symbols/tick_value_with_size.md) |
| See all open positions | [opened\_orders](./Orders_Positions_History/opened_orders.md) |
| Get just the ticket numbers | [opened\_orders\_tickets](./Orders_Positions_History/opened_orders_tickets.md) |
| Place a market order | [order\_send](./Trading_Actions/order_send.md) (type=market) |
| Place a limit order | [order\_send](./Trading_Actions/order_send.md) (type=limit) |
| Place a stop order | [order\_send](./Trading_Actions/order_send.md) (type=stop) |
| Modify SL/TP | [order\_modify](./Trading_Actions/order_modify.md) |
| Close a position | [order\_close\_delete](./Trading_Actions/order_close_delete.md) |
| Delete pending order | [order\_close\_delete](./Trading_Actions/order_close_delete.md) |
| Close by opposite position | [order\_close\_by](./Trading_Actions/order_close_by.md) |
| Stream live prices | [on\_symbol\_tick](./Streams/on_symbol_tick.md) |
| Watch for trade executions | [on\_trade](./Streams/on_trade.md) |
| Monitor open tickets | [on\_opened\_orders\_tickets](./Streams/on_opened_orders_tickets.md) |
| Monitor profit changes | [on\_opened\_orders\_profit](./Streams/on_opened_orders_profit.md) |

---

"May your pips stack high and your drawdowns stay low."
