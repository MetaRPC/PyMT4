# PyMT4 SDK — Cloud Python SDK for MetaTrader 4 (MT4)

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docs](https://img.shields.io/badge/docs-PyMT4-0083ff.svg)](https://metarpc.github.io/PyMT4/)
[![Cloud](https://img.shields.io/badge/VPS-Not_Required-success.svg)](https://mrpc.pro)
[![Platform](https://img.shields.io/badge/OS-Linux%20|%20macOS%20|%20Windows%20|%20Docker-brightgreen.svg)](https://mrpc.pro)

> **Official Python SDK for MetaTrader 4 Cloud API via gRPC & REST.**  
> Connect, stream live ticks, and execute trades on any MT4 broker or prop firm from Linux, macOS, Docker, or AWS Lambda — **without running a Windows VPS or desktop terminal.**

---

## ⚡ Why MetaRPC PyMT4?

- **Zero Windows VPS**: Stop paying $20–$80/month for buggy Windows servers. Run MT4 trading bots in lightweight Linux containers or serverless workers.
- **Ultra-Low Latency**: High-speed gRPC streaming and execution co-located with London (LD4) and New York (NY4) broker data centers (<20ms execution).
- **Universal MT4 Broker & Prop Firm Support**: Connects to 500+ brokers and prop firms including **FTMO, IC Markets, Pepperstone, Exness, FundedNext, Tickmill, XM, FXCM**.
- **Automatic Identity Derivation**: Account GUID (`id`) and cryptographic headers are derived automatically from your credentials.
- **Asyncio Native**: Modern asynchronous Python design with automatic reconnection, heartbeat monitoring, and resilience.

---

## 📦 Installation

```bash
pip install MetaRpcMT4
```

---

## 🚀 30-Second Quick Start

```python
import asyncio
from pymt4 import MT4Account

async def main():
    # 1. Initialize account with your credentials
    # Sign up at https://mrpc.pro/signup to get your free API key
    account = MT4Account(
        user=12345678,                      # Your MT4 Login
        password="your_mt4_password",        # Your MT4 Password
        grpc_server="mt4.mrpc.pro:443",      # Cloud gRPC Endpoint
        api_key="your_mrpc_api_key"          # From https://mrpc.pro/my
    )

    # 2. Connect by broker server name
    print("Connecting to MetaTrader 4 Cloud...")
    await account.connect_by_server_name("MetaQuotes-Demo", base_chart_symbol="EURUSD", timeout_seconds=30)
    print("Connected successfully!")

    # 3. Get real-time account summary
    summary = await account.account_summary()
    print(f"Balance: ${summary.account_balance:,.2f}")
    print(f"Equity:  ${summary.account_equity:,.2f}")
    print(f"Free Margin: ${summary.account_margin_free:,.2f}")

    # 4. Fetch live quotes
    quote = await account.get_quote("EURUSD")
    print(f"EURUSD Bid: {quote.bid} | Ask: {quote.ask}")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 🔑 Getting Your API Key & Free Trial

1. **Sign Up**: Create your free account at [https://mrpc.pro/signup](https://mrpc.pro/signup).
2. **Copy API Key**: Open your portal dashboard at [https://mrpc.pro/my](https://mrpc.pro/my) and grab your personal API token.
3. **Connect**: Pass your key in code or set the `MRPC_API_KEY` environment variable:
   ```bash
   export MRPC_API_KEY="your_api_token_here"
   ```

---

## 🌐 Production Endpoints

| Environment | Host / URL | Port | Protocol | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **MT4 Production gRPC** | `mt4.mrpc.pro` | `443` | TLS / gRPC | High-throughput trading & streaming |
| **Interactive API UI (Swagger)** | [https://mt4.mrpc.pro/apiui](https://mt4.mrpc.pro/apiui) | `443` | HTTPS / REST | Interactive REST endpoints & testing |
| **Portal Dashboard** | [https://mrpc.pro/my](https://mrpc.pro/my) | `443` | HTTPS | Manage terminals, copiers & keys |
| **Account Registration** | [https://mrpc.pro/signup](https://mrpc.pro/signup) | `443` | HTTPS | Instant free trial registration |

---

## 🏢 Compatible Brokers & Prop Firms

Tested and verified with over 500+ MetaTrader server environments:
- **Prop Firms**: FTMO, FundedNext, The Funded Trader, E8 Funding, Alpha Capital, SurgeTrader.
- **Brokers**: IC Markets, Pepperstone, Exness, Tickmill, XM, FXCM, FP Markets, Eightcap, AvaTrade.

---

## 📚 Complete Documentation & Code Examples

- 📖 [Comprehensive Documentation](https://metarpc.github.io/PyMT4/)
- 🚀 [10-Minute First Project Guide](https://metarpc.github.io/PyMT4/All_Guides/Your_First_Project/)
- 📡 [Live Tick & Bar gRPC Streaming](https://metarpc.github.io/PyMT4/All_Guides/GRPC_STREAM_MANAGEMENT/)
- 💼 [Order Execution & Position Management](https://metarpc.github.io/PyMT4/API_Reference/MT4Account/)
- 💡 [Example Scripts & Strategies](https://github.com/MetaRPC/PyMT4/tree/main/examples)

---

## 📄 License

This SDK is open-sourced under the [MIT License](LICENSE).  
Cloud infrastructure and API services are operated by [MetaRPC](https://mrpc.pro).
