# Symbol Parameters

> The per-symbol rulebook: digits, lot limits, stops level, tick value, trade mode and more — for one symbol or all of them.

**API Information:**

* **Low-level API:** `MT4Account.symbol_params_many(...)` (defined in `package/MetaRpcMT4/mt4_account.py`)
* **gRPC service:** `mt4_term_api.AccountHelper`
* **RPC:** `SymbolParamsMany(SymbolParamsManyRequest) -> SymbolParamsManyReply`
* **Payload:** `SymbolParamsManyData`

## 💬 Just the essentials

* **What it is.** The trading specification for symbols — the numbers you need to size, round and validate orders.
* **Why you need it.** To normalize volume/price, respect the broker's minimum stop distance, and compute money-per-pip.
* **When to use.** Before sizing or sending orders; cache the result and refresh occasionally.

---

## 🎯 Purpose

* Volume min / max / step / limit
* Digits and point size (precision)
* Stops & freeze levels (minimum SL/TP distance)
* Tick value / tick size / contract size (P/L math)
* Trade mode, execution mode, margin calc mode
* Swaps, margins, base/profit/margin currencies

---

## Method Signature

```python
async def symbol_params_many(
    self,
    symbol_name: Optional[str] = None,
    deadline: Optional[datetime] = None,
    cancellation_event: Optional[asyncio.Event] = None,
)
```

**Request message:**

```protobuf
message SymbolParamsManyRequest {
  string symbol_name = 1;   // one symbol; omit/empty for all
}
```

**Payload message:**

```protobuf
message SymbolParamsManyData {
  repeated SymbolParamsManyInfo symbol_infos = 1;
}
```

`SymbolParamsManyInfo` has ~75 fields; the trading-relevant ones are below.

---

## 🔽 Input

| Parameter | Type | Description |
|-----------|------|-------------|
| `symbol_name` | str, optional | Restrict to one symbol; omit for all symbols. |
| `deadline` | datetime, optional | Absolute UTC deadline for the gRPC call. |
| `cancellation_event` | asyncio.Event, optional | Set to abort the request. |

---

## ⬆️ Output — `SymbolParamsManyData`

`symbol_infos` — a list of `SymbolParamsManyInfo`. Key fields (note the PascalCase names):

**Identity & precision**

| Field | Python Type | Description |
|-------|-------------|-------------|
| `SymbolName` | `str` | Symbol name |
| `Digits` | `int` | Price decimal places |
| `Point` | `float` | Point size (e.g. 0.00001) |
| `SymDescription` | `str` | Human description |
| `Path` | `str` | Market Watch path/category |

**Volume (lots)**

| Field | Python Type | Description |
|-------|-------------|-------------|
| `VolumeMin` / `VolumeMax` | `float` | Min / max lots per order |
| `VolumeStep` | `float` | Lot increment |
| `VolumeLimit` | `float` | Max total volume per symbol (0 = none) |

**Trade rules**

| Field | Python Type | Description |
|-------|-------------|-------------|
| `TradeStopsLevel` | `int` | Min distance (points) for SL/TP from price |
| `TradeFreezeLevel` | `int` | Freeze distance (points) near price |
| `TradeMode` | `SP_ENUM_SYMBOL_TRADE_MODE` | What's allowed (full / long-only / …) |
| `TradeExeMode` | `SP_ENUM_SYMBOL_TRADE_EXECUTION` | Execution model |
| `TradeCalcMode` | `SP_ENUM_TRADE_CALC_MODE` | Margin calculation mode |

**P/L & cost math**

| Field | Python Type | Description |
|-------|-------------|-------------|
| `TradeTickValue` | `float` | Money per tick for 1 lot |
| `TradeTickSize` | `float` | Price change of one tick |
| `TradeContractSize` | `float` | Units per lot |
| `SwapLong` / `SwapShort` | `float` | Swap rates |
| `MarginInitial` | `float` | Initial margin per lot |
| `CurrencyBase` / `CurrencyProfit` / `CurrencyMargin` | `str` | Symbol currencies |

**Prices** (`Bid`, `BidHigh`, `BidLow`, `AskHigh`, `AskLow`, `SessionOpen`, `SessionClose`, …) are also present for convenience.

---

## 🧱 Related enums (from proto)

### `SP_ENUM_SYMBOL_TRADE_MODE` — field `TradeMode`

| Constant | Value | Meaning |
|----------|-------|---------|
| `SYMBOL_TRADE_MODE_DISABLED` | 0 | Trading disabled |
| `SYMBOL_TRADE_MODE_LONGONLY` | 1 | Longs only |
| `SYMBOL_TRADE_MODE_SHORTONLY` | 2 | Shorts only |
| `SYMBOL_TRADE_MODE_CLOSEONLY` | 3 | Close only |
| `SYMBOL_TRADE_MODE_FULL` | 4 | Full access |

### `SP_ENUM_SYMBOL_TRADE_EXECUTION` — field `TradeExeMode`

