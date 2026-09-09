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

- [ ] Kiểm chứng CI `deploy.yml`: `scp` với `strip_components: 1` +
      `COMPOSE_FILE`/`COMPOSE_ENV_FILES` (chỉ chạy khi push `main`).

> **Model image = phần riêng, độc lập với app.** Pipeline model tự build
> multi-arch, tự set package **public**. App chỉ *consume*: `ModelCatalog` đọc
> `ghcr.io/v2/{owner}/{pkg}` **vô danh** (public) — không cần PAT cho MVP.
> `MODEL_REGISTRY__TOKEN` để trống, chỉ điền khi chuyển package sang private
> hoặc cần nới GHCR rate limit.

---

## C. Chặn — trạng thái

- [x] **WIP MCP/assistant** — đã commit `9f080f9`: fix `MCPServer→FastMCP`,
      smoke test dùng `/help`. `server` test **26 pass / 1 fail**
      (`test_violation_over_bus_records_and_alerts` — bug WIP có sẵn, ghi ở
      `REFACTOR_TODO.md`).
- [x] **artifact_uri/S3 cleanup** — commit `c950797`.
- [ ] Frontend WIP còn treo (6 file sửa + `LogsEventSidebar.tsx`,
      `PageLayout.tsx`) — chưa rõ ranh giới với MCP feature; S2b sẽ đụng
      `ModelsPage.tsx` nên gộp/xử ở đó.
- [ ] `svc_core` submodule có WIP `ai_core/commands/` + `S3Config` `__all__` (mình
      dọn) — quyết định commit trong submodule + bump con trỏ, hay để nguyên.

---

## D. Stateless refactor — S0..S6 XONG, S3.3/S7 dở

Mỗi bước: BE + FE + test xanh cùng nhau. S1→S5 tuần tự; S6/S7 độc lập.

- [x] **S1/S3.1 — `DEVICE_ID` string PK** (commit `3b2c37d`) — protocol + server
  + FE + `device_id_from_envelope` bỏ `int()` (fix bug agent gửi `edge-dev-1`).
- [x] **S2 — `ModelCatalog` đọc GHCR** (commit `56a328a` + `393a2af`)
  - S2a `catalog.py` (`ModelCatalog`/`ModelImage`) + `Settings.model_registry` + test
  - S2b `GET /models` + `/models/{tag}` từ catalog; bỏ `POST /models`/versions/status;
    xoá ORM `models`/`model_versions`/repo/service/schemas/rules; `deployment` +
    `gateway` dùng `image` ref; `active_model_version_id` → `active_image` (protocol
    + agent + Device); FE types + `ai.ts` service + `ModelsPage`/`DeploymentsPage`
  - còn: 5 dòng E501 pre-existing trong `deployment/router.py` (không đụng ở S2b)
- [~] **S3.2 + S4 — `Device` = desired config; `FleetRegistry` in-memory**
      (commit `add9d86`)
  - [x] `Device` ORM giờ chỉ desired (device_id, name, site, labels,
        desired_image, cameras, inference/agent overrides). Bỏ mọi cột reported.
  - [x] `FleetRegistry` (`app/modules/agent/fleet_registry.py` + `app/core/fleet.py`)
        — dict in-memory, dựng lại từ heartbeat + state report. Không persist.
  - [x] `AgentService` merge `DeviceOut` (config + runtime + `known` + `in_sync`);
        device lạ báo MQTT → view chưa provision. Bỏ `PresenceRegistry` (xoá 3 file
        + test_presence).
  - [x] gateway: state report → `fleet.record_state`; `sweep_presence` →
        `fleet.sweep()` → `DeviceWentOffline`.
  - [ ] **còn**: agent publish `state` retained + LWT — cần svc_core
        `publish(retain=)` (submodule). LWT có thể set qua `MQTT__WILL_*` config
        ngay. Chưa làm → restart server mất ~1 nhịp heartbeat để roster về.
  - [x] **S3.3 config** (`0ca775b`): `ConfigResolver` (model labels < `app_settings`
        `inference_policy` < `Device.inference`); operator sửa inference →
        `DeviceConfigChanged` → `T_UPDATE_CONFIG`. `ModelImage` + Dockerfile thêm
        `conf/iou/imgsz` labels.
  - [ ] **S3.3 còn**: gộp `cameras`/`camera_groups` vào `Device.cameras`
        (streaming dùng `camera_id: int` → đổi trước); FE Fleet defaults page.
- [x] **S5** (`293481c`) — deploy = command; xoá ORM Deployment; GET /deployments = per-device view.
- [x] **S6** (`847244c`) — metrics ring buffer in-memory (FleetRegistry); xoá `metric_samples`. Prometheus remote-write để sau.
- [~] **S7** — `backend/schema.sql` regen (14 bảng); `ARCHITECTURE.md` + `deploy-model.md` dọn. `chat_messages` giữ (assistant). `docs/flows/*` mermaid chưa vẽ lại.

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
