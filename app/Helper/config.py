# app/config.py
from dataclasses import dataclass
from typing import Optional
import json, os
from pathlib import Path

@dataclass
class MT4Config:
    user: int
    password: str                      # read from ENV preferably
    grpc_server: str = "mt4.mrpc.pro:443"   # gRPC gateway
    server_name: Optional[str] = None       # ConnectEx (preferred)
    broker_host: Optional[str] = None       # Connect(host, port) fallback
    broker_port: int = 443
    base_chart_symbol: str = "EURUSD"
    timeout_seconds: int = 25               # <= 30, because the RPC packet timeout is ~30s

    @staticmethod
    def load(path: str = "Config/appsettings.json") -> "MT4Config":
        cfg = {}
        p = Path(path)
        if p.exists():
            with p.open("r", encoding="utf-8") as f:
                raw = json.load(f)
                cfg.update(raw.get("grpc", {}))
                mt4 = raw.get("mt4", {})
                cfg.update({k: v for k, v in mt4.items()})

        # ENV overrides (prefer)
        def getenv(key, default=None): return os.getenv(key, default)

        user = int(getenv("MT4_LOGIN", cfg.get("login")))
        password = getenv("MT4_PASSWORD", cfg.get("password", ""))
        grpc_server = getenv("GRPC_SERVER", cfg.get("server", "mt4.mrpc.pro:443"))
        server_name = getenv("MT4_SERVER_NAME", cfg.get("server_name"))
        broker_host = getenv("BROKER_HOST", cfg.get("broker_host"))
        broker_port = int(getenv("BROKER_PORT", cfg.get("broker_port", 443)))
        base_symbol = getenv("BASE_SYMBOL", cfg.get("base_symbol", "EURUSD"))
        timeout_seconds = int(getenv("TIMEOUT_SECONDS", cfg.get("timeout_seconds", 25)))

        if not user or not password:
            raise ValueError("MT4 login/password are required (use appsettings.json or ENV).")

        return MT4Config(
            user=user, password=password, grpc_server=grpc_server,
            server_name=server_name, broker_host=broker_host, broker_port=broker_port,
            base_chart_symbol=base_symbol, timeout_seconds=timeout_seconds
        )

    def resolve_mode(self) -> str:
        """Return 'server_name' or 'host_port' depending on filled fields."""
        if self.server_name and self.server_name.strip():
            return "server_name"
        if self.broker_host and self.broker_host.strip():
            return "host_port"
        raise ValueError("Provide MT4 server_name OR broker_host/port.")
