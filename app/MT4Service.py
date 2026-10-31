# app/MT4Service.py
"""
MT4Service - Low-level wrapper around MT4Account (protobuf API).

This module provides a thin abstraction layer over the raw MT4Account protobuf interface,
handling common patterns like:
- Unpacking protobuf responses into Python lists/dicts
- Normalizing symbol names and parameters
- Providing flexible method signatures with sensible defaults
- Converting between different enum representations

The service is designed to be used directly or wrapped by higher-level abstractions
like MT4Sugar for more convenient trading operations.
"""
from __future__ import annotations

from typing import Any, Dict, Optional, Union, Sequence, Iterable, AsyncIterator, TYPE_CHECKING
from datetime import datetime, timedelta

from MetaRpcMT4.mt4_account import MT4Account
import logging
from app.Helper.errors import map_backend_error
from app.Helper.rate_limit import RateLimiter
# Protobuf enums for mapping types
from package.MetaRpcMT4 import mt4_term_api_market_info_pb2 as market_info_pb2
from package.MetaRpcMT4 import mt4_term_api_account_helper_pb2 as account_helper_pb2
from package.MetaRpcMT4 import mt4_term_api_trading_helper_pb2 as trading_helper_pb2

if TYPE_CHECKING:
    from app.MT4Sugar import MT4Sugar


# ───────────────────────── HELPER FUNCTIONS ─────────────────────────

def _as_list(obj: Any) -> list:
    """
    Safely unpack protobuf response into a plain Python list.

    Handles various protobuf container types (data, items, symbols, etc.)
    and nested structures. Returns empty list if obj is None.
    """
    if obj is None:
        return []
    if isinstance(obj, (list, tuple, set)):
        return list(obj)
    if isinstance(obj, dict):
        vals = list(obj.values())
        if len(vals) == 1 and isinstance(vals[0], (list, tuple, set)):
            return list(vals[0])
        return vals

    # Common protobuf container field names
    for attr in (
        "data", "items", "symbols", "names", "values",
        "Data", "Items", "Symbols", "Names", "Values",
        "result", "Result",
        # MT4 protobuf repeated-field names
        "SymbolNameInfos", "symbol_infos", "order_infos", "orders_info",
        "infos", "quotes",
    ):
        if hasattr(obj, attr):
            try:
                seq = getattr(obj, attr)
                return list(seq)
            except Exception:
                pass

    # Sometimes data is nested deeper: .data.data
    for a1 in ("data", "Data", "result", "Result"):
        inner = getattr(obj, a1, None)
        if inner is not None:
            try:
                return _as_list(inner)
            except Exception:
                pass

    try:
        return list(obj)
    except TypeError:
        return [obj]


def _norm_sym_name(s: str) -> str:
    """
    Normalize symbol name to standard format.

    - Strips whitespace
    - Converts to uppercase
    - Removes trailing dots (e.g., 'EURUSD.' -> 'EURUSD')
    """
    if not s:
        return ""
    s = str(s).strip().upper()
    if s.endswith("."):
        s = s[:-1]
    return s


def _sym_name(x: Any) -> str:
    """
    Extract symbol name from various input types.

    Handles: string, dict, protobuf object with 'symbol'/'name' fields.
    Returns normalized uppercase symbol name.
    """
    # 1) Plain string
    if isinstance(x, str):
        return _norm_sym_name(x)

    # 2) Dictionary with symbol fields
    if isinstance(x, dict):
        for k in (
            "symbol", "name", "Symbol", "symbol_name", "SymbolName",
            "code", "Code", "instrument", "Instrument", "value", "Value",
        ):
            if k in x and x[k]:
                return _norm_sym_name(x[k])
        # Nested structure: {"symbol": {"name": "EURUSD"}}
        for k in ("symbol", "Symbol", "instrument", "Instrument"):
            v = x.get(k)
            if isinstance(v, dict):
                for kk in ("name", "symbol", "Symbol", "code", "Code", "value", "Value"):
                    if kk in v and v[kk]:
                        return _norm_sym_name(v[kk])

    # 3) Protobuf object with attributes
    for k in (
        "symbol", "name", "Symbol", "symbol_name", "SymbolName",
        "code", "Code", "instrument", "Instrument", "value", "Value",
    ):
        if hasattr(x, k):
            try:
                v = getattr(x, k)
                if v:
                    return _norm_sym_name(v)
            except Exception:
                pass

    # 4) Deep nesting: obj.symbol.name
    try:
        sym = getattr(x, "symbol", None) or getattr(x, "Symbol", None) or getattr(x, "instrument", None)
        if sym is not None:
            if isinstance(sym, str):
                return _norm_sym_name(sym)
            for kk in ("name", "symbol", "Symbol", "code", "Code", "value", "Value"):
                if hasattr(sym, kk):
                    v = getattr(sym, kk)
                    if v:
                        return _norm_sym_name(v)
                elif isinstance(sym, dict) and kk in sym and sym[kk]:
                    return _norm_sym_name(sym[kk])
    except Exception:
        pass

    return ""


