# MT4Account — Master Overview

> One page to orient fast: the low-level gRPC client for MetaTrader 4. Jump to any group overview or method spec from here.

`MT4Account` is **Layer 1** — direct gRPC/protobuf calls to the MT4 terminal gateway. `MT4Service` (typed facade) and `MT4Sugar` (high-level helpers) build on top of it.

It exposes **25 feature methods** across 5 groups (plus connection & stream helpers). MT4 has a single order list — no positions/deals split, Depth-of-Market, `order_check` or `order_calc_*` (those are MT5-only).

---

## 🚦 Start here — Section Overviews

* **[1. Account Information — Overview](./1.%20Account_Information/Account_Information.Overview.md)**  
  Account snapshot plus performance: balance/equity/margin, trade statistics, equity curve and unrealized-P/L extrema.
* **[2. Orders & History — Overview](./2.%20Orders_History/Orders_History.Overview.md)**  
  Currently open orders (market + pending), their ticket lists, and closed-order history.
* **[3. Symbols & Quotes — Overview](./3.%20Symbols_Quotes/Symbols_Quotes.Overview.md)**  
  Symbol list, live quotes, OHLC bar history, per-symbol parameters, tick value, Market Watch select and server timezone.
* **[4. Trading Operations — Overview](./4.%20Trading_Operations/Trading_Operations.Overview.md)**  
  Send market/pending orders, modify SL/TP/price, close or delete, and close-by.
* **[5. Streaming Methods — Overview](./5.%20Streaming_Methods/Streaming_Methods.Overview.md)**  
  Real-time async generators: ticks, trade events, ticket lists and open-order profit.

---

## 🧭 Method groups

| Group | Methods |
|-------|---------|
| Account Information | `account_summary`, `trade_stats`, `trade_unrealized_pl`, `equity_history`, `trade_stats_equity_history` |
| Orders & History | `opened_orders`, `opened_orders_tickets`, `orders_history` |
| Symbols & Quotes | `symbols`, `quote`, `quote_many`, `quote_history`, `symbol_params_many`, `tick_value_with_size`, `symbol_select`, `server_timezone` |
| Trading Operations | `order_send`, `order_modify`, `order_close_delete`, `order_close_by` |
| Streaming Methods | `on_symbol_tick`, `on_trade`, `on_opened_orders_tickets`, `on_opened_orders_profit`, `on_connect_state` |

---

## 🔌 Usage pattern (Python async/await)

```python
import asyncio
from MetaRpcMT4.mt4_account import MT4Account

async def main():
    account = MT4Account(
        user=12345678,
        password="your_password",
        grpc_server="mt4.mrpc.pro:443",
        api_key="TRIAL",
    )
    await account.connect_by_server_name(
        server_name="MetaQuotes-Demo",
        base_chart_symbol="EURUSD",
        timeout_seconds=30,
    )

    summary = await account.account_summary()
    print(summary.account_balance, summary.account_equity)

    await account.channel.close()

asyncio.run(main())
```

> Every method is `async` and must be awaited. Errors surface as exceptions
> (`ApiExceptionMT4` / `ConnectExceptionMT4`) — see the
> [Return Codes Reference](../All_Guides/RETURN_CODES_REFERENCE.md).

---

## See Also

* [ENUMS Usage Reference](../All_Guides/ENUMS_USAGE_REFERENCE.md)
* [gRPC Stream Management](../All_Guides/GRPC_STREAM_MANAGEMENT.md)
* [MT4Service Overview](../MT4Service/MT4Service.Overview.md) · [MT4Sugar Reference](../MT4Sugar/MT4Sugar.Master.Overview.md)
