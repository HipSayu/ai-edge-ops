---
id: skill_fleet_health_report
name: Báo cáo sức khỏe toàn bộ fleet / một cụm
category: monitoring
version: 1.0.0
tools: [list_clusters, list_nodes, list_runtimes, get_latest_telemetry, get_node_events, list_deployments]
summary: >-
  Quy trình tổng hợp báo cáo tình trạng toàn bộ hệ thống edge (fleet) hoặc một cụm cụ thể (nhà máy, kho,
  site, khu vực) đang thế nào: số node
  ONLINE, OFFLINE, DEGRADED, runtime đang chạy và lỗi, deployment thất bại, node quá nhiệt, gần đầy đĩa, FPS
  thấp, sự kiện lỗi gần đây, xếp hạng các vấn đề cần xử lý trước. Dùng khi người dùng hỏi "tình hình hệ
  thống thế nào", "báo cáo tổng quan", "hôm nay có gì bất thường", "cụm Hà Nội có ổn không", "tóm tắt đầu ca".
  Phối hợp list_clusters, list_nodes, list_runtimes, get_latest_telemetry cho từng node, get_node_events và
  list_deployments.
---

# Báo cáo sức khỏe toàn bộ fleet / một cụm

## Khi nào dùng
- "Tổng quan hệ thống", "Báo cáo đầu ca", "Có node nào đang có vấn đề không?", "Cụm kho vận thế nào?"
- Chỉ hỏi về một node → `skill_node_health_diagnosis`.

## Quy trình
1. **Phạm vi** – `list_clusters`; nếu người dùng nêu cụm thì chỉ lấy cụm đó.
2. **Node** – `list_nodes(cluster)` cho mỗi cụm: đếm `ONLINE` / `DEGRADED` / `OFFLINE` / `UNKNOWN`.
   Node `OFFLINE` ghi kèm `last_heartbeat_at` (mất liên lạc bao lâu).
3. **Runtime** – `list_runtimes()` (toàn fleet) hoặc theo node: đếm `RUNNING`, `FAILED`, `RESTARTING`,
   `STOPPED`; liệt kê runtime lỗi kèm node.
4. **Deployment** – `list_deployments()`: deployment `FAILED` hoặc kẹt `IN_PROGRESS`/`PENDING` lâu.
5. **Tài nguyên** – `get_latest_telemetry(node)` cho mỗi node ONLINE/DEGRADED (bỏ qua node OFFLINE, dữ
   liệu cũ). Đánh dấu theo `doc_metrics_thresholds`: nhiệt độ/throttling, `disk_usage_pct`,
   `memory_usage_pct`, `effective_fps_ratio` của từng runtime, `camera_status`.
   Fleet lớn (> 20 node): ưu tiên node DEGRADED và node có runtime lỗi, báo rõ phạm vi đã kiểm tra.
6. **Sự kiện** – `get_node_events(node, limit=20)` cho các node có vấn đề: lỗi ERROR/CRITICAL gần nhất.
7. **Xếp hạng vấn đề**:
   1. Node OFFLINE (mất giám sát PPE hoàn toàn).
   2. Runtime FAILED / crash-loop, camera DISCONNECTED/FROZEN (mất giám sát một khu vực).
   3. CRITICAL tài nguyên (throttling, đĩa ≥ 90 %, RAM ≥ 95 %).
   4. WARNING hiệu năng (FPS ratio < 0.9), deployment FAILED.

## Kết luận & trả lời
1. Một dòng tổng quan: "N cụm, M node: a ONLINE, b DEGRADED, c OFFLINE; r runtime lỗi".
2. Bảng theo cụm (node online/tổng, runtime lỗi, cảnh báo chính).
3. Danh sách vấn đề đã xếp hạng, mỗi mục một dòng kèm số liệu và tài liệu xử lý (runbook/skill).
4. Nếu không có vấn đề: nói rõ và nêu 2-3 chỉ số tiêu biểu.

## An toàn
Quy trình chỉ đọc.
