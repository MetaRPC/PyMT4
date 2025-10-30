# main_streams.py

## What this file is

Demonstration script for **server-streaming APIs** (real-time subscriptions).
Shows how to consume async streams and handle cooperative cancellation.

## Low‑level methods used here

- `on_symbol_tick(...)` → see [on_symbol_tick.md](../MT4Account/Streams/on_symbol_tick.md)
- `on_trade(...)` → see [on_trade.md](../MT4Account/Streams/on_trade.md)
- `on_opened_orders_tickets(...)` → see [on_opened_orders_tickets.md](../MT4Account/Streams/on_opened_orders_tickets.md)
- `on_opened_orders_profit(...)` → see [on_opened_orders_profit.md](../MT4Account/Streams/on_opened_orders_profit.md)

## Tips for working with stream demos

- **Cooperative shutdown.** Pass a cancellation event and stop cleanly.
- **Back-pressure.** Debounce or sample incoming ticks to avoid UI/CPU spikes.
- **Scoped subscriptions.** Keep symbol lists compact; use snapshots (`quote_many`) for refills.
- **Structured logging.** Log symbol, bid/ask, latency markers; avoid per-tick verbose logs.

## Output

You should see a rolling log of streamed updates (ticks, trades, tickets, etc.).

![Streams Output](../Examples_of_illustrations/Stream.bmp)
