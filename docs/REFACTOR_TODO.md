# Backend Refactor — TODO

Ngày lập: 2026-09-09. Mục tiêu: (a) nhấc hạ tầng thuần từ `backend/server/app` lên
`backend/packages/svc_core` (`dqh.svc_core`), (b) chuẩn hoá module contract của
server, (c) áp rule code-style mới.

## Trạng thái (branch `refactor/svc-core-extract-1`)

| Commit | Nội dung |
|---|---|
| server `8dab862` + svc_core `509663d` | PR1 — EventBus + StrEnum + configure_logging (1.1/1.2/1.6) |
| server `47249b8` | PR2.1 — ModuleRegistry auto-discovery + observability subscribers wired |
| server `9d62577` + svc_core `cac594a` | PR1.3 — RedisPubSubMessageBus → svc_core `[redis]` |
| server `0977400` + svc_core `b48bed4` | PR1.4 — persistence: Base/EngineFactory/BaseRepository/TimestampMixin/DbEnum → svc_core `[sqlalchemy]` |
| server `ad68dd5` + svc_core `566cc78` | PR1.5 — auth split: PasswordHasher/TokenCodec → svc_core `[security]`; app `bearer_auth.py` |

**PHẦN 1 (extract → svc_core) + 1.7 (pyproject) + 2.1 (subscribers): XONG.**
svc_core 0.1.0 → 0.5.0, 41 test pass. server: 24 pass / 3 fail.

**3 test đỏ CÒN LẠI = bug có sẵn trong WIP chưa commit, KHÔNG do refactor:**
- `test_edge_gateway::test_violation_over_bus_records_and_alerts` — violation
  không được route qua bus (edge_protocol/gateway WIP đang dở)
- `test_api_smoke::test_violation_flow_creates_alert_and_shows_in_analytics` — cùng gốc
- `test_ws_alerts::test_alert_raised_is_pushed_over_websocket` — WS đóng khi connect
  (ws-auth trong `observability/router.py` WIP)
Đã xác minh: revert sạch mọi thay đổi refactor → vẫn đúng 3 test này đỏ.

**Còn lại:** PHẦN 2 (module contract: rename domain.py→rules.py, khuôn đồng nhất),
PHẦN 3 (xẻ edge gateway), PHẦN 4 (import-linter + workspace).

---

## Rule code-style (áp cho MỌI code mới + code động vào khi refactor)

- **Ưu tiên class hoá.** Logic có state / lifecycle / nhiều method liên quan → bọc
  trong class. Không để hàm rời rạc ở module level.
- **1 file `.py` = 1 việc.** Mỗi file một class (hoặc một khái niệm) duy nhất; tên
  file = tên thứ nó chứa (`event_bus.py` → `class EventBus`). Cấm `utils.py` /
  `helpers.py` gom nhiều thứ.
- **Ngoại lệ cho pure helper:** hàm stateless cực nhỏ (1–3 dòng, không I/O) được
  phép để là hàm — nhưng vẫn ở file riêng đặt theo tên hàm (`average.py`).
- **Wiring / singleton:** package chỉ export class. App tạo *một* instance dùng
  chung trong đúng một file `app/core/<name>.py` (thay cho global kiểu
  `event_bus = EventBus()` nằm lẫn trong file định nghĩa).
- **Không raise lỗi HTTP/framework từ lớp lõi.** `svc_core` raise exception của
  riêng nó; adapter (FastAPI) mới dịch sang `HTTPException`.

---

## PHẦN 1 — Tách lên `svc_core`

### 1.1 `dqh.svc_core.events` — domain event bus  ·  rủi ro: 0  ·  ✅ DONE (svc_core 509663d)
- [x] `events/__init__.py` + `events/event_bus.py` — `class EventBus` (subscribe/publish/clear), chỉ stdlib
- [x] `svc_core/tests/test_events_bus.py` (3 test, pass)
- [x] App: `app/core/events.py` chỉ còn import `EventBus` + tạo `event_bus` instance
- [x] bump `dqh-svc-core` 0.1.0 → 0.2.0; `pytest`: svc_core 31 pass, server 25 pass
      (4 fail có SẴN trên working tree trước khi refactor — telemetry_relay WIP gọi
      `ws_hub.publish` khi bus chưa connect + observability subscribers chưa được
      wire; xem PHẦN 2.1. Không phải regression của PR này.)

