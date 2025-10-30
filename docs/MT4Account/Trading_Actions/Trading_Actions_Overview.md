# MT4Account · Trading Actions — Overview

> Entry / exit operations for **live trading** on MT4 accounts.
> Use this page to choose the correct action quickly.

---

## 📁 What lives here

* **[order_send](./order_send.md)** — place **market** or **pending** order (with optional SL/TP, expiration).
* **[order_modify](./order_modify.md)** — update **SL/TP**, **pending price**, and **expiration**.
* **[order_close_delete](./order_close_delete.md)** — **close** market position (full/partial) or **delete** pending order.
* **[order_close_by](./order_close_by.md)** — close one hedge position **by another** opposite one (same symbol) → netting.

---

## 🧭 Plain English

* **order_send** → **Enter the market** or schedule a pending entry.
* **order_modify** → Adjust protection or re-price pending order.
* **order_close_delete** → **Exit** or cancel waiting order.
* **order_close_by** → Fast **de-hedge**: match BUY vs SELL to reduce costs.

> Rule of thumb:  
> ✅ You want **to enter** → `order_send()`  
> ✅ You want **to exit or cancel** → `order_close_delete()`  
> ✅ You want **to tweak SL/TP or pending** → `order_modify()`  
> ✅ Hedge account and you want **clean netting** → `order_close_by()`

---

## Quick choose

| If you need… | Use | Works on | Key inputs | Safety notes |
|--------------|-----|----------|------------|--------------|
| Market entry or pending order | `order_send` | BUY / SELL / LIMIT / STOP | symbol, op_type, volume, SL/TP | Check StopsLevel / FreezeLevel |
| Update SL/TP / pending price / expiration | `order_modify` | Market or pending | ticket, new\_sl/tp, new\_price | Only pendings accept new\_price |
| Close position or delete pending | `order_close_delete` | Market or pending | ticket, lots?, slippage? | Respect volume step; slippage only for market |
| Close one hedge position by another | `order_close_by` | Hedge accounts only | two tickets | Same symbol, opposite side only |

---

## ❌ Cross-refs & Gotchas

* **Volume rules**: snap to `VolumeMin/Max/Step` (`symbol_params_many`)
* **Protection distance**: `StopsLevel` + `FreezeLevel` must be respected
* **Expiration** only applies to **pending** orders
* **Partial close** only through `order_close_delete`
* **Close By** not available on netting accounts
* On retry (reconnect) events may duplicate — keep UI actions idempotent