def _to_timeframe_enum(tf: Union[str, int]) -> int:
    """
    Convert timeframe string to protobuf enum value.

    Supports MT4 standard format ("M1", "H1", "D1") and enum names ("QH_PERIOD_H1").
    Returns the corresponding ENUM_QUOTE_HISTORY_TIMEFRAME value.
    """
    if isinstance(tf, int):
        return tf
    key = str(tf).strip().upper()
    # Allow direct enum name like "QH_PERIOD_H1"
    if hasattr(market_info_pb2.ENUM_QUOTE_HISTORY_TIMEFRAME, key):
        return getattr(market_info_pb2.ENUM_QUOTE_HISTORY_TIMEFRAME, key)
    # Map short forms to enum names
    table = {
        "M1": "QH_PERIOD_M1", "1M": "QH_PERIOD_M1",
        "M5": "QH_PERIOD_M5", "5M": "QH_PERIOD_M5",
        "M15": "QH_PERIOD_M15", "15M": "QH_PERIOD_M15",
        "M30": "QH_PERIOD_M30", "30M": "QH_PERIOD_M30",
        "H1": "QH_PERIOD_H1", "1H": "QH_PERIOD_H1",
        "H4": "QH_PERIOD_H4", "4H": "QH_PERIOD_H4",
        "D1": "QH_PERIOD_D1", "1D": "QH_PERIOD_D1", "D": "QH_PERIOD_D1",
        "W1": "QH_PERIOD_W1", "1W": "QH_PERIOD_W1", "W": "QH_PERIOD_W1",
        "MN1": "QH_PERIOD_MN1", "1MN": "QH_PERIOD_MN1", "MN": "QH_PERIOD_MN1", "MO": "QH_PERIOD_MN1",
    }
    name = table.get(key, key)
    return getattr(market_info_pb2.ENUM_QUOTE_HISTORY_TIMEFRAME, name)


def _to_opened_sort(sort: Optional[Union[str, int]]) -> Optional[int]:
    """Convert sort mode string/int to protobuf enum value for opened_orders sorting."""
    if sort is None:
        return None
    if isinstance(sort, int):
        return sort
    name = sort.strip().upper()
    return getattr(account_helper_pb2.EnumOpenedOrderSortType, name)


def _to_history_sort(sort: Optional[Union[str, int]]) -> Optional[int]:
    """Convert history sort mode string/int to protobuf enum value."""
    if sort is None:
        return None
    if isinstance(sort, int):
        return sort
    name = sort.strip().upper()
    return getattr(account_helper_pb2.EnumOrderHistorySortType, name)


def _to_operation_type(
    *,
    side: Optional[str] = None,
    type_: Optional[str] = None,
    op: Optional[Union[str, int]] = None,
):
    """
    Convert order operation parameters to protobuf OrderSendOperationType enum.

    Supports direct enum values, enum names, or combinations of side/type.
    Examples: "buy"+"market" -> OC_OP_BUY, "sell"+"limit" -> OC_OP_SELLLIMIT
    """
    if op is not None:
        if isinstance(op, int):
            return op
        name = str(op).strip().upper()
        # Check for enum prefixes
        if not name.startswith("OC_OP_") and not name.startswith("OP_"):
            name = "OC_OP_" + name
        # Replace old OP_ prefix with OC_OP_
        elif name.startswith("OP_") and not name.startswith("OC_OP_"):
            name = "OC_" + name
        return getattr(trading_helper_pb2.OrderSendOperationType, name)

    s = (side or "").strip().lower()
    t = (type_ or "").strip().lower()
    if t in ("market", "instant", "immediate"):
        return getattr(trading_helper_pb2.OrderSendOperationType, "OC_OP_BUY" if s == "buy" else "OC_OP_SELL")
    if t == "limit":
        return getattr(trading_helper_pb2.OrderSendOperationType, "OC_OP_BUYLIMIT" if s == "buy" else "OC_OP_SELLLIMIT")
    if t == "stop":
        return getattr(trading_helper_pb2.OrderSendOperationType, "OC_OP_BUYSTOP" if s == "buy" else "OC_OP_SELLSTOP")
    return getattr(trading_helper_pb2.OrderSendOperationType, "OC_OP_BUY" if s == "buy" else "OC_OP_SELL")


# ───────────────────────── MT4SERVICE CLASS ─────────────────────────

