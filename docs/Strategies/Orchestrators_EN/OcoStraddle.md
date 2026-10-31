# OCO Straddle (breakout)

> A bi-directional breakout: **buy-stop above + sell-stop below** the price; when one triggers, the other is cancelled (OCO).

* **Source:** `Strategy/orchestrator/oco_straddle.py`
* **Entry:** `run_oco_straddle(service, strategy, risk, ...)`
* **Demo:** `examples/4_orchestrators/14_oco_straddle.py` · `python main.py oco`

---

## What it does

1. Places a **buy stop** `offset_pips` above and a **sell stop** `offset_pips` below the
   current price, each with its own bracket.
2. Waits up to `timeout_s`. When one side triggers, it **cancels the opposite** pending order.
3. Sizes each leg per `risk_mode` (`"per_leg_full"` = full risk on each leg).
4. Returns a `dict` result.

Use it to catch a breakout in either direction (e.g. around news or a consolidation).

---

## Signature

```python
async def run_oco_straddle(
    svc,
    sp: StrategyPreset,
    rp: RiskPreset,
    *,
    offset_pips: float = 10.0,          # distance above/below price for the stops
    timeout_s: int = 1200,              # how long to wait for a breakout
    risk_mode: str = "per_leg_full",    # "per_leg_full" | "split_total"
    max_spread_pips: float | None = None,
) -> dict
```

---

## Example

```python
from Strategy.orchestrator import run_oco_straddle
from Strategy.presets.strategy import StrategyPreset
from Strategy.presets.risk import RiskPreset

strategy = StrategyPreset(symbol="EURUSD", use_market=False, lots=0.01, magic=104)
risk = RiskPreset(risk_percent=1.0, sl_pips=20, tp_pips=40)

result = await run_oco_straddle(
    service, strategy, risk,
    offset_pips=10, timeout_s=300, risk_mode="per_leg_full",
)
```

> Slippage during fast breakouts can briefly trigger both legs — the orchestrator cancels the loser as soon as one fills.

---

## 📚 See also

* [Strategies — Master Overview](../Strategies.Master.Overview.md)
* [Presets](../Presets/Presets.md)
* [Grid DCA](./GridDCA.md) · [Pending Bracket](./PendingBracket.md)
