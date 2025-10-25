# ensure_connected()

**TL;DR:** Make sure the MT4 session is alive; if it’s not, reconnect and verify again. ✅

## What it does

* Performs a lightweight health check via `svc.get_headers()` (fast and cheap).
* If the check fails, it runs `await svc.reconnect()` and emits the `on_reconnect` hook.
* Verifies connectivity again with `get_headers()`.
* On failure, raises a meaningful, mapped error (so the caller sees a clear reason, not a low‑level traceback).

## Why it matters

Use this before any “sugary” method (`buy`, `sell`, `close_all`, …) so you don’t worry about the connection state mid‑flow. `ensure_connected()` guarantees a live session or fails fast with a clear error—fewer random timeouts and fewer surprises. 🧯

## How it works (logic)

1. Try `get_headers()` → if OK, return.
2. If not OK → `await reconnect()` → emit `on_reconnect`.
3. Try `get_headers()` again → if OK, return.
4. If still not OK → raise a mapped exception.

> Note: This method **does not** perform a cold connect (`connect_by_*`). It assumes an initial session was established earlier and that `reconnect()` knows how to recover.

## Returns

`None` — side effect only: guarantees a working session or throws.

## Errors you can expect

* Reconnection/availability errors wrapped by your `map_backend_error(..., context="reconnect")` implementation.

---

## Usage

Call it right before any networked action:

```py
# comments in English only

async def buy(self, symbol: str, volume: float):
    await self.ensure_connected()           # guarantee live session
    return await self._svc.order_buy(symbol=symbol, volume=volume)
```

Or as a universal pre‑hook in your orchestrations:

```py

async def place_bracket(self, symbol: str, side: str, entry: float, sl_pips: int, tp_pips: int):
    await self.ensure_connected()
    # ... validations and RPC calls ...
```

> If you need a **cold start** when there is absolutely no session, wire that into your bootstrap (initial `connect_by_*`) or teach `svc.reconnect()` to attempt a cold path using stored policy.

---

## Sketch implementation

```py

from typing import Any

class MT4Sugar:
    def __init__(self, svc, hooks, log, map_backend_error):
        """
        svc: low-level service (wraps MT4Account RPCs)
        hooks: callback hub with .emit(event, payload)
        log: logger
        map_backend_error: function to map backend exceptions to API exceptions
        """
        self._svc = svc
        self.hooks = hooks
        self.log = log
        self._map = map_backend_error

    async def ensure_connected(self) -> None:
        """Ensure there is an active session. Reconnect if needed, then re-check."""
        # 1) quick health-check (cheap)
        try:
            _ = self._svc.get_headers()   # lightweight "ping"
            return
        except Exception:
            pass

        # 2) try fast reconnect
        try:
            await self._svc.reconnect()
            await self.hooks.emit("on_reconnect", {"source": "ensure_connected"})
            # 3) confirm connectivity again
            _ = self._svc.get_headers()
            return
        except Exception as e2:
            self.log.error("Reconnect failed", exc_info=False)
            # 4) raise a meaningful, mapped error
            raise self._map(e2, context="reconnect")
```

---

## FAQ

**Why `get_headers()` instead of `account_summary()`?**
Because it’s the lightest fast‑path. The goal is to confirm “is the session alive?” without adding load.

**What if the socket is alive but the terminal is stuck?**
That’s rare in this stack. If you need a stronger readiness probe, create a **separate** method (e.g., `ensure_ready(deadline=...)`) that calls `account_summary()` with a short timeout. Keep `ensure_connected()` lean and predictable. ⚡

**Where should cold‑connect happen?**
In bootstrap (initial `connect_by_*`) or inside `svc.reconnect()` (extended to attempt a cold path using saved policy). `ensure_connected()` is intentionally not about that.

