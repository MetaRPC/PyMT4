# MT4 Error / Return Codes Reference - Python

## 🛡️ How MT4 reports errors

Unlike MT5 (which returns a numeric `returned_code` / `TRADE_RETCODE_*` on every trade
result), **MT4 reports failures as Python exceptions**. A trading call either:

- **succeeds** — and returns its data (e.g. `order_send` returns a ticket), or
- **fails** — and raises an exception carrying a structured error.

> There is **no** `returned_code` field and **no** `TRADE_RETCODE_*` constants in
> PyMT4. The classic MQL4 error codes live in the `MqlErrorCode` enum (see below).

### Quick example

```python
from MetaRpcMT4.mt4_account import ApiExceptionMT4

try:
    ticket = await sugar.buy_market("EURUSD", lots=0.01)
    print(f"✓ Order opened: #{ticket}")
except ApiExceptionMT4 as e:
    # e.error is the structured protobuf Error
    print(f"✗ Trade failed: {e.error.mql_error_description} "
          f"(code {e.error.mql_error_int_code})")
```

**Key point:** no exception = the trade went through; an exception tells you *why* it
did not.

---

## Where do the codes come from?

The error codes are the standard **MQL4 error codes**, defined in the protobuf enum
`MqlErrorCode` inside `package/MetaRpcMT4/mrpc_mt4_error_pb2.py`. They are returned by
the trading server and mirror the codes `GetLastError()` returns inside an MQL4 EA.

---

## How errors surface in the API

### Low level — `MT4Account`

`MT4Account` raises two exception types (defined in `MetaRpcMT4.mt4_account`):

| Exception | When |
|-----------|------|
| `ConnectExceptionMT4` | A method was called before `connect_by_server_name` / `connect_by_host_port` |
| `ApiExceptionMT4` | The server returned an error for the request |

`ApiExceptionMT4.error` is a protobuf `Error` message with these fields:

| Field | Type | Meaning |
|-------|------|---------|
| `type` | `ErrorType` | High-level category: `MRPC`, `MRPC_VALIDATION`, `MRPC_TIMEOUT`, `TERMINAL_API_TIMEOUT`, … |
| `error_code` | `string` | Gateway error code (e.g. `GETTING_CONNECTION_EX_DATA_FROM_INCOMING_REQUEST_ERROR`) |
| `error_message` | `string` | Human-readable gateway message |
| `mql_error_code` | `MqlErrorCode` | Symbolic MQL4 error (e.g. `ERR_NOT_ENOUGH_MONEY`) |
| `mql_error_int_code` | `int` | Numeric MQL4 error (e.g. `134`) |
| `mql_error_description` | `string` | Description of the MQL4 error |
| `stack_trace` | `string` | Server-side stack trace (diagnostics) |
| `command_type_name` | `string` | Which RPC produced the error |

### High level — `MT4Service` / `MT4Sugar`

The Sugar layer translates backend errors into domain exceptions from
`app/Helper/errors.py`:

| Exception | Raised for (by context) |
|-----------|-------------------------|
| `OrderRejected` | `order_send` / `place_order` failures |
| `ModifyRejected` | `order_modify` / `order_close_delete` / `order_close_by` failures |
| `ConnectivityError` | reconnect / session / handshake issues |
| `RateLimitExceeded` | client-side rate-limit guard tripped |
| `MT4Error` | base class / anything else |

Each `MT4Error` has optional `.code` and `.details` attributes, and its message wraps
the original low-level error.

---

## MQL4 Error Codes (`MqlErrorCode`)

### Trade server & common codes

