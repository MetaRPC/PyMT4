# 🍭 Core & Defaults — Sugar Methods
_Auto-generated from code; examples enriched with `main_sugar.py` excerpts._
## `set_defaults(symbol=None, magic=None, deviation_pips=None, slippage_pips=None, risk_percent=None)`
Set user-friendly defaults for subsequent operations.
**Usage**
```python
sugar.set_defaults(symbol="EURUSD", magic=1001, deviation_pips=5, risk_percent=1.0)
```
**Call Flow**
- `main_sugar.py` → `MT4Sugar.set_defaults` → in-memory defaults store
- Low-level: [PyMT4/app/MT4Sugar.py](../../PyMT4/app/MT4Sugar.py)

---
## `with_defaults(**overrides)`
Temporarily override defaults within a context block.
**Usage**
```python
# English comments only:
params = sugar.with_defaults(symbol=None, magic=None, deviation_pips=None)
```
**Call Flow**
- `main_sugar.py` → `MT4Sugar.with_defaults` → in-memory defaults store
- Low-level: [PyMT4/app/MT4Sugar.py](../../PyMT4/app/MT4Sugar.py)

---
## `get_default(key, fallback=None)`
Return a default value by key with fallback.
**Parameters**
| Param | Description |
|---|---|
| `key` |  |
| `fallback` |  |

**Usage**
```python
magic = sugar.get_default("magic")
```
**Call Flow**
- `main_sugar.py` → `MT4Sugar.get_default` → in-memory defaults store
- Low-level: [PyMT4/app/MT4Sugar.py](../../PyMT4/app/MT4Sugar.py)

---
## `async ensure_connected()`
Reconnect if needed to guarantee an active session.
**Usage**
```python
sugar.ensure_connected()
```
**Call Flow**
- `main_sugar.py` → `MT4Sugar.ensure_connected()` → connection service
- Low-level: _(file not found in tree)_

---
## `async ping()`
Lightweight connectivity probe returning True/False.
**Usage**
```python
if sugar.ping():
    print("OK")
```
**Call Flow**
- `main_sugar.py` → `MT4Sugar.ping()` → connection/health RPC
- Low-level: _(file not found in tree)_

---