class MT4Service:
    """
    Low-level service wrapper around MT4Account protobuf API.

    Provides consistent method signatures and convenient parameter handling
    for MT4 trading operations. Acts as a thin translation layer between
    protobuf API and Python-friendly interfaces.

    This service can be used directly or wrapped by MT4Sugar for high-level operations.
    """

    def __init__(self, account: MT4Account) -> None:
        self._acc = account
        self._sugar: Optional["MT4Sugar"] = None

    @property
    def sugar(self) -> "MT4Sugar":
        """Lazy-loaded MT4Sugar instance for high-level operations."""
        if self._sugar is None:
            from app.MT4Sugar import MT4Sugar
            self._sugar = MT4Sugar(self)
        return self._sugar  # type: ignore[return-value]

    # ───────────────── CONNECTION ─────────────────

    async def disconnect(self, delete: bool = False) -> None:
        """Disconnect from MT4 server and close the channel."""
        if hasattr(self._acc, "disconnect"):
            try:
                await self._acc.disconnect(delete=delete)
            except TypeError:
                # Older MT4Account.disconnect() has no `delete` parameter.
                await self._acc.disconnect()
        elif hasattr(self._acc, "channel") and self._acc.channel:
            await self._acc.channel.close()

    async def __aenter__(self) -> "MT4Service":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.disconnect()

    def get_headers(self) -> dict:
        """Get current connection headers (terminal ID, etc.)."""
        return self._acc.get_headers()

    async def reconnect(self) -> None:
        """Reconnect to MT4 server using existing credentials."""
        await self._acc.reconnect()

    async def connect_by_host_port(
        self,
        host: str,
        port: int,
        base_symbol: Optional[str] = None,
        timeout_s: Optional[float] = None,
    ) -> Any:
        """
        Connect to MT4 server via direct host:port.

        Args:
            host: Server hostname or IP address
            port: Server port (typically 443)
            base_symbol: Initial chart symbol (default "EURUSD")
            timeout_s: Connection timeout in seconds
        """
        kwargs = {}
        if base_symbol is not None:
            kwargs["base_chart_symbol"] = base_symbol
        if timeout_s is not None:
            kwargs["timeout_seconds"] = int(timeout_s)
        return await self._acc.connect_by_host_port(host=host, port=port, **kwargs)

    async def connect_by_server_name(
        self,
        server_name: str,
        base_symbol: Optional[str] = None,
        timeout_s: Optional[float] = None,
    ) -> Any:
        kwargs = {"server_name": server_name}
        if base_symbol is not None:
            kwargs["base_chart_symbol"] = base_symbol
        if timeout_s is not None:
            kwargs["timeout_seconds"] = int(timeout_s)
        return await self._acc.connect_by_server_name(**kwargs)

    # ───────────────── ACCOUNT ────────────────────

    async def account_summary(self) -> Any:
        return await self._acc.account_summary()

    async def trade_stats(self, since: Optional[datetime] = None) -> Any:
        """Aggregated trade statistics. Pass-through to MT4Account.trade_stats."""
        return await self._acc.trade_stats(from_time=since)

    async def trade_unrealized_pl(self, since: Optional[datetime] = None) -> Any:
        """Per-open-order unrealized P/L extrema (MFE/MAE)."""
        return await self._acc.trade_unrealized_pl(from_time=since)

    async def equity_history(
        self, since: Optional[datetime] = None, exclude_same_bars: Optional[bool] = None
    ) -> Any:
        """Equity-curve points with running drawdowns."""
        return await self._acc.equity_history(from_time=since, exclude_same_bars=exclude_same_bars)

    async def trade_stats_equity_history(
        self, since: Optional[datetime] = None, exclude_same_bars: Optional[bool] = None
    ) -> Any:
        """Stats + equity points + trades in one call."""
        return await self._acc.trade_stats_equity_history(
            from_time=since, exclude_same_bars=exclude_same_bars
        )

    # ─────────────── SYMBOLS / QUOTES ─────────────

    async def symbols(self, mask: Optional[Union[str, Sequence[str]]] = None) -> Any:
        """
        MT4Account.symbols() returns a pb container—unpack and filter it.
    mask:
          - None -> no filter
          - str -> substring (case-insensitive)
          - Sequence[str] -> exact names (case-insensitive), with normalization
        """
        raw = await self._acc.symbols()
        items = _as_list(raw)

        if mask is None:
            return items

        # list of names
        if isinstance(mask, (list, tuple, set)):
            target = {_norm_sym_name(x) for x in mask}
            return [x for x in items if _sym_name(x) in target]

        # mask string
        m = str(mask).lower()
        return [x for x in items if m in _sym_name(x).lower()]

    async def symbol_params_many(
        self,
        symbols: Union[str, Sequence[str], None],
    ) -> Any:
        """
        In the package: symbol_params_many(symbol_name: Optional[str])
        - string -> send a single symbol,
        - None -> take all,
        - list -> take all and filter by normalized names.
        """
        if isinstance(symbols, str):
            return await self._acc.symbol_params_many(symbol_name=symbols)

        all_params_raw = await self._acc.symbol_params_many(symbol_name=None)
        all_params = _as_list(all_params_raw)
        if symbols is None:
            return all_params

        want = {_norm_sym_name(s) for s in symbols}
        out = []
        for it in all_params:
            name = _sym_name(it)
            if name and name in want:
                out.append(it)
        return out

    async def quote(self, symbol: str) -> Any:
        return await self._acc.quote(symbol)

    async def quote_many(self, symbols: Sequence[str]) -> Any:
        return await self._acc.quote_many(list(symbols))

    async def quote_history(
        self,
        symbol: str,
        *,
        timeframe: Union[str, int] = "H1",
        since: datetime | None = None,
        until: datetime | None = None,
        limit: Optional[int] = 100,
    ) -> Any:
        """
     If since/until are not specified, we substitute a window by tf and limit:
     until := now (UTC naive)
     since := until - bars * duration_per_bar
     Then we try the packet signatures.
        """
        # 1) let's substitute a reasonable range
        now = datetime.utcnow()
        if until is None:
            until = now

        # bar length estimation
        tf_map_minutes = {
            "M1": 1, "M5": 5, "M15": 15, "M30": 30,
            "H1": 60, "H4": 240, "D1": 1440, "W1": 10080, "MN1": 43200,
        }
        if isinstance(timeframe, str):
            tf_key = timeframe.strip().upper()
            bar_minutes = tf_map_minutes.get(tf_key, 60)
        else:
            bar_minutes = 60  # default if enum/int is passed

        bars = int(limit or 100)
        approx = timedelta(minutes=bar_minutes * bars)
        if since is None:
            since = until - approx

        fn = getattr(self._acc, "quote_history")

        # 2) first signatures that expect since/until/limit by name
        try:
            return await fn(symbol=symbol, since=since, until=until, limit=limit)
        except TypeError:
            pass
        try:
            return await fn(symbol=symbol, start=since, end=until, limit=limit)
        except TypeError:
            pass

        # 3) if the build requires a timeframe enum positionally
        tf_val = _to_timeframe_enum(timeframe)
        try:
            return await fn(symbol, tf_val, since, until)
        except TypeError:
            return await fn(symbol=symbol, timeframe=tf_val, since=since, until=until, limit=limit)

    async def tick_value_with_size(
        self,
        symbol: Optional[str] = None,
        *,
        symbols: Optional[Sequence[str]] = None,
    ) -> Any:
        """
        In package: tick_value_with_size(symbol_names: list[str])
        """
        names = list(symbols) if symbols else ([symbol] if symbol else ["EURUSD"])
        return await self._acc.tick_value_with_size(symbol_names=names)

    async def symbol_select(self, symbol: str, select: bool = True) -> Any:
        """Add/remove a symbol in Market Watch."""
        return await self._acc.symbol_select(symbol, select)

    async def server_timezone(self) -> Any:
        """Trade-server timezone / UTC offset."""
        return await self._acc.server_timezone()

    # ─────────────── ORDERS / HISTORY ─────────────

    async def opened_orders(
        self,
        *,
        sort: Optional[Union[str, int]] = None,
    ) -> Any:
        if sort is None:
            return await self._acc.opened_orders()
        sort_mode = _to_opened_sort(sort)
        return await self._acc.opened_orders(sort_mode=sort_mode)

    async def opened_orders_tickets(self) -> Any:
        return await self._acc.opened_orders_tickets()

    async def orders_history(
        self,
        *,
        sort: Optional[Union[str, int]] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
    ) -> Any:
        kwargs = {}
        if sort is not None:
            kwargs["sort_mode"] = _to_history_sort(sort)
        if since is not None:
            kwargs["from_time"] = since
        if until is not None:
            kwargs["to_time"] = until
        if page is not None:
            kwargs["page_number"] = page
        if page_size is not None:
            kwargs["items_per_page"] = page_size
        return await self._acc.orders_history(**kwargs)

    # ─────────────────── TRADING ──────────────────

    async def order_send(self, **kwargs: Any) -> Any:
        """
        Exact in package:
          order_send(symbol, operation_type, volume, price=None, slippage=None,
                     stoploss=None, takeprofit=None, comment=None,
                     magic_number=None, expiration=None)

        We accept friendly keys: side/type/lots/deviation_pips/magic.
        """
        symbol = kwargs.pop("symbol")
        op = kwargs.pop("operation_type", None)
        side = kwargs.pop("side", None)
        type_ = kwargs.pop("type", None)
        operation_type = _to_operation_type(side=side, type_=type_, op=op)

        volume = kwargs.pop("volume", None)
        if volume is None:
            volume = kwargs.pop("lots", None)
        if volume is None:
            raise ValueError("volume/lots is required")

        if "deviation_pips" in kwargs and "slippage" not in kwargs:
            try:
                kwargs["slippage"] = int(kwargs.pop("deviation_pips"))
            except Exception:
                kwargs.pop("deviation_pips", None)

        if "magic" in kwargs and "magic_number" not in kwargs:
            kwargs["magic_number"] = kwargs.pop("magic")

        # Map sl/tp to stoploss/takeprofit
        if "sl" in kwargs and "stoploss" not in kwargs:
            kwargs["stoploss"] = kwargs.pop("sl")
        if "tp" in kwargs and "takeprofit" not in kwargs:
            kwargs["takeprofit"] = kwargs.pop("tp")

        return await self._acc.order_send(
            symbol=symbol,
            operation_type=operation_type,
            volume=volume,
            **kwargs,
        )

    async def order_modify(self, ticket: int, **kwargs: Any) -> Any:
        """
        Exact:
          order_modify(order_ticket, new_price=None, new_stop_loss=None,
                       new_take_profit=None, new_expiration=None)
        Accepts: sl_price -> new_stop_loss, tp_price -> new_take_profit.
        """
        if "sl_price" in kwargs and "new_stop_loss" not in kwargs:
            kwargs["new_stop_loss"] = kwargs.pop("sl_price")
        if "tp_price" in kwargs and "new_take_profit" not in kwargs:
            kwargs["new_take_profit"] = kwargs.pop("tp_price")
        return await self._acc.order_modify(order_ticket=ticket, **kwargs)

    async def order_close_delete(self, ticket: int, **kwargs: Any) -> Any:
        """Exact: order_close_delete(order_ticket, lots=None, closing_price=None, slippage=None)."""
        return await self._acc.order_close_delete(order_ticket=ticket, **kwargs)

    async def order_close_by(self, ticket_a: int, ticket_b: int, **kwargs: Any) -> Any:
        """Exact: order_close_by(ticket_to_close, opposite_ticket_closing_by)."""
        return await self._acc.order_close_by(
            ticket_to_close=ticket_a,
            opposite_ticket_closing_by=ticket_b,
            **kwargs,
        )

    # ─────────────────── STREAMS ──────────────────

    async def on_symbol_tick(self, symbols: Union[str, Iterable[str]]) -> AsyncIterator[Any]:
        names = [symbols] if isinstance(symbols, str) else list(symbols) or ["EURUSD"]
        async for item in self._acc.on_symbol_tick(names):
            yield item

    async def on_trade(self) -> AsyncIterator[Any]:
        async for item in self._acc.on_trade():
            yield item

    async def on_opened_orders_tickets(
        self,
        pull_interval_milliseconds: Optional[int] = None,
    ) -> AsyncIterator[Any]:
        if pull_interval_milliseconds is None:
            async for item in self._acc.on_opened_orders_tickets():
                yield item
        else:
            async for item in self._acc.on_opened_orders_tickets(
                pull_interval_milliseconds=pull_interval_milliseconds
            ):
                yield item

    async def on_opened_orders_profit(
        self,
        timer_period_milliseconds: Optional[int] = None,
    ) -> AsyncIterator[Any]:
        if timer_period_milliseconds is None:
            async for item in self._acc.on_opened_orders_profit():
                yield item
        else:
            async for item in self._acc.on_opened_orders_profit(
                timer_period_milliseconds=timer_period_milliseconds
            ):
                yield item

    async def on_connect_state(
        self,
        terminal_ids: Optional[Sequence[str]] = None,
    ) -> AsyncIterator[Any]:
        """Stream terminal connection-state changes."""
        async for item in self._acc.on_connect_state(
            terminal_ids=list(terminal_ids) if terminal_ids else None
        ):
            yield item

