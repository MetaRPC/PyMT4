# app/MT4Service_Trade_mod.py
from __future__ import annotations
from typing import Any, Optional, Dict, TYPE_CHECKING
import logging

from app.Helper.rate_limit import RateLimiter
from app.Helper.errors import map_backend_error

if TYPE_CHECKING:
    from app.MT4Service import MT4Service

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