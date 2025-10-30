# MT4 API Examples

Примеры использования PyMT4 с четырьмя уровнями абстракции.

## Демонстрационные файлы

### 1. **Low_level_call.py** - Low-Level API (19 методов)
Прямые gRPC вызовы без оберток, максимальный контроль.

```bash
python examples/Low_level_call.py
```

**Демонстрирует:**
- Connection (2 метода): `connect_by_server_name()`, `connect_by_host_port()`
- Account (1 метод): `account_summary()`
- Market Data (6 методов): `symbols()`, `quote()`, `quote_many()`, `quote_history()`, etc.
- Orders (3 метода): `opened_orders()`, `orders_history()`, etc.
- Trading (4 метода): `order_send()`, `order_modify()`, `order_close_delete()`, `order_close_by()`
- Streaming (4 метода): `on_symbol_tick()`, `on_trade()`, `on_opened_orders_tickets()`, etc.

**Особенности:**
- Принудительные таймауты для стримов (решена проблема зависания)
- 3-приоритетная система подключения
- По умолчанию торговля выключена (`ENABLE_TRADING=0`)

---

### 2. **Call_sugar.py** - Sugar API (~20 методов)
Высокоуровневые обертки с удобным интерфейсом и пипсами.

```bash
python examples/Call_sugar.py
```

**Демонстрирует:**
- Connection: `ensure_connected()`, `ping()`
- Symbol Info: `digits()`, `point()`, `pip_size()`, `spread_pips()`, `mid_price()`
- Risk Management: `calc_lot_by_risk()`, `calc_cash_risk()`
- Exposure: `exposure_summary()`, `opened_orders()`
- Trading: `buy_market()`, `sell_market()`, `buy_limit()`, `sell_stop()`
- Order Management: `modify_sl_tp_by_pips()`, `close()`, `close_partial()`

**Особенности:**
- Все SL/TP задаются в пипсах
- Автоматический расчет лотов по риску
- Удобные хелперы для работы с ценами

---

### 3. **Orchestrator_demo.py** - Strategy Orchestrators
Модульные торговые сценарии с пресетами и гвардами.

```bash
python examples/Orchestrator_demo.py
```

**Демонстрирует 4 оркестра:**

#### 1. `market_one_shot` - Рыночный ордер с автоматикой
```python
from Strategy.presets import MarketEURUSD, Balanced
from Strategy.orchestrator.market_one_shot import run_market_one_shot

result = await run_market_one_shot(svc, MarketEURUSD, Balanced)
# Открывает рыночный ордер + trailing stop + auto-breakeven
```

#### 2. `pending_bracket` - Отложенный ордер с таймаутом
```python
from Strategy.presets import LimitEURUSD, Conservative
from Strategy.orchestrator.pending_bracket import run_pending_bracket

strategy = LimitEURUSD(price=1.0850)
result = await run_pending_bracket(svc, strategy, Conservative, timeout_s=900)
# Ждет исполнения, если не сработал - отменяет
```

#### 3. `spread_guard` - Фильтр по спреду
```python
from Strategy.orchestrator.spread_guard import market_with_spread_guard

result = await market_with_spread_guard(
    svc, strategy, risk,
    max_spread_pips=1.5  # Торгует только если спред <= 1.5 пипсов
)
```

#### 4. `session_guard` - Торговые окна
```python
from Strategy.orchestrator.session_guard import run_with_session_guard

windows = [('08:00', '11:30'), ('13:00', '17:00')]
result = await run_with_session_guard(
    svc=svc,
    runner_coro_factory=lambda: run_market_one_shot(svc, strategy, risk),
    windows=windows,
    tz='Europe/London',
    weekdays=[0,1,2,3,4]  # Пн-Пт
)
```

**Доступные пресеты:**

**Strategy Presets:**
- `MarketEURUSD` - рыночный ордер
- `LimitEURUSD(price)` - лимитный ордер
- `BreakoutBuy(symbol, offset_pips)` - пробой уровня

**Risk Presets:**
- `Conservative` - 0.5% риск, SL=25p, TP=50p
- `Balanced` - 1.0% риск, SL=20p, TP=40p
- `Aggressive` - 2.0% риск, SL=15p, TP=30p
- `Scalper` - 1.0% риск, SL=8p, TP=12p, trailing=6p
- `Walker` - 0.75% риск, SL=30p, TP=60p, breakeven=20p+2p

**Другие оркестры (доступны в коде):**
- `oco_straddle` - двухсторонний вход (OCO)
- `bracket_trailing_activation` - активация трейлинга по условию
- `equity_circuit_breaker` - аварийная остановка при просадке
- `dynamic_deviation_guard` - адаптивный девиейшн
- `rollover_avoidance` - избежание времени свопа
- `grid_dca_common_sl` - сетка с общим SL

---

## Запуск

### Через appsettings.json (рекомендуется)
```bash
python examples/Low_level_call.py
python examples/Call_sugar.py
python examples/Orchestrator_demo.py
```

Скрипты автоматически читают `appsettings.json` из корня проекта.