"""
╔══════════════════════════════════════════════════════════════════════════════╗
║ FILE app/MT4Service.py — Low-level service wrapper over MT4Account (pb API)  ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ Purpose:                                                                     ║
║   Thin abstraction above MT4Account protobuf RPCs: normalizes inputs/outputs,║
║   unifies method signatures, maps enums/flags, and relays streams.           ║
║                                                                              ║
║ Depends:                                                                     ║
║   MetaRpcMT4.mt4_account.MT4Account (core),                                  ║
║   package.MetaRpcMT4.*_pb2 (market_info, account_helper, trading_helper).    ║
║                                                                              ║
║ Exports:                                                                     ║
║   MT4Service class with:                                                     ║
║     • Connection: get_headers(), reconnect(),                                ║
║       connect_by_host_port(), connect_by_server_name().                      ║
║     • Account:  account_summary().                                           ║
║     • Market:   symbols(), symbol_params_many(), quote(),                    ║
║                  quote_many(), quote_history(), tick_value_with_size().      ║
║     • Orders:   opened_orders(), opened_orders_tickets(), orders_history().  ║
║     • Trading:  order_send(), order_modify(),                                ║
║                  order_close_delete(), order_close_by().                     ║
║     • Streams:  on_symbol_tick(), on_trade(),                                ║
║                  on_opened_orders_tickets(), on_opened_orders_profit().      ║
║     • sugar property: lazy MT4Sugar facade for high-level ops.               ║
║                                                                              ║
║ Behavior / Defaults:                                                         ║
║   • Friendly args → pb fields: side/type/lots/deviation_pips/magic/sl/tp     ║
║     are translated into operation_type/volume/slippage/magic_number/...      ║
║   • Symbols normalized (trim/upper/remove trailing dot).                     ║
║   • symbols(mask): supports None / str contains / list-of-exact names.       ║
║   • quote_history(): timeframe str ("H1") or enum; auto infers since/until   ║
║     by (limit * TF) if not provided; tries multiple package signatures.      ║
║   • Sorting: opened_orders/orders_history accept str/int mapped to pb enums. ║
║   • Streams: simply relay underlying async generators from MT4Account.       ║
║                                                                              ║
║ Rate limit:                                                                  ║
║   • None at service level (no throttling here).                              ║
║                                                                              ║
║ Safety / Notes:                                                              ║
║   • No implicit pips↔price math (absolute prices expected at this layer).    ║
║   • Returns raw pb objects (or plain lists via _as_list where sensible).     ║
║   • Acts as a translation layer; does not hide MT4Account capabilities.      ║
╚══════════════════════════════════════════════════════════════════════════════╝


╔═════════════════════════════════════════════════════════════════════════════════╗
║ API Map — friendly parameters → protobuf payloads                               ║
╠══════════════════════════════════════╦══════════════════════════════════════════╣
║ Input (friendly)                     ║ Mapped to (pb)                           ║
╠══════════════════════════════════════╬══════════════════════════════════════════╣
║ side="buy"/"sell", type_="market"    ║ trading_helper_pb2.OrderSendOperationType║
║ /"limit"/"stop" or op enum/name      ║ (auto-detected in _to_operation_type)    ║
╠──────────────────────────────────────╬──────────────────────────────────────────╣
║ lots                                 ║ volume                                   ║
╠──────────────────────────────────────╬──────────────────────────────────────────╣
║ deviation_pips                       ║ slippage (int)                           ║
╠──────────────────────────────────────╬──────────────────────────────────────────╣
║ magic                                ║ magic_number                             ║
╠──────────────────────────────────────╬──────────────────────────────────────────╣
║ sl / tp                              ║ stoploss / takeprofit                    ║
╠──────────────────────────────────────╬──────────────────────────────────────────╣
║ sl_price / tp_price (order_modify)   ║ new_stop_loss / new_take_profit          ║
╠──────────────────────────────────────╬──────────────────────────────────────────╣
║ timeframe="H1"/"M5"/"D1" or enum     ║ ENUM_QUOTE_HISTORY_TIMEFRAME             ║
╠──────────────────────────────────────╬──────────────────────────────────────────╣
║ sort (str/int) for opened/history    ║ account_helper_pb2 enum values           ║
╚══════════════════════════════════════╩══════════════════════════════════════════╝


╔══════════════════════════════════════════════════════════════════════════════╗
║ Helper internals (key utilities)                                             ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ _as_list(obj)             — safely flattens pb containers to Python list     ║
║ _norm_sym_name(s)         — trims/uppercases/removes trailing dot            ║
║ _sym_name(x)              — extracts symbol from str/dict/pb/nested fields   ║
║ _to_timeframe_enum(tf)    — maps "H1"/"D1"/enum-name → pb enum               ║
║ _to_opened_sort()/…       — maps string/int → sort enums for pb              ║
║ _to_operation_type(...)   — side+type/op → OrderSendOperationType            ║
╚══════════════════════════════════════════════════════════════════════════════╝

"""
# Cheat sheet of correspondences

