# app/errors.py
from __future__ import annotations
from typing import Any, Optional


class MT4Error(Exception):
    """Base MT4 domain error with optional code and details."""

    def __init__(self, message: str, *, code: Optional[int] = None, details: Any = None) -> None:
        super().__init__(message)
        self.code = code
        self.details = details

    def __str__(self) -> str:
        base = super().__str__()
        if self.code is not None:
            return f"[{self.code}] {base}"
        return base


class ConnectivityError(MT4Error):
    """Connectivity / session issues (reconnect failed, handshake error, etc.)."""
    pass


class OrderRejected(MT4Error):
    """Order was rejected by server/broker."""
    pass


class ModifyRejected(MT4Error):
    """Order modify/delete was rejected."""
    pass


class RateLimitExceeded(MT4Error):
    """Client-side guard: too many requests in a short time."""
    pass


class TradeOutcomeUnknown(MT4Error):
    """
    A trade call failed in transport after it may have reached the terminal
    (MetaRpcMT4.TradeOutcomeUnknownError). It may or may not have been executed and
    was NOT re-sent: check open orders before retrying. Deliberately not an
    OrderRejected/ModifyRejected - the trade was not (known to be) rejected.

    Attributes: error_code ("TRADE_OUTCOME_UNKNOWN"), operation, transport_error (the
    original grpc error: transport_error.code() / .details()), details (the SDK exception,
    also __cause__), payload.
    """

    error_code = "TRADE_OUTCOME_UNKNOWN"

    def __init__(self, message: str, *, sdk_error: Exception, payload: Any = None) -> None:
        super().__init__(message, details=sdk_error)
        self.operation = getattr(sdk_error, "operation", None)
        self.transport_error = getattr(sdk_error, "transport_error", sdk_error)
        self.payload = payload
        self.__cause__ = sdk_error


# --- optional helpers to map backend / pb errors into our classes ---

def map_backend_error(
    raw_exc: Exception | None = None,
    *,
    code: int | None = None,
    reason: str | None = None,
    context: str | None = None,
    payload: Any = None,
) -> MT4Error:
    """
    Translate low-level exception or (code, reason) from backend into a domain MT4Error.

    Args:
        raw_exc: original exception (if any)
        code: numeric error code from backend/pb, if available
        reason: textual reason from backend
        context: where it happened (e.g., 'order_send', 'order_modify', 'reconnect')
        payload: any extra data for debugging

    Returns:
        MT4Error subclass instance.
    """
    msg = reason or (str(raw_exc) if raw_exc else "MT4 backend error")
    if context:
        msg = f"{context}: {msg}"

    # A trade with an unknown outcome is not a rejection: never map it to OrderRejected /
    # ModifyRejected (callers would treat it as "not executed" and may send it again).
    if raw_exc is not None and getattr(raw_exc, "error_code", None) == TradeOutcomeUnknown.error_code:
        return TradeOutcomeUnknown(msg, sdk_error=raw_exc, payload=payload)

    # If you have stable pb codes, put precise mapping here:
    PB_CODE_MAP = {
        # 1001: OrderRejected("Invalid volume step"),
        # 1002: OrderRejected("Insufficient margin"),
        # 2001: ModifyRejected("SL/TP out of range"),
        # 3001: ConnectivityError("Session expired"),
    }

    if code in PB_CODE_MAP:
        err = PB_CODE_MAP[code]
        # If mapping stored as MT4Error instance, enrich and return
        if isinstance(err, MT4Error):
            err.code = code
            if payload is not None:
                err.details = payload
            return err
        # If mapping stored as str, convert to generic class
        return MT4Error(str(err), code=code, details=payload)

    # Heuristics by context if no code supplied
    if context in ("order_send", "place_order"):
        return OrderRejected(msg, code=code, details=payload)
    if context in ("order_modify", "order_close_delete", "order_close_by"):
        return ModifyRejected(msg, code=code, details=payload)
    if context in ("reconnect", "ensure_connected", "get_headers"):
        return ConnectivityError(msg, code=code, details=payload)

    # Fallback
    return MT4Error(msg, code=code, details=payload)


"""
Exception hierarchy for the MT4 API with support for error codes and details.
MT4Error — base class for all MT4 errors with optional code and details fields.
ConnectivityError — connection problems (disconnected, handshake errors).
OrderRejected — order rejected by the broker (insufficient margin, invalid volume, etc.).
ModifyRejected — order modification/closure rejected (SL/TP out of range, etc.).
RateLimitExceeded — request limit exceeded (client protection).
The map_backend_error() function converts low-level protobuf/gRPC errors into domain-specific exceptions.
"""
