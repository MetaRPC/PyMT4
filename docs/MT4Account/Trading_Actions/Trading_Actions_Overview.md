# MT4Account · Streams — Overview

> Real‑time APIs for **live ticks** and **trade state**. Use this page to pick the right stream fast; links jump to detailed specs.

## 📁 What lives here

* **[on_symbol_tick](./on_symbol_tick.md)** — server‑stream of **ticks** for one or more symbols (bid/ask or last, timestamp).
* **[on_trade](./on_trade.md)** — unified stream of **trade events** (orders, deals, positions) for the current account.
* **[on_opened_orders_tickets](./on_opened_orders_tickets.md)** — lightweight stream of the **current ticket set** (IDs only; detect opens/closes).
* **[on_opened_orders_profit](./on_opened_orders_profit.md)** — stream of **aggregated floating P/L** (total, optionally per symbol).

---

## 🧭 Plain English

* **on_symbol_tick** → your **price wire**. Keeps tiles and signal logic fed without polling.
* **on_trade** → the **trade newsfeed** (opens, modifies, closes, fills, position updates).
* **on_opened_orders_tickets** → the **change detector**. Cheap way to know when set of tickets changed.
* **on_opened_orders_profit** → the **KPI ticker**. Live total P/L for dashboards and risk alerts.

> Rule of thumb: need **prices** → `on_symbol_tick`; need **what changed in trading** → `on_trade`; need **to refresh only on structural changes** → `on_opened_orders_tickets`; need **running P/L** → `on_opened_orders_profit`.

---

## Quick choose

| If you need…                              | Use                        | Yields                         | Key inputs / notes                                  |
| ----------------------------------------- | -------------------------- | ------------------------------ | --------------------------------------------------- |
| Live ticks for symbols                    | `on_symbol_tick`           | `OnSymbolTickData` (per tick)  | `symbols: list[str]`, optional `cancellation_event` |
| All trade events (orders/deals/positions) | `on_trade`                 | `OnTradeData` (mixed subtypes) | *(none)* + optional `cancellation_event`            |
| Detect open/close via ticket set changes  | `on_opened_orders_tickets` | `OnOpenedOrdersTicketsData`    | *(none)* + optional `cancellation_event`            |
| Live aggregated floating P/L              | `on_opened_orders_profit`  | `OnOpenedOrdersProfitData`     | *(none)* + optional `cancellation_event`            |

---

## ❌ Cross‑refs & gotchas

* **Reconnects happen.** Wrappers use retry/reconnect under the hood; make handlers **idempotent**.
* **Snapshots after reconnect.** For UI consistency, pull `opened_orders()` and/or `orders_history()` once streams resume.
* **Field names vary slightly** across builds (`symbol` vs `symbolName`, `bid/ask` vs `last`). Use `getattr(...)` fallbacks.
* **Keep symbol lists small** in `on_symbol_tick` for latency; use `quote_many(...)` for bulk refills.
* **Totals vs details.** `on_opened_orders_profit` gives the number; use `opened_orders()` when you need the objects.

---

## 🟢 Minimal snippets

```python
# on_symbol_tick — debounce UI updates
from time import monotonic
last_ui = 0
DEBOUNCE = 0.25
async for t in acct.on_symbol_tick(["EURUSD","XAUUSD"]):
    now = monotonic()
    if now - last_ui >= DEBOUNCE:
        last_ui = now
        # assemble and push a compact UI snapshot
```

```python
# on_trade — route by operation type
from MetaRpcMT4 import mt4_term_api_subscriptions_pb2 as sub_pb
async for ev in acct.on_trade():
    op = getattr(ev, 'type', None)
    if op is None:
        continue
    name = sub_pb.SUB_ORDER_OPERATION_TYPE.Name(op)
    if name.startswith('OP_OPEN'):
        ...  # created
    elif name.startswith('OP_MODIFY'):
        ...  # modified
    elif name.startswith('OP_CLOSE'):
        ...  # closed
```

```python
# on_opened_orders_tickets — diff and refresh details on change
prev = set()
async for s in acct.on_opened_orders_tickets():
    cur = set(getattr(s, 'tickets', []))
    if cur != prev:
        details = await acct.opened_orders()
        # update UI list from details
    prev = cur
```

```python
# on_opened_orders_profit — threshold alert
THRESH = -100.0
async for p in acct.on_opened_orders_profit():
    if getattr(p, 'total_profit', 0.0) <= THRESH:
        # trigger alert / hedge action
        ...
```

---

## See also

* **Snapshots:** [`opened_orders`](../Orders_Positions_History/opened_orders.md), [`orders_history`](../Orders_Positions_History/orders_history.md)
* **Quotes & symbols:** [`quote`](../Market_quota_symbols/quote.md), [`quote_many`](../Market_quota_symbols/quote_many.md), [`symbols`](../Market_quota_symbols/symbols.md)
* **Trading actions:** [`order_send`](../Trading_Actions/order_send.md), [`order_modify`](../Trading_Actions/order_modify.md), [`order_close_delete`](../Trading_Actions/order_close_delete.md), [`order_close_by`](../Trading_Actions/order_close_by.md)
