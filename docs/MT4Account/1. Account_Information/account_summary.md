# Account Summary (RECOMMENDED)

> Complete account snapshot (balance, equity, margin, leverage, currency, server time) in a single call.

**API Information:**

* **Low-level API:** `MT4Account.account_summary(...)` (defined in `package/MetaRpcMT4/mt4_account.py`)
* **gRPC service:** `mt4_term_api.AccountHelper`
* **RPC:** `AccountSummary(AccountSummaryRequest) -> AccountSummaryReply`
* **Payload:** `AccountSummaryData`

## 💬 Just the essentials

* **What it is.** One call that returns every essential account property.
* **Why you need it.** The most efficient way to read balance/equity/margin at once — one round-trip instead of many single-field calls.
* **When to use.** At session start (banner / sanity check), and right before any risk decision or order.

---

## 🎯 Purpose

* RECOMMENDED way to read account state
* Balance, equity, credit in one round-trip
* Login, name, server, company
* Leverage and trade mode (DEMO/REAL)
* Currency and server time

---

## Method Signature

```python
async def account_summary(
    self,
    deadline: Optional[datetime] = None,
    cancellation_event: Optional[asyncio.Event] = None,
)
```

**Request message:**

```protobuf
message AccountSummaryRequest {
}
```

**Payload message:**

```protobuf
message AccountSummaryData {
  int64 account_login = 1;
  double account_balance = 2;
  double account_equity = 3;
  string account_user_name = 4;
  int64 account_leverage = 5;
  EnumAccountTradeMode account_trade_mode = 6;
  string account_company_name = 7;
  string account_currency = 8;
  Timestamp server_time = 9;
  Timestamp server_time_utc = 15;
  double account_credit = 10;
  bool is_investor = 11;
  int32 utc_server_time_shift_minutes = 12;
  int32 server_utc_offset_seconds = 14;
  double account_margin = 13;
  double account_margin_free = 16;
  double account_margin_level = 17;
  EnumAccountMarginMode account_margin_mode = 18;
  bool account_trade_allowed = 19;
  bool account_trade_expert = 20;
}
```

---

## 🔽 Input

| Parameter | Type | Description |
|-----------|------|-------------|
| `deadline` | datetime, optional | Absolute UTC deadline for the gRPC call. |
| `cancellation_event` | asyncio.Event, optional | Set to abort the request. |

---

## ⬆️ Output — `AccountSummaryData`

| Field | Proto Type | Python Type | Description |
|-------|-----------|-------------|-------------|
| `account_login` | int64 | `int` | Account number |
| `account_balance` | double | `float` | Balance in deposit currency (excludes floating P/L) |
| `account_equity` | double | `float` | Equity = balance + floating P/L of open orders |
| `account_user_name` | string | `str` | Account owner |
| `account_leverage` | int64 | `int` | Leverage (e.g. 100 = 1:100) |
| `account_trade_mode` | EnumAccountTradeMode | `int` | DEMO / CONTEST / REAL |
| `account_company_name` | string | `str` | Broker name |
| `account_currency` | string | `str` | Deposit currency (e.g. USD) |
| `server_time` | Timestamp | `datetime` | Current server time |
| `server_time_utc` | Timestamp | `datetime` | Current server time in UTC |
| `account_credit` | double | `float` | Credit in deposit currency |
| `is_investor` | bool | `bool` | True if connected with the investor (read-only) password |
| `utc_server_time_shift_minutes` | int32 | `int` | Server time shift from UTC, minutes |
| `server_utc_offset_seconds` | int32 | `int` | Server UTC offset, seconds |
| `account_margin` | double | `float` | Margin currently used by open orders |
| `account_margin_free` | double | `float` | Free margin available for new orders |
| `account_margin_level` | double | `float` | Margin level % = equity / margin × 100 |
| `account_margin_mode` | EnumAccountMarginMode | `int` | Margin calculation mode |
| `account_trade_allowed` | bool | `bool` | Trading allowed on the account |
| `account_trade_expert` | bool | `bool` | Expert/automated trading allowed |

---

## 🧱 Related enums (from proto)

### `EnumAccountTradeMode`

| Constant | Value | Meaning |
|----------|-------|---------|
| `ACCOUNT_TRADE_MODE_DEMO` | 0 | Demo / practice account |
| `ACCOUNT_TRADE_MODE_CONTEST` | 1 | Contest account |
| `ACCOUNT_TRADE_MODE_REAL` | 2 | Real (live) account |

### `EnumAccountMarginMode`

| Constant | Value | Meaning |
|----------|-------|---------|
| `ACCOUNT_MARGIN_MODE_RETAIL_NETTING` | 0 | Retail, netting |
| `ACCOUNT_MARGIN_MODE_EXCHANGE` | 1 | Exchange margin model |
| `ACCOUNT_MARGIN_MODE_RETAIL_HEDGING` | 2 | Retail, hedging (typical MT4) |

> In Python, access values via the pb2 module, e.g. `account_helper_pb2.EnumAccountTradeMode.ACCOUNT_TRADE_MODE_REAL`.

---

## 🧩 Notes & Tips

