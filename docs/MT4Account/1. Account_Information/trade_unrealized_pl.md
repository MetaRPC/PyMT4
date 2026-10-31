# Unrealized P/L Extrema

> For each open order, the **best and worst floating P/L** it has reached (with timestamps) — classic MFE / MAE excursion data.

**API Information:**

* **Low-level API:** `MT4Account.trade_unrealized_pl(...)` (defined in `package/MetaRpcMT4/mt4_account.py`)
* **gRPC service:** `mt4_term_api.TradeStats`
* **RPC:** `TradeUnrealizedPL(TradeUnrealizedPLRequest) -> TradeUnrealizedPLReply`
* **Payload:** `TradeUnrealizedPLData`

## 💬 Just the essentials

* **What it is.** Per open order, the maximum favorable (`max_unrealized_pl`) and maximum adverse (`min_unrealized_pl`) floating P/L reached since it opened, each with a timestamp.
* **Why you need it.** MFE/MAE analysis — how far trades run in your favor before you exit, and how deep they dip before recovering.
* **When to use.** Tuning stop-loss / take-profit placement and trailing logic from real behaviour.

---

## 🎯 Purpose

* See the peak profit each open order reached (MFE)
* See the deepest drawdown each open order survived (MAE)
* Timestamps of both extrema (server and UTC)
* Drive data-informed SL/TP and trailing decisions

---

## Method Signature

```python
async def trade_unrealized_pl(
    self,
    from_time: Optional[datetime] = None,
    deadline: Optional[datetime] = None,
    cancellation_event: Optional[asyncio.Event] = None,
)
```

**Request message:**

```protobuf
message TradeUnrealizedPLRequest {
  string from = 1;       // ISO-8601 start; empty = full history
  string from_utc = 2;   // ISO-8601 start in UTC
}
```

**Payload message:**

```protobuf
message TradeUnrealizedPLData {
  repeated TradeUnrealizedExtremaData extrema = 1;
}

message TradeUnrealizedExtremaData {
  int64 ticket = 1;
  string symbol = 2;
  Timestamp max_unrealized_time = 3;      // when peak profit was reached
  Timestamp max_unrealized_time_utc = 4;
  double max_unrealized_pl = 5;           // MFE — best floating P/L
  Timestamp min_unrealized_time = 6;      // when deepest loss was reached
  Timestamp min_unrealized_time_utc = 7;
  double min_unrealized_pl = 8;           // MAE — worst floating P/L
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

## ⬆️ Output — `TradeUnrealizedPLData`

| Field | Python Type | Description |
|-------|-------------|-------------|
| `extrema` | `list[TradeUnrealizedExtremaData]` | One entry per order with excursion data |

Each `TradeUnrealizedExtremaData`:

| Field | Python Type | Description |
|-------|-------------|-------------|
| `ticket` | `int` | Order ticket |
| `symbol` | `str` | Symbol |
| `max_unrealized_pl` | `float` | **MFE** — highest floating P/L reached |
| `max_unrealized_time` / `_utc` | `datetime` | When the MFE occurred (server / UTC) |
| `min_unrealized_pl` | `float` | **MAE** — lowest floating P/L reached |
| `min_unrealized_time` / `_utc` | `datetime` | When the MAE occurred (server / UTC) |

---

## 🧩 Notes & Tips

* **MFE vs MAE.** `max_unrealized_pl` is how good the trade got (Maximum Favorable Excursion); `min_unrealized_pl` is how bad it got (Maximum Adverse Excursion). Both are *floating* values seen while the order was open, not the realized result.
* **Use it to size stops.** If winners routinely dip to −15 pips (MAE) before running, a −10 pip stop was too tight. If MFE far exceeds your actual exits, your TP is leaving money on the table.
* **Signs matter.** `max_unrealized_pl` is usually ≥ 0 and `min_unrealized_pl` usually ≤ 0, but a trade that was never in profit can have a negative MFE — don't assume positivity.
* **Timestamps are protobuf Timestamps** — convert with `.ToDatetime()`.
* **`from_time` scopes the set**; omit for everything available.

---

## 🔗 Usage Examples

### 1) MFE / MAE table

Show, per order, how far it ran in your favor and how deep it dipped.

```python
async def excursion_table(account):
    data = await account.trade_unrealized_pl()
    print(f"{'Ticket':>10} {'Symbol':<8} {'MFE':>10} {'MAE':>10}")
    for e in data.extrema:
        print(f"{e.ticket:>10} {e.symbol:<8} {e.max_unrealized_pl:>10.2f} {e.min_unrealized_pl:>10.2f}")
```

### 2) Were my stops too tight?

Find winners that first went underwater — their MAE tells you the stop distance they actually needed.

```python
async def stop_pressure(account, threshold: float = -10.0):
    data = await account.trade_unrealized_pl()
    deep = [e for e in data.extrema if e.min_unrealized_pl <= threshold]
    deep.sort(key=lambda e: e.min_unrealized_pl)  # deepest first
    print(f"{len(deep)} order(s) dipped below {threshold:.2f} before now:")
    for e in deep[:10]:
        when = e.min_unrealized_time.ToDatetime()
        print(f"  #{e.ticket} {e.symbol}: MAE {e.min_unrealized_pl:.2f} at {when:%Y-%m-%d %H:%M}")
```

### 3) Profit give-back detector

Highlight orders that reached a solid peak — candidates where a trailing stop or earlier TP would have locked in more.

```python
async def giveback(account, min_peak: float = 20.0):
    data = await account.trade_unrealized_pl()
    for e in data.extrema:
        if e.max_unrealized_pl >= min_peak:
            print(f"#{e.ticket} {e.symbol}: peaked at {e.max_unrealized_pl:.2f} "
                  f"(worst {e.min_unrealized_pl:.2f}) — review exit/trailing")
```

---

## ⚠️ Pitfalls

* **Open orders only.** These extrema describe currently-open orders' journey so far; for closed-trade results use [orders_history](../2. Orders_History/orders_history.md) or [trade_stats](trade_stats.md).
* **Floating, not realized.** A high MFE doesn't mean you captured it — that's exactly the point of the give-back check.
* **Empty when flat.** With no open orders, `extrema` is empty — handle the zero case.

---

## 🧪 Testing Suggestions

* **With open orders.** `extrema` is non-empty; for each entry `max_unrealized_pl >= min_unrealized_pl`.
* **Flat account.** Returns an empty `extrema` list without error.
* **Timestamp sanity.** `min_unrealized_time` / `max_unrealized_time` convert to datetimes that fall after the order's open time.

---

## 📚 See also

* [Account Summary](account_summary.md)
* [Trade Statistics](trade_stats.md)
* [Equity Curve](equity_history.md)
* [Stats + Equity + Trades](trade_stats_equity_history.md)

* **Back to:** [Account Information — Overview](Account_Information.Overview.md) · [MT4Account — Master Overview](../MT4Account.Master.Overview.md)
