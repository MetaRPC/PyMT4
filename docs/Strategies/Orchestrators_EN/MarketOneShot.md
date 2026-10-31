# Market One-Shot

> Open a market order with an automatic SL/TP bracket — the simplest orchestrator.

* **Source:** `Strategy/orchestrator/market_one_shot.py`
* **Entry:** `run_market_one_shot(service, strategy, risk) -> dict`
* **Demo:** `examples/4_orchestrators/11_market_one_shot.py` · `python main.py market`

---

## What it does

1. Reads the `StrategyPreset` (symbol, lots, magic) and `RiskPreset` (sl/tp in pips).
2. Opens a **market** order via MT4Sugar.
3. Attaches a bracket — stop-loss and take-profit derived from the risk preset's pips.
4. Returns a `dict` describing the opened order / result.

Use it when you simply want a protected market entry in one call.

---

## Signature

```python
async def run_market_one_shot(
    svc: MT4Service,
    strategy: StrategyPreset,
    risk: RiskPreset,
) -> dict
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `svc` | `MT4Service` | A connected service (or `service.sugar` is used internally). |
| `strategy` | `StrategyPreset` | `symbol`, `lots`, `magic`, `deviation_pips`, `comment`. `use_market=True`. |
| `risk` | `RiskPreset` | `risk_percent`, `sl_pips`, `tp_pips` — sizing & bracket. |

**Returns:** a `dict` with the result (ticket and the keys the orchestrator reports).

---

## Example

```python
from Strategy.orchestrator import run_market_one_shot
from Strategy.presets.strategy import StrategyPreset
from Strategy.presets.risk import RiskPreset

strategy = StrategyPreset(symbol="EURUSD", use_market=True, lots=0.01, magic=101,
                          deviation_pips=3.0, comment="pymt4 market_one_shot")
risk = RiskPreset(risk_percent=1.0, sl_pips=20, tp_pips=40)

result = await run_market_one_shot(service, strategy, risk)
print("result keys:", list(result.keys()))
```

> If `lots` is omitted in the `StrategyPreset`, sizing can come from `risk_percent` + `sl_pips` via MT4Sugar's `calc_lot_by_risk`.

---

## 📚 See also

* [Strategies — Master Overview](../Strategies.Master.Overview.md)
* [Presets](../Presets/Presets.md)
* [Bracket + Trailing](./BracketTrailing.md) · [Pending Bracket](./PendingBracket.md)
