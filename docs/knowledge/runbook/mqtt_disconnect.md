---
id: runbook_mqtt_disconnect
name: Mất kết nối MQTT giữa edge và cloud
category: edge_operations
version: 1.0.0
tools: [list_clusters, list_nodes, get_node, get_latest_telemetry, get_telemetry_history, get_node_events]
summary: >-
  Runbook xử lý sự cố kết nối MQTT giữa edge agent và broker trên cloud: nhiều node cùng OFFLINE một lúc,
  node ONLINE/OFFLINE chập chờn (flapping), telemetry đến trễ hoặc gián đoạn, lệnh deploy / restart gửi xuống
  không được thực hiện, connection_reconnect_count tăng, mqtt_publish_latency_ms cao, telemetry_queue_size
  dồn. Phân biệt sự cố phía cloud (broker Mosquitto, cổng 11883) với sự cố mạng của một site. Dùng khi hỏi
  "cả cụm mất kết nối", "node lúc online lúc offline", "lệnh không xuống được node", "dữ liệu bị trễ",
  "MQTT broker lỗi". Phối hợp list_clusters, list_nodes, get_node, get_telemetry_history, get_node_events.
---

# Mất kết nối MQTT giữa edge và cloud

Mọi trao đổi edge ↔ cloud đi qua broker MQTT (cổng 11883 trên cloud): heartbeat/state, telemetry, event,
và lệnh từ cloud xuống. Mất MQTT = node OFFLINE và lệnh không tới được node.

## Bước 1 – Phạm vi
`list_clusters` → `list_nodes(cluster)` cho mọi cụm:
- **Node OFFLINE ở nhiều cụm / nhiều site khác nhau cùng thời điểm** → sự cố phía cloud (broker dừng, cloud
  host mất mạng, tường lửa chặn 11883).
- **Chỉ các node của một site** → mạng / internet của site đó.
- **Một node** → `runbook_node_offline`.

## Bước 2 – Chất lượng kết nối (node còn ONLINE / chập chờn)
`get_telemetry_history(node, "system", limit=360)`: `connection_reconnect_count` tăng (≥ 3 / 10 phút),
`mqtt_publish_latency_ms` ≥ 1000, `telemetry_queue_size` tăng, `packet_loss_pct`, `network_rtt_ms`.
Trạng thái node đổi ONLINE ↔ OFFLINE liên tục (`get_node_events`) → flapping do mạng yếu.

## Bước 3 – Lệnh không được thực hiện
Deployment kẹt `PENDING`/`IN_PROGRESS` trên node vừa mất kết nối: lệnh sẽ không tự gửi lại. Sau khi node
ONLINE lại, kiểm tra `get_deployment`; nếu vẫn kẹt, tạo lại lệnh (update / control) sau khi người dùng xác nhận.

## Hướng dẫn xử lý
Phía cloud (quản trị hệ thống):
1. Container broker `mqtt` trong stack `edgeops-cloud` có chạy không (`docker compose ps`).
2. Cổng 11883 mở trên firewall / security group của cloud host.
3. Log broker (`docker compose logs mqtt`) tìm lỗi kết nối / hết tài nguyên.
Phía site:
1. Internet của site, ping cloud host, `nc -vz <cloud-host> 11883`.
2. Cấu hình `EDGE_MQTT_HOST` / `EDGE_MQTT_PORT` của agent đúng địa chỉ.
Agent tự kết nối lại khi mạng trở lại; không cần khởi động lại node.

## Trả lời
Phạm vi (cloud / site / node), thời điểm bắt đầu, dấu hiệu mạng, lệnh bị ảnh hưởng, việc cần làm và ai làm.
