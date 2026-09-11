# Refactor — server "stateless" cho fleet & model

Ngày lập: 2026-09-09. Nối tiếp [`REFACTOR_TODO.md`](REFACTOR_TODO.md) (đã xong
phần svc_core extract) và [model deploy = image](../deploy/compose.edge.yml).

## Tiến độ (2026-09-09)

| | commit | |
|---|---|---|
| ✅ | `01957e8` | S0 — 1 multi-arch Dockerfile, `_resolve_device` |
| ✅ | `c950797` | bỏ artifact_uri/S3 path |
| ✅ | `56a328a`+`393a2af` | S2 — `ModelCatalog` đọc GHCR; xoá ORM `models`/`model_versions`; deploy theo `image` |
| ✅ | `a984068` | `ModelCatalog` dùng `svc_core.HttpClient` (svc_core 0.8.0) |
| ✅ | `3b2c37d` | S1/S3.1 — `DEVICE_ID` string PK khắp nơi |
| ✅ | `add9d86` | S3.2+S4 — `Device` = desired config; `FleetRegistry` in-memory; bỏ `PresenceRegistry` |
| ✅ | `293481c` | S5 — deploy = command; xoá ORM `Deployment`; `GET /deployments` = per-device view |
| ✅ | `0ca775b` | S3.3 (một phần) — `ConfigResolver` (model labels < policy < device) + `T_UPDATE_CONFIG` |
| ✅ | `847244c` | S6 — metrics = ring buffer in-memory; xoá `metric_samples` |
| ✅ | (S7) | `schema.sql` regen; dọn `ARCHITECTURE.md` + flow |

**Còn lại:**
- **camera-fold huỷ** (user): giữ `cameras`/`camera_groups` tables. Chỉ còn
  FE "Fleet defaults" page.
- MQTT retained `state` publish (cần `svc_core` MessageBus `publish(retain=)`);
  LWT set được ngay qua `MQTT__WILL_*`.
- Prometheus remote-write (S6 nâng cấp).
- `edge_agent` chưa string-hoá hết đâu? (đã dùng string sẵn, ok).

## Mục tiêu

Server **không persist thứ gì có thể dựng lại được**:

- **Model catalog** → đọc thẳng từ OCI registry (tags + image labels).
- **Fleet state** (device nào sống, đang chạy image gì, health) → dựng lại từ
  MQTT retained `state` + heartbeat mỗi lần server khởi động.
- **Metrics history** → đẩy ra Prometheus/Timescale, không giữ trong Postgres.

Postgres chỉ còn giữ thứ **không suy ra được**: bằng chứng vi phạm, người dùng,
audit log, và **desired config** của mỗi device (operator gõ từ dashboard).

## Nguyên tắc — 3 tầng state

| Tầng | Ví dụ | Nguồn sự thật | Server restart |
|---|---|---|---|
| **Bootstrap** (tĩnh, trên box) | `DEVICE_ID`, `MQTT__HOST/PORT/TLS`, certs | `deploy/.env.edge` (~5 dòng) | n/a |
| **Desired** (động, operator sửa) | cameras, model, threshold, log level | Postgres `device_config`, key = `device_id` | load lại từ DB |
| **Reported / live** (device báo) | caps, active image, runtime_status, health | MQTT retained `state` + heartbeat | re-subscribe, vài giây là đủ |

Reconcile: `desired` (server) ⇄ `reported` (device) — agent đã có sẵn máy
(`services/agent.py`, `core/state.py`, `reconcile_interval_s`).

---

## Kiến trúc đích

### `ModelCatalog` — thay `models` + `model_versions`

- `app/modules/model_registry/catalog.py` — `class ModelCatalog`.
- Registry = **GHCR**, package **public** → toàn bộ dùng **Registry v2 API vô danh**:
  - token vô danh: `GET https://ghcr.io/token?scope=repository:{owner}/{pkg}:pull`
  - tags: `GET https://ghcr.io/v2/{owner}/{pkg}/tags/list`
  - labels: `GET .../manifests/{tag}` → manifest list → config blob →
    `GET .../blobs/{digest}` → `.config.Labels` + `.created`
  - Config: `MODEL_REGISTRY__{OWNER,PACKAGE}`; `MODEL_REGISTRY__TOKEN` **optional**
    — chỉ khi package private hoặc cần nới rate limit.
  - (Build image + set public = pipeline model riêng, không thuộc app.)
