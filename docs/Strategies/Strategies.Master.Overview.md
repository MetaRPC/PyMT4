# Strategies — Master Overview

> One page to orient fast: the ready-made **orchestrators** and **presets** that ship with PyMT4, how to pick one, and links to each spec.

---

## ⚠️ Educational & demonstration only

The orchestrators and presets here are **demonstration examples** — templates for building your own strategies, not production trading systems.

- Simplified logic, no portfolio-level risk controls, no economic-calendar integration.
- **Demo accounts only.** Study the code, test on demo, add your own risk management before considering anything live.
- Trading involves substantial risk of loss; you are responsible for your decisions.

They live in the repo under `Strategy/orchestrator/` and `Strategy/presets/`, and are driven by [`MT4Service`](../MT4Service/MT4Service.Overview.md) / [`MT4Sugar`](../MT4Sugar/MT4Sugar.Master.Overview.md). The numbered examples `11`–`16` run them.

---

## 🚦 Orchestrators

Each orchestrator is a single `async def run_*(service, strategy, risk, ...)` coroutine that
takes a [`StrategyPreset`](./Presets/Presets.md#strategypreset) (what/where to enter) and a
[`RiskPreset`](./Presets/Presets.md#riskpreset) (how much to risk / protect), and returns a
`dict` result.

| Orchestrator | Entry | What it does | Demo |
|--------------|-------|--------------|------|
| **[Market One-Shot](./Orchestrators_EN/MarketOneShot.md)** | `run_market_one_shot` | Open a market order with an automatic SL/TP bracket. | `python main.py market` (11) |
| **[Bracket + Trailing](./Orchestrators_EN/BracketTrailing.md)** | `run_bracket_with_trailing_activation` | Entry with a bracket; trailing stop switches on once price is far enough in profit. | `python main.py trailing` (12) |
| **[Grid DCA (common SL)](./Orchestrators_EN/GridDCA.md)** | `run_grid_dca_common_sl` | A grid of averaging entries sharing one common stop-loss. | `python main.py grid` (13) |
| **[OCO Straddle](./Orchestrators_EN/OcoStraddle.md)** | `run_oco_straddle` | Buy-stop above + sell-stop below; one triggers, the other cancels (breakout). | `python main.py oco` (14) |
| **[Pending Bracket](./Orchestrators_EN/PendingBracket.md)** | `run_pending_bracket` | Place a pending order with an automatic bracket, wait for fill. | `python main.py pending` (15) |

---

## 🎛️ Presets

Two small dataclasses configure every orchestrator (see **[Presets](./Presets/Presets.md)**):

* **`StrategyPreset`** — `symbol`, `use_market`, `entry_price`, `lots`, `magic`, `deviation_pips`, `comment`.
* **`RiskPreset`** — `risk_percent`, `sl_pips`, `tp_pips`, `trailing_pips`, `be_trigger_pips`, `be_plus_pips`.

Ready-made presets and factories ship too — `MarketEURUSD`, `LimitEURUSD(price)`, `BreakoutBuy(...)`, `Conservative`, risk profiles (`ScalperEURUSD()`, `SwingEURUSD()`), per-symbol factories (`strategy_symbols`), plus ATR- and session-based risk. Example `16` (`python main.py presets`) prints them all.

---

## 🔌 Usage pattern (Python async/await)

```python
import asyncio
from MetaRpcMT4.mt4_account import MT4Account
from app.MT4Service import MT4Service
from Strategy.orchestrator import run_market_one_shot
from Strategy.presets.strategy import StrategyPreset
from Strategy.presets.risk import RiskPreset

async def main():
    account = MT4Account(user=..., password=..., grpc_server="mt4.mrpc.pro:443")
    await account.connect_by_server_name(server_name="MetaQuotes-Demo",
                                         base_chart_symbol="EURUSD", timeout_seconds=30)
    service = MT4Service(account)

    strategy = StrategyPreset(symbol="EURUSD", use_market=True, lots=0.01, magic=101)
    risk = RiskPreset(risk_percent=1.0, sl_pips=20, tp_pips=40)

    result = await run_market_one_shot(service, strategy, risk)
    print(result)

    await account.channel.close()

asyncio.run(main())
```

---

## 🧭 Which orchestrator?

* **Simple entry with protection** → [Market One-Shot](./Orchestrators_EN/MarketOneShot.md)
* **Let winners run** → [Bracket + Trailing](./Orchestrators_EN/BracketTrailing.md)
* **Average into a range** → [Grid DCA](./Orchestrators_EN/GridDCA.md)
* **Trade a breakout either way** → [OCO Straddle](./Orchestrators_EN/OcoStraddle.md)
* **Wait at a price with a bracket** → [Pending Bracket](./Orchestrators_EN/PendingBracket.md)

---

## 📖 Related documentation

* [MT4Account — Master Overview](../MT4Account/MT4Account.Master.Overview.md)
* [MT4Service — Overview](../MT4Service/MT4Service.Overview.md)
* [MT4Sugar — Master Overview](../MT4Sugar/MT4Sugar.Master.Overview.md)
* [gRPC Stream Management](../All_Guides/GRPC_STREAM_MANAGEMENT.md) · [UserCode Sandbox](../All_Guides/USERCODE_SANDBOX_GUIDE.md)

---

*Trade safely, code cleanly — and always close what you open.*