### 1.2 Dedupe helpers  ·  rủi ro: 0  ·  ✅ DONE (svc_core 509663d)
- [x] `svc_core/helpers/str_enum.py` — `class StrEnum`; export ở `helpers/__init__.py`
- [x] `utcnow`: dùng `dqh.svc_core.helpers.time.utcnow` sẵn có (giữ là hàm — pure,
      1 dòng; `Clock` class hoãn, không đáng churn `PresenceRegistry(clock=...)`)
- [x] App: xoá `app/shared/helpers/{time,enums}.py`, repoint import (4×domain.py,
      3×service.py, presence/registry.py, telemetry_relay.py)
- [x] `average_or_none` → `app/shared/stats/average.py`; xoá `app/shared/helpers/stats.py`

### 1.6 `configure_logging` → svc_core  ·  ✅ DONE (svc_core 509663d)
- [x] `svc_core/middleware/logging.py` thêm `configure_logging(level)` idempotent
- [x] App: xoá `app/core/logging.py`, `main.py` import từ `dqh.svc_core.middleware.logging`

### 1.3 `dqh.svc_core.transports.event_driven.redis`  ·  rủi ro: thấp
- [ ] Thêm extra `redis = ["redis>=5.0"]` vào `svc_core/pyproject.toml`
- [ ] `transports/event_driven/redis.py` — chuyển `class RedisPubSubMessageBus`
      từ `app/core/messaging/redis_bus.py` (đã implement đúng `MessageBus` port)
- [ ] `svc_core/tests/test_messaging_redis.py` (khuôn theo `test_messaging_inmemory.py`,
      dùng `fakeredis`)
- [ ] App: xoá `app/core/messaging/redis_bus.py`; `build_realtime_bus` import từ
      `dqh.svc_core.transports.event_driven.redis`
- [ ] `RealtimeBusFactory` — class hoá `build_realtime_bus` trong
      `app/core/messaging/realtime_bus_factory.py` (memory ↔ redis selector).
      `app/core/messaging/__init__.py` chỉ re-export.

### 1.4 `dqh.svc_core.persistence.sqlalchemy` (extra `[sqlalchemy]`)  ·  rủi ro: trung bình
- [ ] Thêm extra `sqlalchemy = ["sqlalchemy[asyncio]>=2.0"]`
- [ ] `persistence/sqlalchemy/base.py` — `class Base(DeclarativeBase)`
- [ ] `persistence/sqlalchemy/engine_factory.py` — `class EngineFactory`:
      `__init__(cfg: DatabaseConfig)`, `.create() -> AsyncEngine`
- [ ] `persistence/sqlalchemy/session_provider.py` — `class SessionProvider`:
      giữ `async_sessionmaker`; `.scope()` (contextmanager cho worker/handler),
      `.dependency()` (FastAPI `get_db`). Đọc factory tại call-time để test swap được.
- [ ] `persistence/sqlalchemy/repository.py` — `class BaseRepository` từ
      `app/shared/repository.py`
- [ ] `persistence/sqlalchemy/timestamp_mixin.py` — `class TimestampMixin` từ
      `app/shared/models.py`
- [ ] `persistence/sqlalchemy/db_enum.py` — `class DbEnum` (callable) thay hàm
      `db_enum()` từ `app/shared/helpers/database.py`
- [ ] `svc_core/tests/test_persistence_*.py` (dùng `aiosqlite`)
- [ ] App: `app/core/database.py` teo còn: khởi tạo `EngineFactory` + `SessionProvider`
      từ `settings.db`, export `engine` / `async_session` / `session_scope` / `get_db`,
      giữ `init_db()` (vì phải `import app.modules` để nạp metadata) và `Base`
      (re-export từ svc_core)
- [ ] App: xoá `app/shared/repository.py`, `app/shared/models.py`,
      `app/shared/helpers/database.py`; sửa import toàn repo

