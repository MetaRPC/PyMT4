# using_account(login: int | None = None)

**TL;DR:** A sugary async context manager that temporarily sets the *session context* — such as which login, headers, and default trade parameters to use inside a block. Once you exit the block, everything is restored to its previous state. 🎯

---

## What it does

* Temporarily stores the current **login** and **default parameters** (like `magic`, `comment_prefix`, `deviation`) inside the `MT4Sugar` object.
* All sugar methods (`buy`, `sell`, `place_limit`, …) automatically inherit these defaults while inside the block.
* On exit, the previous values are fully restored (supports nesting).

---

## Why it matters

When your low-level layer expects `login` or metadata — this context fills them automatically.
If your LL doesn’t require login explicitly, it’s still a convenient *scoping* mechanism for defaults like `magic`, `comment_prefix`, or `deviation`. 🚀

It makes sugar methods cleaner and eliminates repetitive arguments in your orchestration code.

---

## How it works

1. Saves the current `login` and default values in `MT4Sugar`.
2. Replaces them with the temporary ones you passed to `using_account()`.
3. Inside the block, all sugar calls (`buy`, `sell`, …) pull from this temporary context.
4. On exit, everything is restored — safe and nested‑friendly.

---

## Example usage

```python

# 1) Scoped login and defaults for a sequence of operations
async with sugar.using_account(login=12345678, magic=9001, comment_prefix="[BOT] ", deviation=10):
    await sugar.ensure_connected()
    await sugar.buy("EURUSD", volume=0.1)
    await sugar.place_limit("EURUSD", side="sell", entry_price=1.09876, sl_pips=20, tp_pips=40)

# 2) Nested override for partial context
async with sugar.using_account(login=12345678, magic=9001):
    await sugar.buy("EURUSD", volume=0.1)
    async with sugar.using_account(magic=7777):
        await sugar.buy("EURUSD", volume=0.05)  # temporary magic=7777
    await sugar.buy("EURUSD", volume=0.1)       # back to magic=9001
```

---

## Implementation sketch

```python
from contextlib import asynccontextmanager
from typing import Any, Dict, Optional

class MT4Sugar:
    def __init__(self, svc):
        self._svc = svc
        self._ctx_login: Optional[int] = None
        self._ctx_defaults: Dict[str, Any] = {
            "magic": None,
            "comment_prefix": None,
            "deviation": None,
        }

    @asynccontextmanager
    async def using_account(self, login: Optional[int] = None, **defaults):
        """Temporarily set session context (login + defaults) for all sugar calls inside the block."""
        prev_login = self._ctx_login
        prev_defaults = self._ctx_defaults.copy()

        # Apply new values
        if login is not None:
            self._ctx_login = int(login)
        for k, v in defaults.items():
            if k in self._ctx_defaults:
                self._ctx_defaults[k] = v

        try:
            yield self
        finally:
            # Restore previous state
            self._ctx_login = prev_login
            self._ctx_defaults = prev_defaults

    def _apply_ctx(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Merge explicit params with current context."""
        out = dict(params)
        out.setdefault("login", self._ctx_login)

        # Merge defaults if not explicitly passed
        for key, val in self._ctx_defaults.items():
            if key in ("magic", "deviation") and out.get(key) is None and val is not None:
                out[key] = val

        # Comment prefix handling
        prefix = self._ctx_defaults.get("comment_prefix")
        if prefix:
            if out.get("comment"):
                if not out["comment"].startswith(prefix):
                    out["comment"] = f"{prefix}{out['comment']}"
            else:
                out["comment"] = prefix

        return out
```

---

## Notes

* **Nesting safe:** Each nested block restores its own previous state.
* **Predictable merge order:** Explicit parameters > context defaults > global defaults.
* **Not for connectivity or timeouts:** This handles *parameters*, not network or deadlines (those are `ensure_connected()` and `with_timeout()`).
* **Comment prefix:** Added once — avoids duplicate prefixes when chaining calls.

---

### ✅ Summary

✔️ Perfectly fits the sugar layer (`MT4Sugar`).
✔️ Implements scoped session context (login + defaults).
✔️ Safe, reversible, and composable with `ensure_connected()` and `with_timeout()`.
🐍 Clean syntax and predictable behavior — ideal for real trading orchestration code.
