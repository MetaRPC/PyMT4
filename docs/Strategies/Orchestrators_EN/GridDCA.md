# Grid DCA (common SL)

> A grid of averaging (DCA) entries that all share **one common stop-loss**.

* **Source:** `Strategy/orchestrator/grid_dca_common_sl.py`
* **Entry:** `run_grid_dca_common_sl(service, strategy, risk, ...)`
* **Demo:** `examples/4_orchestrators/13_grid_dca.py` · `python main.py grid`

---

## What it does

1. Places a ladder of `steps` pending orders, `step_pips` apart, from `base_price`
   (mid price if `None`), in the `side` direction.
2. As legs fill (at least `arm_when_filled_at_least`), it manages **one common stop-loss**
   anchored per `sl_anchor`.
3. Splits risk across the grid (`risk_mode="split_total"`) or risks each leg fully
   (`"per_leg_full"`).
4. Returns a `dict` result.

Use it to average into a move with a single, controlled risk envelope — best in ranges / mean-reversion.

---

## Signature

```python
async def run_grid_dca_common_sl(
    svc,
    sp: StrategyPreset,
    rp: RiskPreset,
    *,
    side: str = "buy",
    steps: int = 5,
    step_pips: float = 10.0,
    base_price: float | None = None,         # None -> mid price
    arm_when_filled_at_least: int = 1,       # manage common SL after N fills
    sl_anchor: str = "lowest_leg",           # "lowest_leg" (BUY) / "highest_leg" (SELL)
    risk_mode: str = "split_total",          # "split_total" | "per_leg_full"
    risk_total_percent: float | None = None, # total risk when splitting
    # ... further tuning knobs
) -> dict
```

---

## Example

```python
from Strategy.orchestrator import run_grid_dca_common_sl
from Strategy.presets.strategy import StrategyPreset
from Strategy.presets.risk import RiskPreset

strategy = StrategyPreset(symbol="EURUSD", use_market=False, lots=0.01, magic=103)
risk = RiskPreset(risk_percent=2.0, sl_pips=60, tp_pips=40)

result = await run_grid_dca_common_sl(
    service, strategy, risk,
    side="buy", steps=5, step_pips=10,
    risk_mode="split_total", risk_total_percent=2.0,
)
```

> ⚠️ Grids increase exposure as more legs fill — keep `steps` modest and the common SL tight.

---

## 📚 See also

* [Strategies — Master Overview](../Strategies.Master.Overview.md)
* [Presets](../Presets/Presets.md)
* [OCO Straddle](./OcoStraddle.md) · [Pending Bracket](./PendingBracket.md)
