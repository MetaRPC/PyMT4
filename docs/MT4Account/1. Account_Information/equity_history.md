# Equity Curve

> Time series of balance/equity points with running drawdowns — your equity curve, ready to chart or export.

**API Information:**

* **Low-level API:** `MT4Account.equity_history(...)` (defined in `package/MetaRpcMT4/mt4_account.py`)
* **gRPC service:** `mt4_term_api.TradeStats`
* **RPC:** `EquityHistory(EquityHistoryRequest) -> EquityHistoryReply`
* **Payload:** `EquityHistoryData`

## 💬 Just the essentials

* **What it is.** A chronological list of points, each with balance, equity, running drawdowns and the cash flow at that moment.
* **Why you need it.** To plot the equity curve, measure maximum drawdown, or export performance to a spreadsheet.
* **When to use.** Reporting, charting, drawdown analysis.

---

## 🎯 Purpose

* Balance & equity over time (the curve)
* Running balance/equity drawdowns (money and %)
* Realized / unrealized P/L and cash flow per point
* Feed charts, CSV exports and risk reports

---

## Method Signature

```python
async def equity_history(
    self,
    from_time: Optional[datetime] = None,
    exclude_same_bars: Optional[bool] = None,
    deadline: Optional[datetime] = None,
    cancellation_event: Optional[asyncio.Event] = None,
)
```

**Request message:**

```protobuf
message EquityHistoryRequest {
  string from = 1;              // ISO-8601 start; empty = full history
  string from_utc = 2;          // ISO-8601 start in UTC
  bool exclude_same_bars = 3;   // collapse consecutive equal points
}
```

**Payload message:**

```protobuf
message EquityHistoryData {
  repeated EquityPointData points = 1;
}

message EquityPointData {
  Timestamp time = 1;
  Timestamp time_utc = 2;
  double balance = 3;
  double equity = 4;
  double balance_drawdown_raw = 5;
  double balance_drawdown_relative = 6;   // percent
  double equity_drawdown_raw = 7;
  double equity_drawdown_relative = 8;     // percent
  double realized_pl = 9;
  double unrealized_pl = 10;
  double cash_flow = 11;                   // deposits/withdrawals at this point
}
```

---

## 🔽 Input

| Parameter | Type | Description |
|-----------|------|-------------|
| `from_time` | datetime, optional | Start of the window; serialized to an ISO-8601 string. Omit for full history. |
| `exclude_same_bars` | bool, optional | Collapse consecutive equal points to shrink the payload. |
| `deadline` | datetime, optional | Absolute UTC deadline for the gRPC call. |
| `cancellation_event` | asyncio.Event, optional | Set to abort the request. |

---

## ⬆️ Output — `EquityHistoryData`

| Field | Python Type | Description |
|-------|-------------|-------------|
| `points` | `list[EquityPointData]` | The equity-curve points, in time order |

Each `EquityPointData`:

| Field | Python Type | Description |
|-------|-------------|-------------|
| `time` / `time_utc` | `datetime` | Point timestamp (server / UTC) |
| `balance` | `float` | Balance at this point |
| `equity` | `float` | Equity at this point |
| `balance_drawdown_raw` / `_relative` | `float` | Balance drawdown (money / %) |
| `equity_drawdown_raw` / `_relative` | `float` | Equity drawdown (money / %) |
| `realized_pl` | `float` | Realized P/L to this point |
| `unrealized_pl` | `float` | Floating P/L at this point |
| `cash_flow` | `float` | Deposit/withdrawal applied at this point |

---

## 🧩 Notes & Tips

* **Drawdowns are precomputed.** You don't have to derive the running peak yourself — `equity_drawdown_relative` is already the % below the high-water mark at each point.
* **`cash_flow` separates deposits from trading.** A jump in `balance` with a matching `cash_flow` is a deposit/withdrawal, not a trade — exclude it when measuring trading performance.
* **This payload can be large.** A long-lived account has many points; pass `from_time` to scope the window and/or `exclude_same_bars=True` to drop flat stretches.
* **Timestamps are protobuf Timestamps** — convert with `.ToDatetime()`.
* **Pairs with [trade_stats](trade_stats.md).** Use `trade_stats` for the headline ratios and `equity_history` for the curve, or [trade_stats_equity_history](trade_stats_equity_history.md) to fetch both at once.

---

## 🔗 Usage Examples

### 1) Export the curve to CSV

Dump the equity curve so you can chart it in a spreadsheet or notebook.

```python
import csv

async def export_equity_csv(account, path: str = "equity.csv"):
    data = await account.equity_history(exclude_same_bars=True)
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["time_utc", "balance", "equity", "equity_dd_%"])
        for p in data.points:
            w.writerow([p.time_utc.ToDatetime().isoformat(),
                        f"{p.balance:.2f}", f"{p.equity:.2f}",
                        f"{p.equity_drawdown_relative:.2f}"])
    print(f"wrote {len(data.points)} points -> {path}")
```

### 2) Maximum drawdown from the curve

Find the deepest equity drawdown and when it happened.

```python
async def max_drawdown(account):
    data = await account.equity_history()
    if not data.points:
        print("no equity history")
        return
    worst = max(data.points, key=lambda p: p.equity_drawdown_relative)
    when = worst.time_utc.ToDatetime()
    print(f"Max equity drawdown: {worst.equity_drawdown_relative:.2f}% "
          f"({worst.equity_drawdown_raw:,.2f}) at {when:%Y-%m-%d %H:%M} UTC")
```

### 3) Trading-only result (strip deposits)

Separate trading performance from deposits/withdrawals using `cash_flow`.

```python
async def trading_pnl(account):
    data = await account.equity_history()
    if not data.points:
        return 0.0
    net_cash = sum(p.cash_flow for p in data.points)
    start, end = data.points[0].balance, data.points[-1].balance
    trading = (end - start) - net_cash
    print(f"balance {start:,.2f} -> {end:,.2f} | deposits/withdrawals {net_cash:+,.2f} "
          f"| trading P/L {trading:+,.2f}")
    return trading
```

---

## ⚠️ Pitfalls

* **Large payloads.** Full history can be big — scope with `from_time` and/or `exclude_same_bars=True`; print counts rather than every point.
* **Deposits skew raw balance deltas.** Use `cash_flow` to isolate trading P/L from account funding.
* **Empty history.** A fresh account returns an empty `points` list — guard before indexing `points[0]` / `points[-1]`.

---

## 🧪 Testing Suggestions

* **Happy path (demo with history).** `points` is non-empty and ordered by time; `equity_drawdown_relative >= 0` for every point.
* **`exclude_same_bars`.** The collapsed call returns no more points than the full call.
* **Windowing.** A recent `from_time` returns fewer points than full history.

---

## 📚 See also

* [Account Summary](account_summary.md)
* [Trade Statistics](trade_stats.md)
* [Unrealized P/L Extrema](trade_unrealized_pl.md)
* [Stats + Equity + Trades](trade_stats_equity_history.md)

* **Back to:** [Account Information — Overview](Account_Information.Overview.md) · [MT4Account — Master Overview](../MT4Account.Master.Overview.md)
