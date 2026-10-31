# Trade Statistics

> Aggregated trade statistics — profit factor, win/loss, drawdowns, expectancy and a per-market breakdown, in one call.

**API Information:**

* **Low-level API:** `MT4Account.trade_stats(...)` (defined in `package/MetaRpcMT4/mt4_account.py`)
* **gRPC service:** `mt4_term_api.TradeStats`
* **RPC:** `TradeStats(TradeStatsRequest) -> TradeStatsReply`
* **Payload:** `StatsData`

## 💬 Just the essentials

* **What it is.** A rollup of your trading performance: headline ratios, drawdowns, and a breakdown per market.
* **Why you need it.** The numbers a dashboard or weekly review needs — without computing them yourself from raw history.
* **When to use.** Reporting, periodic performance checks, "how am I doing?" screens.

---

## 🎯 Purpose

* Profit factor, expectancy, Sharpe ratio, GHPR, Z-score
* Win/loss counts and percentages
* Balance & equity drawdowns (absolute and relative)
* Per-market breakdown (trades, lots, profit, win rate)
* Account totals: deposits, withdrawals, growth %

---

## Method Signature

```python
async def trade_stats(
    self,
    from_time: Optional[datetime] = None,
    deadline: Optional[datetime] = None,
    cancellation_event: Optional[asyncio.Event] = None,
)
```

**Request message:**

```protobuf
message TradeStatsRequest {
  string from = 1;       // ISO-8601 start; empty = full history
  string from_utc = 2;   // ISO-8601 start in UTC
}
```

**Payload message (top level):**

```protobuf
message StatsData {
  TradeSummaryData summary = 1;              // open/day/week/month/total profit
  double max_balance_drawdown_raw = 2;
  double max_balance_drawdown_relative = 3;  // percent
  double max_equity_drawdown_raw = 4;
  double max_equity_drawdown_relative = 5;   // percent
  repeated MarketTradeCountData markets = 6; // per-symbol breakdown
  ProfitabilityData profitability = 7;       // won/lost counts & percentages
  double pips = 8;
  double lots = 9;
  double comissions = 10;
  AveragePipsUsdData average_win = 11;
  AveragePipsUsdData average_lost = 12;
  WonData longs_won = 13;
  WonData shorts_won = 14;
  ProfitData best_trade = 15;
  ProfitData worst_trade = 16;
  ProfitData best_trade_pips = 17;
  ProfitData worst_trade_pips = 18;
  string average_trade_length = 19;
  double profit_factor = 20;
  double standard_deviation = 21;
  double sharpe_ratio = 22;
  ZScoreData z_score = 23;
  ExpectancyData expectancy = 24;            // pips & dollar
  double ghpr = 25;                          // geometric holding period return
  int64 trades = 26;
  double growth_percent = 27;
  double deposits = 28;
  double withdrawals = 29;
}
```

---

## 🔽 Input

| Parameter | Type | Description |
|-----------|------|-------------|
| `from_time` | datetime, optional | Start of the window; serialized to an ISO-8601 string. Omit for full history. |
| `deadline` | datetime, optional | Absolute UTC deadline for the gRPC call. |
| `cancellation_event` | asyncio.Event, optional | Set to abort the request. |

---

## ⬆️ Output — `StatsData`

Headline **scalars**:

| Field | Python Type | Description |
|-------|-------------|-------------|
| `profit_factor` | `float` | Gross profit ÷ gross loss (> 1 is profitable) |
| `expectancy` | `ExpectancyData` | Expected result per trade (`.pips`, `.dollar`) |
| `sharpe_ratio` | `float` | Risk-adjusted return |
| `ghpr` | `float` | Geometric holding-period return |
| `standard_deviation` | `float` | Std-dev of trade results |
| `pips` / `lots` / `comissions` | `float` | Total pips, lots traded, commissions |
| `trades` | `int` | Total number of trades |
| `growth_percent` | `float` | Account growth, % |
| `deposits` / `withdrawals` | `float` | Totals in deposit currency |
| `max_balance_drawdown_raw` | `float` | Worst balance drawdown (money) |
| `max_balance_drawdown_relative` | `float` | Worst balance drawdown (%) |
| `max_equity_drawdown_raw` | `float` | Worst equity drawdown (money) |
| `max_equity_drawdown_relative` | `float` | Worst equity drawdown (%) |
| `average_trade_length` | `str` | Average holding time |

Nested **submessages**:

