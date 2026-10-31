# User Code Sandbox Guide

## What is this?

This is **your sandbox** for writing custom MT4 trading code in Python. Connection setup is already done - you only need to add your trading logic!

## 🏁 Quick Start

1. **Already wired into main.py**
   - Open `examples/main.py`
   - Entry **17** ("Your sandbox") is ready to use

2. **Open `examples/5_usercode/17_usercode.py`**
   - Write your code or uncomment the examples inside `run_user_code(account, service, sugar)`

3. **Run:**
   ```bash
   cd examples
   python main.py usercode
   ```

That's it! Your code runs with a live MT4 connection already established.

## How to use

The sandbox hands you three ready objects inside `run_user_code(account, service, sugar)`:

- `account` - low-level gRPC client (`MT4Account`)
- `service` - typed facade (`MT4Service`)
- `sugar` - high-level helpers (`MT4Sugar`)

### Option 1: Uncomment an example

```python
# q = await sugar.last_quote("EURUSD")
# print(f"EURUSD: Bid={q['bid']:.5f} Ask={q['ask']:.5f}")
```

Just remove `#` to activate.

### Option 2: Write your own code

```python
# =================================================================
# YOUR CODE HERE
# =================================================================

# Your trading strategy here...

# =================================================================
```

## Available commands

```bash
# From the examples directory
python main.py usercode
python main.py 17
python main.py user
python main.py sandbox
```

## What's already configured

+ **Connection** - MT4 terminal connected via gRPC
+ **Configuration** - loaded from `examples/0_common/settings.json`
+ **account** - low-level gRPC client (`MT4Account`)
+ **service** - typed facade (`MT4Service`)
+ **sugar** - high-level Sugar API (`MT4Sugar`)
+ **async/await** - all methods are asynchronous

## 🧩 Can I mix API levels?

**Yes!** All three objects talk to the same connection:

```python
# Low-level (direct gRPC protobuf)
summary = await account.account_summary()
balance_pb = summary.account_balance

# Mid-level (MT4Service) - same protobuf object, via the facade
summary_svc = await service.account_summary()
balance_svc = summary_svc.account_balance

# High-level (MT4Sugar) - convenience helpers
q = await sugar.last_quote("EURUSD")
```

- `account` - for full control (gRPC protobuf)
- `service` - the typed facade over MT4Account
- `sugar` - for the simplest one-liners

## Quick reference

### Get account information

```python
# Account state comes from account_summary() (protobuf object)
summary = await service.account_summary()
print(f"Balance: {summary.account_balance:.2f} {summary.account_currency}")
print(f"Equity:  {summary.account_equity:.2f}")
print(f"Free margin: {summary.account_margin_free:.2f}")
```

### Get current price

```python
# Sugar API
q = await sugar.last_quote("EURUSD")          # {"bid": ..., "ask": ..., "time": ...}
print(f"EURUSD: Bid={q['bid']:.5f}, Ask={q['ask']:.5f}")
mid = await sugar.mid_price("EURUSD")

# Service API
tick = await service.quote("EURUSD")
print(f"EURUSD Bid: {tick.bid:.5f}, Ask: {tick.ask:.5f}")
```

### Open market order

```python
# Sugar API (lots is keyword-only)
try:
    ticket = await sugar.buy_market("EURUSD", lots=0.01)
    print(f"Order opened: #{ticket}")
except Exception as e:
    print(f"Order failed: {e}")

# With SL/TP in pips
ticket = await sugar.buy_market("EURUSD", lots=0.01, sl_pips=20, tp_pips=30)

# Lot size based on risk (2% with 50-pip SL)
lots = await sugar.calc_lot_by_risk("EURUSD", risk_percent=2.0, stop_pips=50)
ticket = await sugar.buy_market("EURUSD", lots=lots, sl_pips=50, tp_pips=100)
```

### Place pending order

```python
# Buy Limit with absolute price and SL/TP in pips
ticket = await sugar.buy_limit("EURUSD", price=1.0850, lots=0.01, sl_pips=20, tp_pips=30)

# Buy Stop with absolute price
ticket = await sugar.buy_stop("EURUSD", price=1.0950, lots=0.01)

# Sell Limit with absolute SL/TP prices
ticket = await sugar.sell_limit("EURUSD", price=1.1050, lots=0.01,
                                sl_price=1.1070, tp_price=1.1030)
```

### List open orders

```python
# Sugar API - returns a list of dicts
orders = await sugar.find_orders(symbol="EURUSD")
print(f"Open orders: {len(orders)}")
for o in orders:
    print(o)

# Service API - low-level protobuf
data = await service.opened_orders()
for o in data.order_infos:
    print(f"  #{o.ticket} {o.symbol} {o.lots:.2f} lot, profit: {o.profit:.2f}")
```

### Close orders

```python
# Close a specific order (market) or delete a pending one
await sugar.close(ticket)

# Close all orders for a symbol
await sugar.close_all(symbol="EURUSD")

# Close all orders (all symbols)
await sugar.close_all()

# Cancel pending orders only
await sugar.cancel_pendings(symbol="EURUSD")
```

### Modify order

```python
# Modify SL/TP by absolute prices
await sugar.modify_sl_tp_by_price(ticket, sl_price=1.0850, tp_price=1.0950)

# Modify SL/TP by pips relative to entry
await sugar.modify_sl_tp_by_pips(ticket, sl_pips=20, tp_pips=40)
```

### Calculate lot size