| Constant | Value | Meaning |
|----------|-------|---------|
| `SYMBOL_TRADE_EXECUTION_REQUEST` | 0 | Request execution |
| `SYMBOL_TRADE_EXECUTION_INSTANT` | 1 | Instant execution |
| `SYMBOL_TRADE_EXECUTION_MARKET` | 2 | Market execution |
| `SYMBOL_TRADE_EXECUTION_EXCHANGE` | 3 | Exchange execution |

### `SP_ENUM_TRADE_CALC_MODE` — field `TradeCalcMode`

| Constant | Value | Meaning |
|----------|-------|---------|
| `SYMBOL_TRADE_MARGINE_CALC_MODE_FOREX` | 0 | Forex margin calc |
| `SYMBOL_TRADE_MARGINE_CALC_MODE_FUTURES` | 1 | Futures margin calc |
| `SYMBOL_TRADE_MARGINE_CALC_MODE_CFD` | 2 | CFD margin calc |

> Access via `account_helper_pb2.SP_ENUM_SYMBOL_TRADE_MODE.SYMBOL_TRADE_MODE_FULL`, etc.

---

## 🧩 Notes & Tips

* **PascalCase field names.** Most fields are `Digits`, `Point`, `VolumeMin`, `TradeMode` — capitalized, unlike the snake_case elsewhere in the API.
* **Stops level is in points, not pips.** `TradeStopsLevel` is the minimum SL/TP distance in points — convert with `Point` (and remember 1 pip = 10 points on 5-digit symbols).
* **This is the source for normalization.** `VolumeMin/Max/Step` round lots; `Digits`/`Point` round prices. MT4Sugar's `normalize_lot` / `normalize_price` are built on these.
* **Request one or all.** Pass `symbol_name` for a single symbol; omit it to fetch the whole table (can be large).
* **Cache it.** These rarely change intraday — fetch once and reuse, refreshing occasionally.

---

## 🔗 Usage Examples

### 1) Normalize a lot to the broker's rules

Round any desired volume into the allowed `[min, max]` range on the correct step.

```python
async def normalize_lot(account, symbol: str, lots: float) -> float:
    info = (await account.symbol_params_many(symbol)).symbol_infos[0]
    step, lo, hi = info.VolumeStep, info.VolumeMin, info.VolumeMax
    lots = max(lo, min(hi, lots))
    steps = round(lots / step)
    return round(steps * step, 8)

# normalize_lot(account, "EURUSD", 0.0234) -> 0.02
```

### 2) Is my SL far enough from price?

Validate a stop distance against `TradeStopsLevel` before sending an order.

```python
async def sl_distance_ok(account, symbol: str, sl_distance_price: float) -> bool:
    info = (await account.symbol_params_many(symbol)).symbol_infos[0]
    min_distance = info.TradeStopsLevel * info.Point
    if sl_distance_price < min_distance:
        print(f"SL too close: {sl_distance_price:.5f} < min {min_distance:.5f}")
        return False
    return True
```

### 3) Money per pip for a lot

Compute the P/L value of one pip for sizing by risk.

```python
async def money_per_pip(account, symbol: str, lots: float = 1.0) -> float:
    info = (await account.symbol_params_many(symbol)).symbol_infos[0]
    # pip = 10 points on 5/3-digit symbols, else 1 point
    pip_points = 10 if info.Digits in (3, 5) else 1
    value = info.TradeTickValue * (pip_points * info.Point / info.TradeTickSize) * lots
    print(f"{symbol}: ~{value:.2f} {info.CurrencyProfit} per pip for {lots} lot")
    return value
```

---

## ⚠️ Pitfalls

* **PascalCase, not snake_case.** `info.VolumeMin`, not `info.volume_min` — an easy `AttributeError`.
* **Points vs pips.** `TradeStopsLevel`, `TradeFreezeLevel` and `Point` are in points; convert to pips before comparing to pip-based SL/TP.
* **`TradeStopsLevel` may be 0.** Some brokers report 0 (no minimum) — your SL/TP can then sit anywhere, but still normalize to `Digits`.
* **Large payload for "all".** Omitting `symbol_name` returns every symbol — request one when you only need one.

---

## 🧪 Testing Suggestions

* **Single symbol.** `symbol_params_many("EURUSD").symbol_infos` has one entry with `SymbolName == "EURUSD"`.
* **Normalization.** `normalize_lot(..., 0.0234)` returns a multiple of `VolumeStep` within `[VolumeMin, VolumeMax]`.
* **All symbols.** Omitting `symbol_name` returns many entries; each has positive `Digits` and `VolumeStep`.

---

## 📚 See also

* [Tick Value & Size](tick_value_with_size.md)
* [Symbols](symbols.md)
* [Quote](quote.md)

* **Back to:** [Symbols & Quotes — Overview](Symbols_Quotes.Overview.md) · [MT4Account — Master Overview](../MT4Account.Master.Overview.md)
