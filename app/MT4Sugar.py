# app/MT4Sugar.py
# High-level sugar helpers for MT4Service
from __future__ import annotations

# add imports on top
import logging
import asyncio
from contextlib import contextmanager
from typing import Any, Dict, Iterator, Optional

from .Helper.errors import MT4Error, ConnectivityError, OrderRejected, ModifyRejected, map_backend_error
from .Helper.hooks import HookBus
from .Helper.rate_limit import RateLimiter

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.MT4Service import MT4Service

# Only keys we allow to be set as defaults
_DEFAULT_KEYS = {"symbol", "magic", "deviation_pips", "slippage_pips", "risk_percent"}


class MT4Sugar:
    """High-level sugar layer on top of MT4Service."""

    _defaults: Dict[str, Any]

    def __init__(self, service: "MT4Service") -> None:
        self._svc = service

        # Logger (simple, can be reconfigured in main)
        self.log = logging.getLogger("MT4Sugar")
        if not self.log.handlers:
            h = logging.StreamHandler()
            h.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s %(name)s: %(message)s"))
            self.log.addHandler(h)
            self.log.setLevel(logging.INFO)

        # Event hooks bus
        self.hooks = HookBus()

        # Rate limiter for order submissions (10 ops/sec by default)
        self._order_send_rl = RateLimiter(per_second=10.0)

        # Minimal, sensible defaults
        self._defaults = {
            "symbol": None,
            "magic": None,
            "deviation_pips": None,
            "slippage_pips": None,
            "risk_percent": None,
        }

    # ──────────────────────────────────
    # region DEFAULTS & CONTEXT
    # ──────────────────────────────────

    def set_defaults(
        self,
        *,
        symbol: Optional[str] = None,
        magic: Optional[int] = None,
        deviation_pips: Optional[float] = None,
        slippage_pips: Optional[float] = None,
        risk_percent: Optional[float] = None,
    ) -> None:
        """Set user-friendly defaults for subsequent operations.

        Notes:
            - Only non-None values are applied.
            - Keeps other defaults intact.
        """
        updates = {
            "symbol": symbol,
            "magic": magic,
            "deviation_pips": deviation_pips,
            "slippage_pips": slippage_pips,
            "risk_percent": risk_percent,
        }
        for k, v in updates.items():
            if v is not None and k in _DEFAULT_KEYS:
                self._defaults[k] = v

    @contextmanager
    def with_defaults(self, **overrides: Any) -> Iterator[None]:
        """Temporarily override defaults within a context block.

        Example:
            with sugar.with_defaults(symbol="EURUSD", risk_percent=1.0):
                await sugar.ensure_connected()
        """
        snapshot = dict(self._defaults)
        try:
            for k, v in overrides.items():
                if k in _DEFAULT_KEYS and v is not None:
                    self._defaults[k] = v
            yield
        finally:
            self._defaults = snapshot

    async def ensure_connected(self) -> None:
        """Reconnect if needed to guarantee an active session."""
        try:
            _ = self._svc.get_headers()
            return
        except Exception:
            try:
                await self._svc.reconnect()
                await self.hooks.emit("on_reconnect", {"source": "ensure_connected"})
                _ = self._svc.get_headers()
            except Exception as e2:
                self.log.error("Reconnect failed", exc_info=False)
                raise map_backend_error(e2, context="reconnect")

    async def ping(self) -> bool:
        """Lightweight connectivity probe returning True/False."""
        try:
            _ = self._svc.get_headers()
            return True
        except Exception:
            try:
                await self._svc.reconnect()
                _ = self._svc.get_headers()
                return True
            except Exception:
                return False

    def get_default(self, key: str, fallback: Any = None) -> Any:
        """Return a default value by key with fallback."""
        return self._defaults.get(key, fallback)

    # endregion


    # ──────────────────────────────────
    # region SYMBOLS & PRICING UTILS
    # ──────────────────────────────────

    # Simple in-memory cache for symbol params to avoid extra RPC calls
    _sym_cache: dict[str, dict]

    def _extract_quote_field(self, q: Any, field: str) -> float | None:
        """Extract field from quote (protobuf or dict)."""
        if hasattr(q, field):
            return float(getattr(q, field))
        if hasattr(q, field.capitalize()):
            return float(getattr(q, field.capitalize()))
        if isinstance(q, dict):
            return float(q.get(field) or q.get(field.capitalize()) or 0)
        return None

    async def _get_symbol_params(self, symbol: str, force_refresh: bool = False) -> dict:
        """Fetch and cache symbol parameters via service.symbol_params_many()."""
        if not hasattr(self, "_sym_cache"):
            self._sym_cache = {}

        key = symbol.upper()
        params = self._sym_cache.get(key) if not force_refresh else None
        if params is None:
            try:
                # Expect service to return a mapping {symbol: {param_name: value, ...}}
                data = await self._svc.symbol_params_many([key])
            except Exception as e:
                raise map_backend_error(e, context="symbol_params_many", payload={"symbol": key})
            params = (data or {}).get(key) or {}
            self._sym_cache[key] = params
        return params

    async def ensure_symbol(
        self,
        symbol: str,
        *,
        preload_params: bool = True,
        require_trade_allowed: bool = False,
        force_refresh: bool = False,
    ) -> None:
        """
        Ensure the symbol exists and (optionally) preload/cache its trading params.
        - preload_params: if True, fetch and cache symbol params even when symbols() succeeded
        - require_trade_allowed: if True, raise if trade is not allowed for the symbol
        - force_refresh: if True, bypass cache when fetching params
        """
        key = (symbol or "").strip().upper()
        if not key:
            raise ValueError("Symbol must be a non-empty string")

        # 1) Try to ensure the symbol is known/loaded by the backend (and possibly activate it)
        try:
            _ = await self._svc.symbols([key])
        except Exception:
            # Fallback for backends without symbols()
            try:
                _ = await self._get_symbol_params(key, force_refresh=force_refresh)
            except Exception as e:
                raise map_backend_error(e, context="symbols", payload={"symbol": key})

        # 2) Optionally preload params into local cache (and/or validate trade_allowed)
        if preload_params or require_trade_allowed or force_refresh:
            p = await self._get_symbol_params(key, force_refresh=force_refresh)

            if require_trade_allowed:
                ta = (
                    p.get("trade_allowed")
                    if "trade_allowed" in p
                    else p.get("TradeAllowed")
                )
                if ta is False:
                    raise RuntimeError(f"Trade not allowed for symbol '{key}'")


    async def point(self, symbol: str) -> float:
        """Return symbol's minimal price step (Point)."""
        p = await self._get_symbol_params(symbol)
        return float(p.get("point") or p.get("Point") or 1e-5)

    async def digits(self, symbol: str) -> int:
        """Return symbol's digits."""
        p = await self._get_symbol_params(symbol)
        if "digits" in p:
            return int(p["digits"])
        if "Digits" in p:
            return int(p["Digits"])
        pt = float(p.get("point") or 1e-5)
        import math
        return max(0, int(round(-math.log10(pt))))

    async def pip_size(self, symbol: str) -> float:
        """Return pip size in price units for this symbol."""
        pt = await self.point(symbol)
        d = await self.digits(symbol)
        if d in (3, 5):
            return pt * 10.0
        return pt

    async def spread_pips(self, symbol: str) -> float:
        """Return current spread in pips (ask-bid converted to pips)."""
        try:
            q = await self._svc.quote(symbol)
        except Exception as e:
            raise map_backend_error(e, context="quote", payload={"symbol": symbol})
        pip = await self.pip_size(symbol)
        bid = self._extract_quote_field(q, "bid")
        ask = self._extract_quote_field(q, "ask")
        if bid is None or ask is None or pip == 0:
            raise MT4Error("quote fields missing or pip_size=0", details={"symbol": symbol, "quote": q})
        return (float(ask) - float(bid)) / float(pip)

    async def mid_price(self, symbol: str) -> float:
        """Return mid price = (bid + ask)/2."""
        try:
            q = await self._svc.quote(symbol)
        except Exception as e:
            raise map_backend_error(e, context="quote", payload={"symbol": symbol})
        bid = self._extract_quote_field(q, "bid")
        ask = self._extract_quote_field(q, "ask")
        if bid is None or ask is None:
            raise MT4Error("quote fields missing", details={"symbol": symbol, "quote": q})
        return (float(bid) + float(ask)) / 2.0

    async def _lot_step(self, symbol: str) -> float:
        """Return lot step (volume_step) or 0.01 as a safe default."""
        p = await self._get_symbol_params(symbol)
        return float(p.get("volume_step") or p.get("VolumeStep") or 0.01)

    async def _lot_bounds(self, symbol: str) -> tuple[float | None, float | None]:
        """Return (min_lot, max_lot) if available."""
        p = await self._get_symbol_params(symbol)
        mn = p.get("min_lot") or p.get("volume_min") or p.get("VolumeMin")
        mx = p.get("max_lot") or p.get("volume_max") or p.get("VolumeMax")
        return (float(mn) if mn is not None else None, float(mx) if mx is not None else None)

    def _round_to_grid(self, value: float, step: float) -> float:
        """Round value to nearest multiple of step (banker's rounding avoided)."""
        if step <= 0:
            return value
        k = round(value / step)
        return k * step

    async def pips_to_price(self, symbol: str, pips: float) -> float:
        """Convert pips into absolute price delta for the symbol."""
        return float(pips) * (await self.pip_size(symbol))

    async def price_to_pips(self, symbol: str, price_delta: float) -> float:
        """Convert absolute price delta into pips for the symbol."""
        pip = await self.pip_size(symbol)
        if pip == 0:
            return 0.0
        return float(price_delta) / float(pip)

    async def normalize_price(self, symbol: str, price: float) -> float:
        """Round price to allowed precision for the symbol."""
        pt = await self.point(symbol)
        return self._round_to_grid(float(price), float(pt))

    async def normalize_lot(self, symbol: str, lots: float) -> float:
        """Round lot size to allowed step for the symbol and clamp to bounds if known."""
        step = await self._lot_step(symbol)
        v = self._round_to_grid(float(lots), float(step))
        mn, mx = await self._lot_bounds(symbol)
        if mn is not None:
            v = max(v, mn)
        if mx is not None:
            v = min(v, mx)
        return v

    # endregion

    # ──────────────────────────────────
    # region QUOTES & HISTORY
    # ──────────────────────────────────

    async def last_quote(self, symbol: str) -> dict:
        """Return last bid/ask and time for a symbol."""
        await self.ensure_symbol(symbol)
        try:
            q = await self._svc.quote(symbol)
        except Exception as e:
            raise map_backend_error(e, context="quote", payload={"symbol": symbol})
        bid = self._extract_quote_field(q, "bid")
        ask = self._extract_quote_field(q, "ask")
        if bid is None or ask is None:
            raise MT4Error("quote fields missing", details={"symbol": symbol, "quote": q})

        # Extract time field
        time_val = None
        if hasattr(q, "time"):
            time_val = q.time
        elif hasattr(q, "date_time"):
            time_val = q.date_time
        elif isinstance(q, dict):
            time_val = q.get("time") or q.get("date_time")

        return {
            "bid": float(bid),
            "ask": float(ask),
            "time": time_val,
        }

    async def quotes(self, symbols: list[str]) -> dict[str, dict]:
        """Batch get last quotes for multiple symbols."""
        if not symbols:
            return {}
        # ensure all symbols exist (best effort)
        for s in symbols:
            try:
                await self.ensure_symbol(s)
            except Exception:
                pass
        try:
            data = await self._svc.quote_many(symbols)
        except Exception as e:
            raise map_backend_error(e, context="quote_many", payload={"symbols": symbols})

        out: dict[str, dict] = {}

        # Handle protobuf response with 'quotes' field
        quotes_list = []
        if hasattr(data, "quotes"):
            quotes_list = data.quotes
        elif isinstance(data, list):
            quotes_list = data
        elif isinstance(data, dict):
            quotes_list = data.values()

        for q in quotes_list:
            # Extract symbol
            if hasattr(q, "symbol"):
                sym = q.symbol
            elif isinstance(q, dict):
                sym = q.get("symbol")
            else:
                continue

            if not sym:
                continue

            bid = self._extract_quote_field(q, "bid")
            ask = self._extract_quote_field(q, "ask")
            if bid is None or ask is None:
                continue

            # Extract time field
            time_val = None
            if hasattr(q, "time"):
                time_val = q.time
            elif hasattr(q, "date_time"):
                time_val = q.date_time
            elif isinstance(q, dict):
                time_val = q.get("time") or q.get("date_time")

            out[sym.upper()] = {
                "bid": float(bid),
                "ask": float(ask),
                "time": time_val,
            }
        return out

    async def wait_price(
        self, symbol: str, target: float, direction: str = ">=", timeout_s: float | None = None
    ) -> float:
        """Wait until price crosses target; returns actual trigger price."""
        import asyncio, time

        await self.ensure_symbol(symbol)
        if direction not in (">=", "<=", ">", "<"):
            raise ValueError("direction must be one of '>=', '<=', '>', '<'")

        start = time.monotonic()
        poll_interval = 0.25  # seconds

        def _hit(px: float) -> bool:
            return (
                (direction == ">=" and px >= target)
                or (direction == "<=" and px <= target)
                or (direction == ">"  and px >  target)
                or (direction == "<"  and px <  target)
            )

        while True:
            try:
                q = await self._svc.quote(symbol)
            except Exception as e:
                raise map_backend_error(e, context="quote", payload={"symbol": symbol})
            bid = self._extract_quote_field(q, "bid")
            ask = self._extract_quote_field(q, "ask")
            if bid is None or ask is None:
                raise MT4Error("quote fields missing", details={"symbol": symbol, "quote": q})
            mid = (float(bid) + float(ask)) / 2.0
            if _hit(mid):
                return mid
            if timeout_s is not None and (time.monotonic() - start) > timeout_s:
                raise TimeoutError(f"wait_price timeout for {symbol}: target={target}, dir={direction}")
            await asyncio.sleep(poll_interval)

    async def bars(
        self,
        symbol: str,
        timeframe: str,
        *,
        count: int | None = None,
        since: int | None = None,
        until: int | None = None,
    ) -> list[dict]:
        """Return OHLCV bars; aggregates from ticks if bars API is unavailable."""
        ticks = await self.ticks(symbol, since=since, until=until, limit=None)
        if not ticks:
            return []
        tf_sec = self._timeframe_to_seconds(timeframe)
        if tf_sec <= 0:
            raise ValueError(f"Unsupported timeframe: {timeframe}")
        bars = self._aggregate_ticks_to_bars(ticks, tf_sec)
        if count is not None and count > 0:
            bars = bars[-count:]
        return bars

    async def ticks(
        self, symbol: str, *, since: int | None = None, until: int | None = None, limit: int | None = None
    ) -> list[dict]:
        """Return tick history: [{'time': epoch_ms, 'bid': float, 'ask': float}, ...]."""
        await self.ensure_symbol(symbol)
        try:
            data = await self._svc.quote_history(symbol=symbol, since=since, until=until, limit=limit)
        except Exception as e:
            raise map_backend_error(e, context="quote_history", payload={"symbol": symbol, "since": since, "until": until, "limit": limit})

        out: list[dict] = []

        # Handle protobuf response - could be repeated field or list
        ticks_list = []
        if hasattr(data, "ticks"):
            ticks_list = data.ticks
        elif hasattr(data, "quotes"):
            ticks_list = data.quotes
        elif hasattr(data, "bars"):
            ticks_list = data.bars
        elif isinstance(data, list):
            ticks_list = data
        else:
            # Try to extract any iterable field
            ticks_list = data if data else []

        for t in ticks_list:
            try:
                # Extract time field
                time_val = None
                if hasattr(t, "time"):
                    time_val = int(t.time) if hasattr(t.time, '__int__') else int(t.time.seconds) if hasattr(t.time, 'seconds') else None
                elif hasattr(t, "date_time"):
                    dt = t.date_time
                    time_val = int(dt.seconds) if hasattr(dt, 'seconds') else None
                elif isinstance(t, dict):
                    time_val = int(t.get("time") or t.get("date_time") or 0)

                if time_val is None:
                    continue

                # Extract bid/ask
                bid = self._extract_quote_field(t, "bid")
                ask = self._extract_quote_field(t, "ask")

                if bid is None or ask is None:
                    continue

                out.append({"time": time_val, "bid": float(bid), "ask": float(ask)})
            except Exception:
                continue

        out.sort(key=lambda x: x["time"])
        return out

    # --- helpers (private) ---

    def _timeframe_to_seconds(self, tf: str) -> int:
        """Translate common MT timeframes to seconds."""
        tf = (tf or "").upper()
        if tf == "M1":  return 60
        if tf == "M5":  return 300
        if tf == "M15": return 900
        if tf == "M30": return 1800
        if tf == "H1":  return 3600
        if tf == "H4":  return 14400
        if tf == "D1":  return 86400
        return -1

    def _aggregate_ticks_to_bars(self, ticks: list[dict], tf_sec: int) -> list[dict]:
        """Aggregate tick sequence into OHLCV-like bars (no real volume available)."""
        if not ticks:
            return []
        bars: list[dict] = []
        ms_bucket = tf_sec * 1000

        def _mid(t: dict) -> float:
            return (float(t["bid"]) + float(t["ask"])) / 2.0

        def _spr(t: dict) -> float:
            return float(t["ask"]) - float(t["bid"])

        cur_open_ms = (int(ticks[0]["time"]) // ms_bucket) * ms_bucket
        open_px = high = low = close = _mid(ticks[0])
        spr_sum = _spr(ticks[0]); spr_n = 1

        for t in ticks[1:]:
            ts = int(t["time"]); bucket = (ts // ms_bucket) * ms_bucket
            px = _mid(t); sp = _spr(t)
            if bucket != cur_open_ms:
                bars.append({"time": cur_open_ms, "open": open_px, "high": high, "low": low, "close": close, "spread": spr_sum / max(1, spr_n)})
                cur_open_ms = bucket; open_px = high = low = close = px
                spr_sum = sp; spr_n = 1
            else:
                close = px
                if px > high: high = px
                if px < low:  low = px
                spr_sum += sp; spr_n += 1

        bars.append({"time": cur_open_ms, "open": open_px, "high": high, "low": low, "close": close, "spread": spr_sum / max(1, spr_n)})
        return bars

    # endregion



    # ──────────────────────────────────
    # region RISK & SIZING
    # ──────────────────────────────────

    async def _money_per_pip_for_lots(self, symbol: str, lots: float) -> float:
        """Return monetary value of 1 pip for the given lot size.

        money_per_pip(lots) = tick_value_per_lot * lots * (pip_size / point)
        """
        pip = await self.pip_size(symbol)
        pt = await self.point(symbol)
        if pip <= 0 or pt <= 0:
            return 0.0
        try:
            # Get tick value info for the symbol (returns value per standard lot)
            result = await self._svc.tick_value_with_size(symbol=symbol)

            # Extract tick value from the result
            # Result is a protobuf object with 'infos' field containing list of SymbolTickValueWithSizeInfo
            if hasattr(result, "infos") and len(result.infos) > 0:
                tick_val_per_lot = float(result.infos[0].TradeTickValue)
            else:
                raise ValueError(f"No tick value info returned for {symbol}")

            # Scale by number of lots
            tick_val = tick_val_per_lot * lots
        except Exception as e:
            raise map_backend_error(e, context="tick_value_with_size", payload={"symbol": symbol, "lots": lots})
        return float(tick_val) * (pip / pt)

    async def calc_lot_by_risk(
        self, symbol: str, risk_percent: float, stop_pips: float, *, balance: float | None = None
    ) -> float:
        """Compute lot size by risk percent and stop distance."""
        if stop_pips <= 0:
            raise ValueError("stop_pips must be > 0")

        # Balance source
        cash_src = balance
        if cash_src is None:
            try:
                acc = await self._svc.account_summary()
            except Exception as e:
                raise map_backend_error(e, context="account_summary")
            # Handle protobuf response
            if hasattr(acc, "account_balance"):
                cash_src = float(acc.account_balance)
            elif hasattr(acc, "account_equity"):
                cash_src = float(acc.account_equity)
            elif isinstance(acc, dict):
                cash_src = float(acc.get("balance") or acc.get("Balance") or acc.get("equity") or 0.0)
            else:
                cash_src = 0.0

        cash_risk = cash_src * (float(risk_percent) / 100.0)

        # Pip value for 1 lot
        mpp_1lot = await self._money_per_pip_for_lots(symbol, lots=1.0)
        if mpp_1lot <= 0:
            return 0.0

        raw_lots = cash_risk / (mpp_1lot * float(stop_pips))
        return await self.normalize_lot(symbol, raw_lots)

    async def calc_cash_risk(self, symbol: str, lots: float, stop_pips: float) -> float:
        """Compute monetary risk for given lot and stop distance: money_per_pip(lots) * stop_pips."""
        if lots <= 0 or stop_pips <= 0:
            return 0.0
        mpp = await self._money_per_pip_for_lots(symbol, lots=lots)
        return mpp * float(stop_pips)

    async def tick_value(self, symbol: str, lots: float = 1.0) -> float:
        """
        Get tick value in account currency for specified symbol and lot size.
        Returns the monetary value of one tick (minimal price change).

        Example:
            tick_val = await sugar.tick_value("EURUSD", lots=0.01)
            # Returns how much 1 tick movement is worth for 0.01 lots
        """
        await self.ensure_symbol(symbol)
        try:
            result = await self._svc.tick_value_with_size(symbol=symbol)
        except Exception as e:
            raise map_backend_error(e, context="tick_value_with_size", payload={"symbol": symbol, "lots": lots})

        # Handle protobuf response
        tick_val = None
        if hasattr(result, "tick_value"):
            tick_val = float(result.tick_value)
        elif hasattr(result, "value"):
            tick_val = float(result.value)
        elif isinstance(result, dict):
            tick_val = float(result.get("tick_value") or result.get("value") or 1.0)
        else:
            tick_val = 1.0

        # Scale by lot size (1.0 lot is the base)
        return tick_val * float(lots)

    def breakeven_price(self, entry_price: float, commission: float = 0.0, swap: float = 0.0) -> float:
        """Approximate breakeven price considering commissions/swaps (as price deltas)."""
        return float(entry_price) + float(commission) + float(swap)

    async def exposure_summary(self, *, by_symbol: bool = True) -> dict:
        """Return aggregated exposure/PnL/margin either per-symbol or total."""
        # 1) account-level snapshot
        try:
            acc = await self._svc.account_summary()
        except Exception as e:
            raise map_backend_error(e, context="account_summary")

        # Handle protobuf response
        if hasattr(acc, "account_balance"):
            balance = float(acc.account_balance)
            equity = float(acc.account_equity)
            # Note: margin and free_margin are not available in the protobuf response
            margin = 0.0
            free_margin = 0.0
        elif isinstance(acc, dict):
            balance = float(acc.get("balance") or acc.get("Balance") or 0.0)
            equity = float(acc.get("equity") or acc.get("Equity") or 0.0)
            margin = float(acc.get("margin") or acc.get("Margin") or 0.0)
            free_margin = float(acc.get("free_margin") or acc.get("FreeMargin") or 0.0)
        else:
            balance = equity = margin = free_margin = 0.0

        account_info = {
            "balance": balance,
            "equity": equity,
            "margin": margin,
            "free_margin": free_margin,
            "open_positions": 0,
        }

        # 2) open orders/positions
        try:
            orders_result = await self._svc.opened_orders()
        except Exception as e:
            raise map_backend_error(e, context="opened_orders")

        # Extract orders from protobuf response
        if hasattr(orders_result, "order_infos"):
            orders = orders_result.order_infos
        elif isinstance(orders_result, list):
            orders = orders_result
        else:
            orders = []

        groups: dict[str, dict] = {}
        total = {"lots_net": 0.0, "lots_long": 0.0, "lots_short": 0.0, "pnl": 0.0, "margin": 0.0}

        def _get_field(o, *field_names):
            """Get field from protobuf or dict object."""
            for name in field_names:
                if hasattr(o, name):
                    return getattr(o, name)
                elif isinstance(o, dict) and name in o:
                    return o[name]
            return None

        def _side_mult(o) -> float:
            # For protobuf: order_type is enum (OO_OP_BUY=0, OO_OP_SELL=1, etc.)
            order_type = _get_field(o, "order_type", "side", "Side", "type", "Type")
            if hasattr(order_type, "value"):
                # Protobuf enum
                type_val = order_type.value if hasattr(order_type, "value") else int(order_type)
            elif isinstance(order_type, int):
                type_val = order_type
            elif isinstance(order_type, str):
                side_str = order_type.lower()
                if "buy" in side_str or "long" in side_str or side_str == "0":
                    return 1.0
                if "sell" in side_str or "short" in side_str or side_str == "1":
                    return -1.0
                return 1.0
            else:
                return 1.0

            # 0 = BUY, 1 = SELL (for market orders)
            if type_val == 0:
                return 1.0
            elif type_val == 1:
                return -1.0
            return 1.0

        for o in (orders or []):
            sym = str(_get_field(o, "symbol", "Symbol") or "").upper()
            lots = float(_get_field(o, "lots", "volume", "Lots", "Volume") or 0.0)
            pnl = float(_get_field(o, "profit", "Profit") or 0.0)
            mgn = float(_get_field(o, "margin", "Margin") or 0.0)
            sgn = _side_mult(o)

            bucket = groups.setdefault(sym or "UNKNOWN",
                                       {"lots_net": 0.0, "lots_long": 0.0, "lots_short": 0.0, "pnl": 0.0, "margin": 0.0})
            bucket["pnl"] += pnl
            bucket["margin"] += mgn
            if sgn > 0:
                bucket["lots_long"] += lots
                bucket["lots_net"] += lots
            else:
                bucket["lots_short"] += lots
                bucket["lots_net"] -= lots

            total["pnl"] += pnl
            total["margin"] += mgn
            if sgn > 0:
                total["lots_long"] += lots
                total["lots_net"] += lots
            else:
                total["lots_short"] += lots
                total["lots_net"] -= lots

        account_info["open_positions"] = len(orders or [])

        return {"account": account_info, "by_symbol": groups, "total": total} if by_symbol else {"account": account_info, "total": total}

    # endregion


    # ────────────────────────────────────────────
    # region SMART ORDERS — MARKET/LIMIT/STOP
    # ────────────────────────────────────────────

    # --- helpers --------------------------------------------------------------

    async def _resolve_symbol(self, symbol: str | None) -> str:
        s = symbol or self.get_default("symbol")
        if not s:
            raise ValueError("symbol must be provided (no default configured)")
        await self.ensure_connected()
        await self.ensure_symbol(s)
        return s

    def _resolve_magic(self, magic: int | None) -> int | None:
        return magic if magic is not None else self.get_default("magic")

    def _resolve_deviation_pips(self, deviation_pips: float | None) -> float | None:
        return deviation_pips if deviation_pips is not None else self.get_default("deviation_pips")

    async def _normalize_lots_or_default(self, symbol: str, lots: float | None) -> float:
        v = lots if lots is not None else 0.01  # safe tiny default
        return await self.normalize_lot(symbol, float(v))

    async def _entry_price_for_market(self, symbol: str, side: str) -> float:
        try:
            q = await self._svc.quote(symbol)
        except Exception as e:
            raise map_backend_error(e, context="quote", payload={"symbol": symbol})
        bid = self._extract_quote_field(q, "bid")
        ask = self._extract_quote_field(q, "ask")
        if bid is None or ask is None:
            raise MT4Error("quote fields missing", details={"symbol": symbol, "quote": q})
        return float(ask) if side == "buy" else float(bid)

    async def _derive_sl_tp_prices(
        self,
        *,
        symbol: str,
        side: str,  # "buy" | "sell"
        entry_price: float,
        sl_pips: float | None,
        tp_pips: float | None,
        sl_price: float | None,
        tp_price: float | None,
    ) -> tuple[float | None, float | None]:
        """Derive absolute SL/TP prices using either pips or direct price."""
        sl_abs = sl_price
        tp_abs = tp_price

        if sl_abs is None and sl_pips is not None:
            d = await self.pips_to_price(symbol, float(sl_pips))
            sl_abs = entry_price - d if side == "buy" else entry_price + d

        if tp_abs is None and tp_pips is not None:
            d = await self.pips_to_price(symbol, float(tp_pips))
            tp_abs = entry_price + d if side == "buy" else entry_price - d

        if sl_abs is not None:
            sl_abs = await self.normalize_price(symbol, float(sl_abs))
        if tp_abs is not None:
            tp_abs = await self.normalize_price(symbol, float(tp_abs))
        return sl_abs, tp_abs

    async def _prepare_order_payload(
        self,
        *,
        side: str,                # "buy" | "sell"
        order_type: str,          # "market" | "limit" | "stop"
        symbol: str,
        lots: float,
        price: float | None,
        sl_pips: float | None,
        tp_pips: float | None,
        sl_price: float | None,
        tp_price: float | None,
        comment: str | None,
        magic: int | None,
        deviation_pips: float | None,
    ) -> dict:
        """Build order_send payload with normalized values."""
        if order_type == "market":
            entry = await self._entry_price_for_market(symbol, side)
        else:
            if price is None:
                raise ValueError("price is required for limit/stop orders")
            entry = await self.normalize_price(symbol, float(price))

        sl_abs, tp_abs = await self._derive_sl_tp_prices(
            symbol=symbol,
            side=side,
            entry_price=entry,
            sl_pips=sl_pips,
            tp_pips=tp_pips,
            sl_price=sl_price,
            tp_price=tp_price,
        )

        payload = {
            "symbol": symbol,
            "side": side,                 # expected by service
            "type": order_type,           # "market" | "limit" | "stop"
            "price": entry if order_type != "market" else None,
            "lots": lots,
            "sl": sl_abs,
            "tp": tp_abs,
            "comment": comment,
            "magic": magic,
            "deviation_pips": deviation_pips,
        }
        return {k: v for k, v in payload.items() if v is not None}

    # --- public API -----------------------------------------------------------

    async def place_order(
        self,
        *,
        side: str,               # "buy" | "sell"
        order_type: str,         # "market" | "limit" | "stop"
        symbol: str | None = None,
        price: float | None = None,
        lots: float | None = None,
        sl_pips: float | None = None,
        tp_pips: float | None = None,
        sl_price: float | None = None,
        tp_price: float | None = None,
        comment: str | None = None,
        magic: int | None = None,
        deviation_pips: float | None = None,
    ) -> int:
        """High-level order entry with flexible parameters."""
        sym = await self._resolve_symbol(symbol)
        mgc = self._resolve_magic(magic)
        dev = self._resolve_deviation_pips(deviation_pips)
        vol = await self._normalize_lots_or_default(sym, lots)

        payload = await self._prepare_order_payload(
            side=side.lower(),
            order_type=order_type.lower(),
            symbol=sym,
            lots=vol,
            price=price,
            sl_pips=sl_pips,
            tp_pips=tp_pips,
            sl_price=sl_price,
            tp_price=tp_price,
            comment=comment,
            magic=mgc,
            deviation_pips=dev,
        )

        # Rate-limit + send
        await self._order_send_rl.acquire()
        try:
            result = await self._svc.order_send(**payload)
        except Exception as e:
            self.log.error("order_send failed: %s", e, exc_info=False)
            raise map_backend_error(e, context="order_send", payload=payload)

        # Extract ticket from response (protobuf or dict)
        if hasattr(result, "ticket"):
            ticket = int(result.ticket)
        elif hasattr(result, "Ticket"):
            ticket = int(result.Ticket)
        elif isinstance(result, dict):
            ticket = int(result.get("ticket") or result.get("Ticket") or result.get("order") or result.get("Order"))
        else:
            ticket = int(result)

        self.log.info("order_sent ticket=%s %s", ticket, payload)
        await self.hooks.emit("on_order_sent", {"ticket": ticket, "payload": payload})
        return ticket

    async def buy_market(
        self,
        symbol: str | None = None,
        *,
        lots: float | None = None,
        sl_pips: float | None = None,
        tp_pips: float | None = None,
        sl_price: float | None = None,
        tp_price: float | None = None,
        comment: str | None = None,
        magic: int | None = None,
        deviation_pips: float | None = None,
    ) -> int:
        return await self.place_order(
            side="buy",
            order_type="market",
            symbol=symbol,
            price=None,
            lots=lots,
            sl_pips=sl_pips,
            tp_pips=tp_pips,
            sl_price=sl_price,
            tp_price=tp_price,
            comment=comment,
            magic=magic,
            deviation_pips=deviation_pips,
        )

    async def sell_market(self, **kwargs) -> int:
        kwargs = dict(kwargs)
        kwargs.update({"side": "sell", "order_type": "market"})
        return await self.place_order(**kwargs)

    async def buy_limit(
        self,
        symbol: str | None = None,
        *,
        price: float,
        lots: float | None = None,
        sl_pips: float | None = None,
        tp_pips: float | None = None,
        sl_price: float | None = None,
        tp_price: float | None = None,
        comment: str | None = None,
        magic: int | None = None,
    ) -> int:
        return await self.place_order(
            side="buy",
            order_type="limit",
            symbol=symbol,
            price=price,
            lots=lots,
            sl_pips=sl_pips,
            tp_pips=tp_pips,
            sl_price=sl_price,
            tp_price=tp_price,
            comment=comment,
            magic=magic,
        )

    async def sell_limit(self, **kwargs) -> int:
        kwargs = dict(kwargs)
        kwargs.update({"side": "sell", "order_type": "limit"})
        return await self.place_order(**kwargs)

    async def buy_stop(self, **kwargs) -> int:
        kwargs = dict(kwargs)
        kwargs.update({"side": "buy", "order_type": "stop"})
        return await self.place_order(**kwargs)

    async def sell_stop(self, **kwargs) -> int:
        kwargs = dict(kwargs)
        kwargs.update({"side": "sell", "order_type": "stop"})
        return await self.place_order(**kwargs)

    # endregion


    # ──────────────────────────────────
    # region MODIFY / CLOSE HELPERS
    # ──────────────────────────────────

    # --- private helpers ------------------------------------------------------

    @staticmethod
    def _get_field(obj, *field_names):
        """Get field from protobuf or dict object."""
        for name in field_names:
            if hasattr(obj, name):
                val = getattr(obj, name)
                # Handle protobuf enum values
                if hasattr(val, "value"):
                    return val.value
                return val
            elif isinstance(obj, dict) and name in obj:
                return obj[name]
        return None

    async def _get_order_by_ticket(self, ticket: int):
        """Find an opened order by ticket."""
        try:
            orders_result = await self._svc.opened_orders()
        except Exception as e:
            raise map_backend_error(e, context="opened_orders")

        # Extract orders from protobuf response
        if hasattr(orders_result, "order_infos"):
            orders = orders_result.order_infos
        elif isinstance(orders_result, list):
            orders = orders_result
        else:
            orders = []

        for o in (orders or []):
            # Handle both protobuf and dict
            if hasattr(o, "ticket"):
                t = o.ticket
            elif hasattr(o, "Ticket"):
                t = o.Ticket
            elif isinstance(o, dict):
                t = o.get("ticket") or o.get("Ticket") or o.get("order") or o.get("Order")
            else:
                continue

            try:
                if int(t) == int(ticket):
                    return o
            except Exception:
                continue
        return None

    def _order_symbol(self, o) -> str:
        return str(self._get_field(o, "symbol", "Symbol") or "").upper()

    def _order_side(self, o) -> str:
        """Return 'buy' or 'sell' best-effort."""
        # For protobuf: order_type is enum (OO_OP_BUY=0, OO_OP_SELL=1)
        order_type = self._get_field(o, "order_type", "side", "Side", "type", "Type")

        if isinstance(order_type, int):
            # 0 = BUY, 1 = SELL
            return "buy" if order_type == 0 else "sell"
        elif isinstance(order_type, str):
            s = order_type.lower()
            if "buy" in s or "long" in s or s == "0":
                return "buy"
            if "sell" in s or "short" in s or s == "1":
                return "sell"
        return "buy"

    def _order_open_price(self, o) -> float | None:
        v = self._get_field(o, "price_open", "open_price", "OpenPrice", "PriceOpen")
        try:
            return float(v) if v is not None else None
        except Exception:
            return None

    def _order_lots(self, o) -> float:
        v = self._get_field(o, "lots", "volume", "Lots", "Volume") or 0.0
        try:
            return float(v)
        except Exception:
            return 0.0

    def _is_pending(self, o) -> bool:
        """Heuristic to detect pending order."""
        # For protobuf: order_type values 3-6 are pending orders
        # (BUYLIMIT=3, BUYSTOP=4, SELLLIMIT=5, SELLSTOP=6)
        order_type = self._get_field(o, "order_type", "type", "Type")

        if isinstance(order_type, int):
            return order_type >= 3  # Pending orders have type >= 3
        elif isinstance(order_type, str):
            t = order_type.lower()
            return "limit" in t or "stop" in t or "pending" in t
        return False

    # --- public API -----------------------------------------------------------

    async def modify_sl_tp_by_pips(
        self, ticket: int, *, sl_pips: float | None = None, tp_pips: float | None = None
    ) -> None:
        """Modify SL/TP by pips relative to entry."""
        o = await self._get_order_by_ticket(ticket)
        if not o:
            raise ValueError(f"order not found by ticket {ticket}")

        symbol = self._order_symbol(o)
        side = self._order_side(o)
        entry = self._order_open_price(o)
        if entry is None:
            entry = o.get("price") or o.get("Price")
            entry = float(entry) if entry is not None else None
        if entry is None:
            raise ValueError("entry/open price is unknown; cannot compute SL/TP by pips")

        sl_abs = tp_abs = None
        if sl_pips is not None:
            d = await self.pips_to_price(symbol, float(sl_pips))
            sl_abs = entry - d if side == "buy" else entry + d
        if tp_pips is not None:
            d = await self.pips_to_price(symbol, float(tp_pips))
            tp_abs = entry + d if side == "buy" else entry - d
        if sl_abs is not None:
            sl_abs = await self.normalize_price(symbol, sl_abs)
        if tp_abs is not None:
            tp_abs = await self.normalize_price(symbol, tp_abs)

        try:
            await self._svc.order_modify(ticket=ticket, sl_price=sl_abs, tp_price=tp_abs)
        except Exception as e:
            self.log.error("order_modify failed: %s", e, exc_info=False)
            raise map_backend_error(e, context="order_modify", payload={"ticket": ticket, "sl": sl_abs, "tp": tp_abs})
        self.log.info("order_modify ticket=%s sl=%s tp=%s", ticket, sl_abs, tp_abs)
        await self.hooks.emit("on_modify", {"ticket": ticket, "sl": sl_abs, "tp": tp_abs})

    async def modify_sl_tp_by_price(
        self, ticket: int, *, sl_price: float | None = None, tp_price: float | None = None
    ) -> None:
        """Modify SL/TP using absolute prices."""
        o = await self._get_order_by_ticket(ticket)
        if not o:
            raise ValueError(f"order not found by ticket {ticket}")
        symbol = self._order_symbol(o)

        sl_abs = await self.normalize_price(symbol, float(sl_price)) if sl_price is not None else None
        tp_abs = await self.normalize_price(symbol, float(tp_price)) if tp_price is not None else None

        try:
            await self._svc.order_modify(ticket=ticket, sl_price=sl_abs, tp_price=tp_abs)
        except Exception as e:
            self.log.error("order_modify failed: %s", e, exc_info=False)
            raise map_backend_error(e, context="order_modify", payload={"ticket": ticket, "sl": sl_abs, "tp": tp_abs})
        self.log.info("order_modify ticket=%s sl=%s tp=%s", ticket, sl_abs, tp_abs)
        await self.hooks.emit("on_modify", {"ticket": ticket, "sl": sl_abs, "tp": tp_abs})

    async def close(self, ticket: int) -> None:
        """Close a single order (market) or delete pending."""
        try:
            await self._svc.order_close_delete(ticket=ticket)
        except Exception as e:
            self.log.error("order_close/delete failed: %s", e, exc_info=False)
            raise map_backend_error(e, context="order_close_delete", payload={"ticket": ticket})
        self.log.info("order_close ticket=%s", ticket)
        await self.hooks.emit("on_close", {"ticket": ticket})

    async def close_partial(self, ticket: int, lots: float) -> None:
        """Close part of the position (if allowed)."""
        if lots <= 0:
            return
        try:
            await self._svc.order_close_delete(ticket=ticket, lots=float(lots))
            self.log.info("order_close_partial ticket=%s lots=%s", ticket, lots)
            await self.hooks.emit("on_close", {"ticket": ticket, "lots": float(lots), "partial": True})
            return
        except Exception:
            # Fallback: reduce exposure via opposite market order
            o = await self._get_order_by_ticket(ticket)
            if not o:
                raise
            symbol = self._order_symbol(o)
            side = self._order_side(o)
            opp = "sell" if side == "buy" else "buy"
            await self.place_order(side=opp, order_type="market", symbol=symbol, lots=float(lots))
            # on_order_sent hook already emitted by place_order

    async def close_by(self, ticket_a: int, ticket_b: int) -> None:
        """
        Close two opposite positions against each other (hedge close).
        Only works on hedge accounts where you can have opposite positions.

        Args:
            ticket_a: First order ticket
            ticket_b: Second order ticket (opposite direction)

        Example:
            # Close BUY position #123 against SELL position #456
            await sugar.close_by(123, 456)
        """
        try:
            await self._svc.order_close_by(ticket_a=ticket_a, ticket_b=ticket_b)
            self.log.info("order_close_by ticket_a=%s ticket_b=%s", ticket_a, ticket_b)
            await self.hooks.emit("on_close_by", {"ticket_a": ticket_a, "ticket_b": ticket_b})
        except Exception as e:
            self.log.error("order_close_by failed: %s", e, exc_info=False)
            raise map_backend_error(
                e, context="order_close_by", payload={"ticket_a": ticket_a, "ticket_b": ticket_b}
            )

    async def close_all(
        self, *, symbol: str | None = None, magic: int | None = None, only_profit: bool | None = None
    ) -> None:
        """Bulk close with filters."""
        try:
            orders_result = await self._svc.opened_orders()
        except Exception as e:
            raise map_backend_error(e, context="opened_orders")

        # Extract orders from protobuf response
        if hasattr(orders_result, "order_infos"):
            orders = list(orders_result.order_infos)
        elif isinstance(orders_result, list):
            orders = orders_result
        else:
            orders = []

        if not orders:
            return

        sym_up = symbol.upper() if symbol else None
        mgc = str(magic) if magic is not None else None

        for o in orders:
            osym = self._order_symbol(o)
            if sym_up and osym != sym_up:
                continue
            omagic = self._get_field(o, "magic", "Magic", "magic_number")
            if mgc is not None and str(omagic) != mgc:
                continue
            if only_profit is True:
                pnl = float(self._get_field(o, "profit", "Profit") or 0.0)
                if pnl <= 0:
                    continue
            if only_profit is False:
                pnl = float(self._get_field(o, "profit", "Profit") or 0.0)
                if pnl >= 0:
                    continue

            t = int(self._get_field(o, "ticket", "Ticket"))
            try:
                await self._svc.order_close_delete(ticket=t)
            except Exception as e:
                self.log.error("order_close/delete failed: %s", e, exc_info=False)
                raise map_backend_error(e, context="order_close_delete", payload={"ticket": t})
            self.log.info("order_close ticket=%s", t)
            await self.hooks.emit("on_close", {"ticket": t})

    async def cancel_pendings(self, *, symbol: str | None = None, magic: int | None = None) -> None:
        """Cancel pending orders by filters."""
        try:
            orders = await self._svc.opened_orders()
        except Exception as e:
            raise map_backend_error(e, context="opened_orders")
        if not orders:
            return

        sym_up = symbol.upper() if symbol else None
        mgc = str(magic) if magic is not None else None

        for o in orders:
            if not self._is_pending(o):
                continue
            osym = self._order_symbol(o)
            if sym_up and osym != sym_up:
                continue
            omagic = o.get("magic") or o.get("Magic")
            if mgc is not None and str(omagic) != mgc:
                continue
            t = int(o.get("ticket") or o.get("Ticket"))
            try:
                await self._svc.order_close_delete(ticket=t)
            except Exception as e:
                self.log.error("order_delete pending failed: %s", e, exc_info=False)
                raise map_backend_error(e, context="order_close_delete", payload={"ticket": t})
            self.log.info("order_delete pending ticket=%s", t)
            await self.hooks.emit("on_close", {"ticket": t, "pending": True})

    async def close_by_breakeven(self, ticket: int, plus_pips: float = 0.0) -> None:
        """Move SL to breakeven (+optional pips)."""
        o = await self._get_order_by_ticket(ticket)
        if not o:
            raise ValueError(f"order not found by ticket {ticket}")

        symbol = self._order_symbol(o)
        side = self._order_side(o)
        entry = self._order_open_price(o)
        if entry is None:
            raise ValueError("entry/open price is unknown; cannot set breakeven")

        delta = await self.pips_to_price(symbol, float(plus_pips))
        be = entry + delta if side == "buy" else entry - delta
        be = await self.normalize_price(symbol, be)

        try:
            await self._svc.order_modify(ticket=ticket, sl_price=be, tp_price=None)
        except Exception as e:
            self.log.error("order_modify(be) failed: %s", e, exc_info=False)
            raise map_backend_error(e, context="order_modify", payload={"ticket": ticket, "sl": be})
        self.log.info("order_modify(be) ticket=%s sl=%s", ticket, be)
        await self.hooks.emit("on_modify", {"ticket": ticket, "sl": be})

    async def close_by_tickets(self, ticket_a: int, ticket_b: int) -> None:
        """Hedge close-by operation (if backend supports)."""
        try:
            await self._svc.order_close_by(ticket_a=ticket_a, ticket_b=ticket_b)
        except Exception as e:
            self.log.error("order_close_by failed: %s", e, exc_info=False)
            raise map_backend_error(e, context="order_close_by", payload={"ticket_a": ticket_a, "ticket_b": ticket_b})
        self.log.info("order_close_by a=%s b=%s", ticket_a, ticket_b)
        await self.hooks.emit("on_close", {"ticket_a": ticket_a, "ticket_b": ticket_b, "close_by": True})

    # endregion


    # ────────────────────────────────────────
    # region [08] TRAILING & AUTOMATION
    # ────────────────────────────────────────

    # Internal registry for background workers
    def _ensure_workers(self) -> None:
        if not hasattr(self, "_workers"):
            self._workers: dict[str, "asyncio.Task"] = {}
            self._workers_meta: dict[str, dict] = {}

    async def set_trailing_stop(self, ticket: int, *, distance_pips: float, step_pips: float | None = None) -> str:
        """Start a trailing worker for the ticket; returns subscription id."""
        import asyncio, uuid

        if distance_pips <= 0:
            raise ValueError("distance_pips must be > 0")
        self._ensure_workers()

        sub_id = f"trail-{uuid.uuid4().hex[:12]}"

        async def _worker() -> None:
            try:
                while True:
                    o = await self._get_order_by_ticket(ticket)
                    if not o:
                        return

                    symbol = self._order_symbol(o)
                    side = self._order_side(o)

                    # current mid price
                    try:
                        q = await self._svc.quote(symbol)
                    except Exception as e:
                        # map and stop worker on hard backend error
                        self.log.error("trailing quote failed: %s", e, exc_info=False)
                        return
                    bid = self._extract_quote_field(q, "bid")
                    ask = self._extract_quote_field(q, "ask")
                    if bid is None or ask is None:
                        return
                    mid = (float(bid) + float(ask)) / 2.0

                    # desired SL in price
                    delta = await self.pips_to_price(symbol, float(distance_pips))
                    desired_sl = mid - delta if side == "buy" else mid + delta
                    desired_sl = await self.normalize_price(symbol, desired_sl)

                    # current SL if any
                    cur_sl = o.get("sl") or o.get("sl_price") or o.get("SL") or o.get("StopLoss")
                    cur_sl = float(cur_sl) if cur_sl is not None else None

                    # Only tighten SL (improve protection)
                    need = False
                    if cur_sl is None:
                        need = True
                    else:
                        if side == "buy" and desired_sl > cur_sl:
                            need = True
                        if side == "sell" and desired_sl < cur_sl:
                            need = True

                    # Apply step threshold in pips if requested
                    if need and step_pips:
                        step_delta = await self.pips_to_price(symbol, float(step_pips))
                        if cur_sl is not None and abs(desired_sl - cur_sl) < step_delta:
                            need = False

                    if need:
                        try:
                            await self._svc.order_modify(ticket=ticket, sl_price=desired_sl, tp_price=None)
                            self.log.info("trailing modify ticket=%s sl=%s", ticket, desired_sl)
                            await self.hooks.emit("on_modify", {"ticket": ticket, "sl": desired_sl, "trailing": True})
                        except Exception as e:
                            # stop gracefully if modify rejected or order gone
                            self.log.error("trailing modify failed: %s", e, exc_info=False)
                            return

                    await asyncio.sleep(0.3)

            finally:
                self._workers.pop(sub_id, None)
                self._workers_meta.pop(sub_id, None)

        task = asyncio.create_task(_worker(), name=sub_id)
        self._workers[sub_id] = task
        self._workers_meta[sub_id] = {"kind": "trailing", "ticket": ticket, "distance_pips": distance_pips, "step_pips": step_pips}
        return sub_id

    async def unset_trailing_stop(self, subscription_id: str) -> None:
        """Stop trailing worker."""
        self._ensure_workers()
        task = self._workers.get(subscription_id)
        if task and not task.done():
            task.cancel()
            try:
                await task
            except Exception:
                pass
        # cleanup
        self._workers.pop(subscription_id, None)
        self._workers_meta.pop(subscription_id, None)

    async def auto_breakeven(self, ticket: int, *, trigger_pips: float, plus_pips: float = 0.0) -> str:
        """Start auto-breakeven worker; returns subscription id."""
        import asyncio, uuid

        if trigger_pips <= 0:
            raise ValueError("trigger_pips must be > 0")
        self._ensure_workers()

        sub_id = f"breakeven-{uuid.uuid4().hex[:12]}"

        async def _worker() -> None:
            try:
                o = await self._get_order_by_ticket(ticket)
                if not o:
                    return

                symbol = self._order_symbol(o)
                side = self._order_side(o)
                entry = self._order_open_price(o)

                # For pending orders, wait until we have entry price
                while entry is None:
                    o = await self._get_order_by_ticket(ticket)
                    if not o:
                        return
                    entry = self._order_open_price(o)
                    if entry is None:
                        await asyncio.sleep(0.2)

                trigger_delta = await self.pips_to_price(symbol, float(trigger_pips))
                plus_delta = await self.pips_to_price(symbol, float(plus_pips))

                target_sl = entry + plus_delta if side == "buy" else entry - plus_delta
                target_sl = await self.normalize_price(symbol, target_sl)

                while True:
                    cur = await self._get_order_by_ticket(ticket)
                    if not cur:
                        return
                    try:
                        q = await self._svc.quote(symbol)
                    except Exception as e:
                        self.log.error("auto_be quote failed: %s", e, exc_info=False)
                        return
                    bid = self._extract_quote_field(q, "bid")
                    ask = self._extract_quote_field(q, "ask")
                    if bid is None or ask is None:
                        return
                    mid = (float(bid) + float(ask)) / 2.0

                    moved = (mid - entry) >= trigger_delta if side == "buy" else (entry - mid) >= trigger_delta
                    if moved:
                        try:
                            await self._svc.order_modify(ticket=ticket, sl_price=target_sl, tp_price=None)
                            self.log.info("auto_be modify ticket=%s sl=%s", ticket, target_sl)
                            await self.hooks.emit("on_modify", {"ticket": ticket, "sl": target_sl, "auto_be": True})
                        except Exception as e:
                            self.log.error("auto_be modify failed: %s", e, exc_info=False)
                        return

                    await asyncio.sleep(0.25)

            finally:
                self._workers.pop(sub_id, None)
                self._workers_meta.pop(sub_id, None)

        task = asyncio.create_task(_worker(), name=sub_id)
        self._workers[sub_id] = task
        self._workers_meta[sub_id] = {"kind": "auto_be", "ticket": ticket, "trigger_pips": trigger_pips, "plus_pips": plus_pips}
        return sub_id

    # endregion



    # ──────────────────────────────────
    # region STREAMS & AWAITERS
    # ──────────────────────────────────

    async def watch_ticks(
        self, symbol: str, on_tick, *, throttle_ms: int | None = None
    ) -> str:
        """Subscribe to symbol ticks; return subscription id."""
        import asyncio, time, uuid

        self._ensure_workers()
        sym = await self._resolve_symbol(symbol)
        sub_id = f"ticks-{sym}-{uuid.uuid4().hex[:8]}"
        interval = (throttle_ms or 0) / 1000.0

        async def _worker() -> None:
            last_emit = 0.0
            try:
                # backend stream
                async for t in self._svc.on_symbol_tick(sym):
                    now = time.monotonic()
                    if interval > 0 and (now - last_emit) < interval:
                        await asyncio.sleep(interval - (now - last_emit))
                        now = time.monotonic()
                    last_emit = now
                    try:
                        res = on_tick(t)
                        if asyncio.iscoroutine(res):
                            await res
                    except Exception:
                        # keep the stream alive even if callback failed
                        pass
            except Exception as e:
                # stop silently; caller can re-subscribe
                self.log.error("watch_ticks stream error: %s", e, exc_info=False)
            finally:
                self._workers.pop(sub_id, None)
                self._workers_meta.pop(sub_id, None)

        task = asyncio.create_task(_worker(), name=sub_id)
        self._workers[sub_id] = task
        self._workers_meta[sub_id] = {"kind": "watch_ticks", "symbol": sym, "throttle_ms": throttle_ms}
        return sub_id

    async def watch_trades(self, on_event) -> str:
        """Subscribe to trade events; return subscription id."""
        import asyncio, uuid

        self._ensure_workers()
        sub_id = f"trades-{uuid.uuid4().hex[:8]}"

        async def _worker() -> None:
            try:
                async for e in self._svc.on_trade():
                    try:
                        res = on_event(e)
                        if asyncio.iscoroutine(res):
                            await res
                    except Exception:
                        pass
            except Exception as e:
                self.log.error("watch_trades stream error: %s", e, exc_info=False)
            finally:
                self._workers.pop(sub_id, None)
                self._workers_meta.pop(sub_id, None)

        task = asyncio.create_task(_worker(), name=sub_id)
        self._workers[sub_id] = task
        self._workers_meta[sub_id] = {"kind": "watch_trades"}
        return sub_id

    async def watch_opened_orders(self, on_event) -> str:
        """Subscribe to opened orders updates; return subscription id (fallback to polling)."""
        import asyncio, uuid

        self._ensure_workers()
        sub_id = f"opened-{uuid.uuid4().hex[:8]}"

        async def _stream_worker() -> None:
            try:
                if hasattr(self._svc, "on_opened_orders_tickets"):
                    async for e in self._svc.on_opened_orders_tickets():
                        try:
                            res = on_event(e)
                            if asyncio.iscoroutine(res):
                                await res
                        except Exception:
                            pass
                else:
                    prev_snapshot = None
                    while True:
                        try:
                            cur = await self._svc.opened_orders()
                        except Exception as e:
                            self.log.error("watch_opened_orders poll error: %s", e, exc_info=False)
                            return
                        if cur != prev_snapshot:
                            try:
                                res = on_event(cur)
                                if asyncio.iscoroutine(res):
                                    await res
                            except Exception:
                                pass
                            prev_snapshot = cur
                        await asyncio.sleep(1.0)
            finally:
                self._workers.pop(sub_id, None)
                self._workers_meta.pop(sub_id, None)

        task = asyncio.create_task(_stream_worker(), name=sub_id)
        self._workers[sub_id] = task
        self._workers_meta[sub_id] = {"kind": "watch_opened_orders"}
        return sub_id

    async def watch_profit(self, on_event, *, timer_period_ms: int = 1000) -> str:
        """
        Subscribe to real-time profit updates for all open positions.
        Calls on_event(profit_data) whenever profit changes.

        Args:
            on_event: Callback function(profit_data) -> None or async
            timer_period_ms: Polling interval in milliseconds (default 1000ms)

        Returns:
            Subscription ID for later cancellation

        Example:
            def profit_changed(data):
                print(f"Total profit: ${data}")

            sub_id = await sugar.watch_profit(profit_changed)
            # Later: await sugar.unwatch(sub_id)
        """
        import asyncio, uuid

        self._ensure_workers()
        sub_id = f"profit-{uuid.uuid4().hex[:8]}"

        async def _worker() -> None:
            try:
                async for profit_data in self._svc.on_opened_orders_profit(
                    timer_period_milliseconds=timer_period_ms
                ):
                    try:
                        res = on_event(profit_data)
                        if asyncio.iscoroutine(res):
                            await res
                    except Exception:
                        pass
            except Exception as e:
                self.log.error("watch_profit stream error: %s", e, exc_info=False)
            finally:
                self._workers.pop(sub_id, None)
                self._workers_meta.pop(sub_id, None)

        task = asyncio.create_task(_worker(), name=sub_id)
        self._workers[sub_id] = task
        self._workers_meta[sub_id] = {"kind": "watch_profit", "timer_ms": timer_period_ms}
        return sub_id

    async def watch_tickets(self, on_event, *, pull_interval_ms: int = 500) -> str:
        """
        Subscribe to changes in open order tickets (new orders, closed orders).
        Calls on_event(tickets_list) when the set of tickets changes.

        Args:
            on_event: Callback function(list[int]) -> None or async
            pull_interval_ms: Polling interval in milliseconds (default 500ms)

        Returns:
            Subscription ID for later cancellation

        Example:
            def tickets_changed(tickets):
                print(f"Open tickets: {tickets}")

            sub_id = await sugar.watch_tickets(tickets_changed)
            # Later: await sugar.unwatch(sub_id)
        """
        import asyncio, uuid

        self._ensure_workers()
        sub_id = f"tickets-{uuid.uuid4().hex[:8]}"

        async def _worker() -> None:
            try:
                async for tickets_data in self._svc.on_opened_orders_tickets(
                    pull_interval_milliseconds=pull_interval_ms
                ):
                    try:
                        res = on_event(tickets_data)
                        if asyncio.iscoroutine(res):
                            await res
                    except Exception:
                        pass
            except Exception as e:
                self.log.error("watch_tickets stream error: %s", e, exc_info=False)
            finally:
                self._workers.pop(sub_id, None)
                self._workers_meta.pop(sub_id, None)

        task = asyncio.create_task(_worker(), name=sub_id)
        self._workers[sub_id] = task
        self._workers_meta[sub_id] = {"kind": "watch_tickets", "pull_ms": pull_interval_ms}
        return sub_id

    async def unwatch(self, subscription_id: str) -> None:
        """Cancel a subscription created by watch_* methods."""
        task = self._workers.get(subscription_id)
        if task and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        self._workers.pop(subscription_id, None)
        self._workers_meta.pop(subscription_id, None)

    async def wait_filled(self, ticket: int, *, timeout_s: float | None = None) -> dict:
        """Await order filled; return final fill info."""
        import asyncio, time

        start = time.monotonic()
        while True:
            o = await self._get_order_by_ticket(ticket)
            if o and not self._is_pending(o):
                return o
            if timeout_s is not None and (time.monotonic() - start) > timeout_s:
                raise TimeoutError(f"wait_filled timeout for ticket {ticket}")
            await asyncio.sleep(0.2)

    async def wait_closed(self, ticket: int, *, timeout_s: float | None = None) -> dict:
        """Await order closed; return {'ticket': int, 'status': 'closed', ...}."""
        import asyncio, time

        last = await self._get_order_by_ticket(ticket)
        start = time.monotonic()
        while True:
            cur = await self._get_order_by_ticket(ticket)
            if cur is None:
                info = {"ticket": int(ticket), "status": "closed"}
                if last:
                    info.update({"symbol": self._order_symbol(last), "lots": self._order_lots(last)})
                return info
            last = cur
            if timeout_s is not None and (time.monotonic() - start) > timeout_s:
                raise TimeoutError(f"wait_closed timeout for ticket {ticket}")
            await asyncio.sleep(0.25)

    # endregion


    # ──────────────────────────────────
    # region [10] BATCH & QUERIES
    # ──────────────────────────────────

    async def _normalize_orders(self, arr):
        """Best-effort normalization guard. Extracts orders from protobuf or list."""
        # Handle protobuf response
        if hasattr(arr, "order_infos"):
            return list(arr.order_infos)
        elif isinstance(arr, list):
            return arr
        elif arr is None:
            return []
        else:
            return []

    def _match_symbol(self, o, sym_up: str | None) -> bool:
        if not sym_up:
            return True
        return self._order_symbol(o) == sym_up

    def _match_magic(self, o, mgc: str | None) -> bool:
        if mgc is None:
            return True
        omagic = self._get_field(o, "magic", "Magic", "magic_number")
        return str(omagic) == mgc if omagic is not None else False

    def _match_side(self, o, side: str | None) -> bool:
        if not side:
            return True
        return self._order_side(o) == side.lower()

    def _match_profit(self, o, min_profit: float | None) -> bool:
        if min_profit is None:
            return True
        pnl = float(self._get_field(o, "profit", "Profit") or 0.0)
        return pnl >= float(min_profit)

    async def find_orders(
        self,
        *,
        symbol: str | None = None,
        magic: int | None = None,
        side: str | None = None,
        state: str | None = None,   # "open" | "pending" | "closed"
        min_profit: float | None = None,
    ) -> list[dict]:
        """Search orders by filters."""
        sym_up = symbol.upper() if symbol else None
        mgc = str(magic) if magic is not None else None
        side_norm = side.lower() if side else None

        out: list[dict] = []

        if state == "closed":
            try:
                closed = await self._svc.orders_history()
            except Exception as e:
                raise map_backend_error(e, context="orders_history")
            for o in await self._normalize_orders(closed):
                if not self._match_symbol(o, sym_up):
                    continue
                if not self._match_magic(o, mgc):
                    continue
                if side_norm and self._order_side(o) != side_norm:
                    continue
                if not self._match_profit(o, min_profit):
                    continue
                out.append(o)
            return out

        # opened (default), possibly filtered by "open"/"pending"
        try:
            opened = await self._svc.opened_orders()
        except Exception as e:
            raise map_backend_error(e, context="opened_orders")

        for o in await self._normalize_orders(opened):
            if not self._match_symbol(o, sym_up):
                continue
            if not self._match_magic(o, mgc):
                continue
            if side_norm and self._order_side(o) != side_norm:
                continue
            if not self._match_profit(o, min_profit):
                continue

            if state == "open" and self._is_pending(o):
                continue
            if state == "pending" and not self._is_pending(o):
                continue

            out.append(o)

        return out

    async def positions_value(self, *, symbol: str | None = None, magic: int | None = None) -> dict:
        """Aggregate metrics for positions (lots, pnl, margin)."""
        sym_up = symbol.upper() if symbol else None
        mgc = str(magic) if magic is not None else None

        try:
            opened = await self._svc.opened_orders()
        except Exception as e:
            raise map_backend_error(e, context="opened_orders")

        total = {"lots_net": 0.0, "lots_long": 0.0, "lots_short": 0.0, "pnl": 0.0, "margin": 0.0}

        for o in await self._normalize_orders(opened):
            if self._is_pending(o):
                continue
            if not self._match_symbol(o, sym_up):
                continue
            if not self._match_magic(o, mgc):
                continue

            lots = self._order_lots(o)
            pnl = float(self._get_field(o, "profit", "Profit") or 0.0)
            mgn = float(self._get_field(o, "margin", "Margin") or 0.0)
            side = self._order_side(o)

            if side == "buy":
                total["lots_long"] += lots
                total["lots_net"] += lots
            else:
                total["lots_short"] += lots
                total["lots_net"] -= lots

            total["pnl"] += pnl
            total["margin"] += mgn

        return total

    async def orders_for_symbol(self, symbol: str) -> list[dict]:
        """Quick filter to get symbol's orders (opened: market + pending)."""
        sym_up = symbol.upper()
        try:
            opened = await self._svc.opened_orders()
        except Exception as e:
            raise map_backend_error(e, context="opened_orders")
        return [o for o in await self._normalize_orders(opened) if self._order_symbol(o) == sym_up]

    # endregion


    # ──────────────────────────────────
    # region DIAGNOSTICS
    # ──────────────────────────────────

    async def diag_snapshot(self) -> dict:
        """Return compact snapshot: account summary + exposure + open orders + spread."""
        import time

        await self.ensure_connected()

        # Account summary (defensive)
        try:
            acc = await self._svc.account_summary()
        except Exception as e:
            raise map_backend_error(e, context="account_summary")

        # Handle protobuf response
        if hasattr(acc, "account_balance"):
            balance = float(acc.account_balance)
            equity = float(acc.account_equity)
            currency = acc.account_currency if hasattr(acc, "account_currency") else None
            margin = 0.0
            free_margin = 0.0
        elif isinstance(acc, dict):
            balance = float(acc.get("balance") or acc.get("Balance") or 0.0)
            equity = float(acc.get("equity") or acc.get("Equity") or 0.0)
            margin = float(acc.get("margin") or acc.get("Margin") or 0.0)
            free_margin = float(acc.get("free_margin") or acc.get("FreeMargin") or 0.0)
            currency = acc.get("currency") or acc.get("Currency") or None
        else:
            balance = equity = margin = free_margin = 0.0
            currency = None

        account = {
            "balance": balance,
            "equity": equity,
            "margin": margin,
            "free_margin": free_margin,
            "currency": currency,
        }

        # Opened orders (market + pending)
        try:
            opened_result = await self._svc.opened_orders()
        except Exception as e:
            raise map_backend_error(e, context="opened_orders")

        # Extract orders from protobuf response
        if hasattr(opened_result, "order_infos"):
            opened = list(opened_result.order_infos)
        elif isinstance(opened_result, list):
            opened = opened_result
        else:
            opened = []

        open_count = len(opened)

        # Exposure summary (by symbol + totals)
        exposure = await self.exposure_summary(by_symbol=True)

        # Symbols for spread check (from opened orders + default)
        symbols: set[str] = set()
        for o in opened:
            s = str(self._get_field(o, "symbol", "Symbol") or "").upper()
            if s:
                symbols.add(s)
        default_sym = self.get_default("symbol")
        if default_sym:
            symbols.add(str(default_sym).upper())

        # Build spread map using last_quote()/spread_pips()
        spreads: dict[str, dict] = {}
        for s in sorted(symbols):
            try:
                q = await self.last_quote(s)
                spr = await self.spread_pips(s)
                spreads[s] = {"bid": q["bid"], "ask": q["ask"], "time": q.get("time"), "spread_pips": spr}
            except Exception as e:
                # Keep snapshot robust: log and continue
                self.log.error("diag spread failed for %s: %s", s, e, exc_info=False)
                continue

        sample_n = min(10, open_count)
        sample = opened[:sample_n] if sample_n else []

        return {
            "generated_at_ms": int(time.time() * 1000),
            "account": account,
            "exposure": exposure,
            "open_orders_count": open_count,
            "open_orders_sample": sample,
            "spreads": spreads,
        }

    # endregion

"""
╔══════════════════════════════════════════════════════════════════════════════╗
║ FILE app/MT4Sugar.py — High-level sugar helpers on top of MT4Service         ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ Purpose                                                                      ║
║   Provide a clean, ergonomic API over MT4Service with:                       ║
║   • Defaults context (symbol/magic/deviation/risk)                           ║
║   • Smart order entry (market/limit/stop with pips → price helpers)          ║
║   • Safe normalization (lot/price grid, digits, point)                       ║
║   • Risk sizing helpers (lot by risk %, cash risk)                           ║
║   • Automation workers (trailing & auto-breakeven)                           ║
║   • Watchers (ticks, trades, tickets, profit)                                ║
║   • Diagnostics snapshot (account + exposure + spreads)                      ║
║                                                                              ║
║ What this adds beyond MT4Service                                             ║
║   • Friendly parameters: pips-based SL/TP, side="buy|sell", type semantics   ║
║   • Defaults merging + context overrides (with_defaults)                     ║
║   • Robust protobuf/dict field extraction for mixed backends                 ║
║   • Rate limiting on order_send (10 ops/sec)                                 ║
║   • Background tasks registry + clean unwatch/unset APIs                     ║
║                                                                              ║
║ Dependencies                                                                 ║
║   - app.MT4Service.MT4Service (low-level RPCs)                               ║
║   - .Helper.errors: MT4Error, map_backend_error, ...                         ║
║   - .Helper.hooks.HookBus (event hooks)                                      ║
║   - .Helper.rate_limit.RateLimiter                                           ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ Architecture Overview                                                        ║
║   [Defaults] set_defaults / with_defaults → stored in _defaults              ║
║   [Symbols] ensure_connected → ensure_symbol → _get_symbol_params cache      ║
║   [Prices] point/digits/pip_size → pips_to_price/price_to_pips/normalize_*   ║
║   [Orders] place_order → _prepare_order_payload → svc.order_send             ║
║   [Modify] order_modify mapping via svc.order_modify                         ║
║   [Close] close / close_partial / close_by / close_all / cancel_pendings     ║
║   [Risk] calc_lot_by_risk / calc_cash_risk / tick_value                      ║
║   [Automation] set_trailing_stop / auto_breakeven (background workers)       ║
║   [Watch] watch_ticks/trades/opened_orders/profit/tickets + unwatch          ║
║   [Awaiters] wait_filled / wait_closed                                       ║
║   [Diagnostics] diag_snapshot / exposure_summary                             ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ Defaults & Context                                                           ║
║   • set_defaults(symbol, magic, deviation_pips, slippage_pips, risk_percent) ║
║   • with_defaults(**overrides) — temporary override inside context           ║
║   • get_default(key, fallback)                                               ║
║   Notes: only keys in {"symbol","magic","deviation_pips","slippage_pips",    ║
║          "risk_percent"} are stored.                                         ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ Public API — Groups & Short Descriptions                                     ║
║                                                                              ║
║ [A] Symbols & Pricing                                                        ║
║   ensure_connected()                 → Reconnect if needed                   ║
║   ensure_symbol(symbol, ...)         → Validate symbol; optional trade flag  ║
║   point(symbol)                      → Minimal price step (Point)            ║
║   digits(symbol)                     → Digits; infers from point if absent   ║
║   pip_size(symbol)                   → Pip size (5/3-digit aware)            ║
║   spread_pips(symbol)                → (ask-bid) in pips                     ║
║   mid_price(symbol)                  → (bid+ask)/2                           ║
║   pips_to_price(symbol, pips)        → Convert pips → absolute price delta   ║
║   price_to_pips(symbol, delta)       → Convert price delta → pips            ║
║   normalize_price(symbol, price)     → Round to symbol point grid            ║
║   normalize_lot(symbol, lots)        → Round vol. to step & clamp to bounds  ║
║   last_quote(symbol)                 → {bid, ask, time}                      ║
║   quotes(symbols)                    → {SYM: {bid,ask,time}, ...}            ║
║   wait_price(symbol, target, dir, t) → Await mid crosses target              ║
║   ticks(symbol, since/until/limit)   → Tick history (best-effort)            ║
║   bars(symbol, timeframe, ...)       → OHLC from ticks (aggregation)         ║
║                                                                              ║
║ [B] Risk & Sizing                                                            ║
║   calc_lot_by_risk(symbol, risk%, sl_pips, balance?) → Lots by risk          ║
║   calc_cash_risk(symbol, lots, sl_pips)           → $ risk for given input   ║
║   tick_value(symbol, lots=1.0)                    → $ per tick for lots      ║
║   breakeven_price(entry, commission=0, swap=0)    → Entry adjusted to BE     ║
║   exposure_summary(by_symbol=True)                → Aggregated exposure/PnL  ║
║   positions_value(symbol?, magic?)                → Lots & PnL aggregates    ║
║                                                                              ║
║ [C] Smart Orders — Entry                                                     ║
║   place_order(side, order_type, ...)  → Unified entry builder (market/limit/ ║
║                                         stop) with pips-based SL/TP or       ║
║                                         absolute prices, defaults merged.    ║
║   buy_market(symbol?, *, lots?, sl_pips?, tp_pips?, sl_price?, tp_price?,    ║
║              comment?, magic?, deviation_pips?) → MARKET BUY                 ║
║   sell_market(**kwargs as above)      → MARKET SELL                          ║
║   buy_limit(symbol?, *, price, ...)   → PENDING BUYLIMIT                     ║
║   sell_limit(**kwargs)                → PENDING SELLLIMIT                    ║
║   buy_stop(**kwargs)                  → PENDING BUYSTOP                      ║
║   sell_stop(**kwargs)                 → PENDING SELLSTOP                     ║
║   Notes: price required for limit/stop; market ignores price; SL/TP may be   ║
║          given in pips or absolute price.                                    ║
║                                                                              ║
║ [D] Modify / Close                                                           ║
║   modify_sl_tp_by_pips(ticket, sl_pips?, tp_pips?) → Recompute vs entry      ║
║   modify_sl_tp_by_price(ticket, sl_price?, tp_price?) → Absolute prices      ║
║   close(ticket)                       → Close market or delete pending       ║
║   close_partial(ticket, lots)         → Partial close; fallback via opposite ║
║   close_by(ticket_a, ticket_b)        → Hedge close-by (if supported)        ║
║   close_all(symbol?, magic?, only_profit?) → Bulk close by filters           ║
║   cancel_pendings(symbol?, magic?)    → Cancel all pendings by filters       ║
║   close_by_breakeven(ticket, plus_pips=0) → Move SL to BE (+offset)          ║
║   close_by_tickets(ticket_a, ticket_b)→ Alias for close_by                   ║
║                                                                              ║
║ [E] Automation (Background Workers)                                          ║
║   set_trailing_stop(ticket, distance_pips, step_pips?) → Start worker; id    ║
║   unset_trailing_stop(sub_id)         → Stop trailing worker                 ║
║   auto_breakeven(ticket, trigger_pips, plus_pips=0) → Start worker; id       ║
║                                                                              ║
║ [F] Watchers & Awaiters                                                      ║
║   watch_ticks(symbol, on_tick, throttle_ms?) → Stream ticks → callback; id   ║
║   watch_trades(on_event)              → Stream trade events; id              ║
║   watch_opened_orders(on_event)       → Stream/poll opened orders; id        ║
║   watch_profit(on_event, timer_ms=1000) → Stream profit aggregate; id        ║
║   watch_tickets(on_event, pull_interval_ms=500) → Stream ticket sets; id     ║
║   unwatch(sub_id)                     → Cancel watcher/worker by id          ║
║   wait_filled(ticket, timeout_s?)     → Await pending → filled               ║
║   wait_closed(ticket, timeout_s?)     → Await ticket disappears              ║
║                                                                              ║
║ [G] Diagnostics                                                              ║
║   diag_snapshot() → {account, exposure, open_orders_count, sample, spreads}  ║
║   orders_for_symbol(symbol) → Quick filter over opened orders                ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ Behavior & Contracts                                                         ║
║   • All prices are absolute terminal prices; pips conversions are explicit.  ║
║   • Lot/price normalization uses symbol metadata (point, step, bounds).      ║
║   • Defaults are merged last; per-call kwargs override defaults.             ║
║   • Side inference: "buy"→long, "sell"→short. Market price chosen as ask/bid.║
║   • Pending detection heuristic supports mixed enum/string backends.         ║
║   • Background workers stop silently on severe backend errors or order gone. ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ Error Model                                                                  ║
║   • All low-level exceptions are funneled through map_backend_error(context).║
║   • Common contexts: "quote", "order_send", "order_modify", "opened_orders". ║
║   • ensure_connected() attempts svc.reconnect() and emits hook "on_reconnect"║
╠══════════════════════════════════════════════════════════════════════════════╣
║ Rate Limiting & Concurrency                                                  ║
║   • order_send guarded by RateLimiter(10 ops/sec).                           ║
║   • Watchers/automation run as asyncio Tasks; IDs are stored in _workers.    ║
║   • unwatch()/unset_trailing_stop() cancel the task and clean registry.      ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ Hooks (HookBus)                                                              ║
║   Emits best-effort events:                                                  ║
║   • "on_reconnect"                       • "on_order_sent"                   ║
║   • "on_modify"                          • "on_close"                        ║
║   • "on_close_by"                        • trailing/auto_be include flags    ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ Quick Examples                                                               ║
║   # Defaults + market buy with pips-based SL/TP                              ║
║   sugar.set_defaults(symbol="EURUSD", magic=123, deviation_pips=2.0)         ║
║   t = await sugar.buy_market(lots=0.02, sl_pips=15, tp_pips=30, comment="X") ║
║                                                                              ║
║   # Pending limit with absolute prices                                       ║
║   price = await sugar.mid_price("EURUSD") - await sugar.pips_to_price(...)   ║
║   t = await sugar.buy_limit(price=price, lots=0.01, sl_pips=12, tp_pips=24)  ║
║                                                                              ║
║   # Trailing + auto-breakeven                                                ║
║   sub_trail = await sugar.set_trailing_stop(t, distance_pips=10, step_pips=2)║
║   sub_be    = await sugar.auto_breakeven(t, trigger_pips=12, plus_pips=1)    ║
║                                                                              ║
║   # Close partial; fallback to opposite if backend disallows partial close   ║
║   await sugar.close_partial(t, lots=0.01)                                    ║
║                                                                              ║
║   # Risk-based sizing                                                        ║
║   lots = await sugar.calc_lot_by_risk("EURUSD", risk_percent=1.0, st_pips=15)║
║                                                                              ║
║   # Watch tickets                                                            ║
║   async def on_tickets(ev): print("tickets:", ev)                            ║
║   wid = await sugar.watch_tickets(on_tickets, pull_interval_ms=500)          ║
║   await sugar.unwatch(wid)                                                   ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ Gotchas                                                                      ║
║   • Limit/Stop require explicit price; Market ignores price.                 ║
║   • SL/TP precedence: absolute price beats pips-derived if both provided.    ║
║   • For BE/trailing workers, order disappearance stops the worker silently.  ║
║   • In mixed protobuf/dict backends, field names vary; this class defends.   ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

