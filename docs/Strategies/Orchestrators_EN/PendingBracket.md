# Pending Bracket

> Place a pending order at a chosen price with an automatic SL/TP bracket, then wait for it to fill.

* **Source:** `Strategy/orchestrator/pending_bracket.py`
* **Entry:** `run_pending_bracket(service, strategy, risk, *, timeout_s=900) -> dict`
* **Demo:** `examples/4_orchestrators/15_pending_bracket.py` · `python main.py pending`

---

## What it does

1. Places a **pending** order (limit/stop) at `strategy.entry_price` with a bracket from the
   risk preset.
2. Waits up to `timeout_s` for the order to fill.
3. Returns a `dict` result (filled / still pending / timed out).

Use it for "set your price and wait for the market to come to you" entries.

---

## Signature

```python
async def run_pending_bracket(
    svc,
    strategy: StrategyPreset,
    risk: RiskPreset,
    *,
    timeout_s: int = 900,   # how long to wait for a fill
) -> dict
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `svc` | `MT4Service` | Connected service. |
| `strategy` | `StrategyPreset` | `use_market=False`, `entry_price` set (the pending price), `lots`, `magic`. |
| `risk` | `RiskPreset` | `sl_pips` / `tp_pips` for the bracket. |
| `timeout_s` | `int` | Cancel/stop waiting after this many seconds. |

---

## Example

```python
from Strategy.orchestrator import run_pending_bracket
from Strategy.presets.strategy import StrategyPreset
from Strategy.presets.risk import RiskPreset

mid = await service.sugar.mid_price("EURUSD")
entry = round(mid - 0.0030, 5)   # a BUY LIMIT ~30 pips below the market

strategy = StrategyPreset(symbol="EURUSD", use_market=False, entry_price=entry,
                          lots=0.01, magic=105, comment="pymt4 pending_bracket")
risk = RiskPreset(risk_percent=1.0, sl_pips=25, tp_pips=50)

result = await run_pending_bracket(service, strategy, risk, timeout_s=300)
print("result keys:", list(result.keys()))
```

> In a short demo the limit usually won't fill — use a short `timeout_s` and clean up the pending order afterwards with [`cancel_pendings`](../../MT4Sugar/6.%20Order_Management.md).

---

## 📚 See also

* [Strategies — Master Overview](../Strategies.Master.Overview.md)
* [Presets](../Presets/Presets.md)
* [Market One-Shot](./MarketOneShot.md) · [OCO Straddle](./OcoStraddle.md)
