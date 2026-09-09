# TODO — trạng thái tổng

Cập nhật 2026-09-09. Branch `refactor/svc-core-extract-1`.
Chi tiết kế hoạch: [`REFACTOR_stateless.md`](REFACTOR_stateless.md).

---

## A. Đã xong (committed trên branch này)

- `f8cd84a` — gom mọi docker compose vào `app/deploy/`; prod = infra + app
  overlay; env tách theo concern (`.env.infra/.app/.edge`), compose thuần
  `${VAR}`; **bỏ MinIO/S3** khỏi compose + env + CI.
- `243214f` — doc kế hoạch stateless (S0–S7).
- `01957e8` — **S0**: gộp `Dockerfile.cpu/.gpu` → 1 `Dockerfile` multi-arch
  (`_resolve_device` dò CUDA/MPS/CPU); `Dockerfile.jetson` để dành; contract
  labels `ai.edge-ops.model.*`; `.env.app` thêm `MODEL_REGISTRY__*`.
- `27d9c2e` — chốt MVP: GHCR model package **public**, edge không cần token.
- (chưa commit, an toàn) — xoá `S3__*` khỏi `backend/server/.env`; dọn
  `S3Config` mồ côi trong `svc_core` `__all__`.

---

## B. Việc tay — không phải code

- [ ] Tạo **GitHub PAT `read:packages`** → đã có, đặt `MODEL_REGISTRY__TOKEN`
      trong `deploy/.env.app` (prod: docker secret / Actions secret).
- [ ] Khi có model image đầu tiên: set GHCR package đó **Public**
      (`github.com/<user> → Packages → package → settings → visibility`).
- [ ] Kiểm chứng CI `deploy.yml`: `scp` với `strip_components: 1` +
      `COMPOSE_FILE`/`COMPOSE_ENV_FILES` (chỉ chạy khi push `main`).

---

## C. Chặn — xử trước khi làm S1+

- [ ] **WIP MCP/assistant chưa commit** đang nằm trong working tree
      (`app/mcp/`, `mcp_main.py`, `assistant/{commands,operator_agent,toolset}.py`,
      sửa `assistant/*`, `gateway.py`, `model_registry/{models,schemas}.py`,
      `edge_protocol/messages.py`, tests, `frontend/.../ModelsPage.tsx`,
      `docs/ROLES.md`). **`server` test đang đỏ**: `ModuleNotFoundError:
      mcp.server.mcpserver`.
  → commit / stash / sửa import cho xanh. S1–S5 đụng đúng các file này.
- [ ] `svc_core` submodule có WIP `ai_core/commands/` — quyết định commit trong
      submodule + bump con trỏ, hay để nguyên.

---

## D. Stateless refactor — S1 → S7 (chưa làm)

Mỗi bước: BE + FE + test xanh cùng nhau. S1→S5 tuần tự; S6/S7 độc lập.

- [ ] **S1 — `DEVICE_ID` là string PK ở mọi nơi**
  - `edge_protocol`: payload dùng `device_id: str`
  - `device_id_from_envelope()` bỏ `int()`
  - `violations.device_id` → TEXT (+ chỗ FK còn lại)
  - FE types: `BackendDevice.id`, `DeploymentRecord.device_id`,
    `BackendCamera.id` → `string`; `CreateDevicePayload.device_id`
  - sửa test; fix luôn bug hiện tại (agent gửi `edge-dev-1`, server ép int)
- [ ] **S2 — `ModelCatalog` đọc GHCR**
  - `model_registry/catalog.py` + `Settings.model_registry`
  - `GET /models*` đổi backing; **bỏ `POST /models`**
  - xoá ORM `models`/`model_versions` + repo + `ModelRegistryService`
  - FE: `types/ai.ts` reshape (id=string, versions=tags, field từ labels);
    `ModelsPage` bỏ form register, hiện labels
- [ ] **S3 — `device_config` (desired) + config phân tầng**
  - bảng `device_config` + service; `POST/PATCH /agent/devices` +
    `/agent/cameras` map vào đó
  - khối `inference_policy` global (`/system/settings`) +
    `ConfigResolver.merge(model, global, device, camera)`
  - FE: provision bằng `device_id`; sửa camera inline; trang **Fleet defaults**
    + panel override (kế thừa vs override); `CameraGroupsPage` client-only/bỏ
- [ ] **S4 — `FleetRegistry` in-memory** *(rủi ro cao)*
  - agent `state` publish `retain=True, qos=1` + LWT (`network/link.py`)
  - server subscribe `agent/devices/+/state`; `GET /agent/devices` = union
    known (`device_config`) + online (retained)
  - bỏ `PresenceRegistry`; dùng `evaluate_status`
  - FE: hiện **drift** desired vs reported; live update qua WS
- [ ] **S5 — deploy = command, không ghi row**
  - `/deployments` = set `device_config.desired_image` + publish `T_DEPLOY_MODEL`
  - xoá ORM `deployments`; history → `audit_logs`
  - FE `DeploymentsPage`: chọn device(s) + image tag; tiến trình từ WS
    (`ack`+`state`), bỏ `progressPct`
- [ ] **S6 — metrics ra Prometheus**
  - Prometheus (mới trong `compose.infra.yml`?) — *cần quyết*
  - agent expose `/metrics`; `GET .../metrics` proxy Prometheus hoặc 501
  - xoá `metric_samples`; FE chart live qua WS ring buffer
- [ ] **S7 — dọn**
  - `chat_messages`/assistant — giữ hay bỏ? *(cần quyết)*
  - viết lại `backend/schema.sql` cho khớp DB đích
  - dọn `docs/ARCHITECTURE.md` + `docs/flows/*` (bỏ nhắc artifact/presigned/S3)

**DB đích sau S1–S7:** giữ `device_config`, `violations`, `snapshots`, `alerts`,
`users`/`roles`/`permissions`, `audit_logs`, `app_settings`. Bỏ: `devices`,
`models`, `model_versions`, `deployments`, `cameras`, `camera_groups`,
`metric_samples`, (`chat_messages`).

---

## E. Quyết định còn treo

- [ ] Prometheus: dựng mới trong `compose.infra.yml` hay đã có hạ tầng? → S6
- [ ] `chat_messages` / assistant còn dùng không? → S7
- [ ] `svc_core` submodule: commit WIP `ai_core/commands` bây giờ?

---

## F. Dọn dẹp — nice to have

- [ ] `nginx_data/` còn tracked (`proxy/*.conf`, `server/data.conf`) — trùng
      `deploy/vps-proxy/`, có vẻ commit nhầm. Xoá?
- [ ] `docs/flows/edge-server/deploy-model.md` — nhắc `deployment_id`,
      `model_version_id`, `compose.project_dir` → cập nhật sau S5.
- [ ] `docs/REFACTOR_TODO.md` "Còn mở" (PresenceRegistry, agent logs) — nay
      PresenceRegistry chốt **bỏ** ở S4; ghi lại.
- [ ] Bảo mật model image (private + pull-token ngắn hạn + cosign) — mục
      "Bảo mật sau" trong `REFACTOR_stateless.md`, khi model là IP.
