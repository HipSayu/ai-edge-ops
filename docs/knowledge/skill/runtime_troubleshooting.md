---
id: skill_runtime_troubleshooting
name: Xử lý sự cố một runtime AI
category: edge_operations
version: 1.0.0
tools: [list_runtimes, get_runtime, list_deployments, get_deployment, get_node_events, get_latest_telemetry, get_telemetry_history, control_runtime]
summary: >-
  Quy trình troubleshooting: tìm nguyên nhân và khắc phục khi một runtime AI (container model PPE, detector, YOLO) trên edge
  node gặp sự cố: trạng thái FAILED, RESTARTING, DEGRADED, bị dừng, không chạy, liên tục khởi động lại
  (crash, restart loop), deploy thất bại, hoặc chạy nhưng không cho kết quả. Dùng khi người dùng hỏi
  "runtime X bị lỗi", "model không chạy", "tại sao runtime FAILED", "container cứ restart". Phối hợp
  get_runtime, get_deployment, get_node_events (lịch sử runtime.status, command.*), telemetry runtime
  (runtime_restart_count, inference_error_rate) và control_runtime để restart khi người dùng đồng ý.
---

# Xử lý sự cố một runtime AI

## Khi nào dùng
- "Runtime ppe-detector ở node A bị FAILED", "Model không chạy nữa", "Runtime cứ khởi động lại".
- KHÔNG dùng khi runtime chạy bình thường nhưng chậm → `skill_inference_performance`.
- KHÔNG dùng khi vấn đề là hình ảnh camera → `skill_camera_diagnosis`.

## Dữ liệu cần có
- `runtime_id`. Nếu chỉ có tên runtime và tên node: tìm node (`list_nodes`) → `list_runtimes(node)`
  → khớp `name`.

## Quy trình
1. **Trạng thái runtime** – `get_runtime(runtime)`: `status`, `message`, `image_uri`, `image_tag`,
   `node`, `cluster`, `started_at`.
   - `message` chứa "Cannot pull image" / "not reachable" → nhánh **A (image / engine)**.
   - `message` dạng "exited with code N" → nhánh **B (container crash)**.
   - `status = STOPPED` → có người đã dừng; hỏi người dùng có muốn start lại không (bước 6).
2. **Trạng thái node** – `get_node(node)`: node `OFFLINE` → trạng thái runtime là dữ liệu cũ,
   chuyển sang `runbook_node_offline`.
3. **Lần triển khai gần nhất** – `list_deployments(node)` lấy deployment của runtime, rồi
   `get_deployment(deployment)`: `status`, `message`, `last_command_id`, `spec` (image, config,
   resource_limits). Deployment `FAILED` ngay sau một `update` → nghi phiên bản mới lỗi (xem
   `skill_deployment_update_rollback`).
4. **Dòng thời gian** – `get_node_events(node, limit=100)`, lọc theo `runtime_id`:
   các lần `runtime.status` chuyển RUNNING → FAILED, `command.*` thất bại, thời điểm bắt đầu lỗi.
5. **Telemetry runtime** – `get_telemetry_history(node, "runtime", limit=120)`, lọc theo `runtime_id`:
   - `runtime_restart_count` tăng ≥ 3 trong 10 phút → crash-loop (`runbook_runtime_crashloop`).
   - `runtime_memory_mb` tăng tới sát giới hạn `resource_limits.memory` rồi restart → OOM, cần tăng
     memory hoặc giảm batch/độ phân giải.
   - `inference_error_rate` cao nhưng container vẫn RUNNING → lỗi model/đầu vào, không phải container.
   - Cùng lúc xem system telemetry: `memory_usage_pct` ≥ 95 hoặc `disk_usage_pct` ≥ 90 của node có thể là
     nguyên nhân gốc.

### Nhánh A – image / container engine
- Sai `image_uri`/`image_tag` hoặc registry private chưa đăng nhập → đề xuất sửa deployment
  (`update_deployment` với tag đúng) sau khi người dùng xác nhận.
- "Docker is not reachable" → dịch vụ Docker trên node dừng; cần người vận hành kiểm tra máy (ngoài tầm tool).

### Nhánh B – container crash
- Exit code 137 → bị kill do hết bộ nhớ (OOM). Exit code 1 → lỗi ứng dụng (model file, config).
  Exit code 139 → segfault (thường do thư viện GPU / TensorRT không khớp phần cứng).
- Crash ngay sau update → rollback. Crash sau thời gian dài chạy ổn → xem tài nguyên node.

6. **Khắc phục (cần xác nhận)** – đề xuất một hành động cụ thể và hỏi người dùng:
   - Lỗi nhất thời → `control_runtime(runtime, "restart")`.
   - Runtime bị dừng → `control_runtime(runtime, "start")`.
   Sau khi thực hiện, chờ ~30 giây rồi `get_runtime` để xác nhận `RUNNING`; nếu lại FAILED thì không restart
   lặp lại, báo nguyên nhân và đề xuất sửa cấu hình/rollback.

## Kết luận & trả lời
- Trạng thái hiện tại, thời điểm bắt đầu lỗi, nguyên nhân khả dĩ nhất kèm bằng chứng (message, exit code,
  metric), hành động đề xuất. Nếu chưa đủ dữ liệu, nói rõ cần kiểm tra gì thêm trên máy.

## An toàn
`control_runtime`, `update_deployment` là thao tác ghi: chỉ gọi khi người dùng xác nhận rõ ràng. Không restart
nhiều lần liên tiếp khi runtime crash-loop.
