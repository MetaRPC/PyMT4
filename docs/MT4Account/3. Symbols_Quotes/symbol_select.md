# Symbol Select (Market Watch)

> Add a symbol to, or remove it from, Market Watch.

**API Information:**

* **Low-level API:** `MT4Account.symbol_select(...)` (defined in `package/MetaRpcMT4/mt4_account.py`)
* **gRPC service:** `mt4_term_api.MarketInfo`
* **RPC:** `SymbolSelect(SymbolSelectRequest) -> SymbolSelectReply`
* **Payload:** `SymbolSelectData`

## 💬 Just the essentials

* **What it is.** Toggle a symbol in the terminal's Market Watch (select = add, deselect = remove).
* **Why you need it.** Some brokers won't quote or trade a symbol until it's selected.
* **When to use.** Before quoting/trading a symbol that might not be in Market Watch yet.

---

## 🎯 Purpose

* Add a symbol to Market Watch
* Remove a symbol from Market Watch
* Confirm the operation via `success`

---

## Method Signature

```python
async def symbol_select(
    self,
    symbol: str,
    select: bool = True,
    deadline: Optional[datetime] = None,
    cancellation_event: Optional[asyncio.Event] = None,
)
```

**Request message:**

```protobuf
message SymbolSelectRequest {
  string symbol = 1;
  bool select = 2;     // True = add to Market Watch, False = remove
}
```

**Payload message:**

```protobuf
message SymbolSelectData {
  bool success = 1;
}
```

---

## 🔽 Input

| Parameter | Type | Description |
|-----------|------|-------------|
| `symbol` | `str` | Symbol name. |
| `select` | `bool` | `True` to add to Market Watch, `False` to remove. Default `True`. |
| `deadline` | datetime, optional | Absolute UTC deadline for the gRPC call. |
| `cancellation_event` | asyncio.Event, optional | Set to abort the request. |

---

## ⬆️ Output — `SymbolSelectData`

| Field | Python Type | Description |
|-------|-------------|-------------|
| `success` | `bool` | True if the select/deselect was applied |

---

## 🧩 Notes & Tips

* **Select before you quote/trade** symbols that aren't in Market Watch — some brokers reject data/orders for unselected symbols.
* **Deselect to tidy up** (`select=False`), but don't remove a symbol that still has open orders or active subscriptions.
* **Idempotent-ish.** Selecting an already-selected symbol just returns `success=True`.
* **Validate the name first** with [symbols](symbols.md) — selecting a non-existent symbol fails.

---

## 🔗 Usage Examples

### 1) Ensure a symbol is ready to use

A helper to call before quoting/trading an unfamiliar symbol.

```python
async def ensure_selected(account, symbol: str) -> bool:
    res = await account.symbol_select(symbol, True)
    if not res.success:
        print(f"could not select {symbol}")
    return res.success

# usage:
# if await ensure_selected(account, "XAUUSD"):
#     q = await account.quote("XAUUSD")
```

### 2) Add then remove

```python
async def temp_select(account, symbol: str):
    await account.symbol_select(symbol, True)
    q = await account.quote(symbol)
    print(f"{symbol}: bid={q.bid} ask={q.ask}")
    await account.symbol_select(symbol, False)   # tidy up
```

### 3) Prepare a watchlist

Select everything a strategy needs up front.

```python
async def prepare_watchlist(account, symbols: list[str]):
    ok = {}
    for s in symbols:
        ok[s] = (await account.symbol_select(s, True)).success
    missing = [s for s, good in ok.items() if not good]
    if missing:
        print("failed to select:", missing)
    return ok
```

---

## ⚠️ Pitfalls

* **Invalid symbol.** Selecting a name that isn't on the account fails (or raises) — resolve it against [symbols](symbols.md) first.
* **Don't deselect active symbols.** Removing a symbol with open orders or live streams can disrupt them.
* **Selection ≠ data guarantee.** `success=True` means it's in Market Watch; the first quote may still lag a moment while it populates.

---

## 🧪 Testing Suggestions

* **Select a valid symbol.** Returns `success=True`; a following [quote](quote.md) works.
* **Deselect.** `select=False` returns `success=True` for a selected symbol.
* **Invalid name.** A bogus symbol returns `success=False` or raises `ApiExceptionMT4`.

---

## 📚 See also

* [Symbols](symbols.md)
* [Quote](quote.md)
* [Symbol Parameters](symbol_params_many.md)

* **Back to:** [Symbols & Quotes — Overview](Symbols_Quotes.Overview.md) · [MT4Account — Master Overview](../MT4Account.Master.Overview.md)