"""
# order_send friendly -> pb
await svc.order_send(
    symbol="EURUSD",
    side="buy",          # -> operation_type = OC_OP_BUY
    type="limit",        # buy+limit => OC_OP_BUYLIMIT
    lots=0.10,           # -> volume = 0.10
    deviation_pips=2,    # -> slippage = 2 (integer points as backend expects)
    sl=1.0830,           # -> stoploss = 1.0830 (absolute price)
    tp=1.0930,           # -> takeprofit = 1.0930 (absolute price)
    magic=9001,          # -> magic_number = 9001
    price=1.0850,        # pending price (pb field price)
    comment="DocsDemo",
)

# order_modify friendly -> pb
await svc.order_modify(
    ticket=123456,
    sl_price=1.0820,     # -> new_stop_loss = 1.0820
    tp_price=1.0950,     # -> new_take_profit = 1.0950
    # expiration passes through if provided
)

# "H1" -> ENUM_QUOTE_HISTORY_TIMEFRAME.QH_PERIOD_H1
bars = await svc.quote_history("EURUSD", timeframe="H1", limit=120)


"""


# ============================================================================
# MT4ServiceTrade — trade-convenience shortcuts (merged from MT4Service_Trade_mod)
# ============================================================================
class MT4ServiceTrade:
    """
Narrow shortcuts for navigating the MT4Service platform without any sugar.
- No pips, normalizations, or presets.
- All prices are now absolute.
    """

    def __init__(self, svc: MT4Service) -> None:
        self._svc = svc
        self.log = logging.getLogger("MT4ServiceTrade")
        if not self.log.handlers:
            h = logging.StreamHandler()
            h.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s %(name)s: %(message)s"))
            self.log.addHandler(h)
            self.log.setLevel(logging.INFO)

        self._defaults: Dict[str, Any] = {
            "magic": None,
            "deviation_pips": None,
            "comment": None,
        }
        self._order_send_rl = RateLimiter(per_second=10.0)

    # ── defaults ──────────────────────────────────────────────────────────────
    def set_trade_defaults(
        self,
        *,
        magic: Optional[int] = None,
        deviation_pips: Optional[float] = None,
        comment: Optional[str] = None,
    ) -> None:
        """Set default parameters (magic, deviation, comment) for all subsequent orders."""
        if magic is not None:
            self._defaults["magic"] = magic
        if deviation_pips is not None:
            self._defaults["deviation_pips"] = deviation_pips
        if comment is not None:
            self._defaults["comment"] = comment

    # ── core ──────────────────────────────────────────────────────────────────
    async def order_send_with_defaults(self, **kwargs) -> int:
        """
    Mixes in defaults and calls low-level order_send().
    All values ​​(price/sl/tp) are expected to be absolute prices.
        """
        payload = {
            **{k: v for k, v in self._defaults.items() if v is not None},
            **{k: v for k, v in kwargs.items() if v is not None},
        }

        # We guarantee a quick connection, without any external shocks
        try:
            _ = self._svc.get_headers()
        except Exception:
            try:
                await self._svc.reconnect()
                _ = self._svc.get_headers()
            except Exception as e2:
                raise map_backend_error(e2, context="reconnect")

        await self._order_send_rl.acquire()
        try:
            result = await self._svc.order_send(**payload)
        except Exception as e:
            raise map_backend_error(e, context="order_send", payload=payload)

        # Extract ticket from result (protobuf OrderSendData or dict)
        if hasattr(result, "ticket"):
            ticket = int(result.ticket)
        elif hasattr(result, "Ticket"):
            ticket = int(result.Ticket)
        elif isinstance(result, dict):
            ticket = int(result.get("ticket") or result.get("Ticket") or result.get("order") or result.get("Order"))
        else:
            ticket = int(result)

        return ticket

    # ── market ────────────────────────────────────────────────────────────────
    async def buy_market(
        self, *, symbol: str, lots: float,
        sl: Optional[float] = None, tp: Optional[float] = None,
        magic: Optional[int] = None, deviation_pips: Optional[float] = None,
        comment: Optional[str] = None,
    ) -> int:
        """Send instant BUY market order. Returns ticket number."""
        return await self.order_send_with_defaults(
            symbol=symbol, side="buy", type="market",
            lots=lots, sl=sl, tp=tp, magic=magic,
            deviation_pips=deviation_pips, comment=comment,
        )

    async def sell_market(
        self, *, symbol: str, lots: float,
        sl: Optional[float] = None, tp: Optional[float] = None,
        magic: Optional[int] = None, deviation_pips: Optional[float] = None,
        comment: Optional[str] = None,
    ) -> int:
        """Send instant SELL market order. Returns ticket number."""
        return await self.order_send_with_defaults(
            symbol=symbol, side="sell", type="market",
            lots=lots, sl=sl, tp=tp, magic=magic,
            deviation_pips=deviation_pips, comment=comment,
        )

    # ── pending: limit/stop ───────────────────────────────────────────────────
    async def buy_limit(
        self, *, symbol: str, price: float, lots: float,
        sl: Optional[float] = None, tp: Optional[float] = None,
        magic: Optional[int] = None, comment: Optional[str] = None,
    ) -> int:
        """Place BUY LIMIT order at specified price (below market). Returns ticket number."""
        return await self.order_send_with_defaults(
            symbol=symbol, side="buy", type="limit",
            price=price, lots=lots, sl=sl, tp=tp,
            magic=magic, comment=comment,
        )

    async def sell_limit(
        self, *, symbol: str, price: float, lots: float,
        sl: Optional[float] = None, tp: Optional[float] = None,
        magic: Optional[int] = None, comment: Optional[str] = None,
    ) -> int:
        """Place SELL LIMIT order at specified price (above market). Returns ticket number."""
        return await self.order_send_with_defaults(
            symbol=symbol, side="sell", type="limit",
            price=price, lots=lots, sl=sl, tp=tp,
            magic=magic, comment=comment,
        )

    async def buy_stop(
        self, *, symbol: str, price: float, lots: float,
        sl: Optional[float] = None, tp: Optional[float] = None,
        magic: Optional[int] = None, comment: Optional[str] = None,
    ) -> int:
        """Place BUY STOP order at specified price (above market). Returns ticket number."""
        return await self.order_send_with_defaults(
            symbol=symbol, side="buy", type="stop",
            price=price, lots=lots, sl=sl, tp=tp,
            magic=magic, comment=comment,
        )

    async def sell_stop(
        self, *, symbol: str, price: float, lots: float,
        sl: Optional[float] = None, tp: Optional[float] = None,
        magic: Optional[int] = None, comment: Optional[str] = None,
    ) -> int:
        """Place SELL STOP order at specified price (below market). Returns ticket number."""
        return await self.order_send_with_defaults(
            symbol=symbol, side="sell", type="stop",
            price=price, lots=lots, sl=sl, tp=tp,
            magic=magic, comment=comment,
        )

    # ── modify / close (absolute prices) ──────────────────────────────────────
    async def modify_sl_tp(self, *, ticket: int, sl_price: Optional[float] = None, tp_price: Optional[float] = None) -> None:
        """Modify Stop Loss and/or Take Profit for existing order (absolute prices)."""
        try:
            await self._svc.order_modify(ticket=ticket, sl_price=sl_price, tp_price=tp_price)
        except Exception as e:
            raise map_backend_error(e, context="order_modify", payload={"ticket": ticket, "sl": sl_price, "tp": tp_price})

    async def close(self, *, ticket: int) -> None:
        """Close order completely by ticket number."""
        try:
            await self._svc.order_close_delete(ticket=ticket)
        except Exception as e:
            raise map_backend_error(e, context="order_close_delete", payload={"ticket": ticket})

    async def close_partial(self, *, ticket: int, lots: float) -> None:
        """Close partial volume of order (specify lots to close)."""
        try:
            await self._svc.order_close_delete(ticket=ticket, lots=float(lots))
        except Exception as e:
            raise map_backend_error(e, context="order_close_delete", payload={"ticket": ticket, "lots": lots})

    async def close_by(self, *, ticket_a: int, ticket_b: int) -> None:
        """Close order A by opposite order B (hedge close)."""
        try:
            await self._svc.order_close_by(ticket_a=ticket_a, ticket_b=ticket_b)
        except Exception as e:
            raise map_backend_error(e, context="order_close_by", payload={"ticket_a": ticket_a, "ticket_b": ticket_b})


