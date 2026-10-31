# MT4Sugar — Master Overview

> The **high-level API**: one-liners, pip-based SL/TP, risk sizing, trailing stops, watchers and waiters. The best starting point for most strategies.

`MT4Sugar` is **Layer 3**. It sits on top of [`MT4Service`](../MT4Service/MT4Service.Overview.md) and turns the raw operations into ergonomic one-liners — you pass symbols, lots, pips and prices, and it handles normalization, enum mapping and plumbing.

```
MT4Sugar    (HIGH)   one-liners, risk sizing, trailing, watchers  ← you are here
MT4Service  (MID)    friendly facade over MT4Account
MT4Account  (LOW)    raw gRPC / protobuf
```

Get an instance from a connected service:

```python
import asyncio
from MetaRpcMT4.mt4_account import MT4Account
from app.MT4Service import MT4Service

async def main():
    account = MT4Account(user=..., password=..., grpc_server="mt4.mrpc.pro:443")
    await account.connect_by_server_name(server_name="MetaQuotes-Demo",
                                         base_chart_symbol="EURUSD", timeout_seconds=30)
    service = MT4Service(account)
    sugar = service.sugar                 # ← the high-level API

    # one-liners:
    q = await sugar.last_quote("EURUSD")
    lots = await sugar.calc_lot_by_risk("EURUSD", risk_percent=1.0, stop_pips=50)
    ticket = await sugar.buy_market("EURUSD", lots=lots, sl_pips=50, tp_pips=100)

    await account.channel.close()

asyncio.run(main())
```

> `MT4Sugar(service)` also supports `async with` for scoped use.

---

## 🚦 Method groups

* **[1. Connection & Defaults](./1.%20Connection_Defaults.md)** — `ensure_connected`, `ping`, `set_defaults`, `with_defaults`, `ensure_symbol`, `diag_snapshot`, `disconnect`
* **[2. Prices & Quotes](./2.%20Prices_Quotes.md)** — `last_quote`, `mid_price`, `quotes`, `spread_pips`, `ticks`, `bars`, `wait_price`
* **[3. Symbol Math & Normalization](./3.%20Symbol_Math.md)** — `point`, `digits`, `pip_size`, `pips_to_price`, `price_to_pips`, `normalize_price`, `normalize_lot`, `tick_value`
* **[4. Risk Sizing](./4.%20Risk_Sizing.md)** — `calc_lot_by_risk`, `calc_cash_risk`, `breakeven_price`
* **[5. Order Entry](./5.%20Order_Entry.md)** — `buy_market`, `sell_market`, `buy_limit`, `sell_limit`, `buy_stop`, `sell_stop`, `place_order`
* **[6. Order Management](./6.%20Order_Management.md)** — `modify_sl_tp_by_pips`, `modify_sl_tp_by_price`, `close`, `close_partial`, `close_by`, `close_by_tickets`, `close_all`, `cancel_pendings`
* **[7. Trailing & Breakeven](./7.%20Trailing_Breakeven.md)** — `set_trailing_stop`, `unset_trailing_stop`, `auto_breakeven`, `close_by_breakeven`
* **[8. Watchers & Waiters](./8.%20Watchers_Waiters.md)** — `watch_ticks`, `watch_trades`, `watch_opened_orders`, `watch_profit`, `watch_tickets`, `unwatch`, `wait_filled`, `wait_closed`
* **[9. Order Info & Exposure](./9.%20Order_Info.md)** — `find_orders`, `orders_for_symbol`, `positions_value`, `exposure_summary`

---

## 🧩 Conventions

* **Pips, not points.** SL/TP and distances are in **pips** (`sl_pips`, `tp_pips`, `distance_pips`); Sugar converts to prices via the symbol's pip size.
* **Lots are keyword-only** on the entry methods (`buy_market("EURUSD", lots=0.01)`).
* **Normalization is automatic.** Lots are snapped to the volume step and prices to the symbol's digits.
* **Defaults.** `set_defaults(...)` sets a default symbol/magic/deviation/risk reused across calls; `with_defaults(...)` is a scoped override.
* **Errors** raise `MT4Error` subclasses (`OrderRejected`, `ModifyRejected`, …) — see the [Return Codes Reference](../All_Guides/RETURN_CODES_REFERENCE.md).

---

## See Also

* [MT4Service — Overview](../MT4Service/MT4Service.Overview.md)
* [MT4Account — Master Overview](../MT4Account/MT4Account.Master.Overview.md)
* [Return Codes Reference](../All_Guides/RETURN_CODES_REFERENCE.md)
* [gRPC Stream Management](../All_Guides/GRPC_STREAM_MANAGEMENT.md)
