# Tick Value & Size

> Tick value, tick size and contract size per symbol — the inputs for P/L and risk-based position sizing.

**API Information:**

* **Low-level API:** `MT4Account.tick_value_with_size(...)` (defined in `package/MetaRpcMT4/mt4_account.py`)
* **gRPC service:** `mt4_term_api.AccountHelper`
* **RPC:** `TickValueWithSize(TickValueWithSizeRequest) -> TickValueWithSizeReply`
* **Payload:** `TickValueWithSizeData`

## 💬 Just the essentials

* **What it is.** For each requested symbol: the money value of one tick, the price size of one tick, and the contract size (units per lot).
* **Why you need it.** To turn pips into money — money-per-pip, P/L estimates, and risk-based lot sizing.
* **When to use.** When computing position size from a dollar/percent risk, or valuing a move.

---

## 🎯 Purpose

* Tick value (money per tick for 1 lot)
* Tick size (price change of one tick)
* Contract size (units per lot)
* Lightweight — just the numbers needed for sizing

---

## Method Signature

```python
async def tick_value_with_size(
    self,
    symbol_names: list[str],
    deadline: Optional[datetime] = None,
    cancellation_event: Optional[asyncio.Event] = None,
)
```

**Request message:**

```protobuf
message TickValueWithSizeRequest {
  repeated string symbol_names = 1;
}
```

**Payload message:**

```protobuf
message TickValueWithSizeData {
  repeated SymbolTickValueWithSizeInfo infos = 1;
}

message SymbolTickValueWithSizeInfo {
  int32 index = 1;
  string symbolName = 2;
  double TradeTickValue = 3;      // money per tick, 1 lot
  double TradeTickSize = 4;       // price change per tick
  double TradeContractSize = 5;   // units per lot
}
```

---

## 🔽 Input

| Parameter | Type | Description |
|-----------|------|-------------|
| `symbol_names` | `list[str]` | Symbols to query, e.g. `["EURUSD", "XAUUSD"]`. |
| `deadline` | datetime, optional | Absolute UTC deadline for the gRPC call. |
| `cancellation_event` | asyncio.Event, optional | Set to abort the request. |

---

## ⬆️ Output — `TickValueWithSizeData`

`infos` — a list of `SymbolTickValueWithSizeInfo`:

| Field | Python Type | Description |
|-------|-------------|-------------|
| `symbolName` | `str` | Symbol (note camelCase) |
| `TradeTickValue` | `float` | Money value of one tick, for 1 lot (in deposit currency) |
| `TradeTickSize` | `float` | Price change of one tick |
| `TradeContractSize` | `float` | Units per lot |
| `index` | `int` | Position in the request |

---

## 🧩 Notes & Tips

* **This is the subset of [symbol_params_many](symbol_params_many.md)** needed for sizing — use this when you only need the tick/contract numbers for several symbols at once.
* **Money per pip** = `TradeTickValue × (pip_size / TradeTickSize)`, where `pip_size` is 10 × point on 5/3-digit FX (get `Point`/`Digits` from [symbol_params_many](symbol_params_many.md)).
* **Field names are mixed case.** `symbolName` is camelCase; `TradeTickValue` / `TradeTickSize` / `TradeContractSize` are PascalCase.
* **Values are per 1 lot** in the account's deposit currency — multiply by your lot size.
* **MT4Sugar builds on this** for `calc_lot_by_risk` / `calc_cash_risk`.

---

## 🔗 Usage Examples

### 1) Tick value for a basket

```python
async def tick_values(account, symbols: list[str]):
    data = await account.tick_value_with_size(symbols)
    for i in data.infos:
        print(f"{i.symbolName:<8} tick_value={i.TradeTickValue:.5f} "
              f"tick_size={i.TradeTickSize:.5f} contract={i.TradeContractSize:.0f}")
    return {i.symbolName: i for i in data.infos}
```

### 2) Money per pip

Convert tick value to per-pip value (needs the symbol's pip size).

```python
async def money_per_pip(account, symbol: str, lots: float = 1.0) -> float:
    tv = (await account.tick_value_with_size([symbol])).infos[0]
    p  = (await account.symbol_params_many(symbol)).symbol_infos[0]
    pip_size = p.Point * (10 if p.Digits in (3, 5) else 1)
    value = tv.TradeTickValue * (pip_size / tv.TradeTickSize) * lots
    print(f"{symbol}: {value:.2f} per pip for {lots} lot")
    return value
```

### 3) Risk-based lot size

Size a position so a stop-loss hit costs a fixed amount.

```python
async def lot_for_risk(account, symbol: str, risk_amount: float, sl_pips: float) -> float:
    mpp = await money_per_pip(account, symbol, lots=1.0)   # per-pip for 1 lot
    if mpp <= 0 or sl_pips <= 0:
        return 0.0
    raw = risk_amount / (sl_pips * mpp)
    # round to the broker's volume step
    p = (await account.symbol_params_many(symbol)).symbol_infos[0]
    lots = max(p.VolumeMin, min(p.VolumeMax, round(raw / p.VolumeStep) * p.VolumeStep))
    print(f"risk {risk_amount:.2f} @ {sl_pips} pip SL -> {lots:.2f} lot")
    return round(lots, 2)
```

---

## ⚠️ Pitfalls

* **Mixed-case fields.** `symbolName` (camelCase) but `TradeTickValue` (PascalCase) — match them exactly.
* **Per 1 lot.** Remember to scale by lot size; the raw values assume one lot.
* **Pip vs tick.** Tick ≠ pip. Convert via the symbol's pip size (`Point`/`Digits` from [symbol_params_many](symbol_params_many.md)).
* **Deposit currency.** `TradeTickValue` is already in your account currency — no FX conversion needed.

---

## 🧪 Testing Suggestions

* **Known symbol.** For EURUSD on a USD account, `TradeTickValue` ≈ 1.0 for 1 lot at 0.00001 tick size.
* **Batch.** Requesting 3 symbols returns up to 3 `infos`; match by `symbolName`.
* **Sizing sanity.** `lot_for_risk(risk=50, sl_pips=50)` on EURUSD returns ~0.10 lot (≈ $1/pip) — adjust for the actual tick value.

---

## 📚 See also

* [Symbol Parameters](symbol_params_many.md)
* [Symbols](symbols.md)
* [Account Summary](../1. Account_Information/account_summary.md)

* **Back to:** [Symbols & Quotes — Overview](Symbols_Quotes.Overview.md) · [MT4Account — Master Overview](../MT4Account.Master.Overview.md)
