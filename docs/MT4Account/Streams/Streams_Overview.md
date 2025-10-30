# MT4Account · Streams — Overview

> Real‑time APIs for **live ticks** and **trade state**. Use this page to pick the right stream fast; links jump to detailed specs.

## 📁 What lives here

* **[on_symbol_tick](./on_symbol_tick.md)** — server-stream of **real-time ticks** for one or more symbols (bid/ask/last, timestamp).
* **[on_trade](./on_trade.md)** — unified stream of **trade events** (orders, deals, positions) for the current account.
* **[on_opened_orders_tickets](./on_opened_orders_tickets.md)** — lightweight stream of the **current ticket set** (IDs only; detect opens/closes).
* **[on_opened_orders_profit](./on_opened_orders_profit.md)** — stream of **order profit updates** and account state.

---

## 🧭 Plain English

* **on_symbol_tick** → your **price wire**. Keeps tiles and signal logic fed without polling.
* **on_trade** → the **trade newsfeed** (opens, modifies, closes, fills, position updates).
* **on_opened_orders_tickets** → the **change detector**. Cheap way to know when set of tickets changed.
* **on_opened_orders_profit** → the **KPI ticker**. Live order profit updates and account state for dashboards and risk alerts.

> Rule of thumb: need **prices** → `on_symbol_tick`; need **what changed in trading** → `on_trade`; need **to refresh only on structural changes** → `on_opened_orders_tickets`; need **running P/L and account info** → `on_opened_orders_profit`.

---

## Quick choose

| If you need…                              | Use                        | Yields                         | Key inputs / notes                                  |
| ----------------------------------------- | -------------------------- | ------------------------------ | --------------------------------------------------- |
| Live ticks for symbols                    | `on_symbol_tick`           | `OnSymbolTickData`             | `symbols: list[str]`, optional `cancellation_event` |
| All trade events (orders/deals/positions) | `on_trade`                 | `OnTradeData` (mixed subtypes) | optional `cancellation_event`                       |
| Detect open/close via ticket set changes  | `on_opened_orders_tickets` | `OnOpenedOrdersTicketsData`    | optional `cancellation_event`                       |
| Live order profit and account state       | `on_opened_orders_profit`  | `OnOpenedOrdersProfitData`     | optional `cancellation_event`                       |

---

## ❌ Cross‑refs & gotchas

* **Reconnects happen.** Wrappers use retry/reconnect under the hood; make handlers **idempotent**.
* **Snapshots after reconnect.** For UI consistency, pull `opened_orders()` and/or `orders_history()` once streams resume.
* **Nested structures.** All stream messages have nested data (e.g., `symbol_tick`, `event_data`, `account_info`).
* **Keep symbol lists small** in `on_symbol_tick` for latency; use `quote_many(...)` for bulk refills.
* **Totals vs details.** `on_opened_orders_profit` gives account info with profit; use `opened_orders()` when you need full order details.

---

## 🟢 Minimal snippets

```python
# on_symbol_tick — debounce UI updates
from time import monotonic
last_ui = 0
DEBOUNCE = 0.25
async for t in acct.on_symbol_tick(["EURUSD", "XAUUSD"]):
    now = monotonic()
    if now - last_ui >= DEBOUNCE:
        last_ui = now
        tick = t.symbol_tick
        print(f"{tick.symbol}: {tick.bid}/{tick.ask}")
```

```python
# on_trade — check for new orders
async for ev in acct.on_trade():
    if ev.type == 1 and ev.event_data.new_orders:  # OrderUpdate with new orders
        order = ev.event_data.new_orders
        print(f"New order: {order.symbol} ticket={order.ticket}")
    # Check account state
    if ev.account_info:
        print(f"Balance: {ev.account_info.balance}, Equity: {ev.account_info.equity}")
```

```python
# on_opened_orders_tickets — diff and refresh details on change
prev_positions = set()
prev_pendings = set()
async for s in acct.on_opened_orders_tickets():
    cur_pos = set(s.position_tickets)
    cur_pend = set(s.pending_order_tickets)
    if cur_pos != prev_positions or cur_pend != prev_pendings:
        details = await acct.opened_orders()
        # update UI list from details
    prev_positions = cur_pos
    prev_pendings = cur_pend
```

```python
# on_opened_orders_profit — threshold alert
THRESH = -100.0
async for p in acct.on_opened_orders_profit():
    if p.account_info and p.account_info.profit <= THRESH:
        # trigger alert / hedge action
        print(f"Alert! Profit: {p.account_info.profit}")
```

---

## See also

* **Snapshots:** [`opened_orders`](../Orders_Positions_History/opened_orders.md), [`orders_history`](../Orders_Positions_History/orders_history.md)
* **Quotes & symbols:** [`quote`](../Market_quota_symbols/quote.md), [`quote_many`](../Market_quota_symbols/quote_many.md), [`symbols`](../Market_quota_symbols/symbols.md)
* **Trading actions:** [`order_send`](../Trading_Actions/order_send.md), [`order_modify`](../Trading_Actions/order_modify.md), [`order_close_delete`](../Trading_Actions/order_close_delete.md), [`order_close_by`](../Trading_Actions/order_close_by.md)
