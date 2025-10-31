# Symbols & Quotes

## 📈 `digits(symbol=None)`

**What it does:** Returns the number of decimal places for a symbol.

**Used in:**
* Price formatting and display
* Level normalization and rounding
* SL/TP calculations
* Determining price precision requirements

**Parameters:**
* `symbol` - (Optional) Trading symbol. If None, uses default symbol.

**Returns:** Number of decimal places (int)

**Important notes:**
* EURUSD, GBPUSD: typically 5 digits (1.09567)
* USDJPY: typically 3 digits (150.123)
* Gold (XAUUSD): typically 2 digits (1850.25)

**Related to:** [symbol_params_many.md](../docs/MT4Account/Market_quota_symbols/symbol_params_many.md) (symbol parameters)

**Example 1: Get digits for formatting**

```python
d = sugar.digits("EURUSD")  # -> 5
print(f"Price: {price:.{d}f}")  # Format with correct decimals
```

**Example 2: Multi-symbol display**

```python
symbols = ["EURUSD", "USDJPY", "XAUUSD"]
for sym in symbols:
    digits = await sugar.digits(sym)
    quote = await sugar.last_quote(sym)
    print(f"{sym}: {quote['bid']:.{digits}f}")
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

**Used in:**
* Logging and diagnostics
* Fetching current price before order placement
* Real-time price monitoring
* Spread analysis

**Parameters:**
* `symbol` - (Optional) Trading symbol. If None, uses default symbol.

**Returns:** Dictionary with keys: `bid`, `ask`, `time`

**Related to:** [quote.md](../docs/MT4Account/Market_quota_symbols/quote.md) (single quote)

**Example 1: Get current price**

```python
q = await sugar.last_quote("EURUSD")
print(f"Bid: {q['bid']}, Ask: {q['ask']}, Time: {q['time']}")
```

**Example 2: Check spread before trading**

```python
quote = await sugar.last_quote("EURUSD")
spread = quote["ask"] - quote["bid"]
pip_size = await sugar.pip_size("EURUSD")
spread_pips = spread / pip_size

if spread_pips < 2.0:
    await sugar.buy_market("EURUSD", lots=0.1)
else:
    logger.warning(f"Spread too high: {spread_pips:.1f} pips")
```

**Example 3: Price logging loop**

```python
while True:
    quote = await sugar.last_quote("EURUSD")
    logger.info(f"EURUSD: {quote['bid']}/{quote['ask']}")
    await asyncio.sleep(5)
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

**What it does:** Retrieves quotes for multiple symbols in a single call (or all active ones if None).

**Used in:**
* Bulk data refresh and dashboards
* Pre-decision analytics
* Multi-symbol monitoring
* Portfolio analysis

**Parameters:**
* `symbols` - (Optional) List of symbol names. If None, returns all active symbols.

**Returns:** Dictionary mapping symbol names to quote dicts: `{"EURUSD": {"bid": 1.09, "ask": 1.091, "time": ...}, ...}`

**Important notes:**
* More efficient than calling `last_quote()` multiple times
* Returns dict, not list
* Useful for dashboards and monitoring systems

**Related to:** [quote_many.md](../docs/MT4Account/Market_quota_symbols/quote_many.md) (multi-quote)

**Example 1: Get multiple quotes**

```python
quotes_dict = await sugar.quotes(["EURUSD", "GBPUSD", "USDJPY"])
for symbol, quote in quotes_dict.items():
    print(f"{symbol}: Bid={quote['bid']}, Ask={quote['ask']}")
```

**Example 2: Trading dashboard**

```python
async def show_dashboard():
    """Display real-time trading dashboard"""
    symbols = ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD"]

    while True:
        quotes = await sugar.quotes(symbols)

        print("\n===== TRADING DASHBOARD =====")
        for sym in symbols:
            q = quotes.get(sym)
            if q:
                spread = q["ask"] - q["bid"]
                pip_size = await sugar.pip_size(sym)
                spread_pips = spread / pip_size
                print(f"{sym:8} | Bid: {q['bid']:8.5f} | Ask: {q['ask']:8.5f} | Spread: {spread_pips:.1f} pips")

        await asyncio.sleep(2)
```

**Example 3: Correlation analysis**

```python
# Monitor correlated pairs
correlated_pairs = ["EURUSD", "GBPUSD", "EURGBP"]
quotes = await sugar.quotes(correlated_pairs)

# Calculate mid prices
mids = {sym: (q["bid"] + q["ask"]) / 2 for sym, q in quotes.items()}

# Check if correlation holds
eurusd_gbpusd_ratio = mids["EURUSD"] / mids["GBPUSD"]
eurgbp_price = mids["EURGBP"]

print(f"EURUSD/GBPUSD ratio: {eurusd_gbpusd_ratio:.5f}")
print(f"EURGBP price: {eurgbp_price:.5f}")
print(f"Correlation delta: {abs(eurusd_gbpusd_ratio - eurgbp_price):.5f}")
```

---

## 💸 `spread_pips(symbol=None)`

**What it does:** Returns the current spread in pips for the symbol.

**Used in:**
* Market quality filters and trade entry conditions
* Spread alerts and monitoring
* Cost analysis and optimization
* Broker comparison

**Parameters:**
* `symbol` - (Optional) Trading symbol. If None, uses default symbol.

**Returns:** Current spread in pips (float)

**Important notes:**
* Low spread: < 1.5 pips (good for scalping)
* Normal spread: 1.5-3 pips
* High spread: > 3 pips (avoid trading)
* Spread increases during news and low liquidity periods

**Related to:** [quote.md](../docs/MT4Account/Market_quota_symbols/quote.md) (bid/ask source)

**Example 1: Check spread**

```python
sp = await sugar.spread_pips("EURUSD")
print(f"Spread: {sp:.1f} pips")
```

**Example 2: Spread filter for entries**

```python
# Only trade when spread is acceptable
spread = await sugar.spread_pips("EURUSD")

if spread < 2.0:
    await sugar.buy_market("EURUSD", lots=0.1)
else:
    logger.warning(f"Spread too high: {spread:.1f} pips - skipping trade")
```

**Example 3: Monitor spread across multiple symbols**

```python
symbols = ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD"]

while True:
    print("\n=== Spread Monitor ===")
    for symbol in symbols:
        spread = await sugar.spread_pips(symbol)
        status = "GOOD" if spread < 2.0 else "HIGH"
        print(f"{symbol}: {spread:.1f} pips [{status}]")

    await asyncio.sleep(10)
```

**Example 4: Spread alert system**

```python
MAX_SPREAD = 3.0

async def monitor_spread(symbol):
    while True:
        spread = await sugar.spread_pips(symbol)
        if spread > MAX_SPREAD:
            logger.error(f"ALERT: {symbol} spread={spread:.1f} pips!")
            await send_alert(f"High spread on {symbol}")
        await asyncio.sleep(5)
```
