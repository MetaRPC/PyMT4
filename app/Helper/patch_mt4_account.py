# app/patches/patch_mt4_account.py
"""
Runtime patch for MetaRpcMT4.mt4_account:
- Robust stub selection (AccountHelper/MarketInfo/TradingHelper)
- Safe GUID extraction (snake_case or camelCase)
- Keeps metadata keys lowercase ("id") to avoid INVALID_METADATA
"""

from __future__ import annotations

def apply_patch() -> None:
    # Import inside so the module loads only when patch is applied
    import grpc
    from typing import Optional

    import MetaRpcMT4.mt4_term_api_account_helper_pb2_grpc as ah_grpc
    import MetaRpcMT4.mt4_term_api_trading_helper_pb2_grpc as tr_grpc
    import MetaRpcMT4.mt4_term_api_market_info_pb2_grpc as mi_grpc
    import MetaRpcMT4.mt4_term_api_connection_pb2_grpc as conn_grpc

    import MetaRpcMT4.mt4_account as mod

    MT4Account = mod.MT4Account

    # ---------- helpers ----------

    def _choose_stub(grpc_module, *names):
        """Pick first available Stub class from the grpc module."""
        for n in names:
            cls = getattr(grpc_module, n, None)
            if cls is not None:
                return cls
        return None

    def _extract_guid_from_reply(res) -> Optional[str]:
        """Try both snake_case and camelCase GUID fields in data."""
        data = getattr(res, "data", None)
        if not data:
            return None
        return (
            getattr(data, "terminal_instance_guid", None)
            or getattr(data, "terminalInstanceGuid", None)
        )

    # ---------- patch __init__: keep original, then rebind stubs safely ----------

    _orig_init = MT4Account.__init__

    def _patched_init(self, user: int, password: str, grpc_server: Optional[str] = None, id_: Optional[str] = None):
        _orig_init(self, user=user, password=password, grpc_server=grpc_server, id_=id_)

        # Ensure connection stub exists (name is stable)
        try:
            self.connection_client = conn_grpc.ConnectionStub(self.channel)
        except Exception:
            # If channel not ready yet, recreate it (shouldn't happen, but be defensive)
            self.channel = grpc.aio.secure_channel(self.grpc_server, grpc.ssl_channel_credentials())
            self.connection_client = conn_grpc.ConnectionStub(self.channel)

        # AccountHelper*
        AH = _choose_stub(ah_grpc, "AccountHelperServiceStub", "AccountHelperStub")
        self.account_client = AH(self.channel) if AH else None

        # TradingHelper*
        TH = _choose_stub(tr_grpc, "TradingHelperServiceStub", "TradingHelperStub")
        self.trade_client = TH(self.channel) if TH else None

        # MarketInfo*
        MI = _choose_stub(mi_grpc, "MarketInfoServiceStub", "MarketSymbolsServiceStub", "MarketInfoStub")
        self.market_info_client = MI(self.channel) if MI else None


    MT4Account.__init__ = _patched_init

    # ---------- patch connect_by_host_port ----------

    _orig_connect_host = MT4Account.connect_by_host_port

    async def _patched_connect_host(self, *args, **kwargs):
        res = await _orig_connect_host(self, *args, **kwargs)
        # original returns None, the GUID must be set securely:
        guid = _extract_guid_from_reply(res) if res is not None else None
        # If the original has already set self.id, we'll leave it; otherwise, we'll try to extract it.
        if not getattr(self, "id", None) and guid:
            self.id = str(guid)
        return res

    MT4Account.connect_by_host_port = _patched_connect_host

    # ---------- patch connect_by_server_name ----------

    _orig_connect_name = MT4Account.connect_by_server_name

    async def _patched_connect_name(self, *args, **kwargs):
        res = await _orig_connect_name(self, *args, **kwargs)
        guid = _extract_guid_from_reply(res) if res is not None else None
        if not getattr(self, "id", None) and guid:
            self.id = str(guid)
        return res

    MT4Account.connect_by_server_name = _patched_connect_name

    # ---------- enforce lowercase header key via get_headers (keep signature) ----------

    def _patched_get_headers(self):
        # gRPC metadata requires lowercase ASCII keys; only "id" is safe here
        return [("id", str(getattr(self, "id", "")))]
    MT4Account.get_headers = _patched_get_headers


"""
Runtime patch for MetaRpcMT4.mt4_account — fixes compatibility issues with the Protobuf API.
Addresses three main issues: 1) Robust selection of gRPC stubs (AccountHelper/MarketInfo/TradingHelper)
taking into account different class naming conventions in different versions of the proto files.
2) Safely extracting the terminal GUID from responses (support for snake_case and camelCase fields).
3) Lowercasing metadata keys ("id") to prevent the INVALID_METADATA error in gRPC.
The apply_patch() function patches classes on the fly without changing the source code of the MetaRpcMT4 package.
Called during application initialization to ensure stable operation across different API versions.
"""
