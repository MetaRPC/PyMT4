# Many Quotes

> Latest quotes for several symbols in a single round-trip.

**API Information:**

* **Low-level API:** `MT4Account.quote_many(...)` (defined in `package/MetaRpcMT4/mt4_account.py`)
* **gRPC service:** `mt4_term_api.MarketInfo`
* **RPC:** `QuoteMany(QuoteManyRequest) -> QuoteManyReply`
* **Payload:** `QuoteManyData`

## 💬 Just the essentials

* **What it is.** A batch price read — one call returns a `QuoteData` for each requested symbol.
* **Why you need it.** One round-trip for a basket instead of N separate [quote](quote.md) calls.
* **When to use.** Dashboards, multi-symbol strategies, correlation/spread scans.

---

## 🎯 Purpose

* Quotes for a list of symbols at once
* Fewer round-trips than looping [quote](quote.md)
* Same per-symbol fields as a single quote

---

## Method Signature

```python
async def quote_many(
    self,
    symbols: list[str],
    deadline: Optional[datetime] = None,
    cancellation_event: Optional[asyncio.Event] = None,
)
```

**Request message:**

```protobuf
message QuoteManyRequest {
  repeated string symbols = 1;
}
```

**Payload message:**

```protobuf
message QuoteManyData {
  repeated QuoteData quotes = 1;   // one QuoteData per symbol
}

message QuoteData {
  string symbol = 1;
  double bid = 2;
  double ask = 3;
  Timestamp date_time = 4;
  Timestamp date_time_utc = 5;
  double high = 6;
  double low = 7;
}
```

---

## 🔽 Input

| Parameter | Type | Description |
|-----------|------|-------------|
| `symbols` | `list[str]` | Symbol names, e.g. `["EURUSD", "GBPUSD"]`. |
| `deadline` | datetime, optional | Absolute UTC deadline for the gRPC call. |
| `cancellation_event` | asyncio.Event, optional | Set to abort the request. |

---

## ⬆️ Output — `QuoteManyData`

| Field | Python Type | Description |
|-------|-------------|-------------|
| `quotes` | `list[QuoteData]` | One quote per requested symbol |

Each `QuoteData` has `symbol`, `bid`, `ask`, `high`, `low`, `date_time` / `date_time_utc` — see [quote](quote.md) for the field details.

---

## 🧩 Notes & Tips

* **Prefer this over a loop.** For several symbols, one `quote_many` beats N `quote` calls — fewer round-trips and a consistent snapshot.
* **Match by `symbol`, not position.** Index the result by `q.symbol` rather than assuming the response order matches your request order.
* **Same shape as a single quote** — spread is `ask − bid`, times are protobuf Timestamps.
* **Big baskets.** Requesting many symbols is fine, but keep the list to what you actually use.

---

## 🔗 Usage Examples

### 1) Quote a basket into a dict

Index by symbol so lookups are order-independent.

```python
async def quote_basket(account, symbols: list[str]) -> dict[str, tuple[float, float]]:
    data = await account.quote_many(symbols)
    by_symbol = {q.symbol: (q.bid, q.ask) for q in data.quotes}
    for sym in symbols:
        bid, ask = by_symbol.get(sym, (None, None))
        print(f"{sym:<8} bid={bid} ask={ask}")
    return by_symbol
```

### 2) Rank symbols by spread

Find which instruments are cheapest/most expensive to enter right now.

```python
async def spreads(account, symbols: list[str]):
    data = await account.quote_many(symbols)
    rows = sorted(((q.symbol, q.ask - q.bid) for q in data.quotes), key=lambda x: x[1])
    for sym, sp in rows:
        print(f"{sym:<8} spread={sp:.5f}")
    return rows
```

### 3) Refresh a watchlist snapshot

Pull the whole watchlist at once for a dashboard tick.

```python
WATCH = ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD"]

async def watchlist(account):
    data = await account.quote_many(WATCH)
    for q in data.quotes:
        mid = (q.bid + q.ask) / 2
        print(f"{q.symbol:<8} {mid:.5f}  (bid {q.bid:.5f} / ask {q.ask:.5f})")
```

---

## ⚠️ Pitfalls

* **Don't assume order.** Map results by `q.symbol`; the response list may not mirror the request order, and unknown symbols may be omitted.
* **Snapshot, not a stream.** For continuous updates use [on_symbol_tick](../5. Streaming_Methods/on_symbol_tick.md) with a list of symbols.
* **Spreads differ by symbol.** Compare in pips (via [symbol_params_many](symbol_params_many.md)) when ranking across instruments with different pip sizes.

---

## 🧪 Testing Suggestions

* **Coverage.** Requesting 3 valid symbols returns up to 3 quotes; each `symbol` is one of those requested.
* **Order-independence.** Build the dict and assert lookups by name succeed regardless of response order.
* **Parity with single quote.** A symbol's `quote_many` entry matches a separate [quote](quote.md) call taken at the same moment (within tick noise).

---

## 📚 See also

* [Quote](quote.md)
* [Quote History (OHLC)](quote_history.md)
* [On Symbol Tick (stream)](../5. Streaming_Methods/on_symbol_tick.md)

* **Back to:** [Symbols & Quotes — Overview](Symbols_Quotes.Overview.md) · [MT4Account — Master Overview](../MT4Account.Master.Overview.md)
