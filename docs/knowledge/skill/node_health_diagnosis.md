---
id: skill_node_health_diagnosis
name: Chẩn đoán sức khỏe một edge node
category: edge_operations
version: 1.0.0
tools: [list_nodes, get_node, get_latest_telemetry, get_telemetry_history, get_node_events, list_runtimes]
summary: >-
  Quy trình đánh giá toàn diện sức khỏe một edge node (thiết bị Jetson, máy biên): trạng thái
  ONLINE/OFFLINE/DEGRADED, heartbeat, tài nguyên CPU, RAM, swap, nhiệt độ SoC và GPU, thermal throttling,
  đĩa, mạng, cùng tình trạng các runtime AI đang chạy trên đó. Dùng khi người dùng hỏi "node X có ổn không",
  "kiểm tra tình trạng / tài nguyên / health check thiết bị", "vì sao node bị DEGRADED", "node có quá tải,
  quá nhiệt không". Phối hợp list_nodes (tìm node theo tên), get_node, get_latest_telemetry,
  get_telemetry_history, get_node_events và list_runtimes, rồi tổng hợp thành kết luận có số liệu.
---

# Chẩn đoán sức khỏe một edge node

## Khi nào dùng
- "Kiểm tra node `hn-line-a` giúp tôi", "Jetson ở cổng chính có ổn không?", "Sao node này DEGRADED?"
- Trước khi deploy thêm runtime lên node (xem thêm `skill_safe_deploy`).
- KHÔNG dùng khi node OFFLINE ngay từ đầu → theo `runbook_node_offline`.
- KHÔNG dùng khi câu hỏi chỉ về một runtime cụ thể bị lỗi → `skill_runtime_troubleshooting`.

## Dữ liệu cần có
- `node`: tên, mã (vd `CT-A-01`) hoặc id, truyền thẳng như người dùng nói; thêm `cluster` nếu tên trùng giữa các cụm.
  Nhiều node trùng tên ở các cụm khác nhau → hỏi lại người dùng.

## Quy trình
1. **Trạng thái node** – `get_node(node)`: đọc `status`, `last_heartbeat_at`, `agent_version`,
   `cpu_cores`, `memory_total_mb`, `gpu_name`.
   - `OFFLINE` → dừng quy trình này, chuyển sang `runbook_node_offline`.
   - `last_heartbeat_at` cũ hơn 30 giây nhưng status chưa đổi → coi như sắp OFFLINE, nói rõ với người dùng.
2. **Ảnh chụp hiện tại** – `get_latest_telemetry(node)` trả về dict theo kind `system`, `gpu`, `runtime:<id>`.
   Đối chiếu từng metric với `doc_metrics_thresholds`. Ghi lại mọi metric WARNING/CRITICAL.
   Thiếu kind `gpu` → node không có exporter GPU (bình thường với node CPU); không kết luận là lỗi.
3. **Xu hướng** – với mỗi metric bất thường, gọi `get_telemetry_history(node, kind, limit=60)`
   (≈ 5 phút) để phân biệt đột biến nhất thời với vấn đề kéo dài; `limit=360` (≈ 30 phút) nếu cần baseline.
   - Nhiệt độ tăng đều + `thermal_throttling=true` → nhánh nhiệt (`runbook_gpu_overheating`).
   - `memory_usage_pct` tăng dần + `memory_growth_rate` > 0 → nghi rò rỉ bộ nhớ ở một runtime.
   - `disk_usage_pct` ≥ 90 → `runbook_disk_full`.
4. **Runtime trên node** – `list_runtimes(node)`: đếm theo `status`. Runtime `FAILED`/`RESTARTING`
   chính là lý do node `DEGRADED`. Liệt kê tên, trạng thái, `message`.
5. **Sự kiện gần đây** – `get_node_events(node, limit=50)`: tìm `severity` ERROR/CRITICAL,
   `event_type` `runtime.status` chuyển sang FAILED, lệnh `command.*` thất bại. Ghép thời điểm sự kiện với
   thời điểm metric xấu đi để tìm nguyên nhân.

## Kết luận & trả lời
Trả lời theo cấu trúc:
1. **Tổng quan**: ONLINE / DEGRADED, một câu kết luận.
2. **Vấn đề phát hiện** (sắp theo mức nghiêm trọng): metric, giá trị hiện tại, ngưỡng, xu hướng.
3. **Runtime**: số đang chạy / lỗi, tên runtime lỗi.
4. **Đề xuất**: bước tiếp theo, dẫn tới runbook/skill phù hợp. Không tự thực hiện thao tác ghi.

Nếu mọi thứ bình thường, nói rõ "không phát hiện bất thường" kèm 3-4 số liệu chính (CPU, RAM, nhiệt độ, FPS).

## An toàn
Quy trình chỉ đọc. Mọi hành động khắc phục (restart runtime, gỡ deployment) phải hỏi người dùng xác nhận.