```python
# Lot size based on risk
lots = await sugar.calc_lot_by_risk("EURUSD", risk_percent=2.0, stop_pips=20)
print(f"Lots for 2% risk with 20-pip SL: {lots:.2f}")

# Then use it
ticket = await sugar.buy_market("EURUSD", lots=lots)
```

## ℹ️ Error handling

PyMT4 surfaces failures as **Python exceptions** (there is no MT5-style
`returned_code` to poll). Order helpers return the **ticket number** on success.

- `MT4Account` raises `ApiExceptionMT4` on server errors, `ConnectExceptionMT4`
  if you call a method before connecting.
- `MT4Sugar` raises `MT4Error` subclasses (`OrderRejected`, `ModifyRejected`,
  `ConnectivityError`, `RateLimitExceeded`).

### Recommended pattern

```python
from MetaRpcMT4.mt4_account import ApiExceptionMT4
from app.Helper.errors import OrderRejected, MT4Error

try:
    ticket = await sugar.buy_market("EURUSD", lots=0.01)
    print(f"[OK] Order opened: #{ticket}")
except OrderRejected as e:
    print(f"[X] Order rejected: {e}")
except (ApiExceptionMT4, MT4Error) as e:
    print(f"[X] Error: {e}")
```

## 📝 Documentation

- [MT4Account API Reference](../MT4Account/MT4Account.Master.Overview.md) - low-level API (18 core methods)
- [MT4Service Overview](../MT4Service/MT4Service.Overview.md) - typed facade + trade helpers
- [MT4Sugar Reference](../MT4Sugar/MT4Sugar.Master.Overview.md) - high-level Sugar API (~60 methods)
- [ENUMS Usage Reference](ENUMS_USAGE_REFERENCE.md) - all ENUMs in one place
- [Return Codes Reference](RETURN_CODES_REFERENCE.md) - error / return codes

## 🔑 Configuration

### settings.json

Edit `examples/0_common/settings.json`:

```json
{
  "user": 591129415,
  "password": "YourPassword",
  "grpc_server": "mt4.mrpc.pro:443",
  "mt_cluster": "MetaQuotes-Demo",
  "test_symbol": "EURUSD",
  "test_volume": 0.01,
  "api_key": "TRIAL"
}
```

### Environment overrides

`examples/0_common/demo_helpers.py` lets two environment variables override the
file when set (handy for CI or switching servers without editing JSON):

```bash
# Linux/Mac
export MRPC_API_KEY=mrpc_live_...
export MRPC_GRPC_SERVER=mt4.mrpc.pro:443

# Windows PowerShell
$env:MRPC_API_KEY="mrpc_live_..."
$env:MRPC_GRPC_SERVER="mt4.mrpc.pro:443"
```

## Tips

1. **Start simple** - uncomment one example at a time
2. **Use Sugar API** - `buy_market(..., sl_pips=, tp_pips=)` and `calc_lot_by_risk()` are easier than low-level calls
3. **Handle exceptions** - wrap trading calls in `try/except`
4. **Test on demo** - make sure you're on a demo account first
5. **Read the docs** - [RETURN_CODES_REFERENCE.md](RETURN_CODES_REFERENCE.md) explains error codes
6. **Use async/await** - all methods are asynchronous
7. **Type hints** - rely on IDE autocomplete
8. **Check the examples** - the `examples/` folder has a full set of working examples

## Common mistakes

[X] **Forgot to use await**
```python
q = sugar.last_quote("EURUSD")  # DON'T forget await!
```

[+] **Always use await**
```python
q = await sugar.last_quote("EURUSD")
```

[X] **Passing lots positionally**
```python
ticket = await sugar.buy_market("EURUSD", 0.01)  # lots is keyword-only!
```

[+] **Pass lots as a keyword**
```python
ticket = await sugar.buy_market("EURUSD", lots=0.01)
```

[X] **Not handling exceptions**
```python
ticket = await sugar.buy_market("EURUSD", lots=0.01)  # no try/except!
```

[+] **Always handle exceptions**
```python
try:
    ticket = await sugar.buy_market("EURUSD", lots=0.01)
    print(f"Order opened: #{ticket}")
except Exception as e:
    print(f"Error: {e}")
```

## Getting help

- **Protobuf types**: check the `package/MetaRpcMT4/` folder for all protobuf definitions
- **Error codes**: see [RETURN_CODES_REFERENCE.md](RETURN_CODES_REFERENCE.md)
- **Examples**: check the `examples/` folder for working code
- **API documentation**: see the API Reference section

## Example: Complete sandbox function

This mirrors the real `run_user_code(account, service, sugar)` in
`examples/5_usercode/17_usercode.py` — connection is already done for you, so you
just add logic:

```python
async def run_user_code(account, service, sugar):
    """Your sandbox. `account`, `service`, `sugar` are connected and ready."""

    # Account state
    try:
        summary = await service.account_summary()
        print(f"Balance: {summary.account_balance:.2f} {summary.account_currency}")
    except Exception as e:
        print(f"Balance error: {e}")
        return

    # Lot size based on risk (1% with 50-pip SL)
    try:
        lots = await sugar.calc_lot_by_risk("EURUSD", risk_percent=1.0, stop_pips=50)
    except Exception as e:
        print(f"Lot-size error: {e}")
        return

    # Open a market order with SL/TP in pips
    try:
        ticket = await sugar.buy_market("EURUSD", lots=lots, sl_pips=50, tp_pips=100)
        print(f"[OK] Order opened: #{ticket} with {lots:.2f} lot")
    except Exception as e:
        print(f"Order error: {e}")
        return

    print("Strategy execution completed!")
```

**Happy trading!**
