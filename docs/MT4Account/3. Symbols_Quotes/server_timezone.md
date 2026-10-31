# Server Timezone

> The trade server's timezone / UTC offset — align timestamps and sessions to broker time.

**API Information:**

* **Low-level API:** `MT4Account.server_timezone(...)` (defined in `package/MetaRpcMT4/mt4_account.py`)
* **gRPC service:** `mt4_term_api.ServerTimezone`
* **RPC:** `ServerTimezone(ServerTimezoneRequest) -> ServerTimezoneReply`
* **Payload:** `ServerTimezoneData`

## 💬 Just the essentials

* **What it is.** The broker server's UTC offset (and a label/source for it).
* **Why you need it.** Server timestamps are in broker time; this lets you convert to/from UTC and reason about trading sessions.
* **When to use.** When displaying times, scheduling around sessions, or comparing server time to UTC.

---

## 🎯 Purpose

* Server UTC offset (seconds)
* Server/timezone label
* Source and validation info for the offset

---

## Method Signature

```python
async def server_timezone(
    self,
    deadline: Optional[datetime] = None,
    cancellation_event: Optional[asyncio.Event] = None,
)
```

**Request message:**

```protobuf
message ServerTimezoneRequest {
}
```

**Payload message:**

```protobuf
message ServerTimezoneData {
  string server = 1;             // server / timezone label
  int32 utc_offset_seconds = 2;  // offset from UTC, in seconds
  string source = 3;             // how the offset was determined
  string validated_utc = 4;      // validation reference
}
```

---

## 🔽 Input

| Parameter | Type | Description |
|-----------|------|-------------|
| `deadline` | datetime, optional | Absolute UTC deadline for the gRPC call. |
| `cancellation_event` | asyncio.Event, optional | Set to abort the request. |

---

## ⬆️ Output — `ServerTimezoneData`

| Field | Python Type | Description |
|-------|-------------|-------------|
| `server` | `str` | Server / timezone label |
| `utc_offset_seconds` | `int` | Offset from UTC, in seconds (e.g. 3600 = UTC+1) |
| `source` | `str` | How the offset was determined |
| `validated_utc` | `str` | Validation reference |

---

## 🧩 Notes & Tips

* **Offset is in seconds.** Divide by 3600 for hours (e.g. `3600 → UTC+1`, `10800 → UTC+3`).
* **Server time vs UTC.** `account_summary` returns both `server_time` and `server_time_utc`; this call gives you the offset to convert any server timestamp yourself.
* **DST.** Many FX servers shift with daylight saving — read this at session start rather than hard-coding an offset.
* **Rarely changes within a session** — fetch once and cache; refresh daily or on reconnect.

---

## 🔗 Usage Examples

### 1) Print the server offset

```python
async def show_timezone(account):
    tz = await account.server_timezone()
    hours = tz.utc_offset_seconds / 3600
    print(f"{tz.server}: UTC{hours:+.0f} ({tz.utc_offset_seconds}s)  source={tz.source}")
    return tz
```

### 2) Convert server time ↔ UTC

Use the offset to turn a server timestamp into UTC (and back).

```python
from datetime import timedelta

async def server_to_utc(account, server_dt):
    tz = await account.server_timezone()
    return server_dt - timedelta(seconds=tz.utc_offset_seconds)

async def utc_to_server(account, utc_dt):
    tz = await account.server_timezone()
    return utc_dt + timedelta(seconds=tz.utc_offset_seconds)
```

### 3) Is it the weekend (server time)?

Gate trading around the broker's week using server-local time.

```python
from datetime import datetime, timedelta

async def is_weekend_server(account) -> bool:
    tz = await account.server_timezone()
    server_now = datetime.utcnow() + timedelta(seconds=tz.utc_offset_seconds)
    return server_now.weekday() >= 5   # Sat/Sun in server time
```

---

## ⚠️ Pitfalls

* **Seconds, not hours.** `utc_offset_seconds` is seconds — convert before formatting.
* **DST drift.** Don't cache the offset across days; brokers shift with daylight saving.
* **Session math.** Trading sessions and rollover are defined in server time — convert before comparing to UTC schedules.

---

## 🧪 Testing Suggestions

* **Happy path.** `utc_offset_seconds` is a plausible value (typically a multiple of 1800) and `server` is non-empty.
* **Consistency.** `account_summary().server_time` minus `server_time_utc` roughly equals `utc_offset_seconds`.
* **Conversion round-trip.** `utc_to_server(server_to_utc(dt))` returns the original datetime.

---

## 📚 See also

* [Account Summary](../1. Account_Information/account_summary.md)
* [Quote History (OHLC)](quote_history.md)
* [Symbols](symbols.md)

* **Back to:** [Symbols & Quotes — Overview](Symbols_Quotes.Overview.md) · [MT4Account — Master Overview](../MT4Account.Master.Overview.md)
