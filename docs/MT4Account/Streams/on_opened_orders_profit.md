# ✅ Streaming Aggregated P/L — `on_opened_orders_profit`

> **Stream:** subscribe to **real‑time aggregated profit/loss** for the current set of opened orders/positions.
> Yields `OnOpenedOrdersProfitData` messages continuously until cancelled.

**Source files (SDK):**

* `MetaRpcMT4/mt4_account.py` — method `on_opened_orders_profit(cancellation_event=None)`
* `MetaRpcMT4/mt4_term_api_subscriptions_pb2.py` — `OnOpenedOrdersProfit*` (request/reply/data)

### RPC

* **Service:** `mt4_term_api.Subscriptions`
* **Method (server‑streaming):** `OnOpenedOrdersProfit(OnOpenedOrdersProfitRequest) → stream OnOpenedOrdersProfitReply`
* **Low‑level client:** `SubscriptionsStub.OnOpenedOrdersProfit(request, metadata)` (async stream)
* **SDK wrapper:** `MT4Account.on_opened_orders_profit(cancellation_event=None) → AsyncIterator[OnOpenedOrdersProfitData]`

**Request message:** `OnOpenedOrdersProfitRequest {}`
**Reply message:** `OnOpenedOrdersProfitReply { data: OnOpenedOrdersProfitData }` (streamed)

---

### 🔗 Code Example

```python
# Consume aggregated P/L updates with graceful cancellation
import asyncio

async def watch_pnl(acct):
    stop = asyncio.Event()
    async for msg in acct.on_opened_orders_profit(cancellation_event=stop):
        d = msg  # OnOpenedOrdersProfitData
        total = getattr(d, 'total_profit', None)
        by_sym = getattr(d, 'profit_by_symbol', None)  # map-like field in some builds
        ts = getattr(d, 'date_time', None)
        print("TOTAL PnL:", total, "at", ts)
        if by_sym:
            # e.g., {"EURUSD": 12.34, "XAUUSD": -5.67}
            print("By symbol:", dict(by_sym))
```

---

### Method Signature

```python
async def on_opened_orders_profit(
    self,
    cancellation_event: asyncio.Event | None = None,
) -> AsyncIterator[subscriptions_pb2.OnOpenedOrdersProfitData]
```

---

## 💬 Just the essentials

* **What it is.** A **lightweight stream of totals**: current aggregated floating P/L for all open positions.
* **Why.** Drive header KPIs, risk dashboards, and alerting without polling full order lists.
* **Complement to tickets.** Pair with `on_opened_orders_tickets(...)` to detect structural changes (opens/closes) while keeping a live P/L number.

---

## 🔽 Input

No request fields.

| Parameter            | Type           | Description |                                       |
| -------------------- | -------------- | ----------- | ------------------------------------- |
| `cancellation_event` | `asyncio.Event | None`       | Signal to stop the stream gracefully. |

---

## ⬆️ Output (streamed)

### Message: `OnOpenedOrdersProfitData`

| Field                              | Proto Type                     | Description                                        |
| ---------------------------------- | ------------------------------ | -------------------------------------------------- |
| `type`                             | `enum`                         | Event type (0 = OrderProfit, 1 = OrderUpdate).     |
| `opened_orders_with_profit_updated`| `OnOpenedOrdersProfitOrderInfo`| Order with updated profit information.             |
| `account_info`                     | `OnEventAccountInfo`           | Account state snapshot (balance, equity, etc.).    |
| `terminal_instance_guid_id`        | `string`                       | Terminal instance identifier.                      |

### Nested: `OnOpenedOrdersProfitOrderInfo`

| Field          | Proto Type                  | Description                              |
| -------------- | --------------------------- | ---------------------------------------- |
| `index`        | `int32`                     | Order index.                             |
| `ticket`       | `int32`                     | Order/position ticket.                   |
| `symbol`       | `string`                    | Trading symbol.                          |
| `type`         | `enum`                      | Order type (SUB_OP_BUY, SUB_OP_SELL, etc.). |
| `lots`         | `double`                    | Volume in lots.                          |
| `open_price`   | `double`                    | Entry price.                             |
| `stop_loss`    | `double`                    | Stop loss level.                         |
| `take_profit`  | `double`                    | Take profit level.                       |
| `open_time`    | `google.protobuf.Timestamp` | Order open time (UTC).                   |
| `expiration`   | `google.protobuf.Timestamp` | Pending order expiration (if set).       |
| `magic_number` | `int32`                     | EA magic number.                         |
| `order_profit` | `double`                    | Current/realized profit.                 |
| `swap`         | `double`                    | Swap charged/credited.                   |
| `commission`   | `double`                    | Commission.                              |
| `comment`      | `string`                    | Order comment.                           |

### Nested: `OnEventAccountInfo`

| Field          | Proto Type | Description                     |
| -------------- | ---------- | ------------------------------- |
| `login`        | `int64`    | Account login number.           |
| `balance`      | `double`   | Account balance.                |
| `credit`       | `double`   | Credit amount.                  |
| `equity`       | `double`   | Current equity.                 |
| `margin`       | `double`   | Used margin.                    |
| `free_margin`  | `double`   | Free margin available.          |
| `profit`       | `double`   | Total floating profit (use this for total P/L). |
| `margin_level` | `double`   | Margin level percentage.        |

> Total profit/loss is available in `account_info.profit`. Individual order profit is in `opened_orders_with_profit_updated.order_profit`.

---

## 🧱 Related enums (from pb)

This stream **does not use method‑specific enums**.

---

### 🎯 Purpose

Use this stream to:

* Show **live P/L** at the top of your UI.
* Trigger alerts (e.g., equity drawdown thresholds) without heavy polling.
* Recompute risk metrics on each update.

### 🧩 Notes & Tips

* The wrapper uses `execute_stream_with_reconnect(...)` and will retry on transient disconnects.
* Expect the first message to be the **current** aggregate (not a delta).
* Combine with snapshots after reconnect: `opened_orders()` to re‑sync details.

**See also:**
`on_opened_orders_tickets(...)` — set of open tickets.
`opened_orders(...)` — detailed snapshot of positions.
`account_summary(...)` — account‑level health (balance/equity/credit).

---

## Usage Examples

### 1) Simple KPI widget

```python
async for p in acct.on_opened_orders_profit():
    total = getattr(p, 'total_profit', 0.0)
    print(f"Floating P/L: {total:+.2f}")
```

### 2) Alert when total P/L crosses threshold

```python
THRESH = -100.0
async for p in acct.on_opened_orders_profit():
    if getattr(p, 'total_profit', 0.0) <= THRESH:
        # trigger your alert / hedge action
        ...
```

### 3) Merge with tickets stream

```python
import asyncio

async def run(acct):
    tickets_cur = set()
    pnl_cur = 0.0

    async def t_stream():
        nonlocal tickets_cur
        async for s in acct.on_opened_orders_tickets():
            tickets_cur = set(getattr(s, 'tickets', []))

    async def p_stream():
        nonlocal pnl_cur
        async for p in acct.on_opened_orders_profit():
            pnl_cur = getattr(p, 'total_profit', 0.0)

    await asyncio.gather(t_stream(), p_stream())
```
