---
id: doc_metrics_thresholds
name: Bảng ngưỡng metric và ý nghĩa trạng thái
category: reference
version: 1.0.0
tools: [get_latest_telemetry, get_telemetry_history]
summary: >-
  Bảng tra ngưỡng cảnh báo WARNING / CRITICAL của metric telemetry (CPU, RAM, nhiệt độ, GPU, đĩa, mạng,
  effective_fps_ratio, độ trễ inference, camera, confidence) và ý nghĩa các trạng thái NodeStatus,
  RuntimeStatus, DeploymentStatus, CameraStatus (ONLINE, OFFLINE, DEGRADED, FAILED, RESTARTING, FROZEN).
  Dùng khi hỏi một số đo là bình thường hay bất thường, "bao nhiêu độ là quá nhiệt", "FPS bao nhiêu là thấp",
  "trạng thái này nghĩa là gì".
---

# Bảng ngưỡng metric và ý nghĩa trạng thái

Ngưỡng mặc định cho thiết bị Jetson / GPU NVIDIA. Luôn so sánh thêm với **baseline** của chính node đó
(`get_telemetry_history`): một thay đổi đột ngột so với bình thường quan trọng hơn con số tuyệt đối.
Một chỉ số chỉ được kết luận là bất thường khi vượt ngưỡng **liên tục** (≥ 3 mẫu liên tiếp, telemetry gửi
mỗi 5 giây), không dựa vào một mẫu đơn lẻ.

Giới hạn dữ liệu: `get_telemetry_history(node, kind, limit)` trả mẫu mới nhất trước, tối đa 720 mẫu mỗi
kind và chỉ trong **1 giờ gần nhất**. Kind `runtime` trộn mẫu của mọi runtime trên node, cần lọc theo
`runtime_id`. `get_latest_telemetry` trả dict với khóa `system`, `gpu` và `runtime:<runtime_id>`.
Không có dữ liệu cũ hơn 1 giờ: không kết luận về xu hướng theo ngày.

## Telemetry `system` (kind = "system")

| Metric | Bình thường | WARNING | CRITICAL | Ghi chú |
|---|---|---|---|---|
| `cpu_usage_pct` | < 70 | ≥ 85 | ≥ 95 | Kết hợp `cpu_load_1m` so với số core (`cpu_cores` trong get_node) |
| `cpu_iowait_pct` | < 5 | ≥ 15 | ≥ 30 | Cao → nghẽn đĩa, xem `disk_io_wait_pct` |
| `memory_usage_pct` | < 75 | ≥ 85 | ≥ 95 | `memory_growth_rate` > 0 kéo dài → nghi rò rỉ bộ nhớ |
| `swap_usage_pct` | 0–10 | ≥ 20 | ≥ 50 | Jetson swap cao làm inference chậm đột ngột |
| `temperature_c` (SoC) | < 70 | ≥ 80 | ≥ 90 | `temperature_rate` > 1 °C/phút là đang nóng lên nhanh |
| `thermal_throttling` | false | — | true | true = phần cứng đã tự hạ xung, FPS sẽ giảm |
| `power_throttling` | false | — | true | Nguồn không đủ công suất |
| `disk_usage_pct` | < 75 | ≥ 80 | ≥ 90 | Kèm `disk_free_gb` < 5 GB là CRITICAL |
| `inode_usage_pct` | < 70 | ≥ 85 | ≥ 95 | Nhiều file nhỏ (ảnh, log) |
| `packet_loss_pct` | < 0.5 | ≥ 2 | ≥ 10 | |
| `network_rtt_ms` | < 100 | ≥ 200 | ≥ 1000 | |
| `connection_reconnect_count` | tăng chậm | +3 / 10 phút | +10 / 10 phút | Mạng chập chờn tới broker MQTT |
| `mqtt_publish_latency_ms` | < 200 | ≥ 1000 | ≥ 5000 | |

## Telemetry `gpu` (kind = "gpu")

