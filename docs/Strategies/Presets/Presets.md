# Strategy & Risk Presets

> The two small dataclasses that configure every orchestrator, plus ready-made presets and factories.

* **Source:** `Strategy/presets/` (`strategy.py`, `risk.py`, `risk_profiles.py`, `risk_atr.py`, `risk_session.py`, `strategy_symbols.py`)
* **Demo:** `examples/4_orchestrators/16_presets.py` · `python main.py presets`

Orchestrators take one `StrategyPreset` (what/where to enter) and one `RiskPreset`
(how much to risk / protect):

```python
result = await run_market_one_shot(service, StrategyPreset(...), RiskPreset(...))
```

---

## StrategyPreset

What and where to enter.

```python
@dataclass
class StrategyPreset:
    symbol: str
    use_market: bool = True             # True = market, False = pending (needs entry_price)
    entry_price: float | None = None    # pending-order price
    lots: float | None = None           # None -> size by risk
    magic: int = 0
    deviation_pips: float = 2.0
    comment: str | None = None
```

```python
from Strategy.presets.strategy import StrategyPreset
sp = StrategyPreset(symbol="EURUSD", use_market=True, lots=0.01, magic=101)
```

### Ready-made / factories (`strategy.py`)

| Name | Description |
|------|-------------|
| `MarketEURUSD` | Market EURUSD preset (magic 777). |
| `LimitEURUSD(price)` | A BUY/SELL LIMIT EURUSD at `price`. |
| `BreakoutBuy(symbol="EURUSD", offset_pips=10)` | A breakout-style pending preset. |

### Per-symbol factories (`strategy_symbols.py`)

Limit/breakout factories for many instruments — `LimitGBPUSD(price)`, `LimitXAUUSD(price)`,
`BreakoutGBPUSD`, `BreakoutXAUUSD`, … plus a `REGISTRY` dict of them.

```python
from Strategy.presets import strategy_symbols
sp = strategy_symbols.LimitGBPUSD(1.2600)
print(list(strategy_symbols.REGISTRY.keys()))
```

---

## RiskPreset

How much to risk and how to protect.

```python
@dataclass
class RiskPreset:
    risk_percent: float
    sl_pips: float
    tp_pips: float | None = None
    trailing_pips: float | None = None
    be_trigger_pips: float | None = None   # move to breakeven after N pips
    be_plus_pips: float | None = None      # breakeven + N pips
```

```python
from Strategy.presets.risk import RiskPreset
rp = RiskPreset(risk_percent=1.0, sl_pips=20, tp_pips=40, trailing_pips=15)
```

### Ready-made / profiles

| Name | Source | Description |
|------|--------|-------------|
| `Conservative` | `risk.py` | `risk_percent=0.5, sl_pips=25, tp_pips=50`. |
| `ScalperEURUSD()` / `ScalperXAUUSD()` | `risk_profiles.py` | Tight scalping risk profiles. |
| `SwingEURUSD()` / `SwingXAUUSD()` | `risk_profiles.py` | Wider swing risk profiles. |

```python
from Strategy.presets import risk_profiles
rp = risk_profiles.ScalperEURUSD()
```

### ATR- and session-based risk

* **`risk_atr.py`** — builds a `RiskPreset` whose stops scale with recent volatility (ATR).
* **`risk_session.py`** — adjusts risk by trading session (e.g. tighter outside liquid hours).

---

## Build your own

```python
sp = StrategyPreset(symbol="USDJPY", use_market=True, lots=0.02, magic=1234,
                    deviation_pips=4.0, comment="my strategy")
rp = RiskPreset(risk_percent=1.0, sl_pips=30, tp_pips=60,
                trailing_pips=20, be_trigger_pips=20, be_plus_pips=1)

result = await run_market_one_shot(service, sp, rp)
```

---

## 📚 See also

* [Strategies — Master Overview](../Strategies.Master.Overview.md)
* [Market One-Shot](../Orchestrators_EN/MarketOneShot.md) · [Bracket + Trailing](../Orchestrators_EN/BracketTrailing.md)
* [MT4Sugar — Risk Sizing](../../MT4Sugar/4.%20Risk_Sizing.md)
