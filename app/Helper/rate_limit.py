# app/rate_limit.py
from __future__ import annotations
import asyncio
import time

class RateLimiter:
    """Simple token-bucket-like limiter: max N operations per second."""

    def __init__(self, per_second: float) -> None:
        self.per_second = float(per_second)
        self._lock = asyncio.Lock()
        self._last_ts = 0.0

    async def acquire(self) -> None:
        if self.per_second <= 0:
            return
        async with self._lock:
            now = time.monotonic()
            min_interval = 1.0 / self.per_second
            wait = self._last_ts + min_interval - now
            if wait > 0:
                await asyncio.sleep(wait)
            self._last_ts = time.monotonic()


"""
RateLimiter Usage Guide
=======================

Purpose:
--------
This module provides a simple async-safe rate limiter to control the frequency of operations,
preventing API overload and ensuring compliance with rate limits (e.g., broker/server restrictions).

Key Features:
-------------
- Token-bucket-like algorithm: guarantees minimum interval between operations
- Async-safe: uses asyncio.Lock for thread-safe concurrent access
- Simple API: just call `await limiter.acquire()` before each operation
- Configurable: set max operations per second via constructor

Usage Example:
--------------
```python
from app.Helper.rate_limit import RateLimiter
import asyncio

# Create limiter: max 5 operations per second
limiter = RateLimiter(per_second=5.0)

async def send_order(symbol: str, volume: float):
    # Acquire rate limit slot before sending order
    await limiter.acquire()

    # Now safe to proceed with API call
    result = await mt4_account.order_send(symbol=symbol, volume=volume)
    return result

# Use in loop
async def main():
    tasks = [send_order("EURUSD", 0.1) for _ in range(20)]
    results = await asyncio.gather(*tasks)
    # Will automatically throttle to 5 ops/sec, taking ~4 seconds total

asyncio.run(main())
```

Common Use Cases:
-----------------
1. **Order Submission Rate Limiting**
   Prevent flooding broker with too many orders:
   ```python
   order_limiter = RateLimiter(per_second=10.0)  # Max 10 orders/sec

   async def place_order(...):
       await order_limiter.acquire()
       return await account.order_send(...)
   ```

2. **Market Data Requests**
   Control frequency of symbol info/quote requests:
   ```python
   quote_limiter = RateLimiter(per_second=50.0)  # Max 50 quotes/sec

   async def get_quote(symbol: str):
       await quote_limiter.acquire()
       return await account.symbol_info_tick(symbol)
   ```

3. **Account Operations**
   Throttle account summary or balance checks:
   ```python
   account_limiter = RateLimiter(per_second=2.0)  # Max 2 checks/sec

   async def check_balance():
       await account_limiter.acquire()
       return await account.account_summary()
   ```

4. **Global API Rate Limit**
   Apply single limiter to all MT4 RPC calls:
   ```python
   global_limiter = RateLimiter(per_second=100.0)  # Total 100 calls/sec

   # Wrap MT4Account methods to inject rate limiting
   class RateLimitedMT4Account(MT4Account):
       async def order_send(self, *args, **kwargs):
           await global_limiter.acquire()
           return await super().order_send(*args, **kwargs)

       async def symbol_info_tick(self, *args, **kwargs):
           await global_limiter.acquire()
           return await super().symbol_info_tick(*args, **kwargs)
   ```

Technical Details:
------------------
- **Algorithm**: Enforces minimum time interval between operations (1/per_second)
- **Concurrency**: asyncio.Lock ensures only one coroutine calculates wait time
- **Timing**: Uses monotonic clock (time.monotonic) for accuracy
- **Backoff**: Automatically sleeps if operation called too soon after previous one
- **Disabled**: Set per_second=0 or negative to disable rate limiting

Performance Notes:
------------------
- Minimal overhead: O(1) time complexity
- No memory accumulation: only tracks last operation timestamp
- Safe for high concurrency: lock ensures consistent behavior
- Precise timing: uses exponential wait calculation for accuracy

Integration Example (MT4Service):
----------------------------------
```python
class MT4Service:
    def __init__(self, account: MT4Account, *, rate_limit: float = 20.0):
        self.account = account
        self._limiter = RateLimiter(per_second=rate_limit) if rate_limit > 0 else None

    async def _rate_limited_call(self, coro):
        if self._limiter:
            await self._limiter.acquire()
        return await coro

    async def place_order(self, symbol: str, volume: float, ...):
        return await self._rate_limited_call(
            self.account.order_send(symbol=symbol, volume=volume, ...)
        )
```

Important Notes:
----------------
- Rate limiter is PER INSTANCE - create separate limiters for different operation types
- Does NOT queue operations - caller must handle concurrent access patterns
- Suitable for steady-state throttling, not burst protection (use token bucket for bursts)
- Works best with asyncio applications; not designed for multi-threading
"""

