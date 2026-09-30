---
id: skill_safe_deploy
name: Triển khai runtime AI mới lên edge node an toàn
category: deployment
version: 1.0.0
tools: [list_clusters, list_nodes, get_node, get_latest_telemetry, list_runtimes, list_deployments, create_deployment, get_deployment, get_runtime]
summary: >-
  Quy trình deploy (triển khai, cài đặt, đưa lên) một runtime AI hoặc model mới (image Docker, model PPE,
  YOLO, detector) lên một hoặc nhiều edge node một cách an toàn: kiểm tra node ONLINE, đủ tài nguyên GPU,
  RAM, đĩa, không trùng runtime đã có, xác nhận cấu hình (image_uri, image_tag, model_uri, config,
  resource_limits) với người dùng, gọi create_deployment rồi theo dõi tới khi deployment SUCCEEDED và
  runtime RUNNING. Dùng khi người dùng nói "deploy model X lên node Y", "cài runtime cho cụm", "triển khai
  lên tất cả node của nhà máy". Phối hợp get_node, get_latest_telemetry, list_runtimes, create_deployment,
  get_deployment, get_runtime.
---

# Triển khai runtime AI mới lên edge node an toàn

## Khi nào dùng
- "Deploy image ghcr.io/org/ppe:v2 lên node Hố móng", "Triển khai model PPE cho cả cụm Công trường A".
- KHÔNG dùng để đổi phiên bản runtime đang có → `skill_deployment_update_rollback`.

## Dữ liệu cần có
Bắt buộc: node đích, `name` runtime, `image_uri`. Tùy chọn: `image_tag` (mặc định `latest`, nên yêu cầu tag
cụ thể), `type` (VISION, SAFETY, ANOMALY, OCR, CUSTOM), `model_uri` (URL https tới file model),
`config` (ví dụ `target_fps`, ngưỡng confidence, RTSP), `environment`, `resource_limits`
(`cpus`, `memory`, `gpus`). Thiếu thông tin bắt buộc → hỏi người dùng, không tự bịa image.

## Quy trình
1. **Xác định node đích** – một node: `list_nodes` khớp tên. Cả cụm: `list_clusters` → `list_nodes(cluster)`.
2. **Kiểm tra từng node** (bỏ qua node không đạt và báo lại):
   - `get_node`: phải `ONLINE` (hoặc `DEGRADED` nếu người dùng chấp nhận). `OFFLINE` → loại.
   - `get_latest_telemetry`: `memory_available_mb` ≥ nhu cầu (`resource_limits.memory`, mặc định giả định
     1 GB cho model thị giác), `disk_free_gb` ≥ 5, `gpu_memory_usage_pct` < 80 nếu runtime dùng GPU,
     không có `thermal_throttling`.
   - `list_runtimes(node)`: đã có runtime cùng `name` → đây là cập nhật, chuyển sang
     `skill_deployment_update_rollback`. Đếm runtime đang chạy để cảnh báo quá tải GPU.
3. **Xác nhận với người dùng** – tóm tắt: danh sách node đạt / bị loại (lý do), image:tag, model, config,
   resource_limits. Chỉ tiếp tục khi người dùng đồng ý rõ ràng.
4. **Triển khai** – `create_deployment(node, name, image_uri, image_tag, type, model_uri, config,
   environment, resource_limits)` cho từng node. Với nhiều node: triển khai **1 node trước** (canary),
   xác nhận thành công rồi mới làm các node còn lại.
5. **Theo dõi** – edge báo kết quả bất đồng bộ: `get_deployment(deployment)` mỗi ~15 giây, tối đa ~5 phút
   (lần đầu tải image có thể lâu).
   - `SUCCEEDED` → `get_runtime(runtime)` phải `RUNNING`.
   - `FAILED` → đọc `message`, chuyển sang `skill_runtime_troubleshooting`; với nhiều node thì dừng triển
     khai các node còn lại.
   - Quá thời gian vẫn `IN_PROGRESS` → báo người dùng, kiểm tra node còn ONLINE không.
6. **Kiểm tra sau deploy** – sau 1-2 phút: `get_latest_telemetry` kind `runtime:<id>`:
   `effective_fps_ratio` ≥ 0.9, `inference_error_rate` < 0.01, camera `ONLINE`.

## Kết luận & trả lời
Bảng kết quả theo node: node, deployment, trạng thái, FPS/latency đầu tiên, ghi chú lỗi.

## An toàn
`create_deployment` là thao tác ghi, chỉ gọi sau khi người dùng xác nhận danh sách node và cấu hình.
Triển khai canary khi có từ 2 node trở lên. Không tự chọn image/tag khi người dùng chưa nói.
