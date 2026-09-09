# Roles & Permissions

Phân quyền 2 chiều:

```
User
 ├── Role  ──► LÀM ĐƯỢC GÌ   (tập permission)
 └── Scope ──► LÀM Ở ĐÂU     (nút trong cây tài nguyên)
```

Một **role assignment** = `(user, role, scope)`. User có nhiều assignment.
Quyền hiệu lực khi gọi 1 endpoint đụng tài nguyên `R`: tồn tại assignment mà
`scope` là **tổ tiên-hoặc-chính** `R` và role đó chứa permission code cần thiết.

---

## 1. Cây scope

```
Organization
 └── Site            (1 địa điểm vật lý; Device/Edge gắn ở đây)
      └── Area        (khu vực trong site; đổi từ Camera.zone string)
           └── Camera
```

* **Edge / Device** không phải 1 tầng riêng trong cây — nó là hạ tầng cấp **Site**.
  Grant ở Site phủ mọi Device + Area + Camera của site đó.
* Grant ở 1 nút phủ toàn bộ cây con. Grant ở `Organization` = toàn hệ thống.
* `scope_type ∈ {org, site, area, camera}`, `scope_id` trỏ vào bảng tương ứng
  (`scope_id = NULL` + `org` ⇒ org gốc).

Bảng cần thêm (hiện chưa có — `site`/`zone` mới là string):
`organizations`, `sites`, `areas`; `cameras.area_id`, `devices.site_id`.

Assignment: `user_role_scopes(user_id, role_id, scope_type, scope_id, created_at)`
thay cho `user_roles` hiện tại.

---

## 2. Permission — quy ước code

`"<resource>.<action>"`, lowercase. Checker chấp nhận wildcard:

| Dạng | Khớp |
|---|---|
| `*` | mọi permission (role `admin`) |
| `<prefix>.*` | mọi code bắt đầu `<prefix>.` (vd `cameras.*`) |

Nguồn sự thật: `app/modules/iam/catalog.py` (`Perm` enum + `PERMISSION_CATALOG`),
upsert lúc startup. Thêm ở đây trước, rồi mới `require(Perm.X)` ở router.

**Cột `scope` của mỗi permission** — tầng thấp nhất mà nó có nghĩa:

| `scope` | Ý nghĩa | Assignment ở tầng cao hơn |
|---|---|---|
| `camera` | check theo từng camera | site/area/org đều phủ |
| `site` | check theo site | org phủ |
| `org` | chỉ có nghĩa toàn tổ chức (không scope nhỏ hơn được) | chỉ assignment `org` |

---

## 3. Bảng quyền

### iam / users — `scope: org`
| Code | Cho phép | Endpoint |
|---|---|---|
| `users.read` | Xem user + role/scope của họ | `GET /users`, `GET /users/{id}` |
| `users.manage` | Tạo / sửa / vô hiệu hoá user | `POST /users`, `PATCH /users/{id}` |
| `iam.read` | Xem role, catalog quyền, assignment | `GET /iam/roles`, `GET /iam/permissions`, `GET /iam/users/{id}/roles` |
| `iam.manage` | CRUD role, set grant, gán role+scope cho user | `POST/PATCH/DELETE /iam/roles`, `PUT /iam/roles/{code}/permissions`, `PUT /iam/users/{id}/roles` |

### system — `scope: org`
| Code | Cho phép | Endpoint |
|---|---|---|
| `system.read` | Xem platform settings + audit log | `GET /system/settings`, `GET /system/audit-logs` |
| `system.manage` | Đổi platform settings | `PATCH /system/settings` |

### models (registry) — `scope: org`
Registry dùng chung toàn tổ chức, không scope theo site.
| Code | Cho phép | Endpoint |
|---|---|---|
| `models.read` | List model + version, detail | `GET /models*` |
| `models.manage` | Đăng ký model, upload version | `POST /models`, `POST /models/{id}/versions` |
| `models.promote` | Đổi lifecycle status version (draft → staging → production) | `POST /models/versions/{id}/status` |

### assistant — `scope: org`
| Code | Cho phép | Endpoint |
|---|---|---|
| `assistant.use` | Đọc lịch sử chat + gửi message tới AI assistant | `GET /assistant/messages`, `POST /assistant/messages` |

### sites / areas — `scope: site`
| Code | Cho phép | Endpoint |
|---|---|---|
| `sites.read` | List / xem site, area | `GET /sites*`, `GET /sites/{id}/areas` |
| `sites.manage` | Tạo / sửa / xoá site + area | `POST/PATCH/DELETE /sites`, `.../areas` |

### agents (edge device) — `scope: site`
| Code | Cho phép | Endpoint |
|---|---|---|
| `agents.read` | List device, detail, metrics, health-summary | `GET /agent/devices*`, `GET /agent/health-summary` |
| `agents.manage` | Đăng ký / sửa / xoá device | `POST /agent/devices`, `PATCH /agent/devices/{id}`, `DELETE /agent/devices/{id}` |
| `agents.deploy` | Gửi command (config/model) xuống device | `POST /agent/devices/{id}/commands` |

