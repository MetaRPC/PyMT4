# ✅ Getting an Account Summary

> **Request:** full account summary (`AccountSummaryData`) from **MT4**.
> Fetch all core account metrics in a single call.

**Source files (SDK):**

* `MetaRpcMT4/mt4_account.py` — method `account_summary(...)`
* `MetaRpcMT4/mt4_term_api_account_helper_pb2.py` — `AccountSummary*`, `EnumAccountTradeMode`

### RPC

* **Service:** `mt4_term_api.AccountHelper`
* **Method:** `AccountSummary(AccountSummaryRequest) → AccountSummaryReply`
* **Low-level client:** `AccountHelperStub.AccountSummary(request, metadata, timeout)`
* **SDK wrapper:** `MT4Account.account_summary(deadline=None, cancellation_event=None) -> AccountSummaryData`

**Request message:** `AccountSummaryRequest {}`
**Reply message:** `AccountSummaryReply { data: AccountSummaryData }`

---

### 🔗 Code Example

```python
# High-level (prints formatted summary):
async def show_account_summary(acct):
    s = await acct.account_summary()
    print(
        f"Account Summary: Balance={s.account_balance:.2f}, "
        f"Equity={s.account_equity:.2f}, Currency={s.account_currency}, "
        f"Login={s.account_login}, Leverage={s.account_leverage}, "
        f"Mode={s.account_trade_mode}"
    )

# Low-level (returns the proto message):
summary = await acct.account_summary()
# summary: AccountSummaryData
```

---

### Method Signature

```python
async def account_summary(
    self,
    deadline: datetime | None = None,
    cancellation_event: asyncio.Event | None = None,
) -> account_helper_pb2.AccountSummaryData
```

---

## 💬 Just the essentials

* **What it is.** A single RPC that returns the account state: balance, equity, currency, leverage, trade mode, and server time.
* **Why you need it.** Quick status for UI/CLI; double‑check login/currency/leverage; verify terminal responsiveness via `server_time`.
* **Fast sanity check.** If you see `account_login`, `account_currency`, `account_leverage`, `account_equity` → the connection is alive and data is flowing.

---

## 🔽 Input

No required parameters.

| Parameter            | Type           | Description |                                                    |
| -------------------- | -------------- | ----------- | -------------------------------------------------- |
| `deadline`           | `datetime      | None`       | Absolute per‑call deadline → converted to timeout. |
| `cancellation_event` | `asyncio.Event | None`       | Cooperative cancel for the retry loop.             |

---

## ⬆️ Output

### Payload: `AccountSummaryData` (from `mt4_term_api_account_helper_pb2.py`)

| Field                           | Proto Type                               | Description                                      |
| ------------------------------- | ---------------------------------------- | ------------------------------------------------ |
| `account_login`                 | `int64`                                  | Trading account login (ID).                      |
| `account_balance`               | `double`                                 | Balance excluding floating P/L.                  |
| `account_equity`                | `double`                                 | Equity = balance + floating P/L.                 |
| `account_user_name`             | `string`                                 | Account holder display name.                     |
| `account_leverage`              | `int64`                                  | Leverage (e.g., `100` for 1:100).                |
| `account_trade_mode`            | `enum mt4_term_api.EnumAccountTradeMode` | Account trade mode.                              |
| `account_company_name`          | `string`                                 | Broker/company display name.                     |
| `account_currency`              | `string`                                 | Deposit currency code (e.g., `USD`).             |
| `server_time`                   | `google.protobuf.Timestamp`              | Server time (UTC) at response.                   |
| `account_credit`                | `double`                                 | Credit amount.                                   |
| `is_investor`                   | `bool`                                   | Investor access flag.                            |
| `utc_server_time_shift_minutes` | `int32`                                  | Server time offset relative to UTC (in minutes). |

---

## 🧱 Related enums (from pb)

### `EnumAccountTradeMode`

Account trade mode values:

* `ACCOUNT_TRADE_MODE_DEMO = 0` — Demo/practice account
* `ACCOUNT_TRADE_MODE_CONTEST = 1` — Contest account
* `ACCOUNT_TRADE_MODE_REAL = 2` — Real trading account

> Access in Python: `account_helper_pb2.EnumAccountTradeMode.ACCOUNT_TRADE_MODE_DEMO`
> Map enum → label in UI via `account_helper_pb2.EnumAccountTradeMode.Name(value)`.

---

### 🎯 Purpose

Use it to display real‑time account state and sanity‑check connectivity:

* Dashboard/CLI status in one call.
* Verify free‑margin & equity before trading.
* Terminal heartbeat via `server_time` and `utc_server_time_shift_minutes`.

### 🧩 Notes & Tips

* The wrapper uses `execute_with_reconnect(...)` from `mt4_account.py` to retry transient gRPC errors.
* Prefer a short per‑call timeout (3–5s) with retries if the terminal is warming up or syncing symbols.
* `is_investor=True` → trading operations may be restricted; reflect that in your UX.

**See also:** `OpenedOrders(...)`, `OrdersHistory(...)`, `SymbolParamsMany(...)`, `TickValueWithSize(...)`.

---

## Usage Examples

### 1) Per‑call deadline

```python
# Enforce a short absolute deadline to avoid hanging calls
from datetime import datetime, timedelta, timezone

summary = await acct.account_summary(
    deadline=datetime.now(timezone.utc) + timedelta(seconds=3)
)
print(f"[deadline] Equity={summary.account_equity:.2f}")
```

### 2) Cooperative cancellation (with asyncio.Event)

```python
# Pass a cancellation_event to allow a graceful stop from another task
import asyncio
from datetime import datetime, timedelta, timezone

cancel_event = asyncio.Event()

summary = await acct.account_summary(
    deadline=datetime.now(timezone.utc) + timedelta(seconds=3),
    cancellation_event=cancel_event,
)
print(f"[cancel] Currency={summary.account_currency}")
```

### 3) Compact status line for UI/CLI

```python
# Produce a short, readable one‑liner for dashboards/CLI
s = await acct.account_summary()
status = (
    f"Acc {s.account_login} | {s.account_currency} | "
    f"Bal {s.account_balance:.2f} | Eq {s.account_equity:.2f} | "
    f"Lev {s.account_leverage} | Mode {s.account_trade_mode}"
)
print(status)
```

### 4) Human‑readable server time with timezone shift

```python
# Convert server_time (UTC Timestamp) + shift (minutes) to a local server time string
from datetime import timezone, timedelta

s = await acct.account_summary()
server_dt_utc = s.server_time.ToDatetime().replace(tzinfo=timezone.utc)
shift = timedelta(minutes=int(s.utc_server_time_shift_minutes))
server_local = server_dt_utc + shift
print(f"Server time: {server_local.isoformat()} (shift {shift})")
```

### 5) Map proto → your dataclass (thin view‑model)

```python
# Keep only the fields you actually use; fast and test‑friendly
from dataclasses import dataclass

@dataclass
class AccountSummaryView:
    login: int
    currency: str
    balance: float
    equity: float
    leverage: int
    mode: int  # enum numeric; map to label if needed
    investor: bool

    @staticmethod
    def from_proto(p):
        return AccountSummaryView(
            login=int(p.account_login),
            currency=str(p.account_currency),
            balance=float(p.account_balance),
            equity=float(p.account_equity),
            leverage=int(p.account_leverage),
            mode=int(p.account_trade_mode),
            investor=bool(p.is_investor),
        )

s = await acct.account_summary()
view = AccountSummaryView.from_proto(s)
print(view)
```
