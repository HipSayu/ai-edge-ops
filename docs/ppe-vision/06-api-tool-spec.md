# Đặc tả API và tool

Mọi endpoint có tiền tố `/api`. Lỗi trả JSON `{"detail": "..."}`. Xác thực bằng header
`Authorization: Bearer <access_token>`. Riêng luồng media (stream, snapshot, báo cáo) cho phép thêm
Header `Authorization: Bearer`. Không nhận token trên URL (URL lọt vào log và lịch sử); trang web tải ảnh và tệp bằng `fetch` rồi hiển thị qua blob.

Trạng thái: **Có** = đã viết và có test, **Kế hoạch** = chưa viết.

## 1. Vai trò và quyền

| Hành động | VIEWER | OPERATOR | ADMIN |
|---|---|---|---|
| Đăng nhập, xem hồ sơ | ✅ | ✅ | ✅ |
| Xem camera, vi phạm, lưới trong **cluster được gán** | ✅ | ✅ | ✅ |
| Xem mọi cluster | ❌ | ❌ | ✅ |
| Chat hỏi đáp | ✅ | ✅ | ✅ |
| Xuất báo cáo | ❌ | ✅ | ✅ |
| Tải video, đồng bộ thư mục | ❌ | ✅ | ✅ |
| CRUD cluster, node, camera, người dùng | ❌ | ❌ | ✅ |

Camera ngoài phạm vi trả **404** (không lộ sự tồn tại). Yêu cầu `cluster_id` ngoài phạm vi trả **403**.

## 2. Mã lỗi chung

| Mã | Ý nghĩa |
|---|---|
| 400 | Dữ liệu không hợp lệ (vai trò sai, file không phải video) |
| 401 | Thiếu hoặc sai token, tài khoản bị khóa |
| 403 | Không đủ quyền |
| 404 | Không tìm thấy, hoặc ngoài phạm vi quyền |
| 409 | Xung đột (trùng tên đăng nhập, node đầy camera, đổi cluster khi node còn camera) |

## 3. REST API

### Xác thực
| Endpoint | Quyền | Mô tả | Trạng thái |
|---|---|---|---|
| `GET /health` | công khai | `{"status":"ok"}` | Có |
| `POST /auth/login` `{username, password}` | công khai | Trả `{access_token, user}` | Có |
| `GET /auth/me` | đăng nhập | Hồ sơ và `cluster_ids` | Có |

### Cluster
| Endpoint | Quyền | Mô tả | Trạng thái |
|---|---|---|---|
| `GET /clusters` | đăng nhập | ADMIN: tất cả; còn lại: cluster được gán | Có |
| `POST /clusters` `{name, description?}` | ADMIN | Tạo | Có |
| `PUT /clusters/{id}` | ADMIN | Sửa | Có |
| `DELETE /clusters/{id}` | ADMIN | Xóa kèm node và camera bên trong; file video giữ nguyên | Có |

### Node
| Endpoint | Quyền | Mô tả | Trạng thái |
|---|---|---|---|
| `GET /nodes?cluster_id=` | đăng nhập | Trong phạm vi quyền, có `camera_count` | Có |
| `POST /nodes` `{name, cluster_id, max_cameras=16}` | ADMIN | Tạo; cluster không tồn tại → 404 | Có |
| `PUT /nodes/{id}` | ADMIN | Không đổi cluster khi còn camera; `max_cameras` không nhỏ hơn số camera hiện có → 409 | Có |
| `DELETE /nodes/{id}` | ADMIN | Xóa kèm camera | Có |

### Camera và video
| Endpoint | Quyền | Mô tả | Trạng thái |
|---|---|---|---|
| `GET /cameras` | đăng nhập | Trong phạm vi quyền, kèm `node_name`, `cluster_name`, danh sách `videos` | Có |
| `POST /cameras` `{name, node_id, zone?, enabled}` | ADMIN | Tạo và tạo thư mục video; node đủ `max_cameras` → 409 | Có |
| `PUT /cameras/{id}` `{name, zone?, enabled}` | ADMIN | Không đổi `node_id` vì sẽ phải dời thư mục video | Có |
| `DELETE /cameras/{id}` | ADMIN | Xóa khỏi DB; file video giữ nguyên | Có |
| `POST /cameras/{id}/videos` (multipart `file`) | OPERATOR+ | Lưu vào `video/{cluster}/{node}/{camera}/`; chỉ `.mp4 .avi .mkv` | Có |
| `POST /cameras/sync` | OPERATOR+ | Tạo thư mục thiếu; trả `{cameras, videos, unmatched_folders}` | Có |
| `GET /cameras/{id}/events?limit=` | trong phạm vi | Vi phạm mới nhất | Có |
| `GET /cameras/{id}/stream` | trong phạm vi | MJPEG `multipart/x-mixed-replace` | Kế hoạch |
| `GET /snapshots/{event_id}` | trong phạm vi | Ảnh JPEG của vi phạm | Kế hoạch |

### Lưới và thống kê
| Endpoint | Quyền | Mô tả | Trạng thái |
|---|---|---|---|
| `GET /grid?cluster_id=` | đăng nhập | Camera đã xếp ưu tiên (tối đa `PPE_GRID_SIZE`) | Có |
| `GET /stats?cluster_id=&since_minutes=60` | đăng nhập | `{total, by_type}` | Có |

Phần tử của `/grid`:

```json
{"camera_id":1,"name":"Cổng A","zone":"Tầng 1","node_id":1,"node_name":"Node local",
 "cluster_id":1,"cluster_name":"Công trường mẫu","person_count":3,
 "violation_count_recent":2,"score":9.4,"stream_url":"/api/cameras/1/stream"}
```