# ───────────────────────────────────────────────────────────────────────────
# How to use in main (low-level style)
# from app.MT4Service_Trade_mod import MT4ServiceTrade
# 
# svc = MT4Service(low_acc)            
# trade = MT4ServiceTrade(svc)
# trade.set_trade_defaults(magic=7001, deviation_pips=2.0, comment="LL-Quick")
#
# ticket = await trade.buy_market(symbol="EURUSD", lots=0.01)
# await trade.modify_sl_tp(ticket=ticket, sl_price=1.07650)
# await trade.close_partial(ticket=ticket, lots=0.005)
# await trade.close(ticket=ticket)
# ───────────────────────────────────────────────────────────────────────────

"""
╔══════════════════════════════════════════════════════════════════════════════╗
║ FILE app/MT4Service_Trade_mod.py — MT4 trading shortcuts over MT4Service     ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ Purpose: Thin convenience layer that calls MT4Service trading RPCs, adding   ║
║          sane defaults, rate-limiting, and unified error handling.           ║
║ Depends: MT4Service (low-level), RateLimiter, map_backend_error, reconnect.  ║
║ Exports: MT4ServiceTrade class with “shortcut” methods (buy/sell, modify,    ║
║          close/partial, close_by).                                           ║
║ Defaults: set_trade_defaults(magic, deviation_pips, comment) are merged into ║
║          each order_send call (no unit conversions, absolute prices only).   ║
║ Rate limit: ~10 order_send ops / second via internal RateLimiter.            ║
║ Safety: No pips/points normalization; expects absolute prices. On failure,   ║
║         tries get_headers() and reconnect() before mapping backend errors.   ║
║ Scope: Does NOT replace the service; it forwards to MT4Service methods.      ║
╚══════════════════════════════════════════════════════════════════════════════╝

╔════════════════════════════════════════════════════════════════════════════════╗
║ Shortcuts — what each wrapper does                                             ║
╠════════════════════════════════════════╦═══════════════════════════════════════╣
║ Method                                 ║ What it does / required params        ║
╠════════════════════════════════════════╬═══════════════════════════════════════╣
║ buy_market(symbol, lots, **opts)       ║ Sends MARKET BUY. Forwards to         ║
║                                        ║ order_send with type=BUY, uses        ║
║                                        ║ defaults (magic/deviation/comment).   ║
╠════════════════════════════════════════╬═══════════════════════════════════════╣
║ sell_market(symbol, lots, **opts)      ║ Sends MARKET SELL. Same flow as       ║
║                                        ║ buy_market, different side.           ║
╠════════════════════════════════════════╬═══════════════════════════════════════╣
║ buy_limit(symbol, price, lots, **opts) ║ Creates BUY LIMIT at price. Wrapper   ║
║                                        ║ over order_send(type=BUY_LIMIT).      ║
╠════════════════════════════════════════╬═══════════════════════════════════════╣
║ sell_limit(symbol, price, lots, **opts)║ Creates SELL LIMIT at price.          ║
║                                        ║ order_send(type=SELL_LIMIT).          ║
╠════════════════════════════════════════╬═══════════════════════════════════════╣
║ buy_stop(symbol, price, lots, **opts)  ║ Creates BUY STOP at price.            ║
║                                        ║ order_send(type=BUY_STOP).            ║
╠════════════════════════════════════════╬═══════════════════════════════════════╣
║ sell_stop(symbol, price, lots, **opts) ║ Creates SELL STOP at price.           ║
║                                        ║ order_send(type=SELL_STOP).           ║
╠════════════════════════════════════════╬═══════════════════════════════════════╣
║ modify_sl_tp(ticket, sl=None, tp=None, ║ Adjusts SL/TP via MT4Service.         ║
║ expiration=None)                       ║ Forwards to order_modify (maps        ║
║                                        ║ sl→new_stop_loss, tp→new_take_profit).║
╠════════════════════════════════════════╬═══════════════════════════════════════╣
║ close(ticket, lots=None, price=None,   ║ Closes order or part of it via        ║
║ slippage=None)                         ║ order_close_delete (absolute price)   ║
╠════════════════════════════════════════╬═══════════════════════════════════════╣
║ close_partial(ticket, lots, **opts)    ║ Helper over close() focusing on       ║
║                                        ║ partial volume.                       ║
╠════════════════════════════════════════╬═══════════════════════════════════════╣
║ close_by(ticket_a, ticket_b)           ║ Closes ticket_a by opposite           ║
║                                        ║ ticket_b via order_close_by.          ║
╠════════════════════════════════════════╬═══════════════════════════════════════╣
║ order_send_with_defaults(**kwargs)     ║ Combines per-call kwargs with         ║
║                                        ║ stored defaults, applies rate-limit   ║
║                                        ║ and reconnect/error mapping, then     ║
║                                        ║ calls MT4Service.order_send.          ║
╚════════════════════════════════════════════════════════════════════════════════╝

╔══════════════════════════════════════════════════════════════════════════════╗
║ Notes                                                                        ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ • All prices are expected as absolute terminal prices (no pips math inside). ║
║ • “magic” and “deviation_pips” are convenience aliases; actual MT4Service    ║
║   call uses magic_number and slippage (already handled downstream).          ║
║ • Errors are funneled through map_backend_error with helpful context.        ║
║ • This module is a façade: it keeps call sites clean while preserving the    ║
║   exact gRPC payloads expected by the pb service underneath.                 ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
