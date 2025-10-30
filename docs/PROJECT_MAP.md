# PyMT4 — Project Map & Layers

## 0) TL;DR

* **You edit** (green): `app/`, `examples/`, `Strategy/`, `docs/`, `main*.py`, `appsettings.json`.
* **Don't edit** (lock): `package/MetaRpcMT4/*_pb2*.py` (generated gRPC stubs), build artifacts.
* **Start here**: `main_sugar.py` or `examples/Call_sugar.py` → verify connection → then build strategies in `Strategy/`.
* **Danger zone**: everything that can place/modify/close orders — see `app/MT4Service_Trade_mod.py`. ☢️

Legend: 🟢 = safe to edit, 🔒 = generated/infra, 🎭 = orchestrators, ⚙️ = presets, 📚 = docs, 🧠 = core logic, 🔌 = integration, 🧭 = examples, 🍬 = sugar API.

---

## 1) High-Level Project Map

```
PyMT4/
├── app/                    🟢 🧠 Project application code (services, sugar, helpers)
├── Strategy/               🟢 🎭 Trading orchestrators & presets
├── docs/                   🟢 📚 Documentation (guides, API specs)
├── examples/               🟢 🧭 Runnable demo scripts
├── package/                🔒 Published package sources (incl. generated pb2)
├── main*.py                🟢 Entry points (low_level, sugar, streams, trade_mod)
├── appsettings.json        🟢 Connection settings
├── settings.json           🟢 Project settings
├── README.md               🟢 Project overview
└── mkdocs.yml              🟢 Docs site config
```

### 1.1 `app/` (core SDK wrappers)

```
🟢 app/
├── Helper/                  Configuration, hooks, patches, rate limiting
│   ├── config.py            Settings loader
│   ├── errors.py            Custom exceptions
│   ├── hooks.py             Event hooks system
│   ├── patch_mt4_account.py Compatibility patches
│   ├── rate_limit.py        Rate limiting for API calls
│   └── Design/              Architecture notes
├── MT4Service.py            🔌 Core service wrapper (low-level API)
├── MT4Service_Trade_mod.py ☢️ Trading-focused service wrapper
├── MT4Sugar.py              🍬 High-level sugar API (pip-based, user-friendly)
└── __init__.py
```

Key files:

* `MT4Service.py` — central async client/service wrapper for low-level MT4 API. 🔌
* `MT4Service_Trade_mod.py` — trading operations wrapper (market/pending, modify, close). ☢️
* `MT4Sugar.py` — high-level API with pip-based operations, auto lot calculation, convenience methods. 🍬
* `Helper/config.py` — loads appsettings.json and environment variables. 🧠
* `Helper/hooks.py` — event system for pre/post operation hooks. 🧠
* `Helper/patch_mt4_account.py` — compatibility patches for MT4 quirks. 🧩
* `Helper/rate_limit.py` — prevents API rate limit violations. 🛡️

### 1.2 `Strategy/` (orchestrators & presets)

```
🎭 Strategy/
├── orchestrator/            13 ready-to-use trading scenarios
│   ├── market_one_shot.py           🚀 Instant market execution
│   ├── pending_bracket.py           ⏰ Limit order with timeout
│   ├── spread_guard.py              💰 Cost protection filter
│   ├── session_guard.py             🕐 Time window control
│   ├── oco_straddle.py              🔀 Two-way breakout entry
│   ├── bracket_trailing_activation.py 📈 Conditional trailing
│   ├── equity_circuit_breaker.py    🛑 Drawdown protection
│   ├── dynamic_deviation_guard.py   🎯 Adaptive slippage
│   ├── rollover_avoidance.py        💸 Swap time protection
│   ├── grid_dca_common_sl.py        📊 Grid trading with shared SL
│   ├── kill_switch_review.py        🔴 Emergency stop
│   ├── ladder_builder.py            🪜 Gradual position building
│   └── cleanup.py                   🧹 Close/cancel all
├── presets/                 40+ pre-configured trading profiles
│   ├── risk.py              🎯 Basic risk (Conservative, Balanced, Aggressive, Scalper, Walker)
│   ├── risk_atr.py          📈 ATR-based adaptive risk
│   ├── risk_profiles.py     🎲 Symbol+style combinations
│   ├── risk_session.py      🕐 Session-based risk
│   ├── strategy.py          📋 Strategy base classes
│   └── strategy_symbols.py  💱 30+ symbol presets (EURUSD, XAUUSD, BTCUSD...)
└── __init__.py
```