### 1.5 `dqh.svc_core.security` (extra `[security]`)  ·  rủi ro: trung bình
- [ ] Thêm extra `security = ["argon2-cffi>=23.1", "PyJWT>=2.9"]`
- [ ] `security/password_hasher.py` — `class PasswordHasher` (wrap argon2:
      `.hash()`, `.verify()` nuốt lỗi argon2 → bool)
- [ ] `security/token_codec.py` — `class TokenCodec(secret, algorithm)`:
      `.encode(subject, token_type, ttl) -> (str, datetime)`,
      `.decode(token, expected_type) -> int`. Raise `TokenError` (class riêng
      trong `security/errors.py`), KHÔNG `HTTPException`.
- [ ] `security/errors.py` — `class TokenError(Exception)`
- [ ] `svc_core/tests/test_security_*.py`
- [ ] App: `app/core/token_codec.py` — instance `TokenCodec` từ settings
- [ ] App: `app/core/password_hasher.py` — instance `PasswordHasher`
- [ ] App: `app/core/bearer_auth.py` — `class BearerAuth`: nhận `TokenCodec` +
      session provider qua `__init__`; method `.current_user()` và
      `.require_permission(code)` trả FastAPI dependency. Gom `get_current_user`,
      `require_permission`, `permission_codes` hiện rời trong `app/core/auth.py`.
- [ ] App: xoá `app/core/auth.py`; sửa import (`CurrentUser`, `require_permission`,
      `hash_password`, `verify_password`, `issue_tokens`, `decode_token`)

### 1.7 Dọn `pyproject` sau khi tách
- [ ] `backend/server/pyproject.toml`:
      `dqh-svc-core[fastapi,mqtt]` → `[fastapi,mqtt,sqlalchemy,security,redis]`
- [ ] Bỏ khỏi deps trực tiếp của server: `sqlalchemy`, `asyncpg` (giữ! asyncpg là
      driver, không nằm trong extra), `argon2-cffi`, `PyJWT`, `redis`
      → thực tế: bỏ `sqlalchemy`, `argon2-cffi`, `PyJWT`, `redis`; **giữ** `asyncpg`
- [ ] `uv.lock` cập nhật, CI xanh

### KHÔNG tách (ghi lại để khỏi bàn lại)
- `app/shared/helpers/protocol.py::device_id_from_envelope` — biết "source = int
  device id", là nghiệp vụ edge. Giữ ở app hoặc chuyển vào `edge_protocol`.
- `app/domain/presence`, `app/domain/reconcile` — thuật toán generic nhưng là
  nghiệp vụ điều phối. Chỉ tách thành package RIÊNG (`dqh-reconcile`) nếu có
  service thứ 2 dùng. Không nhồi vào `svc_core`.
- `app/modules/*`, `app/edge/*`.

---

## PHẦN 2 — Chuẩn hoá module contract (server)

Khuôn cố định cho mỗi `app/modules/<context>/` (bỏ file không cần, không để rỗng):

```
__init__.py       # bề mặt công khai DUY NHẤT: export Service + event types
router.py         # class ...Router hoặc APIRouter; chỉ gọi service
service.py        # class ...Service — transaction boundary
repository.py     # class ...Repository — mọi query
models.py         # ORM (nhiều class = nhiều file nếu phình: models/<entity>.py)
schemas.py        # Pydantic I/O
rules.py          # (đổi tên từ domain.py) logic thuần, không I/O
events.py         # dataclass event module PHÁT ra
subscribers.py    # (gộp handlers/integration/realtime) class ...Subscribers
```

- [ ] Đổi tên `domain.py` → `rules.py` ở: agent, deployment, model_registry, observability
- [ ] Gộp `handlers.py` / `integration.py` / `realtime.py` → `subscribers.py`
      (một `class <Context>Subscribers` với method `register(bus)`):
  - [ ] agent: `handlers.py` + `telemetry_relay.py` → `subscribers.py`
  - [ ] observability: `integration.py` + `realtime.py` → `subscribers.py`
- [ ] `access_control`: chỉ có `models.py` — hoặc nâng thành module đủ, hoặc
      nhập models vào `user` rồi xoá thư mục
