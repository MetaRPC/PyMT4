# Symbols & Quotes

## 📈 `digits(symbol=None)`

**What it does:** Returns the number of decimal places for a symbol.
**Used in:** price formatting, level normalization, SL/TP calculations.
**Related to:** [symbol_params_many.md](../docs/MT4Account/Market_quota_symbols/symbol_params_many.md) (symbol parameters)

**Example**

```python
d = sugar.digits("EURUSD")  # -> 5
```

---

## 🧩 `ensure_symbol(symbol)`

**What it does:** Ensures the symbol is available in the terminal (loaded/enabled).
**Used in:** before quotes/orders, during strategy initialization.
**Related to:** [symbols.md](../docs/MT4Account/Market_quota_symbols/symbols.md) (symbol list and availability)

**Example**

```python
sugar.ensure_symbol("EURUSD")
```

---

## 💬 `last_quote(symbol=None)`

**What it does:** Returns the latest quote (bid/ask/time) for the symbol.
**Used in:** logging, diagnostics, fetching current price before order placement.
**Related to:** [quote.md](../docs/MT4Account/Market_quota_symbols/quote.md) (single quote)

**Example**

```python
q = sugar.last_quote("EURUSD")
print(q.bid, q.ask, q.time)
```

---

## ⚖️ `mid_price(symbol=None)`

**What it does:** Returns the mid price = (bid + ask) / 2.
**Used in:** analytics without spread bias, fair price estimation.
**Related to:** [quote.md](../docs/MT4Account/Market_quota_symbols/quote.md) (bid/ask base fields)

**Example**

```python
m = sugar.mid_price("EURUSD")
```

---

## 📏 `pip_size(symbol=None)`

**What it does:** Returns the pip size for the symbol.
**Used in:** converting pips to price and back, SL/TP and risk calculations.
**Related to:** [tick_value_with_size.md](../docs/MT4Account/Market_quota_symbols/tick_value_with_size.md) (tick size/value)

**Example**

```python
pip = sugar.pip_size("EURUSD")  # -> 0.0001 for most majors
```

---

## 🎯 `point(symbol=None)`

**What it does:** Returns the smallest possible price increment (point). Often equals `pip_size / 10` depending on the broker.
**Used in:** price rounding, normalization, internal calculations.
**Related to:** [symbol_params_many.md](../docs/MT4Account/Market_quota_symbols/symbol_params_many.md) (symbol parameters)

**Example**

```python
pt = sugar.point("EURUSD")
```

---

## 📊 `quotes(symbols: list[str] | None = None)`

**What it does:** Retrieves quotes for multiple symbols (or all active ones).
**Used in:** bulk data refresh, dashboards, pre-decision analytics.
**Related to:** [quote_many.md](../docs/MT4Account/Market_quota_symbols/quote_many.md) (multi-quote)

**Example**

```python
for q in sugar.quotes(["EURUSD","GBPUSD","USDJPY"]):
    print(q.symbol, q.bid, q.ask)
```

---

## 💸 `spread_pips(symbol=None)`

**What it does:** Returns the current spread in pips for the symbol.
**Used in:** market quality filters, alerts, entry conditions.
**Related to:** [quote.md](../docs/MT4Account/Market_quota_symbols/quote.md) (bid/ask source)

**Example**

```python
sp = sugar.spread_pips("EURUSD")
print("Spread:", sp, "pips")
```