### 1.3 `examples/` (runnable scripts)

```
🧭 examples/
├── Low_level_call.py        🔧 Low-level API demo (19 methods)
├── Call_sugar.py            🍬 Sugar API demo (~20 methods)
├── Orchestrator_demo.py     🎭 Orchestrators demo (4 scenarios)
├── Presets_demo.py          ⚙️ Presets demo (40+ presets)
└── __init__.py
```

### 1.4 `main*.py` (entry points)

```
🟢 Root level/
├── main_low_level.py        Entry point for low-level API demos
├── main_sugar.py            Entry point for sugar API demos
├── main_streams.py          Entry point for streaming demos
└── main_trade_mod.py        Entry point for trading operations demos
```

### 1.5 `docs/` (documentation)

```
📚 docs/
├── MT4Account/              Low-level API documentation
│   ├── BASE.md              🗺️ Master overview
│   ├── Account_Information/ Account balance/equity/margins
│   ├── Market_quota_symbols/ Quotes, symbols, ticks, history
│   ├── Orders_Positions_History/ Open positions, tickets
│   ├── Trading_Actions/     Order placement, modification, closing
│   └── Streams/             Real-time data streams
├── MT4Sugar/                High-level sugar API docs
│   ├── Core_Defaults.md     Connection, defaults management
│   ├── Symbols_Quotes.md    Symbol info, quotes (8 methods)
│   ├── Market_Data.md       Bars, ticks, price waiting
│   ├── Math_Risk.md         Risk calculations, lot sizing (10 methods)
│   ├── Order_Management.md  Modify, close operations (7 methods)
│   ├── Order_Placement.md   Market, limit, stop orders (7 methods)
│   └── Automation.md        Trailing stops, auto-breakeven
├── Main/                    Entry point documentation
│   ├── main_low_level.md    Low-level API guide
│   ├── main_streams.md      Streaming API guide
│   ├── main_sugar.md        Sugar API guide
│   └── main_trade_mod.md    Trading operations guide
├── Strategy/                Strategy documentation
│   ├── All_about_orchestrator.md 🎭 Orchestrators guide (13 orchestrators)
│   └── All_about_presets.md      ⚙️ Presets guide (40+ presets)
├── Examples/                Examples documentation
│   └── All_about_examples.md     📚 Examples overview
├── Examples_of_illustrations/    Screenshots (LL.bmp, Sugar.bmp, Stream.bmp, Mod.bmp)
└── PROJECT_MAP.md           🗺️ This file
```

### 1.6 `package/MetaRpcMT4` (generated stubs — don't touch)

```
🔒 package/MetaRpcMT4/
├── __init__.py
├── mrpc_mt4_error_pb2(.py|_grpc.py)          🔒 Error codes
├── mt4_term_api_*_pb2(.py|_grpc.py)          🔒 Generated request/response messages & service stubs
├── mt4_account.py                             🟡 Low-level wrapper (avoid editing)
└── ...
```

---

## 2) Who edits what (policy)

* 🟢 **Edit freely**: `app/*`, `Strategy/*`, `examples/*`, `main*.py`, `appsettings.json`, `docs/*`.
* 🛑 **Don't edit**: `package/MetaRpcMT4/*_pb2*.py` (regenerate from proto instead).
* 🧪 **Tests**: put local tests in `package/tests` or add `tests/` at repo root.

---

## 3) Project Trees

### 3.1 Top-level (depth 1)

```
PyMT4/
├── app/                     Core SDK wrappers
├── Strategy/                Orchestrators & presets
├── docs/                    Documentation
├── examples/                Demo scripts
├── package/                 Generated gRPC stubs
├── main_low_level.py        Low-level API entry
├── main_sugar.py            Sugar API entry
├── main_streams.py          Streaming API entry
├── main_trade_mod.py        Trading operations entry
├── appsettings.json         Connection config
├── settings.json            Project settings
├── mkdocs.yml               Docs config
└── README.md
```

### 3.2 `app/` (depth 2)

```
app/
├── Helper/
│   ├── config.py
│   ├── errors.py
│   ├── hooks.py
│   ├── patch_mt4_account.py
│   ├── rate_limit.py
│   └── Design/
├── MT4Service.py
├── MT4Service_Trade_mod.py
├── MT4Sugar.py
└── __init__.py
```

