# ✅ Getting All Symbols — `symbols`

> **Request:** retrieve the full list of **tradable symbols** from the connected terminal as `SymbolsData`.
> Use it to populate dropdowns, build watchlists, and validate symbol names.

**Source files (SDK):**

* `MetaRpcMT4/mt4_account.py` — method `symbols(...)`
* `MetaRpcMT4/mt4_term_api_market_info_pb2.py` — `Symbols*` messages (`SymbolsRequest`, `SymbolsReply`, `SymbolsData`)

### RPC

* **Service:** `mt4_term_api.MarketInfo`
* **Method:** `Symbols(SymbolsRequest) → SymbolsReply`
* **Low‑level client:** `MarketInfoStub.Symbols(request, metadata, timeout)`
* **SDK wrapper:** `MT4Account.symbols(deadline=None, cancellation_event=None) → SymbolsData`

**Request message:** `SymbolsRequest {}`
**Reply message:** `SymbolsReply { data: SymbolsData }`

---

### 🔗 Code Example

```python
# Fetch every tradable symbol from the terminal
s = await acct.symbols()
# Depending on pb layout:
# (A) If the reply exposes a flat list of entries with name+index
for e in s.items:  # or s.SymbolNameInfos
    # e.symbol (str), e.index (int)
    print(e.symbol, e.index)

# (B) If the reply is just names and you need a set for fast lookups
names = { getattr(e, 'symbol', None) or getattr(e, 'symbolName', None) for e in getattr(s, 'items', []) }
```

---

### Method Signature

```python
async def symbols(
    self,
    deadline: datetime | None = None,
    cancellation_event: asyncio.Event | None = None,
) -> market_info_pb2.SymbolsData
```

---

## 💬 Just the essentials

* **What it is.** A **terminal‑side registry** of available symbols.
* **Why.** Populate UI lists, validate user input, and drive bulk market calls (`quote_many`, `symbol_params_many`).
* **When to call.** At startup and then **cache**; refresh on user demand or daily.

---

## 🔽 Input

No required parameters.

| Parameter            | Type           | Description |                                       |
| -------------------- | -------------- | ----------- | ------------------------------------- |
| `deadline`           | `datetime      | None`       | Absolute per‑call deadline.           |
| `cancellation_event` | `asyncio.Event | None`       | Cooperative cancel for retry wrapper. |

---

## ⬆️ Output

### Payload: `SymbolsData`

Typical layout (per pb build): a list of name/index pairs.

| Field   | Type                               | Description                                  |
| ------- | ---------------------------------- | -------------------------------------------- |
| `items` | `[{ symbol: string, index: int }]` | Symbol name and terminal index for each row. |

> Field container name may vary (`items`, `SymbolNameInfos`, etc.). The SDK returns `res.data`.

---

## 🧱 Related enums (from pb)

This RPC **does not use method‑specific enums**.

---

### 🎯 Purpose

Use this method to:

* Build **autocomplete/watchlists** reliably from server truth.
* Validate symbol inputs before calling order/market RPCs.
* Map **symbol → index** if required by other endpoints.

### 🧩 Notes & Tips

* Wrapper uses `execute_with_reconnect(...)` for transient gRPC retries.
* **Cache aggressively**; the list is large and rarely changes intra‑session.
* If your integration supports **hidden**/non‑tradeable symbols, filter them at UI level.

**See also:**
`symbol_params_many(...)` — per‑symbol trading constraints and enums.
`quote_many(...)` — batch price snapshots for multiple symbols.
`opened_orders(...)` — positions by symbol.

---

## Usage Examples

### 1) Build a fast lookup set

```python
s = await acct.symbols()
name_set = { getattr(e, 'symbol', None) or getattr(e, 'symbolName', None) for e in getattr(s, 'items', []) }

def known(sym: str) -> bool:
    return sym in name_set
```

### 2) Populate a dropdown model (sorted)

```python
s = await acct.symbols()
rows = getattr(s, 'items', [])
names = [getattr(e, 'symbol', None) or getattr(e, 'symbolName', None) for e in rows]
ui_model = sorted(filter(None, names))  # feed into your UI
```

### 3) Refresh on demand

```python
# Re-pull on user request or daily schedule
s = await acct.symbols(deadline=some_deadline)
```
