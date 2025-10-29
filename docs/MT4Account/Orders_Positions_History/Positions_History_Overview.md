# MT4Account · Orders & Positions History — Overview

> Live state snapshots + historical ledgers. Use this page to choose the correct data source for your UI, risk system, or analytics.

## 📁 What lives here

* **[opened_orders](./opened_orders.md)** — current **market positions + pending orders** with full details.
* **[opened_orders_tickets](./opened_orders_tickets.md)** — only **ticket IDs** of opened orders/positions (lightweight snapshot).
* **[orders_history](./orders_history.md)** — historical **orders & deals** (closed operations).

---

## 🧭 Plain English

* **opened_orders** → *“What’s live right now?”* — objects you see on the trade tab.
* **opened_orders_tickets** → *“Did something open/close?”* — fast change detection.
* **orders_history** → *“What happened before?”* — time‑ranged closed orders/deals ledger.

> Rule of thumb: UI or risk needs **details now** → `opened_orders()`.
> Need **just IDs** to decide refresh → `opened_orders_tickets()`.
> Need **past actions** → `orders_history()`.

---

## Quick choose

| If you need…                                    | Use                     | Returns                   | Key inputs                                       |
| ----------------------------------------------- | ----------------------- | ------------------------- | ------------------------------------------------ |
| Full details of live positions & pending orders | `opened_orders`         | `OpenedOrdersData`        | `sort_mode?`, `deadline?`, `cancellation_event?` |
| IDs only for open trading objects               | `opened_orders_tickets` | `OpenedOrdersTicketsData` | optional `deadline`, `cancellation_event`        |
| Closed orders & deals over period               | `orders_history`        | `OrdersHistoryData`       | `from`, `to`, `sort_mode`, paging? *(future)*    |

---

## ❌ Cross‑refs & gotchas

* **UTC timestamps** everywhere → convert once.
* **Server‑side sorting** for `opened_orders` — enums drive ordering.
* `orders_history`: mixed **orders & deals** — check which fields are set per row.
* **Filtering by symbol** should be done on client side.
* After reconnects: **stream update** may arrive first → pull a fresh snapshot.

---

## 🟢 Minimal snippets

```python
# Count live objects
od = await acct.opened_orders()
print(len(od.items))  # positions + pendings together
```

```python
# Ticket set for quick diff
s = await acct.opened_orders_tickets()
tickets = set(s.tickets)
print(tickets)
```

```python
# Last 24h closed records (depends on your history time fields)
from datetime import datetime, timedelta, timezone
end = datetime.now(timezone.utc)
start = end - timedelta(days=1)
h = await acct.orders_history(start, end)
print(len(h.history))
```

---

## See also

* **Streams:** [`on_opened_orders_tickets`](../Streams/on_opened_orders_tickets.md), [`on_opened_orders_profit`](../Streams/on_opened_orders_profit.md), [`on_trade`](../Streams/on_trade.md)
* **Quotes & symbols:** [`quote`](../Market_quota_symbols/quote.md), [`symbol_params_many`](../Market_quota_symbols/symbol_params_many.md)
* **Trading actions:** [`order_send`](../Trading_Actions/order_send.md)
