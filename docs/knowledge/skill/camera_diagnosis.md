---
id: skill_camera_diagnosis
name: Chẩn đoán chất lượng và kết nối camera
category: monitoring
version: 1.0.0
tools: [list_runtimes, get_runtime, get_latest_telemetry, get_telemetry_history, get_node_events, control_runtime]
summary: >-
  Quy trình chẩn đoán camera IP / luồng RTSP cấp hình cho runtime AI: camera mất kết nối (DISCONNECTED),
  đứng hình (FROZEN, camera_frame_age_ms cao), rớt khung (camera_frame_drop_pct), FPS camera thấp, ảnh mờ
  (camera_blur_score), quá tối hoặc chói (camera_brightness), bị che hoặc lệch góc (detection_count = 0 kéo
  dài). Dùng khi người dùng hỏi "camera có hình không", "camera bị đơ / mất tín hiệu / mờ / tối", "không phát
  hiện được người". Phối hợp list_runtimes, get_latest_telemetry, get_telemetry_history (runtime),
  get_node_events và control_runtime (restart để kết nối lại RTSP khi người dùng đồng ý).
---

# Chẩn đoán chất lượng và kết nối camera

## Khi nào dùng
- "Camera cổng chính không có hình", "Hình bị đứng", "Camera mờ nên không nhận diện được mũ bảo hộ".
- Mỗi runtime xử lý camera của mình; telemetry camera nằm trong telemetry `runtime`.

## Quy trình
1. **Tìm runtime của camera** – `list_runtimes(node)`; runtime có `config` chứa camera/RTSP tương ứng.
2. **Trạng thái hiện tại** – `get_latest_telemetry(node)`, kind `runtime:<runtime_id>`: `camera_status`,
   `camera_fps`, `camera_target_fps`, `camera_frame_age_ms`, `camera_frame_drop_pct`,
   `camera_freeze_duration_sec`, `camera_blur_score`, `camera_brightness`, `detection_count`.
   Không có telemetry runtime → runtime không chạy → `skill_runtime_troubleshooting`.
3. **Phân nhánh theo triệu chứng** (ngưỡng theo `doc_metrics_thresholds`):
   - `DISCONNECTED` hoặc `camera_fps` = 0 → mất luồng: mạng tới camera, camera mất nguồn, sai RTSP URL/mật
     khẩu. Xem `get_telemetry_history(..., "system")`: `packet_loss_pct` cao → mạng. Theo `runbook_camera_frozen`.
   - `FROZEN` / `camera_frame_age_ms` ≥ 2000 → luồng treo; thường khắc phục được bằng restart runtime.
   - `camera_frame_drop_pct` ≥ 10 → băng thông mạng hoặc giải mã quá tải (`cpu_usage_pct` cao).
   - `camera_blur_score` giảm ≥ 40 % so với baseline → ống kính bẩn/mất nét: cần người ra hiện trường.
   - `camera_brightness` < 40 hoặc > 220 → thiếu sáng / ngược sáng: kiểm tra đèn, chế độ ngày-đêm camera.
   - Chỉ số ảnh bình thường nhưng `detection_count` = 0 kéo dài trong ca làm việc → camera có thể bị lệch
     góc / bị che.
4. **Xu hướng và thời điểm** – `get_telemetry_history(node, "runtime", limit=360)` để biết lỗi liên tục
   hay chập chờn; `get_node_events` tìm sự kiện `runtime.status` cùng thời điểm.
5. **Khắc phục (cần xác nhận)** – với FROZEN/DISCONNECTED: đề xuất `control_runtime(runtime, "restart")`
   để mở lại luồng RTSP; sau ~30 giây kiểm tra `camera_status` = ONLINE. Nếu vẫn lỗi → vấn đề ở camera/mạng
   vật lý, đề xuất kiểm tra tại chỗ.

## Kết luận & trả lời
Trạng thái camera, triệu chứng kèm số liệu, nguyên nhân khả dĩ (phần mềm / mạng / vật lý), hành động đề xuất
và ai cần làm (assistant restart được / cần kỹ thuật viên).

## An toàn
Restart runtime làm gián đoạn giám sát PPE của camera đó vài giây: phải hỏi người dùng trước.
