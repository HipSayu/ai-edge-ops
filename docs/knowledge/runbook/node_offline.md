---
id: runbook_node_offline
name: Node OFFLINE - mất kết nối edge node
category: edge_operations
version: 1.0.0
tools: [get_node, list_nodes, get_node_events, get_telemetry_history, list_runtimes]
summary: >-
  Runbook xử lý khi một edge node chuyển sang OFFLINE: mất heartbeat, mất kết nối tới cloud, thiết bị không
  phản hồi, không gửi telemetry, agent chết, máy bị tắt / mất điện / khởi động lại, mất mạng. Xác định node
  mất liên lạc từ khi nào, trước đó có dấu hiệu gì (nhiệt độ, RAM, mạng chập chờn, reboot), một node hay cả
  cụm cùng mất (sự cố mạng / broker MQTT), và các runtime giám sát PPE nào bị ảnh hưởng. Dùng khi hỏi
  "node X offline", "mất kết nối thiết bị", "không thấy dữ liệu từ node". Phối hợp get_node, list_nodes,
  get_node_events, get_telemetry_history, list_runtimes.
---

# Node OFFLINE - mất kết nối edge node

Node chuyển OFFLINE khi cloud không nhận heartbeat quá 30 giây, hoặc agent ngắt kết nối không sạch
(broker MQTT gửi "last will"). Assistant **không thể** can thiệp phần cứng/mạng; mục tiêu là xác định
phạm vi, nguyên nhân khả dĩ và hướng dẫn người vận hành.

## Bước 1 – Mất từ khi nào
`get_node(node)`: `status`, `last_heartbeat_at`. Tính thời gian đã mất liên lạc.
- < 2 phút: có thể là mạng chập chờn, agent đang khởi động lại; chờ và kiểm tra lại.
- > 10 phút: sự cố thật.

## Bước 2 – Một node hay nhiều node
`list_nodes(cluster)` của cụm chứa node:
- **Nhiều / tất cả node cùng OFFLINE cùng lúc** → sự cố chung: mạng của site, internet, hoặc broker MQTT
  trên cloud (`runbook_mqtt_disconnect`). Không xử lý từng node.
- **Chỉ một node** → sự cố tại thiết bị: tiếp tục bước 3.

## Bước 3 – Dấu hiệu trước khi mất
`get_telemetry_history(node, "system", limit=120)` (dữ liệu chỉ còn trong 1 giờ):
- `temperature_c` tăng dần / `thermal_throttling` → quá nhiệt, thiết bị có thể tự tắt.
- `memory_usage_pct` ≈ 100, `swap_usage_pct` cao → treo máy do hết RAM.
- `packet_loss_pct`, `connection_reconnect_count` tăng → mạng chập chờn.
- `power_throttling` → nguồn yếu.
- Không có dữ liệu → node mất liên lạc hơn 1 giờ; không suy ra được nguyên nhân từ telemetry.
`get_node_events(node, limit=50)`: sự kiện cuối cùng trước khi mất (lỗi runtime, lệnh deploy lớn).

## Bước 4 – Ảnh hưởng
`list_runtimes(node)`: các runtime (camera/khu vực) hiện **không được giám sát PPE**. Trạng thái của chúng
là dữ liệu cũ, không kết luận runtime lỗi.

## Hướng dẫn người vận hành (tại chỗ)
1. Kiểm tra nguồn điện và đèn trạng thái thiết bị; khởi động lại nếu treo.
2. Kiểm tra cáp mạng / Wi-Fi, ping được gateway và cloud (cổng MQTT 11883).
3. Trên máy: `docker ps` xem container `edge-agent` có chạy; `docker logs` agent tìm lỗi kết nối MQTT.
4. Nếu quá nhiệt: kiểm tra quạt, vị trí lắp đặt.
Khi agent kết nối lại, node tự về ONLINE và các runtime được agent nhận lại (không cần deploy lại).

## Trả lời
Thời điểm mất, phạm vi (1 node / cả cụm), dấu hiệu trước đó, runtime/khu vực bị ảnh hưởng, việc cần làm tại chỗ.
