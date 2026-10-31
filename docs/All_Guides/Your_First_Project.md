# Your First Project in 10 Minutes (Python)

> **Hands-on Quick Start** - Create a working trading project with MetaTrader 4 and PyMT4 from scratch.

---

## Step 0: Obtain Your API Key

To connect to MetaRPC endpoints (`mt4.mrpc.pro:443`), obtain your API key:
1. Register for free at [https://mrpc.pro/signup](https://mrpc.pro/signup).
2. Generate your API token in your dashboard at [https://mrpc.pro/my](https://mrpc.pro/my).
3. Set your token in your environment or connection config.

---

## Step 1: Create Your Project

Create a new directory for your trading bot:

```bash
mkdir my_pymt4_bot
cd my_pymt4_bot
```

Install the package:

```bash
pip install MetaRpcMT4
```

---

## Step 2: Write Your Trading Code

Create `main.py` and paste the following complete program:

```python
import asyncio
from MetaRpcMT4.mt4_account import MT4Account

async def main():
    # Session ID generation on Connect and authentication are handled automatically
    account = MT4Account(
        user=12345678,            # your MT4 login
        password="your_password",   # your MT4 password
        grpc_server="mt4.mrpc.pro:443",
        api_key="TRIAL",            # or your key from mrpc.pro/my
    )
    await account.connect_by_server_name(
        server_name="MetaQuotes-Demo",   # your broker's MT4 server name
        base_chart_symbol="EURUSD",
        timeout_seconds=30,
    )

    summary = await account.account_summary()
    print(f"Balance: {summary.account_balance}, Equity: {summary.account_equity}")

    await account.channel.close()

asyncio.run(main())
```

---

## Step 3: Run the Program

Run your application:

```bash
python main.py
```

Expected output (values depend on your account):

```text
Balance: 10000.00, Equity: 10000.00
```

---

## 🚀 Next Steps

Congratulations! You have successfully established a direct gRPC connection to MetaTrader 4. Next:
- Explore **[gRPC Streaming](GRPC_STREAM_MANAGEMENT.md)** to listen to live ticks.
- Check the **[API Reference](../MT4Account/MT4Account.Master.Overview.md)** for all 18 core terminal methods.
- Learn about high-level risk management and auto-normalization in **[MT4Sugar](../MT4Sugar/MT4Sugar.Master.Overview.md)**.
