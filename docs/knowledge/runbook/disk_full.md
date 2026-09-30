---
id: runbook_disk_full
name: Đầy ổ đĩa trên edge node
category: edge_operations
version: 1.0.0
tools: [get_latest_telemetry, get_telemetry_history, list_runtimes, get_node_events, remove_deployment]
summary: >-
  Runbook xử lý khi ổ đĩa (disk, storage, bộ nhớ lưu trữ, eMMC, SSD) của edge node sắp đầy hoặc đã đầy:
  disk_usage_pct cao, disk_free_gb thấp, inode usage cao (inode_usage_pct, quá nhiều file nhỏ), ghi đĩa chậm (disk_io_wait_pct), khiến tải image
  mới thất bại, runtime không ghi được log / ảnh, container lỗi. Nguyên nhân thường gặp: image Docker cũ,
  log container, file model tải về, ảnh vi phạm lưu cục bộ. Dùng khi hỏi "hết dung lượng", "disk full",
  "đầy ổ cứng", "deploy lỗi no space left on device". Phối hợp get_latest_telemetry, get_telemetry_history,
  list_runtimes, get_node_events và remove_deployment (gỡ runtime không dùng khi được đồng ý).
---

# Đầy ổ đĩa trên edge node

## Bước 1 – Mức độ
`get_latest_telemetry(node)` kind `system`: `disk_usage_pct` (WARNING ≥ 80, CRITICAL ≥ 90),
`disk_free_gb` (< 5 GB là CRITICAL), `inode_usage_pct` (≥ 85: quá nhiều file nhỏ).

## Bước 2 – Tốc độ đầy
`get_telemetry_history(node, "system", limit=720)`: `disk_usage_pct` tăng bao nhiêu trong 1 giờ →
ước lượng thời gian còn lại tới 100 %. Tăng nhanh liên tục → có runtime ghi dữ liệu không giới hạn
(ảnh/video/log).

## Bước 3 – Tác động
`get_node_events(node)`: deployment thất bại với lỗi "no space left on device", runtime FAILED.
`list_runtimes(node)`: runtime `STOPPED` lâu ngày / không còn dùng vẫn giữ image trên đĩa.

## Bước 4 – Giải phóng
Qua assistant (cần xác nhận): gỡ runtime không còn dùng bằng `remove_deployment(deployment)` (xóa
container; image cũ vẫn cần dọn tại chỗ).

Tại chỗ (hướng dẫn người vận hành):
1. `docker system df` xem dung lượng image/container/volume.
2. `docker image prune -a` xóa image không dùng (không xóa image của runtime đang chạy).
3. Giới hạn log Docker (`max-size`, `max-file` trong daemon.json).
4. Dọn thư mục artifact cũ của agent (`/var/lib/edge-agent/artifacts`) cho model không còn deploy.
5. Runtime lưu ảnh cục bộ: cấu hình xoay vòng / đẩy lên cloud.

## Trả lời
Dung lượng hiện tại, tốc độ đầy và thời gian ước tính còn lại, nguyên nhân khả dĩ, việc làm qua assistant và
việc làm tại chỗ.