| Code | Constant | Meaning |
|------|----------|---------|
| **0** | `ERR_NO_ERROR` | No error (success) |
| **1** | `ERR_NO_RESULT` | No error, but result unknown |
| **2** | `ERR_COMMON_ERROR` | Common error |
| **3** | `ERR_INVALID_TRADE_PARAMETERS` | Invalid trade parameters |
| **4** | `ERR_SERVER_BUSY` | Trade server is busy |
| **5** | `ERR_OLD_VERSION` | Old terminal version |
| **6** | `ERR_NO_CONNECTION` | No connection to trade server |
| **7** | `ERR_NOT_ENOUGH_RIGHTS` | Not enough rights |
| **8** | `ERR_TOO_FREQUENT_REQUESTS` | Too frequent requests |
| **9** | `ERR_MALFUNCTIONAL_TRADE` | Malfunctional trade operation |
| **64** | `ERR_ACCOUNT_DISABLED` | Account disabled |
| **65** | `ERR_INVALID_ACCOUNT` | Invalid account |
| **128** | `ERR_TRADE_TIMEOUT` | Trade timeout |
| **129** | `ERR_INVALID_PRICE` | Invalid price |
| **130** | `ERR_INVALID_STOPS` | Invalid stops (SL/TP too close to price) |
| **131** | `ERR_INVALID_TRADE_VOLUME` | Invalid trade volume |
| **132** | `ERR_MARKET_CLOSED` | Market is closed |
| **133** | `ERR_TRADE_DISABLED` | Trading is disabled |
| **134** | `ERR_NOT_ENOUGH_MONEY` | Not enough money |
| **135** | `ERR_PRICE_CHANGED` | Price changed |
| **136** | `ERR_OFF_QUOTES` | Off quotes (no prices) |
| **137** | `ERR_BROKER_BUSY` | Broker is busy |
| **138** | `ERR_REQUOTE` | Requote |
| **139** | `ERR_ORDER_LOCKED` | Order is locked |
| **140** | `ERR_LONG_POSITIONS_ONLY_ALLOWED` | Only long positions allowed |
| **141** | `ERR_TOO_MANY_REQUESTS` | Too many requests |
| **145** | `ERR_TRADE_MODIFY_DENIED` | Modification denied (order too close to market) |
| **146** | `ERR_TRADE_CONTEXT_BUSY` | Trade context is busy |
| **147** | `ERR_TRADE_EXPIRATION_DENIED` | Expiration setting denied by broker |
| **148** | `ERR_TRADE_TOO_MANY_ORDERS` | Too many open orders / pending orders |
| **149** | `ERR_TRADE_HEDGE_PROHIBITED` | Hedging prohibited |
| **150** | `ERR_TRADE_PROHIBITED_BY_FIFO` | Prohibited by FIFO rule |

> Codes **4000+** (`ERR_NO_MQLERROR`, `ERR_ZERO_DIVIDE`, …) are MQL4 *runtime* errors
> and rarely appear for API trading. The full enum has 112 entries — introspect
> `MqlErrorCode` in `mrpc_mt4_error_pb2` for the complete list.

---

## Inspecting errors

### Low level (`MT4Account`)

```python
from MetaRpcMT4.mt4_account import ApiExceptionMT4
from MetaRpcMT4 import mrpc_mt4_error_pb2 as err_pb2

try:
    result = await account.order_send(request)
    print(f"✓ Order #{result.ticket} @ {result.price:.5f}")
except ApiExceptionMT4 as e:
    code = e.error.mql_error_int_code
    if code == err_pb2.MqlErrorCode.ERR_NOT_ENOUGH_MONEY:   # 134
        print("Not enough money — reduce volume or add margin")
    elif code == err_pb2.MqlErrorCode.ERR_MARKET_CLOSED:    # 132
        print("Market is closed — try during trading hours")
    else:
        print(f"Trade failed: {e.error.mql_error_description} (code {code})")
```

### High level (`MT4Sugar`)

```python
from app.Helper.errors import OrderRejected, MT4Error

try:
    ticket = await sugar.buy_market("GBPUSD", lots=0.5)
    print(f"✓ Order #{ticket} opened")
except OrderRejected as e:
    print(f"Order rejected: {e}")      # message wraps the server error
    print(f"details: {e.details}")     # payload (symbol, lots, …)
except MT4Error as e:
    print(f"SDK error: {e}")
```

---

