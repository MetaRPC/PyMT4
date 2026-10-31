# Stats + Equity + Trades

> Statistics, the equity curve **and** the trade list — everything a performance report needs, in a single round-trip.

**API Information:**

* **Low-level API:** `MT4Account.trade_stats_equity_history(...)` (defined in `package/MetaRpcMT4/mt4_account.py`)
* **gRPC service:** `mt4_term_api.TradeStats`
* **RPC:** `TradeStatsEquityHistory(TradeStatsEquityHistoryRequest) -> TradeStatsEquityHistoryReply`
* **Payload:** `StatsWithChartsData`

## 💬 Just the essentials

* **What it is.** A combined payload: the same `StatsData` as [trade_stats](trade_stats.md), the equity `charts` (same points as [equity_history](equity_history.md)), plus the closed and open trade lists.
* **Why you need it.** Build a full report (numbers + curve + trades) without three separate calls.
* **When to use.** Report/export screens where you want everything consistent and in one shot.

---

## 🎯 Purpose

* Headline statistics (`stats`)
* Equity-curve points (`charts`)
* Closed trades (`trades`) and currently open trades (`open_trades`)
* One round-trip for a complete report

---

## Method Signature

```python
async def trade_stats_equity_history(
    self,
    from_time: Optional[datetime] = None,
    exclude_same_bars: Optional[bool] = None,
    deadline: Optional[datetime] = None,
    cancellation_event: Optional[asyncio.Event] = None,
)
```

**Request message:**

```protobuf
message TradeStatsEquityHistoryRequest {
  string from = 1;              // ISO-8601 start; empty = full history
  string from_utc = 2;          // ISO-8601 start in UTC
  bool exclude_same_bars = 3;   // collapse consecutive equal equity points
}
```

**Payload message:**

```protobuf
message StatsWithChartsData {
  StatsData stats = 1;                         // see trade_stats
  repeated EquityPointData charts = 2;         // see equity_history
  repeated TradeHistoryItemData trades = 3;    // closed trades
  repeated TradeHistoryItemData open_trades = 4;
}

message TradeHistoryItemData {
  int64 ticket = 1;
  string symbol = 2;
  bool is_buy = 3;
  double lots = 4;
  double open_price = 5;
  double close_price = 6;
  Timestamp open_time = 7;
  Timestamp open_time_utc = 8;
  Timestamp close_time = 9;
  Timestamp close_time_utc = 10;
  double profit = 11;
  double commission = 12;
  double swap = 13;
  string comment = 14;
}
```

---

## 🔽 Input

| Parameter | Type | Description |
|-----------|------|-------------|
| `from_time` | datetime, optional | Start of the window; serialized to an ISO-8601 string. Omit for full history. |
| `exclude_same_bars` | bool, optional | Collapse consecutive equal equity points to shrink `charts`. |
| `deadline` | datetime, optional | Absolute UTC deadline for the gRPC call. |
| `cancellation_event` | asyncio.Event, optional | Set to abort the request. |

---

## ⬆️ Output — `StatsWithChartsData`

| Field | Python Type | Description |
|-------|-------------|-------------|
| `stats` | `StatsData` | Headline statistics — see [trade_stats](trade_stats.md) |
| `charts` | `list[EquityPointData]` | Equity-curve points — see [equity_history](equity_history.md) |
| `trades` | `list[TradeHistoryItemData]` | Closed trades |
| `open_trades` | `list[TradeHistoryItemData]` | Currently open trades |

Each `TradeHistoryItemData`:

| Field | Python Type | Description |
|-------|-------------|-------------|
| `ticket` | `int` | Trade ticket |
| `symbol` | `str` | Symbol |
| `is_buy` | `bool` | True = buy, False = sell |
| `lots` | `float` | Volume |
| `open_price` / `close_price` | `float` | Entry / exit price |
| `open_time` / `close_time` (+ `_utc`) | `datetime` | Entry / exit time |
| `profit` | `float` | Trade profit (excl. commission/swap) |
| `commission` / `swap` | `float` | Costs |
| `comment` | `str` | Order comment |

---

## 🧩 Notes & Tips

* **One call, three views.** `stats` is the summary, `charts` is the curve, `trades`/`open_trades` are the raw rows — everything stays consistent because it's a single snapshot.
* **Net result per trade** is `profit + commission + swap` (commission and swap are usually negative). Don't forget the costs when totalling.
* **`is_buy` is the side** — there's no separate order-type enum here; `True` = long, `False` = short.
* **Can be large.** `charts` and `trades` grow with account age — scope with `from_time` and `exclude_same_bars=True` for the curve.
* **Prefer this over three calls** when you need all three together; use the individual methods when you only need one.

---

## 🔗 Usage Examples

### 1) Full report in one round-trip

Pull everything and print a compact report header.

```python
async def full_report(account):
    r = await account.trade_stats_equity_history(exclude_same_bars=True)
    s = r.stats
    print("── Report ───────────────────────────────────")
    print(f" Profit factor : {s.profit_factor:.2f}")
    print(f" Trades        : {s.trades}  (open now: {len(r.open_trades)})")
    print(f" Growth        : {s.growth_percent:+.2f}%")
    print(f" Equity points : {len(r.charts)}")
    print(f" Closed trades : {len(r.trades)}")
```

### 2) Recent closed trades table

Show the last few closed trades with side, size and net result.

```python
async def recent_trades(account, n: int = 10):
    r = await account.trade_stats_equity_history()
    rows = sorted(r.trades, key=lambda t: t.close_time_utc.ToDatetime(), reverse=True)[:n]
    print(f"{'Ticket':>10} {'Sym':<8} {'Side':<5} {'Lots':>6} {'Net':>10}")
    for t in rows:
        net = t.profit + t.commission + t.swap
        side = "BUY" if t.is_buy else "SELL"
        print(f"{t.ticket:>10} {t.symbol:<8} {side:<5} {t.lots:>6.2f} {net:>10.2f}")
```

### 3) Open exposure right now

Summarize current open trades (count, lots, floating P/L) straight from `open_trades`.

```python
async def open_exposure(account):
    r = await account.trade_stats_equity_history()
    lots = sum(t.lots for t in r.open_trades)
    floating = sum(t.profit + t.commission + t.swap for t in r.open_trades)
    print(f"open trades: {len(r.open_trades)} | lots: {lots:.2f} | floating: {floating:+.2f}")
```

---

## ⚠️ Pitfalls

* **Heaviest call in the group.** It returns stats + curve + every trade — scope it (`from_time`, `exclude_same_bars`) and summarize rather than dumping all rows.
* **Costs are separate.** `profit` excludes `commission` and `swap`; add them for the true net.
* **Empty account.** `trades`, `open_trades` and `charts` can all be empty — guard before indexing.

---

## 🧪 Testing Suggestions

* **Happy path (demo with history).** `stats.trades` equals `len(r.trades)` for the same window; `charts` is non-empty.
* **Open vs closed.** `len(open_trades)` matches what [opened_orders](../2. Orders_History/opened_orders.md) reports.
* **Consistency.** `stats` here equals a separate [trade_stats](trade_stats.md) call over the same `from_time`.

---

## 📚 See also

* [Account Summary](account_summary.md)
* [Trade Statistics](trade_stats.md)
* [Unrealized P/L Extrema](trade_unrealized_pl.md)
* [Equity Curve](equity_history.md)

* **Back to:** [Account Information — Overview](Account_Information.Overview.md) · [MT4Account — Master Overview](../MT4Account.Master.Overview.md)