### 3.3 `Strategy/` (depth 2)

```
Strategy/
├── orchestrator/
│   ├── market_one_shot.py
│   ├── pending_bracket.py
│   ├── spread_guard.py
│   ├── session_guard.py
│   ├── oco_straddle.py
│   ├── bracket_trailing_activation.py
│   ├── equity_circuit_breaker.py
│   ├── dynamic_deviation_guard.py
│   ├── rollover_avoidance.py
│   ├── grid_dca_common_sl.py
│   ├── kill_switch_review.py
│   ├── ladder_builder.py
│   └── cleanup.py
├── presets/
│   ├── risk.py
│   ├── risk_atr.py
│   ├── risk_profiles.py
│   ├── risk_session.py
│   ├── strategy.py
│   └── strategy_symbols.py
└── __init__.py
```

### 3.4 `examples/` (depth 1)

```
examples/
├── Low_level_call.py
├── Call_sugar.py
├── Orchestrator_demo.py
├── Presets_demo.py
└── __init__.py
```

### 3.5 `docs/` structure (key files)

```
docs/
├── MT4Account/BASE.md                        🗺️ Low-level API master overview
├── MT4Sugar/*.md                             🍬 Sugar API methods (7 files)
├── Main/*.md                                 📖 Entry point guides (4 files)
├── Strategy/All_about_orchestrator.md        🎭 Orchestrators guide
├── Strategy/All_about_presets.md             ⚙️ Presets guide
├── Examples/All_about_examples.md            📚 Examples overview
├── Examples_of_illustrations/*.bmp           🖼️ Screenshots
└── PROJECT_MAP.md                            🗺️ This file
```

---

## 4) How to build a trading strategy (step-by-step)

### Level 1: Quick Start (Sugar API)
```python
from app.MT4Sugar import MT4Sugar

sugar = MT4Sugar(...)
await sugar.ensure_connected()

# Simple market order with pip-based stops
await sugar.buy_market("EURUSD", lots=0.1, sl_pips=20, tp_pips=40)
```

### Level 2: Using Presets
```python
from Strategy.presets import MarketEURUSD, Balanced
from Strategy.orchestrator.market_one_shot import run_market_one_shot

# Combine strategy preset + risk preset
result = await run_market_one_shot(svc, MarketEURUSD, Balanced)
```

### Level 3: Custom Orchestrator
```python
from Strategy.orchestrator.spread_guard import market_with_spread_guard
from Strategy.orchestrator.session_guard import run_with_session_guard

# Combine multiple orchestrators
result = await run_with_session_guard(
    svc=svc,
    runner_coro_factory=lambda: market_with_spread_guard(
        svc, MarketEURUSD, Balanced, max_spread_pips=2.0
    ),
    windows=[('08:00', '17:00')],
    tz='Europe/London'
)
```

### Level 4: Custom Strategy
1. **Start** with Sugar API — sketch basic logic in `examples/`
2. **Create preset** — define your strategy in `Strategy/presets/`
3. **Build orchestrator** — compose complex flows in `Strategy/orchestrator/`
4. **Combine** — use multiple guards and automation features

---

## 5) API Layers (from low to high)

```
┌─────────────────────────────────────────────┐
│  Strategy Orchestrators & Presets           │ 🎭 Highest level
│  (market_one_shot, Balanced, etc.)          │ Ready-to-use scenarios
└─────────────────────────────────────────────┘
                    ↓ uses
┌─────────────────────────────────────────────┐
│  MT4Sugar API                                │ 🍬 High level
│  (pip-based, auto-calculation, friendly)    │ User-friendly wrappers
└─────────────────────────────────────────────┘
                    ↓ uses
┌─────────────────────────────────────────────┐
│  MT4Service / MT4Service_Trade_mod          │ 🔌 Medium level
│  (service wrappers, connection mgmt)        │ Service orchestration
└─────────────────────────────────────────────┘
                    ↓ uses
┌─────────────────────────────────────────────┐
│  package/MetaRpcMT4/mt4_account.py          │ 🔧 Low level
│  (direct gRPC wrappers)                     │ Generated stubs
└─────────────────────────────────────────────┘
                    ↓ gRPC
┌─────────────────────────────────────────────┐
│  MT4 Terminal                                │ 💻 Broker connection
│  (actual trading platform)                  │
└─────────────────────────────────────────────┘
```

