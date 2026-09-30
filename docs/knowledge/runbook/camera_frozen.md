---
id: runbook_camera_frozen
name: Camera FROZEN / DISCONNECTED - mất hình hoặc đứng hình
category: monitoring
version: 1.0.0
tools: [get_latest_telemetry, get_telemetry_history, get_node_events, control_runtime]
summary: >-
  Runbook xử lý khi camera của một runtime mất hình hoặc đứng hình: camera_status FROZEN hoặc DISCONNECTED,
  camera_fps = 0, camera_frame_age_ms rất cao, camera_freeze_duration_sec tăng, luồng RTSP bị ngắt, camera IP
  mất nguồn hoặc mất mạng, màn hình đen, hình không cập nhật. Khu vực đó không còn được giám sát PPE. Xử lý:
  kiểm tra mạng node, restart runtime để kết nối lại RTSP, nếu không được thì chuyển kiểm tra tại chỗ.
  Dùng khi hỏi "camera mất hình", "camera đứng hình / treo", "mất tín hiệu camera", "RTSP disconnected".
  Phối hợp get_latest_telemetry, get_telemetry_history, get_node_events và control_runtime (restart).
---

# Camera FROZEN / DISCONNECTED - mất hình hoặc đứng hình

## Bước 1 – Xác nhận
`get_latest_telemetry(node)` kind `runtime:<runtime_id>`: `camera_status`, `camera_fps`,
`camera_frame_age_ms` (≥ 10000 = CRITICAL), `camera_freeze_duration_sec`.

## Bước 2 – Phạm vi
- Mọi camera trên node cùng lỗi → mạng của node / switch: xem `system.packet_loss_pct`,
  `network_rtt_ms`, `connection_reconnect_count`.
- Chỉ một camera → camera đó hoặc luồng RTSP của nó.

## Bước 3 – Chập chờn hay liên tục
`get_telemetry_history(node, "runtime", limit=360)` lọc runtime: `camera_status` đổi qua lại nhiều lần →
mạng/camera chập chờn; lỗi liên tục từ một thời điểm → camera tắt / đổi cấu hình / đổi mật khẩu RTSP.
`get_node_events`: sự kiện cùng thời điểm (runtime restart, update config).

## Bước 4 – Khắc phục (cần xác nhận)
1. FROZEN (luồng treo nhưng camera vẫn trong mạng): `control_runtime(runtime, "restart")`; sau ~30 giây
   kiểm tra `camera_status = ONLINE` và `camera_frame_age_ms` < 500.
2. DISCONNECTED sau restart vẫn lỗi → không restart lặp lại. Hướng dẫn tại chỗ:
   - Nguồn / PoE của camera, cáp mạng, đèn tín hiệu.
   - Mở RTSP URL bằng VLC từ cùng mạng để kiểm tra; đối chiếu URL/mật khẩu với `config` của deployment.
   - Camera đổi IP (DHCP) → cập nhật RTSP URL qua `update_deployment`.

## Trả lời
Camera/khu vực đang mất giám sát, từ khi nào, phạm vi, kết quả restart (nếu có), việc cần làm tại chỗ.
