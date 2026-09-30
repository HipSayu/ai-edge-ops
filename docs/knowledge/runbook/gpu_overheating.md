---
id: runbook_gpu_overheating
name: GPU / SoC quá nhiệt và thermal throttling
category: edge_operations
version: 1.0.0
tools: [get_latest_telemetry, get_telemetry_history, list_runtimes, control_runtime, update_deployment]
summary: >-
  Runbook xử lý khi edge node (Jetson, GPU NVIDIA) quá nhiệt: nhiệt độ GPU cao (gpu_temperature_c),
  nhiệt độ SoC cao (temperature_c),
  cpu_temperature_c tăng nhanh (temperature_rate), thermal_throttling = true (hạ xung, giảm tốc độ), kéo theo
  FPS inference giảm, độ trễ tăng, thiết bị có thể tự tắt. Tìm nguyên nhân: tải GPU quá cao do nhiều runtime,
  target_fps quá lớn, tản nhiệt / quạt / môi trường nóng. Dùng khi hỏi "node nóng quá", "GPU bao nhiêu độ",
  "bị throttling", "nhiệt độ cao", "overheating". Phối hợp get_latest_telemetry, get_telemetry_history
  (gpu, system), list_runtimes, và giảm tải qua update_deployment / control_runtime khi được đồng ý.
---

# GPU / SoC quá nhiệt và thermal throttling

## Bước 1 – Xác nhận
`get_latest_telemetry(node)`: `gpu.gpu_temperature_c`, `system.temperature_c`, `system.cpu_temperature_c`,
`system.thermal_throttling`, `system.power_throttling`. Ngưỡng: GPU WARNING ≥ 83 °C, CRITICAL ≥ 90 °C;
SoC WARNING ≥ 80 °C, CRITICAL ≥ 90 °C; `thermal_throttling = true` luôn là CRITICAL.

## Bước 2 – Xu hướng
`get_telemetry_history(node, "gpu", limit=360)` và `"system"`:
- Nhiệt độ tăng dần cùng `gpu_usage_pct` → quá tải tính toán.
- Nhiệt độ cao dù `gpu_usage_pct` thấp → tản nhiệt kém / môi trường nóng (vấn đề vật lý).
- `temperature_rate` > 1 °C/phút → đang nóng nhanh, cần xử lý ngay.

## Bước 3 – Nguồn tải
`list_runtimes(node)` và telemetry `runtime:<id>` của từng runtime: runtime nào có `inference_fps`/
`target_fps` cao nhất, thời điểm runtime mới được thêm (`get_node_events`, `command.deploy`).

## Bước 4 – Giảm tải (cần xác nhận người dùng)
Theo thứ tự ít gián đoạn nhất:
1. Giảm `target_fps` của runtime nặng nhất qua `update_deployment(deployment, config=...)`
   (ví dụ 30 → 15 FPS; giám sát PPE thường đủ ở 10-15 FPS).
2. Dừng tạm runtime không quan trọng: `control_runtime(runtime, "stop")`.
3. Chuyển bớt runtime sang node khác (`skill_safe_deploy`).
Sau 5-10 phút kiểm tra lại nhiệt độ và `thermal_throttling = false`.

## Hướng dẫn tại chỗ
Kiểm tra quạt, bụi, khe tản nhiệt, vị trí lắp (tránh nắng trực tiếp, tủ kín), chế độ nguồn của Jetson
(`nvpmodel`). Nhiệt cao dù đã giảm tải → cần kỹ thuật viên.

## Trả lời
Nhiệt độ hiện tại / ngưỡng, có throttling không, ảnh hưởng tới FPS, nguyên nhân khả dĩ, đề xuất giảm tải cụ thể.
