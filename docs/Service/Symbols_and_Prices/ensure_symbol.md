# ensure_symbol(symbol)

**TL;DR:** Make sure the symbol exists and is ready; optionally preload/cache its trading params and (optionally) enforce that it’s tradeable. Caches per session for speed. ✅
 ensure_symbol(symbol, *, preload_params=True, require_trade_allowed=False, force_refresh=False)
---

## What it does

* Ensures the symbol is known/loaded on the backend (via `svc.symbols([symbol])`, falling back to a params query if needed).
* Optionally **preloads and caches** key parameters (e.g., `digits`, `point`, `min_lot`, `lot_step`, `max_lot`, `stops_level`, `freeze_level`, `contract_size`, `trade_allowed`).
* Optionally **validates** `trade_allowed` and raises if trading is not permitted.
* Supports **cache refresh** when you suspect stale broker limits. 🧠

---

## Why it matters

Most pricing/volume/SL-TP math depends on correct symbol metadata. By running `ensure_symbol()` up front, your sugary methods won’t trip over “Invalid stops”, odd lot steps, or mis-rounded prices. You get predictable behavior and fewer surprises. 🧯

---

## How it works (logic)

1. Normalize `symbol` (trim, uppercase).
2. Try `svc.symbols([symbol])` to ensure the symbol is available/activated.
3. If that fails, fall back to `_get_symbol_params(symbol)` to at least obtain parameters.
4. If any of the flags are set (`preload_params`, `require_trade_allowed`, `force_refresh`), fetch params and:

   * cache normalized fields (`point`, `digits`, aliases for PascalCase),
   * optionally raise if `trade_allowed is False`.
5. Return `None` (stateful guarantee); further getters (`point()`, `digits()`, `pip_size()`) read from the cache.

---

## Parameters

* `symbol: str` — symbol name (e.g., `"EURUSD"`).
* `preload_params: bool = True` — preload and cache params even when `symbols()` succeeds.
* `require_trade_allowed: bool = False` — if `True`, raise when trading is not allowed for this symbol.
* `force_refresh: bool = False` — bypass cache and refetch params from backend.

---

## Returns

`None` — ensures availability and (optionally) cached params as a side effect.

---

## Errors you can expect

* Backend/transport issues from `symbols()` or params query, mapped by your `map_backend_error(...)`.
* `RuntimeError("Trade not allowed …")` when `require_trade_allowed=True` and the backend reports `trade_allowed=False`.

---

## Example usage

```python

# 1) Default behavior: ensure exists + preload params
await sugar.ensure_symbol("EURUSD")

# 2) Strict validation: also require that symbol is tradeable
await sugar.ensure_symbol("USDJPY", require_trade_allowed=True)

# 3) Force a fresh read (e.g., after reconnect or broker-side change)
await sugar.ensure_symbol("XAUUSD", force_refresh=True)

# 4) Combined: strict + refresh
await sugar.ensure_symbol("US500", require_trade_allowed=True, force_refresh=True)
```

Downstream sugary methods can rely on cached getters:

```python
# comments in English only

pt = await sugar.point("EURUSD")     # normalized "point"
dg = await sugar.digits("EURUSD")    # normalized "digits"
pip = await sugar.pip_size("GBPUSD") # derived pip size (×10 for 3/5 digits)
```

---

## Implementation sketch

```python
async def ensure_symbol(
    self,
    symbol: str,
    *,
    preload_params: bool = True,
    require_trade_allowed: bool = False,
    force_refresh: bool = False,
) -> None:
    key = (symbol or "").strip().upper()
    if not key:
        raise ValueError("Symbol must be a non-empty string")

    # Step 1: try to ensure symbol is known/loaded
    try:
        _ = await self._svc.symbols([key])
    except Exception:
        try:
            _ = await self._get_symbol_params(key, force_refresh=force_refresh)
        except Exception as e:
            raise map_backend_error(e, context="symbols", payload={"symbol": key})

    # Step 2: optionally preload + validate
    if preload_params or require_trade_allowed or force_refresh:
        p = await self._get_symbol_params(key, force_refresh=force_refresh)
        if require_trade_allowed:
            ta = p.get("trade_allowed") if "trade_allowed" in p else p.get("TradeAllowed")
            if ta is False:
                raise RuntimeError(f"Trade not allowed for symbol '{key}'")
```

---

## Notes

* **Units:** Some backends expose `StopsLevel/FreezeLevel` in points/pips. We normalize and keep raw fields; ensure your SL/TP math uses the right unit.
* **Cache invalidation:** Clear the symbol cache on account/server change (e.g., after `reconnect()` hook) to avoid stale `min_lot/lot_step`.
* **Activation vs. params:** `symbols([symbol])` may “activate” a symbol in some terminals. If unavailable, params query still allows you to proceed with proper math.
* **Derived fields:** If `point/digits` are missing, we derive them (e.g., from each other) with safe fallbacks.

---

### ✅ Summary

✔️ Ensures symbol availability.
✔️ Preloads and caches essential parameters.
✔️ Optionally enforces `trade_allowed`.
✔️ Plays nicely with other sugar helpers (`ensure_connected`, `with_timeout`, `using_account`). 🚀
