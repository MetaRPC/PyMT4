
# main_trade_mod.py

## What this file is

Demonstration script focused on **trade modification flows**: placing, modifying, and closing orders.
It shows common sequences like `order_send → order_modify → order_close` with minimal boilerplate.

## Methods used here (with low‑level links)

- `quote(...)` → low‑level: [quote.md](../MT4Account/Market_quota_symbols/quote.md)
- `buy_market(...)` → low‑level: [order_send.md](../MT4Account/Trading_Actions/order_send.md)
- `buy_limit(...)` → low‑level: [order_send.md](../MT4Account/Trading_Actions/order_send.md)
- `close(...)` → low‑level: [order_close_delete.md](../MT4Account/Trading_Actions/order_close_delete.md)
- `close_partial(...)` → low‑level: [order_close_delete.md](../MT4Account/Trading_Actions/order_close_delete.md)
- `sell_market(...)` → low‑level: [order_send.md](../MT4Account/Trading_Actions/order_send.md)
- `close_by(...)` → low‑level: [order_close_by.md](../MT4Account/Trading_Actions/order_close_by.md)
- `opened_orders(...)` → low‑level: [opened_orders.md](../MT4Account/Orders_Positions_History/opened_orders.md)

## Tips for working with this demo

- **Normalize before modify.** Use price/lot normalization helpers to satisfy broker constraints.
- **Convert pips↔price** consistently to avoid off-by-one tick rejections.
- **Respect freeze levels.** Some brokers block SL/TP changes near current price — plan distances.
- **Check order state.** Re‑query tickets before modifying; ensure it's still open and prices changed.
- **Log results.** Store the returned ticket and the final SL/TP to trace outcomes.

## Output

Expect a short log of placement → modification → close results (ticket, prices, statuses).  
Будущий скрин Mod
