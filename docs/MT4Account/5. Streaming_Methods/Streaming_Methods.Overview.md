# MT4Account — Streaming Methods — Overview

> Real-time async generators: ticks, trade events, ticket lists and open-order profit.

## 📁 What lives here

* **[Symbol Tick Stream](on_symbol_tick.md)** — Subscribe to real-time tick (bid/ask) updates for one or more symbols.
* **[Trade Events Stream](on_trade.md)** — Subscribe to trade events (orders opened, updated, removed).
* **[Opened Order Tickets Stream](on_opened_orders_tickets.md)** — Poll-stream the live lists of open position & pending-order tickets.
* **[Open-Order Profit Stream](on_opened_orders_profit.md)** — Stream open-order profit/loss updates (plus an account snapshot).
* **[Connection State Stream](on_connect_state.md)** — Subscribe to terminal connection-state changes.

---

## Quick choose

| Method | What it does |
|--------|--------------|
| `on_symbol_tick` | Subscribe to real-time tick (bid/ask) updates for one or more symbols. |
| `on_trade` | Subscribe to trade events (orders opened, updated, removed). |
| `on_opened_orders_tickets` | Poll-stream the live lists of open position & pending-order tickets. |
| `on_opened_orders_profit` | Stream open-order profit/loss updates (plus an account snapshot). |
| `on_connect_state` | Subscribe to terminal connection-state changes. |

---

* **Back to:** [MT4Account — Master Overview](../MT4Account.Master.Overview.md)