### deployments — `scope: site`
Deployment gắn với 1 device ⇒ scope theo site của device.
| Code | Cho phép | Endpoint |
|---|---|---|
| `deployments.read` | List / xem deployment | `GET /deployments*` |
| `deployments.manage` | Tạo deployment, mark failed, rollback | `POST /deployments`, `.../fail`, `.../rollback` |
| `deployments.activate` | Chuyển deployment sang revision active | `POST /deployments/{id}/activate` |

### cameras — `scope: camera`
| Code | Cho phép | Endpoint |
|---|---|---|
| `cameras.read` | List / xem camera, camera-group, snapshot | `GET /agent/cameras*`, `GET /agent/camera-groups*`, `GET /agent/snapshots` |
| `cameras.manage` | Thêm / sửa camera + camera-group | `POST /agent/cameras`, `PATCH /agent/cameras/{id}`, `POST /agent/camera-groups` |
| `cameras.stream.view` | Lấy WHEP view-token để xem | `GET /streaming/cameras/{id}/view-token` |
| `cameras.stream.publish` | Lấy WHIP publish-token | `GET /streaming/cameras/{id}/publish-token` |

### observability — `scope: camera`
Violation / alert đều gắn camera ⇒ scope theo camera.
| Code | Cho phép | Endpoint |
|---|---|---|
| `observability.read` | Xem violation, alert, analytics (đã lọc theo scope) | `GET /violations`, `GET /alerts`, `GET /analytics/*` |
| `observability.manage` | Acknowledge / resolve alert | `POST /alerts/{id}/acknowledge`, `POST /alerts/{id}/resolve` |
| `observability.export` | Tải bulk evidence + export analytics | evidence download, CSV export |

> Ingest từ edge (`POST /evidence`, `POST /violations` qua MQTT gateway) dùng
> edge-token, không đi qua user RBAC.

---

## 4. Role mặc định

Role định nghĩa toàn cục (tập permission), scope gán riêng cho từng user.
Seed lúc startup, sửa qua `iam.manage` (trừ `admin` — chặn edit/delete).

| Role | Grants | Dùng cho |
|---|---|---|
| `admin` | `*` | Gán ở `org` = chủ platform. Gán ở `site` = toàn quyền trong 1 site (trừ iam/system/models — vốn `scope: org`). |
| `operator` | `*.read`, `agents.deploy`, `deployments.manage`, `deployments.activate`, `models.promote`, `cameras.stream.*`, `observability.manage`, `assistant.use` | Ops: deploy model, chạy camera, xử lý alert. Thường gán ở `site`. |
| `viewer` | `*.read`, `assistant.use` | Read-only. Gán ở `org` / `site` / `area` / `camera` tuỳ phạm vi cần cho xem. |

**Superuser escape hatch:** user có `users.is_superuser = true` (hoặc email trong
`settings.superuser_emails`) qua mọi check bất kể role/scope → IAM không tự khoá
hết. Bypass này được log.

---

## 5. Enforcement

1. `Authz` dependency decode access token → load user (401 nếu thiếu/inactive).
2. Nạp mọi assignment của user `(role → {permission codes}, scope_type, scope_id)`,
   expand wildcard, cache `Principal` trên `request.state` (1 lần/request).
3. Route khai báo quyền **và** cách lấy scope của tài nguyên:
   ```python
   _: Principal = Depends(require(Perm.CAMERAS_MANAGE, scope=CameraScope("camera_id")))
   ```
   Resolver đọc path param → tra ngược chuỗi tổ tiên `camera → area → site → org`.
4. Cho phép nếu ∃ assignment: `code ∈ role.permissions` **và**
   `assignment.scope` nằm trên chuỗi tổ tiên-hoặc-chính của tài nguyên.
5. Endpoint dạng **list** (`GET /agent/cameras`) không check 1 tài nguyên —
   thay vào đó service nhận `principal.scoped_ids(Perm.CAMERAS_READ)` và lọc query.

Permission `scope: org` chỉ khớp assignment `scope_type = org`.

---

## 6. Trạng thái & lộ trình

Hiện có: bảng phẳng `users/roles/permissions/user_roles/role_permissions` +
`require_permission(code)` (không scope); chỉ streaming/deployment/users router
guard; frontend không gate; local env bypass toàn bộ.

Lộ trình (chi tiết ở `docs/REFACTOR_TODO.md` PHẦN 5):

- **PR-A** `catalog.py` (`Perm` enum + cột `scope`) + seed startup; viết lại
  `bearer_auth.py` → `Authz` (Principal cache, wildcard, superuser); bỏ local bypass.
- **PR-B** bảng `organizations/sites/areas` + `cameras.area_id`/`devices.site_id`;
  `user_roles` → `user_role_scopes`; scope resolver + ancestor walk.
- **PR-C** API `/iam/*` (CRUD role, gán role+scope) + `/sites`, `/areas`.
- **PR-D** áp `require(Perm, scope=...)` lên mọi router; list endpoint lọc theo scope.
- **PR-E** frontend: `AuthProvider` với `can(code, resource)`, gate menu/route/nút,
  UI gán role+scope trong `system/`.

Deferred: role inheritance, time-boxed grant, deny-rule, SSO/OIDC.
