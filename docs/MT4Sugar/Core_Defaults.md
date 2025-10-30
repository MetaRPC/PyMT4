# 🍭 Core & Defaults — Sugar Methods

> Short reference auto-generated from `app/MT4Sugar.py`. English-only comments inside code blocks.

||||

## 🧩 `set_defaults(symbol=None, magic=None, deviation_pips=None, slippage_pips=None, risk_percent=None)`

Set user-friendly defaults for subsequent operations.


### Parameters

| Param | Default | Description |
|---|---|---|
| `symbol` | `None` |  |
| `magic` | `None` |  |
| `deviation_pips` | `None` |  |
| `slippage_pips` | `None` |  |
| `risk_percent` | `None` |  |


### Usage

```python
sugar.set_defaults(symbol="EURUSD", magic=1001, deviation_pips=5, risk_percent=1.0)
# Tip: call once at app startup; overrides can be passed per-call later.
```


### Notes

- Keep defaults minimal and explicit. Avoid hidden magic in business logic.

- These helpers are safe to call many times; latest values take precedence.


||||

## 🧪 `with_defaults(**overrides)`

Temporarily override defaults within a context block.


### Parameters

| Param | Default | Description |
|---|---|---|
| `**overrides` | `` |  |


### Usage

```python
# English comments only (as requested):
# Fill missing keyword-args using stored defaults.
params = sugar.with_defaults(symbol=None, magic=None, deviation_pips=None)
# Now you can safely pass `params` to other sugar/service methods.
```


### Notes

- Keep defaults minimal and explicit. Avoid hidden magic in business logic.

- These helpers are safe to call many times; latest values take precedence.


||||

## 🔎 `get_default(key, fallback=None)`

Return a default value by key with fallback.


### Parameters

| Param | Default | Description |
|---|---|---|
| `key` | `` |  |
| `fallback` | `None` |  |


### Usage

```python
# Retrieve a single default value by key.
magic = sugar.get_default("magic")
assert isinstance(magic, int)
```


### Notes

- Keep defaults minimal and explicit. Avoid hidden magic in business logic.


||||

## 🔌 `async ensure_connected()`

Reconnect if needed to guarantee an active session.


### Parameters

_No parameters._


### Usage

```python
# Ensure connection is alive; auto-reconnect if supported by backend.
sugar.ensure_connected()
```


### Notes

- Keep defaults minimal and explicit. Avoid hidden magic in business logic.

- Consider calling before any market operations; combine with `ping()` in long-running loops.


||||

## 📡 `async ping()`

Lightweight connectivity probe returning True/False.


### Parameters

_No parameters._


### Usage

```python
# Lightweight round-trip check; returns latency or raises on failure.
ok = sugar.ping()
print("Ping:", ok)
```


### Notes

- Keep defaults minimal and explicit. Avoid hidden magic in business logic.

- Use for health checks and metrics dashboards.


||||
