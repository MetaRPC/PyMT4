# Core & Defaults

## 🔌 `async ensure_connected()`

**What it does:** Ensures that the connection to the terminal is alive; automatically reconnects if lost.

**Used in:**

* Before any market operations (quotes, bars, orders).
* In long-running loops/workers to avoid silent disconnections.

**Example**

```python
# Ensure connection before any market calls
await sugar.ensure_connected()
price = await api.quote("EURUSD")
```

---

## 🔎 `get_default(key, fallback=None)`

**What it does:** Returns a stored default value by key (`symbol`, `magic`, `deviation_pips`, `risk_percent`, etc.).

**Used in:**

* When you need to read the current default for logic/logging.
* In wrappers where some parameters are auto-filled.

**Example**

```python
magic = sugar.get_default("magic", fallback=1001)
print("Current magic:", magic)
```

---

## 📡 `async ping()`

**What it does:** Lightweight connection health check. Returns `True/False`.

**Used in:**

* Monitoring, watchdog loops, readiness probes before executing critical actions.
* Together with `ensure_connected()` to quickly verify connectivity between operations.

**Example**

```python
# Health check between tasks
if not await sugar.ping():
    await sugar.ensure_connected()
```

---

## 🧬 `set_defaults(symbol=None, magic=None, deviation_pips=None, slippage_pips=None, risk_percent=None)`

**What it does:** Sets human-friendly defaults that will be automatically injected into sugar calls.

**Used in:**

* Once during app/script startup.
* When switching trading contexts (different symbol, different `magic`, etc.).

**Example**

```python
# App bootstrap: configure sane defaults
sugar.set_defaults(
    symbol="EURUSD",
    magic=1001,
    deviation_pips=5,
    slippage_pips=3,
    risk_percent=1.0,
)
```

---

## `with_defaults(**overrides)`

**What it does:** Temporarily override defaults in a limited context (within a code block).

**Used in:**

* Local scenarios: "for this section, trade GBPUSD with another magic."
* Tests/strategies where it’s convenient to change context locally.

**Example**

```python
# Temporarily switch trading context
with sugar.with_defaults(symbol="GBPUSD", magic=2002):
    # Inside this block calls will use these defaults
    await api.order_send(side="buy", lot=0.1)  # uses symbol=GBPUSD, magic=2002

# Outside — back to global defaults
```
