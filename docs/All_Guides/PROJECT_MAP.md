# 🗺️ PyMT4 Project Map

> The whole project as one annotated tree, with links. **Links point to section *overviews*, never to individual method pages** — open an overview to drill down into its methods.

---

## 🧱 The three layers

PyMT4 is built in three decoupled layers. Your code can enter at any level.

| Layer | Source | What it does | Overview |
| ----- | ------ | ------------ | -------- |
| **3 · MT4Sugar** | `app/MT4Sugar.py` | Convenience on top of Service: pips-based SL/TP, risk-based sizing, price/volume normalization, trailing/breakeven, batch close/cancel, watchers. | [MT4Sugar overview](https://metarpc.github.io/PyMT4/MT4Sugar/MT4Sugar.Master.Overview/) |
| **2 · MT4Service** | `app/MT4Service.py` | Typed facade: friendly signatures (string timeframes, masks, sort), unpacked Python data (no raw proto). What most code uses. | [MT4Service overview](https://metarpc.github.io/PyMT4/MT4Service/MT4Service.Overview/) |
| **1 · MT4Account** | `package/MetaRpcMT4/mt4_account.py` | Low-level gRPC: proto request/reply, connect/session, auto-reconnect, streaming. Everything else builds on it. | [MT4Account overview](https://metarpc.github.io/PyMT4/MT4Account/MT4Account.Master.Overview/) |

```
Your code  →  MT4Sugar  →  MT4Service  →  MT4Account  →  gRPC  →  MetaRPC gateway → MT4 terminal
```

---

## 🌳 Repository tree

- **`PyMT4/`** — repo root (SDK layers + runnable demo project)
  - **`app/`** — the mid/high-level layers
    - `MT4Service.py` — **Layer 2** source → [MT4Service overview](https://metarpc.github.io/PyMT4/MT4Service/MT4Service.Overview/)
    - `MT4Sugar.py` — **Layer 3** source → [MT4Sugar overview](https://metarpc.github.io/PyMT4/MT4Sugar/MT4Sugar.Master.Overview/)
    - **`Helper/`** — `errors.py` (domain exceptions), `rate_limit.py`
  - **`package/MetaRpcMT4/`** — low-level gRPC layer (vendored)
    - `mt4_account.py` — **Layer 1** source → [MT4Account overview](https://metarpc.github.io/PyMT4/MT4Account/MT4Account.Master.Overview/)
    - `*_pb2.py` / `*_pb2_grpc.py` — generated gRPC / protobuf stubs (the raw contract)
  - **`Strategy/`** — the strategy library (imported by the orchestrator examples)
    - **`orchestrator/`** — the five orchestrators → [Strategies overview](https://metarpc.github.io/PyMT4/Strategies/Strategies.Master.Overview/)
    - **`presets/`** — strategy & risk presets
  - **`examples/`** — runnable demos (the numbered menu), launched from `main.py`
    - `main.py` — interactive menu / CLI runner → [Getting Started](GETTING_STARTED.md)
    - **`0_common/`** — shared helpers (`demo_helpers.py`, `progress_bar.py`) + `settings.json` (your MT4 credentials) · protobuf inspector (18) → [Protobuf Inspector](PROTOBUF_INSPECTOR_GUIDE.md)
    - **`1_lowlevel/`** — `01`–`03` → [MT4Account overview](https://metarpc.github.io/PyMT4/MT4Account/MT4Account.Master.Overview/)
    - **`2_service/`** — `04` → [MT4Service overview](https://metarpc.github.io/PyMT4/MT4Service/MT4Service.Overview/)
    - **`3_sugar/`** — `06`–`08` → [MT4Sugar overview](https://metarpc.github.io/PyMT4/MT4Sugar/MT4Sugar.Master.Overview/)
    - **`4_orchestrators/`** — `11`–`16` → [Strategies overview](https://metarpc.github.io/PyMT4/Strategies/Strategies.Master.Overview/)
    - **`5_usercode/`** — `17` → [UserCode Sandbox](USERCODE_SANDBOX_GUIDE.md)
  - **`docs/`** — this documentation site (see the map below)
  - `mkdocs.yml` — docs site config · `.github/workflows/` — CI

---

## 📚 Documentation tree

- **`docs/`**
  - [Home](../index.md) — landing page
  - **`All_Guides/`** — the guides (Getting Started, Your First Project, Glossary, Sync vs Async, gRPC Streaming, ENUMs, Return Codes, …); browse them in the left nav or on the [docs site](https://metarpc.github.io/PyMT4/)
  - **`MT4Account/`** — low-level gRPC docs → [overview](https://metarpc.github.io/PyMT4/MT4Account/MT4Account.Master.Overview/) *(per-method pages inside)*
  - **`MT4Service/`** — typed facade docs → [overview](https://metarpc.github.io/PyMT4/MT4Service/MT4Service.Overview/) *(per-group pages inside)*
  - **`MT4Sugar/`** — convenience API docs → [overview](https://metarpc.github.io/PyMT4/MT4Sugar/MT4Sugar.Master.Overview/) *(per-group pages inside)*
  - **`Strategies/`** — the orchestrators → [overview](https://metarpc.github.io/PyMT4/Strategies/Strategies.Master.Overview/) *(per-strategy pages inside)*
  - `Guide_Images/` · `styles/` · `javascripts/` · `includes/` — assets & theme

> The `MT4Account/`, `MT4Service/`, `MT4Sugar/` and `Strategies/` folders hold the detail pages. By design this map links only their **overviews** — each overview is the index into its own pages.

---

## 🎯 Which layer should you use?

- **Most trading apps → [MT4Sugar](https://metarpc.github.io/PyMT4/MT4Sugar/MT4Sugar.Master.Overview/).** Pips-based SL/TP, risk sizing and auto-normalization protect you from off-quote and invalid-volume rejections.
- **Custom execution → [MT4Service](https://metarpc.github.io/PyMT4/MT4Service/MT4Service.Overview/).** Typed calls when you manage your own sizing/normalization.
- **Protocol-level control → [MT4Account](https://metarpc.github.io/PyMT4/MT4Account/MT4Account.Master.Overview/).** Raw proto structures and streams.
