# MT4Service — Overview

> The **mid-level facade**: the same operations as `MT4Account`, but with friendlier Python signatures and unpacked results.

`MT4Service` is **Layer 2**. It wraps a connected [`MT4Account`](../MT4Account/MT4Account.Master.Overview.md) and:

* accepts **string enums** (`timeframe="H1"`, `sort="open_desc"`) instead of protobuf constants,
* **unpacks** protobuf containers into plain Python lists,
* takes **friendly keyword names** (`side`, `lots`, `sl`, `tp`, `magic`) and maps them to the raw request,
* fills **sensible defaults** (e.g. a history window for `quote_history`).

High-level one-liners and risk sizing live one layer up in [`MT4Sugar`](../MT4Sugar/MT4Sugar.Master.Overview.md) (reachable as `service.sugar`).

```
MT4Sugar    (HIGH)   one-liners, risk sizing, watchers
MT4Service  (MID)    friendly facade  ← you are here
MT4Account  (LOW)    raw gRPC / protobuf
```

---

## 🚦 Method groups

Each group is documented in a single page; follow the links.

* **[1. Account Information](./1.%20Account_Information.md)** — `account_summary`, `trade_stats`, `trade_unrealized_pl`, `equity_history`, `trade_stats_equity_history`
* **[2. Orders & History](./2.%20Orders_History.md)** — `opened_orders`, `opened_orders_tickets`, `orders_history`
* **[3. Symbols & Quotes](./3.%20Symbols_Quotes.md)** — `symbols`, `quote`, `quote_many`, `quote_history`, `symbol_params_many`, `tick_value_with_size`, `symbol_select`, `server_timezone`
* **[4. Trading Operations](./4.%20Trading_Operations.md)** — `order_send`, `order_modify`, `order_close_delete`, `order_close_by` **+** the `MT4ServiceTrade` helpers (`buy_market`, `sell_market`, `buy_limit`/`stop`, `sell_limit`/`stop`, `close`, `close_partial`, `close_by`, `modify_sl_tp`, `set_trade_defaults`, `order_send_with_defaults`)
* **[5. Streaming Methods](./5.%20Streaming_Methods.md)** — `on_symbol_tick`, `on_trade`, `on_opened_orders_tickets`, `on_opened_orders_profit`, `on_connect_state`

---

## 🔌 Connection & lifecycle

`MT4Service` wraps an `MT4Account`; connect through either one.

| Method | Description |
|--------|-------------|
| `connect_by_server_name(server_name, base_symbol=None, timeout_s=None)` | Connect via broker server name. |
| `connect_by_host_port(host, port, base_symbol=None, timeout_s=None)` | Connect to a terminal host/port. |
| `reconnect()` | Re-establish the session. |
| `disconnect(delete=False)` | Release the session. |
| `get_headers()` | Current gRPC metadata headers. |

```python
import asyncio
from MetaRpcMT4.mt4_account import MT4Account
from app.MT4Service import MT4Service

async def main():
    account = MT4Account(user=..., password=..., grpc_server="mt4.mrpc.pro:443")
    await account.connect_by_server_name(server_name="MetaQuotes-Demo",
                                         base_chart_symbol="EURUSD", timeout_seconds=30)
    service = MT4Service(account)

    s = await service.account_summary()
    print(s.account_balance, s.account_equity)

    await account.channel.close()

asyncio.run(main())
```

---

## 🧩 The `sugar` property

`service.sugar` returns a ready [`MT4Sugar`](../MT4Sugar/MT4Sugar.Master.Overview.md) bound to this service — the high-level API:

```python
sugar = service.sugar
q = await sugar.last_quote("EURUSD")
```

---

## ⚙️ Trade helpers — `MT4ServiceTrade`

The convenience order helpers live in a small companion class, `MT4ServiceTrade`, built on a `MT4Service`:

```python
from app.MT4Service import MT4Service, MT4ServiceTrade

trade = MT4ServiceTrade(service)
trade.set_trade_defaults(magic=777, deviation_pips=3, comment="my bot")
# ticket = await trade.buy_market("EURUSD", lots=0.01, sl=..., tp=...)
```

They are documented in [4. Trading Operations](./4.%20Trading_Operations.md).

---

## See Also

* [MT4Account — Master Overview](../MT4Account/MT4Account.Master.Overview.md)
* [MT4Sugar Reference](../MT4Sugar/MT4Sugar.Master.Overview.md)
* [Return Codes Reference](../All_Guides/RETURN_CODES_REFERENCE.md)