**Choose your level:**
- **Orchestrators** — for complete trading strategies (recommended)
- **Sugar API** — for custom logic with convenience methods
- **Service wrappers** — for fine control with connection management
- **Low-level API** — for maximum control (experts only)

---

## 6) Configuration Files

### `appsettings.json` (connection config)
```json
{
  "access": ["host:port", "host:port"],
  "login": "12345678",
  "password": "your_password",
  "server": "MetaQuotes-Demo"
}
```

### Environment Variables (override appsettings)
```bash
MT4_LOGIN=12345678
MT4_PASSWORD=your_password
MT4_SERVER=MetaQuotes-Demo
ENABLE_TRADING=1  # Enable real trading (default: 0)
```

---

## 7) Documentation Navigation

### By Role:

**Beginner:**
1. Start: [Examples Overview](./Examples/All_about_examples.md)
2. Try: `python examples/Call_sugar.py`
3. Learn: [Sugar API docs](./MT4Sugar/)

**Intermediate:**
1. Read: [Orchestrators Guide](./Strategy/All_about_orchestrator.md)
2. Read: [Presets Guide](./Strategy/All_about_presets.md)
3. Try: `python examples/Orchestrator_demo.py`

**Advanced:**
1. Read: [MT4Account BASE](./MT4Account/BASE.md)
2. Study: [Low-level API docs](./MT4Account/)
3. Try: `python examples/Low_level_call.py`

### By API Level:

| Level | Documentation | Examples | Code |
|-------|--------------|----------|------|
| 🎭 **Orchestrators** | [All_about_orchestrator.md](./Strategy/All_about_orchestrator.md) | `Orchestrator_demo.py` | `Strategy/orchestrator/` |
| ⚙️ **Presets** | [All_about_presets.md](./Strategy/All_about_presets.md) | `Presets_demo.py` | `Strategy/presets/` |
| 🍬 **Sugar API** | [MT4Sugar/](./MT4Sugar/) | `Call_sugar.py`, `main_sugar.py` | `app/MT4Sugar.py` |
| 🔌 **Service** | [Main/](./Main/) | `main_trade_mod.py` | `app/MT4Service*.py` |
| 🔧 **Low-level** | [MT4Account/](./MT4Account/) | `Low_level_call.py`, `main_low_level.py` | `package/MetaRpcMT4/` |

---

## 8) Common Workflows

### Workflow 1: Test Connection
```bash
python main_sugar.py  # or examples/Call_sugar.py
```

### Workflow 2: Run Strategy with Presets
```bash
python examples/Orchestrator_demo.py
```

### Workflow 3: Build Custom Strategy
1. Edit `Strategy/presets/strategy_symbols.py` — add your symbol
2. Edit `Strategy/presets/risk.py` — customize risk profile
3. Use in orchestrator or create new one in `Strategy/orchestrator/`

### Workflow 4: Debug Low-Level API
```bash
python examples/Low_level_call.py
python main_low_level.py
```

---

## 9) Safety Checklist ✅

Before live trading:

- [ ] Test on demo account first
- [ ] Set `ENABLE_TRADING=0` to test syntax (dry run)
- [ ] Verify `appsettings.json` credentials
- [ ] Check connection: `await sugar.ping()`
- [ ] Test with small lots (0.01)
- [ ] Set stop losses on all positions
- [ ] Use `Conservative` risk preset initially
- [ ] Enable rate limiting (`Helper/rate_limit.py`)
- [ ] Monitor equity circuit breaker
- [ ] Review logs before production

---

## 10) Quick Reference

### Key Classes:
- `MT4Service` — core low-level wrapper
- `MT4Service_Trade_mod` — trading operations wrapper
- `MT4Sugar` — high-level convenience API
- `StrategyPreset` — symbol/entry configuration
- `RiskPreset` — risk management configuration

### Key Concepts:
- **Pips** — universal unit for SL/TP in Sugar API
- **Magic numbers** — organize orders by strategy (771-859 range)
- **Deviation** — slippage tolerance (pips)
- **Orchestrators** — complete trading workflows
- **Presets** — reusable configurations

### Key Files to Check:
- Connection issues → `app/Helper/config.py`
- Trading errors → `app/Helper/errors.py`
- API limits → `app/Helper/rate_limit.py`
- MT4 quirks → `app/Helper/patch_mt4_account.py`

---

"Wishing you tight spreads, clean fills, and profits that compound. 🟢"
