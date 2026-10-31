# Symbols

> The full list of symbols available on the account — names and their index.

**API Information:**

* **Low-level API:** `MT4Account.symbols(...)` (defined in `package/MetaRpcMT4/mt4_account.py`)
* **gRPC service:** `mt4_term_api.MarketInfo`
* **RPC:** `Symbols(SymbolsRequest) -> SymbolsReply`
* **Payload:** `SymbolsData`

## 💬 Just the essentials

* **What it is.** Every instrument the broker exposes on this account, as `(name, index)` pairs.
* **Why you need it.** To discover tradable symbols at runtime and validate user input.
* **When to use.** On startup, when building symbol pickers, or before quoting/trading an unknown name.

---

## 🎯 Purpose

* Full symbol list from the broker
* Validate a symbol name before using it
* Build lookups (name → index) for other calls

---

## Method Signature

```python
async def symbols(
    self,
    deadline: Optional[datetime] = None,
    cancellation_event: Optional[asyncio.Event] = None,
)
```

**Request message:**

```protobuf
message SymbolsRequest {
}
```

**Payload message:**

```protobuf
message SymbolsData {
  repeated SymbolNameInfo SymbolNameInfos = 1;
}

message SymbolNameInfo {
  string symbol_name = 1;
  int32 symbol_index = 2;
}
```

---

## 🔽 Input

| Parameter | Type | Description |
|-----------|------|-------------|
| `deadline` | datetime, optional | Absolute UTC deadline for the gRPC call. |
| `cancellation_event` | asyncio.Event, optional | Set to abort the request. |

---

## ⬆️ Output — `SymbolsData`

| Field | Python Type | Description |
|-------|-------------|-------------|
| `SymbolNameInfos` | `list[SymbolNameInfo]` | All available symbols |

Each `SymbolNameInfo`:

| Field | Python Type | Description |
|-------|-------------|-------------|
| `symbol_name` | `str` | Symbol name (e.g. `"EURUSD"`) |
| `symbol_index` | `int` | Broker-assigned index |

---

## 🧩 Notes & Tips

* **Mind the field name.** The repeated field is `SymbolNameInfos` (PascalCase) — `data.SymbolNameInfos`, not `symbol_name_infos`.
* **Names are the broker's.** Symbols may carry suffixes (`EURUSD.m`, `EURUSD-ECN`) — never assume the bare `"EURUSD"` exists; check the list.
* **This is the catalog, not the rules.** For lot limits, digits and trade mode, use [symbol_params_many](symbol_params_many.md); for prices, use [quote](quote.md).
* **Market Watch.** Some brokers require a symbol be selected before quoting it — see [symbol_select](symbol_select.md).

---

## 🔗 Usage Examples

### 1) List and count

```python
async def list_symbols(account):
    data = await account.symbols()
    names = [s.symbol_name for s in data.SymbolNameInfos]
    print(f"{len(names)} symbols, e.g. {names[:8]}")
    return names
```

### 2) Does a symbol exist (allowing suffixes)?

Validate a desired symbol, tolerating broker suffixes.

```python
async def resolve_symbol(account, wanted: str = "EURUSD"):
    data = await account.symbols()
    names = [s.symbol_name for s in data.SymbolNameInfos]
    if wanted in names:
        return wanted
    # fall back to the first name that starts with the base symbol
    matches = [n for n in names if n.startswith(wanted)]
    if matches:
        print(f"'{wanted}' not found; using '{matches[0]}'")
        return matches[0]
    raise ValueError(f"no symbol matching {wanted!r}")
```

### 3) Name → index map

Build a lookup you can reuse elsewhere.

```python
async def symbol_index_map(account) -> dict[str, int]:
    data = await account.symbols()
    return {s.symbol_name: s.symbol_index for s in data.SymbolNameInfos}
```

---

## ⚠️ Pitfalls

* **Wrong field name.** It's `SymbolNameInfos` (capital S, plural) — a common `AttributeError` source.
* **Suffixes.** Don't hard-code `"EURUSD"`; resolve against the real list to survive brokers that use suffixes.
* **Catalog only.** No prices or trading rules here — pair with [quote](quote.md) / [symbol_params_many](symbol_params_many.md).

---

## 🧪 Testing Suggestions

* **Non-empty.** On a connected demo account, `SymbolNameInfos` has many entries and names are unique.
* **Resolution.** `resolve_symbol("EURUSD")` returns a real name present in the list.
* **Map integrity.** The name→index map has the same length as the symbol list (no duplicate names).

---

## 📚 See also

* [Quote](quote.md)
* [Symbol Parameters](symbol_params_many.md)
* [Symbol Select (Market Watch)](symbol_select.md)

* **Back to:** [Symbols & Quotes — Overview](Symbols_Quotes.Overview.md) · [MT4Account — Master Overview](../MT4Account.Master.Overview.md)