- [ ] `auth`: thêm `service.py` (`class AuthService`) — hiện logic login nằm rải ở
      router
- [ ] camera / system / user / streaming: bổ sung `repository.py` (`class ...Repository`)
      cho đồng nhất, kể cả khi chỉ 1–2 query

### 2.1 Auto-discovery (bỏ liệt kê tay)
- [ ] `app/modules/__init__.py`: `class ModuleRegistry`
  - [ ] `.load_models()` — duyệt `pkgutil.iter_modules`, import `<mod>.models`
  - [ ] `.register_subscribers(bus)` — duyệt, gọi `<mod>.subscribers.*.register()`
  - [ ] Bỏ list `import ... as _x_models` và thân `register_event_handlers()` cũ
- [ ] **VERIFY TRƯỚC KHI SỬA:** `observability/integration.py::register()` và
      `observability/realtime.py::register()` hiện KHÔNG được gọi ở đâu
      (`register_event_handlers` chỉ gọi agent). Xác nhận đây là bug → alert
      device-offline / latency-degraded / deployment-failed và WS alert fan-out
      đang chết. Fix bằng auto-discovery ở trên.

### 2.2 API router
- [ ] `app/api/router.py` → `class ApiRouter` build từ list module router
      (hoặc auto-discover `<mod>.router:router`)

---

## PHẦN 3 — Slim edge gateway (server)

`app/edge/gateway.py` (267 dòng, fan-in 6 module qua import sâu) tách ra:

```
app/edge/
  edge_plane.py            # class EdgePlane (đổi từ runtime.py) — bus lifecycle
  bus_factory.py           # class BusFactory (đổi từ build_bus)
  gateway.py               # class AgentGateway — chỉ wiring route→handler (~60 dòng)
  inbound/
    heartbeat_handler.py   # class HeartbeatHandler — chỉ dùng app.modules.agent (public)
    telemetry_handler.py   # class TelemetryHandler
    violation_handler.py   # class ViolationHandler — app.modules.observability
    bbox_handler.py        # class BboxHandler — app.core.ws
    log_handler.py         # class LogHandler
    stream_token_handler.py# class StreamTokenHandler — app.modules.streaming
  outbound/
    deployment_dispatcher.py # class DeploymentDispatcher — nghe DeploymentActivated
```

- [ ] Mỗi handler là 1 class, `__init__` nhận dependency (session provider,
      service, ws hub) — không import sâu module khác
- [ ] Handler chỉ import `app.modules.<ctx>` (bề mặt công khai), không `.service` / `.schemas`
- [ ] `gateway.py` chỉ map `protocol.T_* → handler.handle` và quản sub lifecycle
- [ ] Cập nhật `tests/test_edge_gateway.py`

---

## PHẦN 4 — Ranh giới & workspace

- [ ] Dời `app/domain/` vào module:
  - [ ] `domain/presence/` → `app/modules/agent/presence_registry.py` (`class PresenceRegistry`)
  - [ ] `domain/reconcile/` → `app/modules/deployment/reconciler.py` (`class Reconciler`)
  - [ ] Xoá thư mục `app/domain/`
- [ ] Thêm `import-linter` vào CI:
  - [ ] contract: `app.modules.*` chỉ import nhau qua `app.modules.<ctx>` (cấm `.service` v.v.)
  - [ ] contract: `svc_core` / `edge_protocol` không import `app.*`
- [ ] Root `pyproject.toml`: thêm `[tool.uv.workspace]` members =
      server, edge_agent, libs/*, packages/*  → một `uv sync` build hết
- [ ] Cập nhật `docs/ARCHITECTURE.md` sau khi PHẦN 1–3 xong

---

## Thứ tự thực thi (mỗi mục = 1 PR, chạy full `pytest` svc_core + server)

1. 1.1 events + 1.2 helpers + 1.6 logging   (gộp, rủi ro 0)
2. 1.3 redis transport
3. 1.4 persistence
4. 1.5 security
5. 1.7 dọn pyproject
6. 2.x module contract + auto-discovery (kèm verify bug subscribers)
7. 3 edge gateway
8. 4 ranh giới + workspace
