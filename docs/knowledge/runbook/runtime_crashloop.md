---
id: runbook_runtime_crashloop
name: Runtime crash-loop (liên tục khởi động lại)
category: edge_operations
version: 1.0.0
tools: [get_runtime, get_node_events, get_telemetry_history, get_deployment, update_deployment, control_runtime]
summary: >-
  Runbook xử lý runtime AI bị crash-loop: container liên tục crash và khởi động lại, trạng thái nhảy giữa
  RUNNING, RESTARTING và FAILED, runtime_restart_count tăng nhanh, exit code 137 (OOM, hết bộ nhớ), 1 (lỗi
  ứng dụng, thiếu file model, sai config), 139 (segfault, TensorRT / CUDA không khớp). Xác định nguyên nhân
  qua message, sự kiện runtime.status, bộ nhớ runtime_memory_mb so với resource_limits, và thay đổi deployment
  gần nhất; khắc phục bằng tăng giới hạn bộ nhớ, sửa config hoặc rollback. Dùng khi hỏi "runtime cứ restart",
  "container bị crash liên tục", "restart loop", "OOM killed". Phối hợp get_runtime, get_node_events,
  get_telemetry_history, get_deployment, update_deployment.
---

# Runtime crash-loop (liên tục khởi động lại)

Docker tự khởi động lại container bị crash (restart policy `unless-stopped`); agent báo `RESTARTING` khi
container đang tự khởi động lại và `FAILED` khi nó dừng hẳn. Restart thủ công **không** chữa được crash-loop.

## Bước 1 – Xác nhận
`get_runtime(runtime)`: `status` RESTARTING/FAILED, `message` ("exited with code N").
`get_telemetry_history(node, "runtime", limit=120)` lọc runtime: `runtime_restart_count` tăng ≥ 3 trong
10 phút → crash-loop.

## Bước 2 – Phân loại theo exit code
| Exit code | Ý nghĩa | Kiểm tra |
|---|---|---|
| 137 | Bị kill do hết bộ nhớ (OOM) | `runtime_memory_mb` sát `resource_limits.memory`; `memory_usage_pct` node |
| 1 | Ứng dụng lỗi khi khởi động | `model_uri` sai / không tải được, `config` sai (RTSP, tham số) |
| 139 | Segfault | Image build cho GPU/JetPack khác phần cứng node |
| 125-127 | Lỗi lệnh khởi động container | Image hỏng / sai entrypoint |

## Bước 3 – Thay đổi gần nhất
`get_node_events(node, limit=100)`: có `command.update` / `command.deploy` ngay trước khi crash?
`get_deployment(deployment)`: `spec` hiện tại. Crash bắt đầu ngay sau update → nguyên nhân gần như chắc
chắn là phiên bản/config mới.

## Bước 4 – Khắc phục (cần xác nhận)
- Do update gần đây → rollback theo `skill_deployment_update_rollback`.
- OOM → `update_deployment(deployment, resource_limits={"memory": "<lớn hơn>"})` nếu node còn RAM
  (`memory_available_mb`), hoặc giảm độ phân giải/batch trong `config`.
- Config/model sai → `update_deployment` với giá trị đúng.
- Sau khi sửa: theo dõi 5 phút, `runtime_restart_count` không tăng, `status` RUNNING.
- Chưa rõ nguyên nhân: có thể `control_runtime(runtime, "stop")` để dừng vòng lặp, tránh làm nóng/chậm node,
  và chuyển cho kỹ sư xem `docker logs` tại chỗ.

## Trả lời
Số lần restart, exit code và ý nghĩa, thay đổi gần nhất, nguyên nhân khả dĩ, hành động đề xuất.
