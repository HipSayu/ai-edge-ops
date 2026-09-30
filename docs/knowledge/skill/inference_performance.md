---
id: skill_inference_performance
name: Phân tích hiệu năng inference (FPS, độ trễ)
category: monitoring
version: 1.0.0
tools: [get_runtime, get_node, get_latest_telemetry, get_telemetry_history, list_runtimes, get_node_events]
summary: >-
  Quy trình phân tích vì sao một runtime AI chạy chậm: FPS thấp, không đạt target_fps, effective_fps_ratio
  giảm, độ trễ inference cao (inference_latency_ms, inference_p95_ms, p99), hàng đợi runtime_queue_size tăng,
  timeout. Tìm nút thắt ở GPU (gpu_usage_pct, gpu_memory_usage_pct, gpu_temperature_c, thermal throttling),
  CPU, RAM/swap, nhiều runtime tranh tài nguyên, hay camera cấp khung hình chậm (camera_fps). Dùng khi người
  dùng hỏi "model chạy chậm", "FPS giảm", "độ trễ cao", "lag", "không đủ realtime". Phối hợp get_runtime,
  get_latest_telemetry, get_telemetry_history (runtime, gpu, system), list_runtimes, get_node_events.
---

# Phân tích hiệu năng inference (FPS, độ trễ)

## Khi nào dùng
- "Runtime ở cổng chính chỉ được 8 FPS", "Độ trễ inference tăng gấp đôi", "Có đạt realtime không?"
- KHÔNG dùng khi runtime FAILED/không chạy → `skill_runtime_troubleshooting`.

## Quy trình
1. **Xác định runtime và mục tiêu** – `get_runtime(runtime)`: `node`, `config.target_fps`.
2. **Hiện tại** – `get_latest_telemetry(node)`, kind `runtime:<runtime_id>`: `inference_fps`,
   `target_fps`, `effective_fps_ratio`, `inference_p50_ms`, `inference_p95_ms`, `runtime_queue_size`,
   `camera_fps`, `camera_target_fps`. Đối chiếu `doc_metrics_thresholds`.
3. **Từ lúc nào** – `get_telemetry_history(node, "runtime", limit=360)` (~30 phút): xác định thời điểm
   FPS bắt đầu giảm; giảm đột ngột (sự kiện) hay giảm dần (nhiệt, rò rỉ bộ nhớ).
4. **Tìm nút thắt** – theo thứ tự:
   - **Nguồn khung hình**: `camera_fps` < `camera_target_fps` → camera cấp chậm, inference không phải
     nguyên nhân (`skill_camera_diagnosis`).
   - **GPU**: `get_telemetry_history(node, "gpu", limit=360)`.
     `gpu_usage_pct` ≥ 95 liên tục → GPU bão hòa. `gpu_temperature_c` ≥ 83 hoặc `thermal_throttling` →
     hạ xung (`runbook_gpu_overheating`). `gpu_memory_usage_pct` ≥ 90 → thiếu VRAM.
     `gpu_usage_pct` ≈ 0 → model chạy trên CPU (sai image/không có GPU trong `resource_limits.gpus`).
   - **CPU / RAM**: `get_telemetry_history(node, "system", limit=360)`: `cpu_usage_pct` ≥ 90
     (tiền xử lý, giải mã video), `swap_usage_pct` ≥ 20 (thiếu RAM).
   - **Tranh chấp**: `list_runtimes(node)` – nhiều runtime cùng dùng GPU; so thời điểm FPS giảm với lúc
     runtime khác được deploy (`get_node_events`: `command.deploy`).
5. **Đề xuất** theo nút thắt: giảm `target_fps`/độ phân giải qua `config`, dùng model nhẹ hơn / TensorRT,
   chuyển bớt runtime sang node khác, xử lý nhiệt. Các thay đổi cấu hình đi theo
   `skill_deployment_update_rollback`.

## Kết luận & trả lời
Nêu: FPS hiện tại / mục tiêu, thời điểm bắt đầu giảm, nút thắt chính kèm số liệu, đề xuất theo thứ tự ưu tiên.

## An toàn
Quy trình chỉ đọc; mọi thay đổi cấu hình phải được người dùng xác nhận.
