# app/hooks.py
from __future__ import annotations
import asyncio
from typing import Callable, Awaitable, Dict, List, Any

Callback = Callable[[dict], Any]  # may return coroutine

class HookBus:
    """Lightweight async-capable event bus."""
    def __init__(self) -> None:
        self._subs: Dict[str, List[Callback]] = {}

    def on(self, event: str, cb: Callback) -> None:
        """Subscribe callback to an event name (e.g., 'on_order_sent')."""
        self._subs.setdefault(event, []).append(cb)

    def off(self, event: str, cb: Callback) -> None:
        """Unsubscribe callback."""
        if event in self._subs:
            self._subs[event] = [x for x in self._subs[event] if x is not cb]

    async def emit(self, event: str, payload: dict) -> None:
        """Emit event with payload; supports sync and async callbacks."""
        for cb in self._subs.get(event, []):
            try:
                res = cb(payload)
                if asyncio.iscoroutine(res):
                    await res
            except Exception:
                # don't break the caller if a hook fails
                pass

"""
HookBus is a simple event bus with async/await support.
It allows you to subscribe to (on), unsubscribe (off), and emit events.
It supports both synchronous and asynchronous callback functions.
It is used to track trading events (sending an order, changing a position, etc.).
If the callback throws an exception, it is ignored to avoid interrupting the main thread.
Example: bus.on('order_sent', lambda data: print(data)); await bus.emit('order_sent', {...})
"""