| Field | Message | Key fields |
|-------|---------|-----------|
| `summary` | `TradeSummaryData` | `open_trades`, `open_profit`, `day_profit`, `week_profit`, `month_profit`, `total_profit` |
| `profitability` | `ProfitabilityData` | `won_trades`, `won_trades_percent`, `lost_trades`, `lost_trades_percent` |
| `markets` (repeated) | `MarketTradeCountData` | `market_name`, `count`, `lots`, `profit`, `win_rate`, `won_count`, `lost_count` |
| `average_win` / `average_lost` | `AveragePipsUsdData` | `average_pips`, `average_usd` |
| `longs_won` / `shorts_won` | `WonData` | `won_count`, `all`, `won_persent` |
| `best_trade` / `worst_trade` | `ProfitData` | `tiket`, `date`, `profit` |

---

## 🧩 Notes & Tips

* **`summary` is the "today/this week/this month" block** — perfect for a compact P/L widget, separate from the all-time ratios.
* **Drawdowns come in two flavours:** balance vs equity, each as raw money and relative %. Equity drawdown is usually the one that matters for risk.
* **`markets` is your per-symbol attribution** — iterate it to see which instruments actually make or lose money.
* **Watch the proto spelling.** Field names carry the server's spelling: `comissions`, `tiket`, `won_persent` — use them as-is.
* **`from_time` trims the window.** Omit it for the full account history; pass it to scope stats to a period (e.g. this month) — it is sent as an ISO-8601 string.
* **Pairs with [equity_history](equity_history.md).** Use `trade_stats` for the numbers and `equity_history` for the curve, or [trade_stats_equity_history](trade_stats_equity_history.md) to get both in one round-trip.

---

## 🔗 Usage Examples

### 1) Weekly performance report

Turn the stats into a readable report line — the kind you log or post to a channel.

```python
async def performance_report(account):
    s = await account.trade_stats()
    p = s.profitability
    win_rate = p.won_trades_percent
    print("── Performance ──────────────────────────────")
    print(f" Trades        : {s.trades}  (win {win_rate:.1f}%)")
    print(f" Profit factor : {s.profit_factor:.2f}")
    print(f" Expectancy    : {s.expectancy.dollar:+.2f} / trade")
    print(f" Growth        : {s.growth_percent:+.2f}%")
    print(f" Max DD (eq)   : {s.max_equity_drawdown_relative:.1f}%"
          f"  ({s.max_equity_drawdown_raw:,.2f})")
    print(f" This week     : {s.summary.week_profit:+,.2f}")
```

### 2) Which markets make money?

Rank the per-market breakdown so you can cut the losers and size up the winners.

```python
async def markets_by_profit(account, top: int = 5):
    s = await account.trade_stats()
    rows = sorted(s.markets, key=lambda m: m.profit, reverse=True)
    print(f"{'Symbol':<10}{'Trades':>7}{'Win%':>7}{'Profit':>12}")
    for m in rows[:top]:
        print(f"{m.market_name:<10}{m.count:>7}{m.win_rate:>6.1f}%{m.profit:>12,.2f}")
    worst = rows[-1] if rows else None
    if worst and worst.profit < 0:
        print(f"Worst: {worst.market_name} ({worst.profit:,.2f}) — review or disable")
```

### 3) Month-to-date health check

Scope the stats to the current month and flag a weak profit factor.

```python
from datetime import datetime

async def month_health(account, min_profit_factor: float = 1.2) -> bool:
    start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    s = await account.trade_stats(from_time=start)
    ok = s.profit_factor >= min_profit_factor
    print(f"MTD: trades={s.trades} PF={s.profit_factor:.2f} "
          f"result={s.summary.month_profit:+,.2f} -> {'OK' if ok else 'WEAK'}")
    return ok
```

---

## ⚠️ Pitfalls

* **Empty history.** A brand-new account with no closed trades returns zeroed stats — guard divisions (e.g. don't trust `profit_factor` when `trades == 0`).
* **Potentially heavy.** The `markets` list grows with the number of traded symbols; it's fine to summarize rather than print everything.
* **Spelling quirks.** `comissions`, `tiket`, `won_persent` are the real field names — a typo-looking attribute access is correct.
* **Scope awareness.** Numbers reflect the `from_time` window (or all history if omitted) — don't compare a month-scoped call with an all-time one.

---

## 🧪 Testing Suggestions

* **Happy path (demo with history).** `trades > 0`, `profit_factor` finite, `len(markets) >= 1`.
* **Fresh account.** With no closed trades, assert the call still succeeds and your report handles zeros without dividing by zero.
* **Windowing.** A `from_time` of today vs a year ago returns different `trades` counts; assert the scoped count ≤ the full count.

---

## 📚 See also

* [Account Summary](account_summary.md)
* [Unrealized P/L Extrema](trade_unrealized_pl.md)
* [Equity Curve](equity_history.md)
* [Stats + Equity + Trades](trade_stats_equity_history.md)

* **Back to:** [Account Information — Overview](Account_Information.Overview.md) · [MT4Account — Master Overview](../MT4Account.Master.Overview.md)