* **One call beats many.** `account_summary()` returns balance, equity, margin, free margin and margin level together — don't fan out into several calls for these.
* **`balance` vs `equity`.** Balance ignores open orders; equity includes their floating P/L. On a flat account they're equal; with open orders, `equity − balance` is your current floating P/L.
* **Money is in the deposit currency.** Every monetary field is in `account_currency`. Don't mix it with an instrument's quote currency without converting.
* **`margin_level` is 0 with no open orders** (division by zero margin is reported as 0), so guard before comparing it to a stop-out threshold.
* **Server time.** `server_time` / `server_time_utc` are protobuf Timestamps — use `.ToDatetime()`; `server_utc_offset_seconds` tells you the broker's offset.
* **Read-only sessions.** If `is_investor` is true (investor password) or `account_trade_allowed` is false, trading calls will be rejected — check these before placing orders.

---

## 🔗 Usage Examples

### 1) Session-start banner

Print a clean account banner when your bot connects — handy for logs and sanity checks.

```python
import MetaRpcMT4.mt4_term_api_account_helper_pb2 as ah

MODE = {
    ah.EnumAccountTradeMode.ACCOUNT_TRADE_MODE_DEMO: "DEMO",
    ah.EnumAccountTradeMode.ACCOUNT_TRADE_MODE_CONTEST: "CONTEST",
    ah.EnumAccountTradeMode.ACCOUNT_TRADE_MODE_REAL: "REAL",
}

async def print_banner(account):
    s = await account.account_summary()
    floating = s.account_equity - s.account_balance
    print("=" * 52)
    print(f" Account #{s.account_login}  ({MODE.get(s.account_trade_mode, '?')})")
    print(f" Broker : {s.account_company_name}")
    print(f" Balance: {s.account_balance:,.2f} {s.account_currency}")
    print(f" Equity : {s.account_equity:,.2f}  (floating {floating:+,.2f})")
    print(f" Margin : used {s.account_margin:,.2f} / free {s.account_margin_free:,.2f}")
    print(f" Leverage 1:{s.account_leverage}")
    print("=" * 52)
```

### 2) Pre-trade risk gate

Refuse to open a new order unless the account can actually take it — a guard you call before every entry.

```python
async def can_open(account, *, min_free_margin: float, min_margin_level: float = 200.0) -> bool:
    s = await account.account_summary()

    if not s.account_trade_allowed or s.is_investor:
        print("Trading not allowed on this account (read-only / disabled).")
        return False

    if s.account_margin_free < min_free_margin:
        print(f"Free margin too low: {s.account_margin_free:.2f} < {min_free_margin:.2f}")
        return False

    # margin_level is 0 when nothing is open — only enforce it once there is margin in use
    if s.account_margin > 0 and s.account_margin_level < min_margin_level:
        print(f"Margin level too low: {s.account_margin_level:.1f}% < {min_margin_level:.1f}%")
        return False

    return True

# usage:
# if await can_open(account, min_free_margin=500):
#     await sugar.buy_market("EURUSD", lots=0.10)
```

### 3) Equity / drawdown monitor

Poll equity on an interval and alert when drawdown from the session peak crosses a limit.

```python
import asyncio

async def watch_drawdown(account, *, max_dd_percent: float = 10.0, interval: float = 5.0):
    peak = None
    while True:
        s = await account.account_summary()
        eq = s.account_equity
        peak = eq if peak is None else max(peak, eq)
        dd = (peak - eq) / peak * 100 if peak > 0 else 0.0
        print(f"equity={eq:,.2f} peak={peak:,.2f} drawdown={dd:.2f}%")
        if dd >= max_dd_percent:
            print(f"[ALERT] drawdown {dd:.2f}% ≥ {max_dd_percent}% — consider de-risking")
            break
        await asyncio.sleep(interval)
```

---

## ⚠️ Pitfalls

* **Snapshot, not a stream.** Equity/margin are a point-in-time read — re-query right before a risk check or order, don't cache them across time.
* **`margin_level` == 0 with nothing open.** Guard `account_margin > 0` before comparing the level to a stop-out/entry threshold.
* **Currency mismatch.** All money fields are in `account_currency`; converting instrument P/L into account currency is on you.
* **Read-only / disabled accounts.** `is_investor` or `account_trade_allowed == False` means orders will be rejected even though this call succeeds.

---

## 🧪 Testing Suggestions

* **Happy path (demo).** Fields are populated; `account_currency` non-empty; on a flat account `equity == balance` and `account_margin == 0`.
* **With open orders.** `equity != balance`, `account_margin > 0`, and `account_margin_level` is a sensible percentage.
* **Risk gate.** Unit-test `can_open()` against synthetic summaries (low free margin, investor session, trading disabled) and assert it refuses.

---

## 📚 See also

* [Trade Statistics](trade_stats.md)
* [Unrealized P/L Extrema](trade_unrealized_pl.md)
* [Equity Curve](equity_history.md)
* [Stats + Equity + Trades](trade_stats_equity_history.md)

* **Back to:** [Account Information — Overview](Account_Information.Overview.md) · [MT4Account — Master Overview](../MT4Account.Master.Overview.md)
