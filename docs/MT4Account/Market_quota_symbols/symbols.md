# ✅ Getting All Symbols

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
for e in s.SymbolNameInfos:
    print(e.symbol_name, e.symbol_index)
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

| Field             | Type               | Description                                           |
| ----------------- | ------------------ | ----------------------------------------------------- |
| `SymbolNameInfos` | `SymbolNameInfo[]` | Array of symbols with names and terminal indices. |

Each `SymbolNameInfo` element contains:

| Field          | Proto Type | Description                     |
| -------------- | ---------- | ------------------------------- |
| `symbol_name`  | `string`   | Symbol name (e.g., "EURUSD").   |
| `symbol_index` | `int32`    | Terminal index for this symbol. |

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
name_set = {e.symbol_name for e in s.SymbolNameInfos}

def known(sym: str) -> bool:
    return sym in name_set
```

### 2) Populate a dropdown model (sorted)

```python
s = await acct.symbols()
names = [e.symbol_name for e in s.SymbolNameInfos]
ui_model = sorted(names)  # feed into your UI
```

### 3) Refresh on demand

```python
# Re-pull on user request or daily schedule
s = await acct.symbols(deadline=some_deadline)
```
