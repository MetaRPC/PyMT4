# ✅ Getting Multiple Quotes) — `quote_many`

> **Request:** retrieve the latest price snapshot for **multiple symbols at once** as `QuoteManyData`.
> Fastest way to fill UI tiles or pre‑validate orders across several instruments.

**Source files (SDK):**

* `MetaRpcMT4/mt4_account.py` — method `quote_many(...)`
* `MetaRpcMT4/mt4_term_api_market_info_pb2.py` — `QuoteMany*` and `QuoteData`

### RPC

* **Service:** `mt4_term_api.MarketInfo`
* **Method:** `QuoteMany(QuoteManyRequest) → QuoteManyReply`
* **Low‑level client:** `MarketInfoStub.QuoteMany(request, metadata, timeout)`
* **SDK wrapper:** `MT4Account.quote_many(symbols: list[str], deadline=None, cancellation_event=None) → QuoteManyData`

**Request message:** `QuoteManyRequest { symbols: string[] }`
**Reply message:** `QuoteManyReply { data: QuoteManyData }`

---

### 🔗 Code Example

```python
# Fetch quotes for a basket of symbols
rows = await acct.quote_many(["EURUSD", "GBPUSD", "XAUUSD"])

# rows: QuoteManyData
# Common patterns (depending on pb schema):
# 1) If the reply contains .items with QuoteData objects in request order:
for q in rows.items:  # list[QuoteData]
    print(f"{q.symbol} bid={q.bid:.5f} ask={q.ask:.5f}")

# 2) If the reply contains name+quote tuples (e.g., SymbolNameInfos):
# for e in rows.SymbolNameInfos:  # list[ { symbolName, data: QuoteData, index } ]
#     q = e.data
#     print(f"{e.symbolName} bid={q.bid:.5f} ask={q.ask:.5f}")
```

---

### Method Signature

```python
async def quote_many(
    self,
    symbols: list[str],
    deadline: datetime | None = None,
    cancellation_event: asyncio.Event | None = None,
) -> market_info_pb2.QuoteManyData
```

---

## 💬 Just the essentials

* **What it is.** A batched quote call that returns **bid/ask + OHLC** per symbol.
* **Why.** Reduces round‑trips versus calling `quote(...)` repeatedly; keeps UI grids snappy.
* **Ordering.** Reply typically preserves **request order** (via `index` or contiguous list semantics).

---

## 🔽 Input

| Parameter            | Type           | Description                                    |                                       |
| -------------------- | -------------- | ---------------------------------------------- | ------------------------------------- |
| `symbols`            | `list[str]`    | Symbols to fetch, e.g., `["EURUSD","XAUUSD"]`. |                                       |
| `deadline`           | `datetime      | None`                                          | Absolute per‑call deadline.           |
| `cancellation_event` | `asyncio.Event | None`                                          | Cooperative cancel for retry wrapper. |

---

## ⬆️ Output

### Payload: `QuoteManyData`

The concrete shape depends on the pb schema used in your build. Two common layouts:

**A) Contiguous list of `QuoteData`**

| Field   | Type          | Description                                |
| ------- | ------------- | ------------------------------------------ |
| `items` | `QuoteData[]` | Quotes in the **same order** as requested. |

**B) Name+Quote tuples (e.g., `SymbolNameInfos`)**

| Field             | Type                                              | Description                                                                   |
| ----------------- | ------------------------------------------------- | ----------------------------------------------------------------------------- |
| `SymbolNameInfos` | array of `{ index, symbolName, data: QuoteData }` | Each element holds the requested index, the symbol name, and the `QuoteData`. |

`QuoteData` fields (from `mt4_term_api_market_info_pb2.py`) typically include:

* `symbol: string`
* `bid: double`, `ask: double`
* `open: double`, `high: double`, `low: double`
* `spread: int32` (if provided)
* `date_time: google.protobuf.Timestamp`
* `tick_volume: int64`, `real_volume: int64`

> Check your `mt4_term_api_market_info_pb2.py` for the exact layout; both variants are used across builds.

---

## 🧱 Related enums (from pb)

This RPC **does not use method‑specific enums**.
Timeframe enums apply to `quote_history(...)`, not to `quote_many`.

---

### 🎯 Purpose

Use this method to:

* Populate price grids/tiles efficiently.
* Validate SL/TP distances across a basket before submitting multiple orders.
* Compute mid/spread metrics in bulk.

### 🧩 Notes & Tips

* Wrapper uses `execute_with_reconnect(...)` for transient gRPC retries.
* Keep the basket reasonable in hot paths; huge symbol lists will increase payload size and latency.
* Combine with `symbol_params_many(...)` for digits/point/SL‑TP constraints and with `tick_value_with_size(...)` for money‑per‑tick conversions.

**See also:**
`quote(...)` — single‑symbol snapshot.
`quote_history(...)` — historical bars with timeframe enum.
`symbol_params_many(...)` — constraints & trade/margin enums.

---

## Usage Examples

### 1) Compact grid printer

```python
rows = await acct.quote_many(["EURUSD","USDJPY","XAUUSD"])
# Variant A: contiguous items
for q in getattr(rows, 'items', []):
    print(f"{q.symbol:8} bid={q.bid:.5f} ask={q.ask:.5f}")

# Variant B: name+quote tuples
for e in getattr(rows, 'SymbolNameInfos', []):
    q = e.data
    print(f"{e.symbolName:8} bid={q.bid:.5f} ask={q.ask:.5f}")
```

### 2) Mid & spread per symbol

```python
rows = await acct.quote_many(["EURUSD","GBPUSD"])  # batch

def handle_quote(q):
    mid = (q.bid + q.ask) / 2
    spread = getattr(q, 'spread', None)
    return mid, spread

if hasattr(rows, 'items'):
    stats = { q.symbol: handle_quote(q) for q in rows.items }
elif hasattr(rows, 'SymbolNameInfos'):
    stats = { e.symbolName: handle_quote(e.data) for e in rows.SymbolNameInfos }

print(stats)
```

### 3) Validate SL/TP distance for all symbols

```python
# For each symbol: fetch params + quote; ensure planned SL distance >= StopsLevel
symbols = ["EURUSD","USDJPY","XAUUSD"]
qmany = await acct.quote_many(symbols)
params_all = await acct.symbol_params_many()  # beware: heavy; prefer single-symbol calls in hot paths

# Build a dict of StopsLevel/Point by symbol
pmap = { p.Symbol: p for p in params_all.params_info }

# Iterate quotes in either layout
def iter_quotes(reply):
    if hasattr(reply, 'items'):
        for q in reply.items:
            yield q.symbol, q
    else:
        for e in reply.SymbolNameInfos:
            yield e.symbolName, e.data

for sym, q in iter_quotes(qmany):
    p = pmap.get(sym)
    if not p:
        continue
    min_pts = max(p.StopsLevel, p.FreezeLevel)
    min_delta = min_pts * p.Point
    # Example: BUY SL must be at least min_delta below bid
    # sl_ok = (q.bid - planned_sl_distance) >= min_delta
```
