# main_low_level.py

## What this file is

Demonstration script showcasing **low‑level MT4 SDK methods** (no sugar wrappers).
Use it to understand the raw RPC surface — quotes, symbols, order actions, and streams.

## Low‑level methods used here

* *This list comes from a static scan of the script. If you add more calls, extend the list accordingly.*
* Each item links to its detailed low‑level documentation under `docs/MT4Account/...`.

<!-- The following bullets were generated from your current project tree. -->

* `quote(...)` → see [quote.md](../MT4Account/Market_quota_symbols/quote.md)
* `quote_many(...)` → see [quote_many.md](../MT4Account/Market_quota_symbols/quote_many.md)
* `quote_history(...)` → see [quote_history.md](../MT4Account/Market_quota_symbols/quote_history.md)
* `symbols(...)` → see [symbols.md](../MT4Account/Market_quota_symbols/symbols.md)
* `symbol_params_many(...)` → see [symbol_params_many.md](../MT4Account/Market_quota_symbols/symbol_params_many.md)
* `tick_value_with_size(...)` → see [tick_value_with_size.md](../MT4Account/Market_quota_symbols/tick_value_with_size.md)
* `opened_orders(...)` → see [opened_orders.md](../MT4Account/Orders_Positions_History/opened_orders.md)
* `opened_orders_tickets(...)` → see [opened_orders_tickets.md](../MT4Account/Orders_Positions_History/opened_orders_tickets.md)
* `order_send(...)` → see [order_send.md](../MT4Account/Trading_Actions/order_send.md)
* `order_modify(...)` → see [order_modify.md](../MT4Account/Trading_Actions/order_modify.md)
* `order_close_delete(...)` → see [order_close_delete.md](../MT4Account/Trading_Actions/order_close_delete.md)
* `order_close_by(...)` → see [order_close_by.md](../MT4Account/Trading_Actions/order_close_by.md)
* `on_symbol_tick(...)` → see [on_symbol_tick.md](../MT4Account/Streams/on_symbol_tick.md)
* `on_trade(...)` → see [on_trade.md](../MT4Account/Streams/on_trade.md)
* `on_opened_orders_tickets(...)` → see [on_opened_orders_tickets.md](../MT4Account/Streams/on_opened_orders_tickets.md)
* `on_opened_orders_profit(...)` → see [on_opened_orders_profit.md](../MT4Account/Streams/on_opened_orders_profit.md)
* `account_summary(...)` → see [account_summary.md](../MT4Account/Account_Information/account_summary.md)

## Tips for working with this demo

* **Connect first, then call.** Always ensure the session is alive before market requests.
* **Enable symbols.** If a symbol is missing, call the symbol‑enable routine in advance.
* **Handle latency and retries.** Use simple health checks and re‑connect logic for transient errors.
* **Separate I/O from math.** Keep pip/lot computations outside of low‑level calls.
* **Log minimally but meaningfully.** Print concise snapshots: symbol, bid/ask, time, operation result.

## Output

You should see structured prints in your terminal (quotes, order results, etc.).
Скрин LL с выводом терминалом

