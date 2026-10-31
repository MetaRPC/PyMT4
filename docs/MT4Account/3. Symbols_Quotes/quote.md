# Quote

> The latest quote for a single symbol — bid, ask, day high/low and timestamp.

**API Information:**

* **Low-level API:** `MT4Account.quote(...)` (defined in `package/MetaRpcMT4/mt4_account.py`)
* **gRPC service:** `mt4_term_api.MarketInfo`
* **RPC:** `Quote(QuoteRequest) -> QuoteReply`
* **Payload:** `QuoteData`

## 💬 Just the essentials

* **What it is.** A one-shot price read for one symbol: current `bid`/`ask`, session `high`/`low`, and the quote time.
* **Why you need it.** To read the market before placing or managing an order.
* **When to use.** Single reads. For a continuous feed, use [on_symbol_tick](../5. Streaming_Methods/on_symbol_tick.md).

---

## 🎯 Purpose

* Current bid / ask for a symbol
* Session high / low
* Quote timestamp (server / UTC)
* Compute spread and check tradability

---

## Method Signature

```python
async def quote(
    self,
    symbol: str,
    deadline: Optional[datetime] = None,
    cancellation_event: Optional[asyncio.Event] = None,
)
```

**Request message:**

```protobuf
message QuoteRequest {
  string symbol = 1;
}
```

**Payload message:**

```protobuf
message QuoteData {
  string symbol = 1;
  double bid = 2;
  double ask = 3;
  Timestamp date_time = 4;
  Timestamp date_time_utc = 5;
  double high = 6;      // session high
  double low = 7;       // session low
}
```

---

## 🔽 Input

| Parameter | Type | Description |
|-----------|------|-------------|
| `symbol` | `str` | Symbol name, e.g. `"EURUSD"`. |
| `deadline` | datetime, optional | Absolute UTC deadline for the gRPC call. |
| `cancellation_event` | asyncio.Event, optional | Set to abort the request. |

---

## ⬆️ Output — `QuoteData`

| Field | Python Type | Description |
|-------|-------------|-------------|
| `symbol` | `str` | Symbol |
| `bid` | `float` | Current bid (you sell at bid) |
| `ask` | `float` | Current ask (you buy at ask) |
| `high` / `low` | `float` | Session high / low |
| `date_time` / `date_time_utc` | `datetime` | Quote time (server / UTC) |

---

## 🧩 Notes & Tips

* **Spread = `ask − bid`.** In price terms; divide by the symbol's pip size to express it in pips.
* **Buy at ask, sell at bid.** A market buy fills near `ask`, a market sell near `bid` — the spread is the immediate cost of entry.
* **Time field is `date_time`** (not `time`). It's a protobuf Timestamp — convert with `.ToDatetime()`.
* **One symbol per call.** For several symbols use [quote_many](quote_many.md); for a live stream use [on_symbol_tick](../5. Streaming_Methods/on_symbol_tick.md).
* **Market Watch.** If a broker returns no price, the symbol may need selecting first — see [symbol_select](symbol_select.md).

---

## 🔗 Usage Examples

### 1) Bid / ask / spread

```python
async def show_quote(account, symbol: str = "EURUSD"):
    q = await account.quote(symbol)
    spread = q.ask - q.bid
    print(f"{q.symbol}: bid={q.bid:.5f} ask={q.ask:.5f} spread={spread:.5f}")
    return q
```

### 2) Only trade when the spread is tight

A guard you call before entering — skip entries when the spread is abnormally wide (news, illiquid hours).

```python
async def spread_ok(account, symbol: str, max_spread: float) -> bool:
    q = await account.quote(symbol)
    spread = q.ask - q.bid
    if spread > max_spread:
        print(f"{symbol}: spread {spread:.5f} > {max_spread:.5f} — skip entry")
        return False
    return True

# usage: if await spread_ok(account, "EURUSD", 0.00020): ...
```

### 3) Where is price in today's range?

Position the current mid inside the session high/low (0% = low, 100% = high).

```python
async def range_position(account, symbol: str = "EURUSD"):
    q = await account.quote(symbol)
    mid = (q.bid + q.ask) / 2
    span = q.high - q.low
    pct = (mid - q.low) / span * 100 if span > 0 else 0.0
    print(f"{symbol}: mid={mid:.5f} in [{q.low:.5f}, {q.high:.5f}] -> {pct:.0f}% of range")
    return pct
```

---

## ⚠️ Pitfalls

* **Snapshot, not a stream.** The quote is the price at call time; don't poll it in a tight loop — use [on_symbol_tick](../5. Streaming_Methods/on_symbol_tick.md) for live updates.
* **Spread is in price units.** Convert to pips with the symbol's pip size (see [symbol_params_many](symbol_params_many.md)) before comparing across symbols.
* **Unselected symbols.** Some brokers return an error/empty price until the symbol is in Market Watch.

---

## 🧪 Testing Suggestions

* **Happy path.** `ask >= bid`, both positive; `low <= bid <= high` (roughly) during the session.
* **Unknown symbol.** A bogus name surfaces an `ApiExceptionMT4`, not a silent zero.
* **Spread gate.** `spread_ok()` returns False for a tiny `max_spread` and True for a generous one.

---

## 📚 See also

* [Many Quotes](quote_many.md)
* [Quote History (OHLC)](quote_history.md)
* [On Symbol Tick (stream)](../5. Streaming_Methods/on_symbol_tick.md)

* **Back to:** [Symbols & Quotes — Overview](Symbols_Quotes.Overview.md) · [MT4Account — Master Overview](../MT4Account.Master.Overview.md)