- Metadata nướng vào **image labels** lúc build model image (pipeline riêng):
  `org.opencontainers.image.{version,created,revision}` +
  `ai.edge-ops.model.{task,classes,map50_95,params_m,latency_ms,base}`.
- Cache TTL ~30s; `GET /models?refresh=1` để ép làm mới.
- **1 multi-arch manifest** (đã chốt): `linux/amd64` + `linux/arm64` (Jetson)
  trong cùng 1 tag. Docker trên device tự kéo đúng arch. GPU-vs-CPU **không**
  do manifest chọn — runtime tự dò `torch.cuda.is_available()` và fallback CPU.
  → `ModelVersion.image_{cpu,gpu}_digest` gộp thành **1** `image` (ref pin digest
  manifest-list). `DeployModelPayload` chỉ còn 1 `image`; server **không** chọn
  variant theo `capabilities.backend` nữa (`backend` vẫn dùng cho
  `composed` vs `deepstream` runtime).

### `FleetRegistry` — thay `devices` (runtime) + `deployments` (current)

- `app/modules/fleet/registry.py` — `class FleetRegistry` (in-memory, 1 instance
  ở `app/core/`).
- Subscribe `agent/devices/+/state` (**retained**, QoS 1) + LWT.
- `{device_id: DeviceState}` với `DeviceState = caps + last_heartbeat +
  reported_image + reported_cameras + reported_config + online`.
- Không có DB. Restart → nhận lại toàn bộ retained `state`.
- `evaluate_status()` (đã có) tính online/stale/offline từ `last_seen` + LWT.
  Bỏ `PresenceRegistry` (xem "Còn mở" trong REFACTOR_TODO — nay chốt: bỏ).

### `device_config` — desired state (Postgres, bảng mới)

```
device_config
  device_id        TEXT PRIMARY KEY        -- = DEVICE_ID trên box
  display_name     TEXT
  site             TEXT
  labels           JSONB
  desired_image    TEXT NULL               -- model ref, hoặc null
  cameras          JSONB                   -- [{id, source, zone, roi, fps_limit, enabled, overrides}]
  inference        JSONB                   -- override thưa: {conf_threshold?, iou?, ...} — null field = kế thừa
  agent            JSONB                   -- override thưa: {telemetry_interval_s?, log_level?, ...}
  created_at, updated_at, updated_by
```

Gộp `cameras` + `camera_groups` cũ vào đây. Bảng *config*, ít ghi.

### Config phân tầng (thresholds, inference, agent...)

Không cấu hình toàn cục HAY theo device — **cả hai, dạng phân tầng**. Dưới đè lên trên:

```
1. Model defaults   ← image labels  ai.edge-ops.model.{conf,iou,imgsz,classes}   (pipeline model nướng vào)
2. Global policy     ← app_settings  khối "inference_policy" (cái gì tính vi phạm,
                       ngưỡng alert, dedup window, evidence retention, severity map)
3. Per-device        ← device_config.inference / .agent   (field null = kế thừa)
4. Per-camera        ← device_config.cameras[].overrides   (source, zone, roi, ngưỡng góc khó)
```

- Server tính `effective = merge(1..4)` → gửi **giá trị đã resolve** trong
  `DeployModelPayload.config` / `UpdateConfigPayload`. **Agent không merge** — chỉ
  nhận dict cuối.
- Global block: thêm `GET/PATCH /system/settings` khối `inference_policy` (dùng
  `app_settings` sẵn có).
- UI: trang **"Fleet defaults"** + panel override per-device/-camera hiện
  `0.45 (kế thừa)` vs `0.6 (override)`.

| Tầng | Ví dụ | Vì sao ở đây |
|---|---|---|
| Global | "helmet + vest tính vi phạm", ngưỡng confidence để alert, dedup 30s | nhất quán toàn đội |
| Per-model | conf/iou tối ưu, imgsz, class list | thuộc tính model |
| Per-device | `fps_limit`, `log_level` (debug 1 box), telemetry interval | phụ thuộc phần cứng / vận hành |
| Per-camera | source, zone, ROI, ngưỡng riêng góc ngược sáng | mỗi camera 1 hiện trường |

### Deploy = bắn command, không ghi row