## Retrying transient errors

Some codes are **temporary** and safe to retry (ideally with a short backoff):

`ERR_SERVER_BUSY` (4), `ERR_NO_CONNECTION` (6), `ERR_TOO_FREQUENT_REQUESTS` (8),
`ERR_TRADE_TIMEOUT` (128), `ERR_PRICE_CHANGED` (135), `ERR_OFF_QUOTES` (136),
`ERR_BROKER_BUSY` (137), `ERR_REQUOTE` (138), `ERR_TRADE_CONTEXT_BUSY` (146),
`ERR_TOO_MANY_REQUESTS` (141).

```python
import asyncio
from MetaRpcMT4.mt4_account import ApiExceptionMT4
from MetaRpcMT4 import mrpc_mt4_error_pb2 as err_pb2

RETRYABLE = {
    err_pb2.MqlErrorCode.ERR_SERVER_BUSY,
    err_pb2.MqlErrorCode.ERR_NO_CONNECTION,
    err_pb2.MqlErrorCode.ERR_TOO_FREQUENT_REQUESTS,
    err_pb2.MqlErrorCode.ERR_TRADE_TIMEOUT,
    err_pb2.MqlErrorCode.ERR_PRICE_CHANGED,
    err_pb2.MqlErrorCode.ERR_OFF_QUOTES,
    err_pb2.MqlErrorCode.ERR_BROKER_BUSY,
    err_pb2.MqlErrorCode.ERR_REQUOTE,
    err_pb2.MqlErrorCode.ERR_TRADE_CONTEXT_BUSY,
}

async def buy_with_retry(sugar, symbol, lots, max_retries=3):
    for attempt in range(1, max_retries + 1):
        try:
            return await sugar.buy_market(symbol, lots=lots)
        except ApiExceptionMT4 as e:
            if e.error.mql_error_int_code in RETRYABLE and attempt < max_retries:
                await asyncio.sleep(attempt)   # 1s, 2s, …
                continue
            raise
    raise RuntimeError(f"failed after {max_retries} attempts")
```

**Permanent** errors (don't retry): `ERR_NOT_ENOUGH_MONEY` (134),
`ERR_INVALID_STOPS` (130), `ERR_INVALID_TRADE_VOLUME` (131),
`ERR_MARKET_CLOSED` (132), `ERR_TRADE_DISABLED` (133). Fix the request or conditions.

---

## Best Practices

### ✅ DO

1. **Wrap trading calls in `try/except`** — that's how MT4 reports failures.
2. **Inspect `e.error.mql_error_int_code`** to branch on the exact reason.
3. **Use the `MqlErrorCode` enum** instead of magic numbers (`ERR_NOT_ENOUGH_MONEY`, not `134`).
4. **Retry only transient codes** with a short backoff.

### ❌ DON'T

1. **Don't poll a `returned_code`** — MT4 has none; a returned ticket already means success.
2. **Don't retry permanent errors** (insufficient money, invalid stops, market closed).
3. **Don't swallow exceptions silently** — log `e.error.mql_error_description`.

---

## Quick Reference Table

| Category | Codes | Action |
|----------|-------|--------|
| **Success** | 0 (`ERR_NO_ERROR`) + a returned ticket | Continue |
| **Transient** | 4, 6, 8, 128, 135, 136, 137, 138, 141, 146 | Retry with delay |
| **Invalid request** | 3, 129, 130, 131 | Fix parameters |
| **Restrictions** | 132, 133, 140, 149, 150 | Check trading conditions |
| **Limits** | 134, 148 | Reduce volume / close orders |
| **Account / rights** | 7, 64, 65 | Check account & permissions |

---

## See Also

- [ENUMS Usage Reference](ENUMS_USAGE_REFERENCE.md) - all protobuf enums
- [MT4Account API Reference](../MT4Account/MT4Account.Master.Overview.md) - low-level API
- [User Code Sandbox Guide](USERCODE_SANDBOX_GUIDE.md) - error-handling patterns in practice