`person_count` hiện luôn là 0 cho tới khi có vision worker.

**Thuật toán xếp hạng.** Điểm tức thời `3 × vi_phạm_60s + 1 × số_người`, làm mượt EMA (giữ 0,7).
Camera ngoài lưới chỉ thay camera yếu nhất trong lưới khi điểm lớn hơn `1,5 × điểm_yếu_nhất + 1`
và camera đó đã ở trong lưới ít nhất 10 giây. Cách này chống nhấp nháy.

### Người dùng
| Endpoint | Quyền | Mô tả | Trạng thái |
|---|---|---|---|
| `GET /users` | ADMIN | Danh sách | Có |
| `POST /users` `{username, password, full_name, role, is_active, cluster_ids}` | ADMIN | Trùng tên → 409; ADMIN không lưu `cluster_ids` | Có |
| `PUT /users/{id}` | ADMIN | `password` bỏ trống thì giữ nguyên | Có |
| `DELETE /users/{id}` | ADMIN | Xóa | Có |

### Chat và báo cáo
| Endpoint | Quyền | Mô tả | Trạng thái |
|---|---|---|---|
| `POST /chat` `{message, session_id?}` | đăng nhập | `{stream_id, session_id}`; lỗi (chưa cấu hình LLM) trả ngay ở bước này | Đã có |
| `GET /chat/stream/{stream_id}` | người đã gọi POST | SSE (mục 4), mô hình viết tới đâu gửi tới đó; đọc được một lần | Đã có |
| `GET /reports` | OPERATOR+ | Báo cáo của mình; ADMIN: tất cả | Kế hoạch |
| `GET /reports/{id}/docx` | Người đã đăng nhập | Tải báo cáo Word (.docx) | Kế hoạch |

## 4. Sự kiện SSE của chat *(kế hoạch)*

Mỗi sự kiện: `event: <tên>` rồi `data: <json>`, cách nhau bằng một dòng trống.

| event | data |
|---|---|
| `tool_start` | `{"agent":"orchestrator\|analyst\|compliance\|reporter","name":"find_ppe_violations"}` |
| `tool_end` | `{"agent":"...","name":"..."}` |
| `token` | `{"content":"..."}` (chỉ từ orchestrator) |
| `report` | `{"report_id":"...","url":"/api/reports/.../docx"}` |
| `done` | `{"reply":"...","session_id":"..."}` |
| `error` | `{"message":"..."}` |

Quy ước: mỗi người dùng một cuộc chat chạy tại một thời điểm (409 nếu đang chạy); bộ nhớ hội thoại giữ 20
message cuối, tách theo người dùng; thiếu `ANTHROPIC_API_KEY` thì trả `error` rõ ràng, không 500.

## 5. Agent và tool *(kế hoạch)*

Bốn agent. Sub-agent được gọi như một tool của orchestrator, chạy chung tiến trình.

| Agent | Nhiệm vụ | Tool |
|---|---|---|
| `orchestrator` | Chat với người dùng, hiểu ý định, giao việc, tổng hợp | `delegate_to_analyst`, `delegate_to_compliance`, `delegate_to_reporter` |
| `analyst` | Suy luận trên sự kiện YOLO: số lượng, xu hướng, mức nghiêm trọng | `find_ppe_violations`, `get_violation_frame` |
| `compliance` | Tìm điều khoản liên quan, trích nguyên văn có nguồn | `lookup_safety_regulation` |
| `reporter` | Dựng báo cáo, chỉ chạy khi được yêu cầu | `export_safety_report` |

| Tool | Đầu vào | Đầu ra | Quyền |
|---|---|---|---|
| `find_ppe_violations` | `camera_id?`, `cluster_id?`, `violation_type?`, `since_minutes=60` | `{total, by_type, by_camera, by_minute, top_events[≤10]}` | Tự lọc theo `allowed_camera_ids` của người dùng |
| `get_violation_frame` | `event_id` | `{event_id, camera, type, created_at, image_url}` | Sự kiện phải thuộc phạm vi quyền |
| `lookup_safety_regulation` | `query` | Tối đa 4 đoạn `{source, heading, text, score}`; rỗng → `{"results":[],"note":"Không tìm thấy căn cứ..."}` | Mọi vai trò |
| `export_safety_report` | `title`, `summary`, `sections[{heading, body_markdown}]`, `event_ids[]` | `{report_id, url}` | OPERATOR+; VIEWER nhận `{"error":"Không đủ quyền xuất báo cáo."}` |
| `delegate_to_analyst` | `task` | Văn bản kết quả (JSON) | Mọi vai trò |
| `delegate_to_compliance` | `task` | Văn bản kết quả | Mọi vai trò |
| `delegate_to_reporter` | `task`, `analysis`, `regulations` | Văn bản kết quả | OPERATOR+ |

**Ràng buộc.**
- Chỉ `analyst` được đọc dữ liệu YOLO. Các agent khác nhận kết quả qua JSON, nên số liệu không do LLM tự bịa.
- `compliance` chỉ trích từ kết quả `lookup_safety_regulation`, mỗi trích dẫn kèm nguồn. Không có căn cứ thì nói rõ là không có.
- `lookup_safety_regulation` đọc văn bản trong `volume/regulations/*.md`; hệ thống không tự điền nội dung điều khoản.
- Tool dữ liệu dùng chung `allowed_camera_ids` với API, nên người dùng không có đường nào xem dữ liệu cluster khác qua trợ lý.