### Через переменные окружения (PowerShell)
```powershell
$env:MT4_LOGIN="12345678"
$env:MT4_PASSWORD="your_password"
$env:MT4_SERVER="MetaQuotes-Demo"
python examples/Low_level_call.py
```

### Включить реальную торговлю
```bash
export ENABLE_TRADING=1
python examples/Call_sugar.py
```

⚠️ **ВНИМАНИЕ**: По умолчанию торговля выключена (`ENABLE_TRADING=0`) - показывается только синтаксис!

---

## Сравнение уровней

| Уровень | Файл | Компонентов | Использование | Гибкость |
|---------|------|-------------|---------------|----------|
| **Low-Level** | `Low_level_call.py` | 19 методов | Прямые gRPC вызовы | Максимальная |
| **Sugar** | `Call_sugar.py` | ~20 методов | Удобные обертки | Высокая |
| **Orchestrator** | `Orchestrator_demo.py` | 4+ оркестра | Готовые сценарии | Модульная |
| **Presets** | `Presets_demo.py` | 40+ пресетов | Конфигурации | Композиция |

---

### 4. **Presets_demo.py** - Reusable Configurations (40+ presets)
Все доступные пресеты для стратегий и риск-менеджмента.

```bash
python examples/Presets_demo.py
```

**Демонстрирует 5 категорий пресетов:**

#### 1. Basic Risk Presets (5 профилей)
```python
from Strategy.presets.risk import Conservative, Balanced, Aggressive, Scalper, Walker

result = await run_market_one_shot(svc, MarketEURUSD, Balanced)
```

#### 2. ATR-Based Risk (3 динамических профиля)
```python
from Strategy.presets.risk_atr import ATR_Scalper, ATR_Balanced, ATR_Swing

risk = await ATR_Balanced(svc, "EURUSD", risk_percent=1.0)
# SL/TP автоматически рассчитываются от ATR (волатильности)
```

#### 3. Risk Profiles (8+ профилей)
```python
from Strategy.presets.risk_profiles import ScalperEURUSD, SwingXAUUSD

# Специализированные под символ и стиль торговли
result = await run_market_one_shot(svc, MarketXAUUSD, SwingXAUUSD())
```

#### 4. Session-Based Risk (4 сессии)
```python
from Strategy.presets.risk_session import session_risk_auto

# Автоматический выбор по текущей сессии
risk = await session_risk_auto(svc, "EURUSD", tz="Europe/London")
# Asia / London / NewYork / Overlap
```

#### 5. Strategy Symbol Presets (30+ символов)
```python
from Strategy.presets.strategy_symbols import (
    MarketEURUSD, MarketXAUUSD, MarketBTCUSD,
    LimitGBPUSD, BreakoutEURUSD
)

# Символы: Forex, Metals, Indices, Crypto
# Типы: Market, Limit, Breakout
```

**Все пресеты:**
- Forex: EURUSD, GBPUSD, USDJPY
- Metals: XAUUSD, XAGUSD
- Indices: US100, US500, GER40
- Crypto: BTCUSD

---

## Структура examples/

```
examples/
├── Low_level_call.py          # Low-level API demo (19 методов)
├── Call_sugar.py              # Sugar API demo (~20 методов)
├── Orchestrator_demo.py       # Orchestrators demo (4 оркестра)
├── Presets_demo.py            # Presets demo (40+ пресетов)
├── .env.example               # Environment variables template
└── README.md                  # This file
```

---

## Переменные окружения

| Переменная | Обязательна | По умолчанию | Описание |
|------------|-------------|--------------|----------|
| `MT4_LOGIN` | ✓* | - | Логин MT4 |
| `MT4_PASSWORD` | ✓* | - | Пароль MT4 |
| `MT4_SERVER` | ✗ | MetaQuotes-Demo | Имя сервера |
| `MT4_HOST` | ✗ | - | Хост для прямого подключения |
| `MT4_PORT` | ✗ | 443 | Порт |
| `BASE_SYMBOL` | ✗ | EURUSD | Базовый символ |
| `SYMBOL` | ✗ | EURUSD | Символ для тестов |
| `ENABLE_TRADING` | ✗ | 0 | Включить торговлю (1=да) |
| `CONNECT_TIMEOUT` | ✗ | 30 | Таймаут подключения |

*если не задан в `appsettings.json`

---

## Решение проблем

### Ошибка подключения
1. Проверьте `appsettings.json` - должен быть список `access` с host:port
2. Проверьте логин/пароль
3. Проверьте имя сервера (`MT4_SERVER`)

### Зависание стримов
Исправлено в `Low_level_call.py` - добавлены принудительные таймауты (1 сек).

### Ошибка импорта
Убедитесь что запускаете из корня проекта:
```bash
cd /path/to/PyMT4
python examples/Low_level_call.py
```

---

## Дополнительные ресурсы

- [Документация MT4Sugar](../app/MT4Sugar.py)
- [Стратегические оркестры](../Strategy/orchestrator/)
- [Пресеты стратегий](../Strategy/presets/)
