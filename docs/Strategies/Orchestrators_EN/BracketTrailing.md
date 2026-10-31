# Bracket + Trailing Activation

> Enter with an SL/TP bracket; the **trailing stop switches on** only once the trade is far enough in profit.

* **Source:** `Strategy/orchestrator/bracket_trailing_activation.py`
* **Entry:** `run_bracket_with_trailing_activation(service, strategy, risk, ...)`
* **Demo:** `examples/4_orchestrators/12_bracket_trailing.py` · `python main.py trailing`

---

## What it does

1. Opens an order (market or pending per the `StrategyPreset`) with a bracket.
2. Polls the position's profit in pips.
3. When profit reaches `activate_trailing_at_pips`, it **activates** a trailing stop at
   `trailing_distance_pips` (falling back to `risk.trailing_pips`), trailed in
   `trailing_step_pips` steps.
4. Returns a `dict` result.

Use it to protect open profit and let winners run without trailing from the very first pip.

---

## Signature

```python
async def run_bracket_with_trailing_activation(
    svc,
    sp: StrategyPreset,
    rp: RiskPreset,
    *,
    side: str = "buy",                              # "buy" or "sell"
    activate_trailing_at_pips: float = 12.0,        # profit needed before trailing turns on
    trailing_distance_pips: float | None = None,    # trail distance; falls back to rp.trailing_pips
    trailing_step_pips: float = 1.0,                # trail step
    wait_fill_timeout_s: int = 1200,                # pending-fill timeout
    max_spread_pips: float | None = None,           # optional spread guard
    poll_interval_s: float = 1.0,                   # profit poll cycle
) -> dict
```

---

## Example

```python
from Strategy.orchestrator import run_bracket_with_trailing_activation
from Strategy.presets.strategy import StrategyPreset
from Strategy.presets.risk import RiskPreset

strategy = StrategyPreset(symbol="EURUSD", use_market=True, lots=0.01, magic=102)
risk = RiskPreset(risk_percent=1.0, sl_pips=25, tp_pips=80, trailing_pips=15)

result = await run_bracket_with_trailing_activation(
    service, strategy, risk,
    side="buy",
    activate_trailing_at_pips=12,   # start trailing after +12 pips
    trailing_step_pips=1,
)
```

> Trailing uses MT4Sugar's [`set_trailing_stop`](../../MT4Sugar/7.%20Trailing_Breakeven.md); the bracket SL/TP come from the `RiskPreset`.

---

## 📚 See also

* [Strategies — Master Overview](../Strategies.Master.Overview.md)
* [Presets](../Presets/Presets.md)
* [Market One-Shot](./MarketOneShot.md) · [Pending Bracket](./PendingBracket.md)
