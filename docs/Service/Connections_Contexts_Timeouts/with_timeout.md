# with_timeout(seconds)

**TL;DR:** Temporarily set a per‑call timeout for all sugar calls executed **inside** the context block. Enter → all RPCs honor the deadline; exit → the previous timeout is restored. ⏱️

---

## What it does

* Temporarily assigns a timeout value (in seconds) to `self._call_timeout`.
* Any call using `await self.call(...)` inside the block is automatically wrapped with `asyncio.timeout(...)`.
* Restores the previous timeout value on exit (supports nesting).

---

## Why it matters

It provides a **scoped timeout** mechanism — perfect when you need a stricter deadline for a short section of your workflow (for example, fast trading checks or temporary network throttling) without changing the global configuration. 🚀

---

## How it works

1. On entering the block, the current timeout is saved.
2. The new timeout (e.g. 3.0 seconds) is set.
3. Every sugar call inside the block that uses `self.call()` will automatically enforce this timeout.
4. When the block ends, the previous timeout is restored.

---

## Example usage

```python
# comments in English only

sugar = MT4Sugar(svc)

async with sugar.with_timeout(3.0):
    await sugar.ensure_connected()
    await sugar.buy("EURUSD", volume=0.1)
# outside the block, the previous timeout is restored
```

---

## Implementation sketch

```python
# comments in English only
import asyncio
from contextlib import asynccontextmanager
from typing import Any, Awaitable, Optional

class MT4Sugar:
    def __init__(self, svc, *, connect_defaults: Optional[dict] = None) -> None:
        self.svc = svc
        self._connect_defaults = connect_defaults or {}
        self._connected = False
        self._last_ok_at = 0.0
        self._call_timeout: Optional[float] = None  # seconds

    @asynccontextmanager
    async def with_timeout(self, seconds: float):
        """Temporarily set a per‑call timeout for all sugar calls inside this block."""
        prev = self._call_timeout
        self._call_timeout = float(seconds) if seconds is not None else None
        try:
            yield self
        finally:
            self._call_timeout = prev

    async def call(self, awaitable: Awaitable[Any]) -> Any:
        """Execute an awaitable honoring the current per‑call timeout if set."""
        if self._call_timeout is not None:
            async with asyncio.timeout(self._call_timeout):
                return await awaitable
        return await awaitable
```

---

## Notes

* **Avoid double timeouts:** Don’t wrap calls that already enforce their own strict timeout unless you really want the shorter one.
* **Scoped and safe:** Timeout applies only within the block; outside, the system behaves normally.
* **Recommended use:** Combine with high‑frequency sugar calls (e.g., batch operations or quick retries).