- `POST /deployments {device_id, image}` → set `device_config.desired_image` +
  publish `T_DEPLOY_MODEL` → trả về ngay.
- Tiến trình: browser theo dõi stream `ack` + `state` qua WS.
- Sự thật cuối: `reported_image` trong FleetRegistry.
- Lịch sử "ai deploy cái gì lúc nào" → `audit_logs` (không phải bảng riêng).

### Fleet view = union 2 nguồn

- **Known**: có `device_config` (operator đã thêm) — hiện cả khi offline.
- **Online**: đang publish retained `state`.
- Device lạ báo `state` mà chưa có `device_config` → auto tạo row rỗng
  (`display_name = device_id`), operator điền camera/model sau.

---

## DB đích

| Giữ | Bỏ |
|---|---|
| `device_config` (mới) | `devices`, `metric_samples` |
| `violations`, `snapshots` | `models`, `model_versions` |
| `alerts` | `deployments` |
| `users`, `roles`, `permissions`, `user_roles`, `role_permissions` | `cameras`, `camera_groups` |
| `audit_logs` | `chat_messages` |
| `app_settings` | |

`init_db()` giữ nguyên (bảng ít + ổn định, chưa cần Alembic).
`schema.sql` viết lại cho khớp.

---

## Thay đổi contract

### edge_protocol

- `StateReportPayload`: bỏ `active_model_version_id` / `deployment_id`; thêm
  `reported_image: str | None`, `cameras: list[IpcCameraSpec]`,
  `config: dict`, `runtime_status`, `detail`. **Publish retained.**
- `DeployModelPayload`: bỏ `deployment_id` + `model_version_id`; giữ
  `command_id`, `image`, `config`.
- `HeartbeatPayload.active_model_version_id` → `active_image: str | None`.
- `DeviceCapabilities`: thêm `name`, `site`, `labels` (agent đọc từ `.env.edge`
  — hoặc để trống, operator đặt trong `device_config`).

### MQTT

- Agent: `state` publish `retain=True, qos=1`; set LWT
  `agent/devices/{id}/state` = `{"online": false}` retained.
- Server: subscribe `agent/devices/+/state` nhận retained lúc connect.
- EMQX: `emqx_data` volume đã bền — retained store sống qua restart. ✓

### DEVICE_ID = string, khóa chính ở mọi nơi

- Bỏ `Device.id` (int). `device_id` (string, vd `plant-a-cam-01`) xuyên suốt
  protocol / API / `device_config` / `violations.device_id`.
- Sửa `device_id_from_envelope()` — trả string, bỏ `int(...)`.
- Fix bug hiện tại (agent gửi `edge-dev-1`, server ép int) luôn ở đây.

### API — giữ shape response, đổi backing

| Endpoint | Trước | Sau |
|---|---|---|
| `GET /models` | query `models` table | `ModelCatalog.list()` |
| `GET /models/{ref}` | DB | catalog + labels |
| `POST /models` | tạo row | **bỏ** (model do CI push, không tạo từ UI) |
| `GET /agent/devices` | `devices` table | union `device_config` + `FleetRegistry` |
| `POST /agent/devices` | tạo Device | tạo `device_config` (provision) |
| `PATCH /agent/devices/{id}` | update Device | update `device_config` + push delta |
| `GET /agent/cameras` | `cameras` table | flatten từ `device_config.cameras` |
| `POST/PATCH /agent/cameras` | CRUD | sửa `device_config.cameras` + push |
| `GET/POST /deployments` | `deployments` table | set `desired_image` + publish cmd |
| `GET /agent/devices/{id}/metrics` | `metric_samples` | proxy Prometheus, hoặc 501 (xem PR-S6) |
| `/violations` `/users` `/system/*` | — | **không đổi** |

### Frontend

**Types (`ui/src/shared/api/types/`):**

| Type | Đổi |
|---|---|
| `ai.ts` `ModelRecord.id` | `number` → `string` (image ref, vd `ghcr.io/.../ppe:1.3.0`) |
| `ai.ts` `ModelVersionRecord` / `ModelWithVersionsRecord` | reshape: 1 model = repo, versions = tags; field từ image labels (`map50_95`, `classes`, `params_m`, `latency_ms`, `digest`, `pushed_at`) |
| `ai.ts` `DeploymentRecord` | `device_id: number → string`; `model_version_id → image: string`; bỏ `progressPct` (tiến trình = WS stream) |
| `agent.ts` `BackendDevice` | `id: number → string`; `active_model_version_id → active_image: string \| null`; thêm `desired_image`, `known: boolean`, `cameras`, `config` |
| `agent.ts` `BackendMetricSample` | giữ shape cho Prometheus proxy, hoặc bỏ tới S6 |
| `agent.ts` `BackendCamera` | `id: number → string`; thêm `device_id: string`, `fps_limit` |
| `agent.ts` `CreateDevicePayload` | thêm `device_id: string` (operator gõ, = `DEVICE_ID` trên box) |