| Metric | Bình thường | WARNING | CRITICAL |
|---|---|---|---|
| `gpu_temperature_c` | < 75 | ≥ 83 | ≥ 90 |
| `gpu_usage_pct` | 30–85 khi đang inference | ≥ 95 liên tục | — |
| `gpu_memory_usage_pct` | < 80 | ≥ 90 | ≥ 97 (nguy cơ OOM) |

`gpu_usage_pct` ≈ 0 trong khi runtime RUNNING và có camera → model có thể đang chạy trên CPU hoặc bị treo.

## Telemetry `runtime` (kind = "runtime")

| Metric | Bình thường | WARNING | CRITICAL | Ghi chú |
|---|---|---|---|---|
| `effective_fps_ratio` (= inference_fps / target_fps) | ≥ 0.95 | < 0.9 | < 0.7 | Chỉ số chính về hiệu năng |
| `inference_p95_ms` | ổn định | +50 % so với baseline | +100 % | So với chính runtime đó |
| `inference_error_rate` | < 0.01 | ≥ 0.01 | ≥ 0.05 | Tỉ lệ 0–1 |
| `inference_timeout_rate` | 0 | ≥ 0.01 | ≥ 0.05 | |
| `runtime_restart_count` | không tăng | +1 / 10 phút | +3 / 10 phút | +3 = crash-loop |
| `runtime_queue_size` | < 5 | ≥ 20 | ≥ 100 | Hàng đợi khung hình dồn → xử lý không kịp |
| `camera_frame_age_ms` | < 500 | ≥ 2000 | ≥ 10000 | Khung hình cũ → camera đứng hình |
| `camera_frame_drop_pct` | < 2 | ≥ 10 | ≥ 30 | |
| `camera_fps` / `camera_target_fps` | ≥ 0.95 | < 0.8 | < 0.5 | |
| `camera_blur_score` | ổn định | −40 % so với baseline | — | Ống kính bẩn, mất nét |
| `camera_brightness` (0–255) | 60–200 | < 40 hoặc > 220 | < 15 hoặc > 245 | Quá tối / chói |
| `confidence_mean` | ổn định | −15 % so với baseline | −30 % | Nghi drift dữ liệu |
| `unknown_detection_rate` | < 0.05 | ≥ 0.1 | ≥ 0.25 | |
| `class_entropy` | ổn định | +30 % so với baseline | — | Phân bố lớp thay đổi |
| `detection_count` | theo cảnh | = 0 kéo dài khi có người | — | Có thể camera lệch góc |

## Trạng thái

**NodeStatus** (`get_node`, `list_nodes`)
- `ONLINE`: heartbeat gần đây, mọi runtime mong muốn đều ổn.
- `DEGRADED`: agent vẫn gửi heartbeat nhưng có runtime `FAILED`/`DEGRADED` đáng lẽ phải chạy.
- `OFFLINE`: không có heartbeat quá 30 giây (hoặc agent tắt không sạch). Mọi telemetry sau đó là cũ.
- `UNKNOWN`: đã đăng ký nhưng agent chưa từng kết nối.

**RuntimeStatus** (`get_runtime`, `list_runtimes`)
- `CREATING` → `STARTING` → `RUNNING`: đang triển khai / đã chạy.
- `RESTARTING`: container đang tự khởi động lại (Docker restart policy), thường do crash lặp lại.
- `FAILED`: container dừng khi lẽ ra phải chạy, hoặc triển khai lỗi; xem `message`.
- `STOPPING` / `STOPPED`: dừng theo yêu cầu. `DEGRADED`: chạy nhưng chất lượng kém.

**DeploymentStatus** (`get_deployment`): `PENDING` → `IN_PROGRESS` → `SUCCEEDED` | `FAILED`;
khi gỡ: `REMOVING` → `REMOVED`. Edge báo kết quả bất đồng bộ, thường trong vài giây đến vài phút (tải image).

**CameraStatus** (trong telemetry runtime): `ONLINE`, `DEGRADED` (drop/blur), `FROZEN` (khung hình không
đổi, `camera_frame_age_ms` cao), `DISCONNECTED` (mất luồng RTSP).