**Services (`shared/api/services/{ai,agent}.ts`):**
- `/models/${id}` → `/models/${encodeURIComponent(ref)}`; bỏ `post('/models')`.
- `/deployments` body → `{ device_id: string, image: string }`.
- `/agent/cameras` → không CRUD rời; sửa qua `PATCH /agent/devices/{id}`.

**Pages:**
- `ai/pages/ModelsPage.tsx` — list từ registry catalog; **bỏ form "register
  model"**; hiện labels (mAP, classes, digest, pushed-at).
- `ai/pages/DeploymentsPage.tsx` — deploy = chọn device(s) + image tag; tiến
  trình đọc từ WS (`ack` + `state` frames), không phải `progressPct` từ DB.
- `agent/pages/{EdgeDevicesPage,DevicesPage}.tsx` — device = merge
  `device_config` (known) + `FleetRegistry` (online); "add device" = provision
  `device_config` với `device_id`; hiện **drift** desired vs reported.
- `agent/pages/{Cameras,CamerasPage}.tsx` — camera nằm *trong* 1 device
  (`device_config.cameras`), sửa inline; `CameraGroupsPage` → client-only hoặc bỏ.
- `overview/pages/{LiveMonitor,AnalyticsPage}.tsx` +
  `agent/components/LiveMonitorPanel.tsx` — chart live qua WS ring buffer;
  history qua Prometheus proxy (ẩn tới S6).

---

## Kế hoạch PR

| PR | Backend / protocol | Frontend | Rủi ro |
|---|---|---|---|
| **S0** ✅ | `inference`: gộp `Dockerfile.cpu`+`.gpu` → **1** `Dockerfile` (multi-arch, `_resolve_device` dò CUDA/MPS/CPU) + `Dockerfile.jetson` (future). Dockerfile mang **contract labels** `ai.edge-ops.model.*`. `.env.app` thêm `MODEL_REGISTRY__*`. **Build model→image KHÔNG nằm trong app** — pipeline riêng dùng Dockerfile này làm contract. Còn lại: tạo GHCR PAT `read:packages` → secret | — | 0 |
| **S1** | `DEVICE_ID` string: `edge_protocol` payloads + `device_id_from_envelope` (bỏ `int()`) + `violations.device_id` TEXT; sửa test | `BackendDevice.id`, `DeploymentRecord.device_id`, `BackendCamera` id → `string`; `CreateDevicePayload.device_id` | tb — đụng nhiều chỗ, cơ học |
| **S2** | `ModelCatalog` (GHCR API) + `Settings.model_registry`; `GET /models*` đổi backing; bỏ `POST /models`; xoá `models`/`model_versions` ORM + repo + `ModelRegistryService` | `types/ai.ts` reshape (`ModelRecord.id: string`, versions=tags, fields từ labels); `ModelsPage` bỏ form register, hiện labels | tb |
| **S3** | Bảng `device_config` + service; `POST/PATCH /agent/devices` + `/agent/cameras` map sang đó; khối `inference_policy` global (`/system/settings`) + `ConfigResolver.merge(model, global, device, camera)`; seed migrate | `EdgeDevicesPage`/`DevicesPage` provision bằng `device_id`; `Cameras*` sửa inline; trang **Fleet defaults** + panel override (kế thừa vs override); `CameraGroupsPage` client-only/bỏ | tb |
| **S4** | `FleetRegistry` in-memory; agent `state` retained+LWT (`network/link.py`); `GET /agent/devices` = union known+online; bỏ `PresenceRegistry` | device list = merge known+online; hiện **drift** desired vs reported; WS live update | **cao** — đường sống fleet |
| **S5** | `/deployments` = set `desired_image` + publish `T_DEPLOY_MODEL`; xoá `deployments` ORM; history → `audit_logs` | `DeploymentsPage`: chọn device(s)+image tag; tiến trình từ WS (`ack`+`state`), bỏ `progressPct` | tb |
| **S6** | Prometheus service vào `compose.infra.yml`; agent expose `/metrics` (scrape); `GET .../metrics` proxy Prometheus hoặc 501; xoá `metric_samples` | chart live qua WS ring buffer; history qua proxy | thấp (phụ) |
| **S7** | Xoá `chat_messages` nếu không dùng; viết lại `schema.sql`; dọn `docs/ARCHITECTURE.md` + flows | dọn type/service chết | 0 |

Mỗi PR: BE + FE + test xanh cùng nhau trước khi qua PR sau. S6/S7 độc lập.

**Thứ tự thực tế (đổi so với đánh số):**
`artifact_uri/S3 cleanup` (xong, `refactor(server): drop the legacy artifact_uri`)
→ **S2** (ModelCatalog — tự chứa nhất, đúng thứ user cần) → **S3** → **S4**.
**S1 (`device_id` string) gộp vào S3+S4**: `device_id: int` xuyên suốt ~50 chỗ ở
agent/camera/deployment/observability; `devices`/`deployments`/`cameras` bị xoá ở
S3/S4 nên migrate FK riêng ở S1 là phí. Khi `devices` → `device_config` +
`FleetRegistry` (S3/S4), khoá là string ngay từ đầu — không cần cầu int↔str.
`violations.device_id` → TEXT làm ở S4 cùng lúc.

---

## KHÔNG làm

- **Alembic** — schema nhỏ đi, `init_db()` đủ.
- **Bỏ Postgres hoàn toàn** — violations + users cần nó (đã chốt).
- **Camera config trên `.env.edge`** — operator sửa từ dashboard, server push
  (đã chốt: "server push, giữ config nhỏ").
- **Sửa máy reconcile của agent** — đã đủ, chỉ đổi payload.
- **Giữ bảng `deployments` cho history** — dùng `audit_logs`.
- **Build model → image trong app CI** — đó là việc của pipeline model (repo/
  quy trình riêng). App chỉ giữ `inference/Dockerfile` làm *contract*
  (code vision_runtime + label schema) và *consume* image từ registry.

## Đã chốt (2026-09-09)

- Violations/snapshots → **Postgres nhỏ**.
- Users/auth → **Postgres nhỏ** (không `users.yaml`).
- Camera config → **server push, giữ config nhỏ** (`device_config.cameras`).
- Metrics history → **sink Prometheus**, server vẫn stateless.
- Registry → **GHCR**. Model image = **phần riêng, độc lập app** (pipeline model
  tự build multi-arch + tự set package **public**). App chỉ consume:
  - edge pull vô danh, `.env.edge` không secret
  - server `ModelCatalog` đọc `ghcr.io/v2` **vô danh**; `MODEL_REGISTRY__TOKEN`
    optional (chỉ private / rate limit)
  Đường bảo mật sau: package private + server phát **pull-token ngắn hạn** qua
  MQTT mTLS link (như stream-token) + **cosign verify** ở agent. Xem "Bảo mật sau".
- Model image → **1 multi-arch manifest** (amd64 + arm64/Jetson), 1 tag; GPU/CPU
  do runtime tự dò, không phải manifest.

## Còn mở

- Prometheus đã có hạ tầng sẵn hay dựng mới trong `compose.infra.yml`? (quyết ở S6)
- `chat_messages` / assistant có còn dùng không? (quyết ở S7)

## Bảo mật sau (không làm ở MVP)

Khi model là IP nhạy cảm — chuyển GHCR package sang **private**:

1. Chỉ **server** giữ PAT `read:packages`.
2. Deploy: server `GET ghcr.io/token?scope=repository:{owner}/{pkg}:pull` → bearer
   ~5 phút → gửi trong `DeployModelPayload.pull_token` qua MQTT (đã mTLS) → agent
   `docker login` bằng token đó → `compose pull` → token hết hạn. Edge **0
   long-lived secret**; mất box → revoke MQTT cert của box đó.
3. **cosign**: CI ký image; agent `cosign verify` trước `compose up`. Device chỉ
   chạy image ký bằng key của bạn.
4. Biến thể: Harbor trong `compose.infra.yml`, mỗi edge 1 robot account, pull qua LAN.
