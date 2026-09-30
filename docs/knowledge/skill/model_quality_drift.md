---
id: skill_model_quality_drift
name: Đánh giá chất lượng model và phát hiện drift
category: model_quality
version: 1.0.0
tools: [list_nodes, list_runtimes, get_runtime, get_latest_telemetry, get_telemetry_history, get_node_events]
summary: >-
  Quy trình đánh giá chất lượng dự đoán của model AI (PPE, phát hiện mũ bảo hộ, áo phản quang, găng tay)
  đang chạy trên edge và phát hiện drift dữ liệu (data drift, model drift) / suy giảm độ chính xác: confidence_mean giảm,
  confidence_std tăng, unknown_detection_rate tăng, class_entropy thay đổi, output_change_rate bất thường,
  detection_count lệch so với bình thường, so sánh giữa các node chạy cùng model. Dùng khi người dùng hỏi
  "model có còn chính xác không", "độ tin cậy giảm", "nhận diện sai nhiều", "có drift không", "có cần
  train lại không". Phối hợp list_runtimes, get_runtime, get_telemetry_history và so sánh nhiều node.
---

# Đánh giá chất lượng model và phát hiện drift

## Khi nào dùng
- "Model PPE ở công trường B còn ổn không?", "Sao nhận diện sai nhiều mấy hôm nay?", "Có nên train lại?"
- Lưu ý: hệ thống không có nhãn thực tế (ground truth) nên chỉ đánh giá **gián tiếp** qua phân bố output;
  kết luận là "nghi drift", không khẳng định độ chính xác.

## Quy trình
1. **Xác định phạm vi** – một runtime (`get_runtime`) hoặc mọi runtime cùng `image_uri`/model trên các node
   (`list_nodes` → `list_runtimes(node)` → lọc theo image/model).
2. **Kiểm tra điều kiện đầu vào trước** – drift giả thường do camera: `get_latest_telemetry` kind runtime:
   `camera_status`, `camera_brightness`, `camera_blur_score`. Camera bất thường → xử lý theo
   `skill_camera_diagnosis` trước, không kết luận drift model.
3. **Chuỗi thời gian** – `get_telemetry_history(node, "runtime", limit=720)` (~1 giờ) cho mỗi runtime:
   tính trung bình đầu kỳ và cuối kỳ của `confidence_mean`, `confidence_std`, `unknown_detection_rate`,
   `class_entropy`, `output_change_rate`, `detection_count`.
4. **Dấu hiệu drift** (theo `doc_metrics_thresholds`):
   - `confidence_mean` giảm ≥ 15 % kèm `confidence_std` tăng → model kém tự tin trên dữ liệu mới.
   - `unknown_detection_rate` ≥ 0.1 → nhiều đối tượng ngoài phân bố huấn luyện.
   - `class_entropy` tăng ≥ 30 % → phân bố lớp thay đổi (đồng phục mới, loại mũ mới, bố cục mới).
   - `output_change_rate` rất cao khi cảnh tĩnh → dự đoán dao động, không ổn định.
5. **So sánh chéo** – cùng model trên node khác bình thường mà node này xấu → nguyên nhân tại chỗ (ánh sáng,
   góc camera, loại PPE riêng của khu vực). Tất cả node cùng xấu đi → drift diện rộng hoặc phiên bản model
   mới kém (kiểm tra `get_node_events` có `command.update` gần đó → `skill_deployment_update_rollback`).
6. **Đề xuất** – thu thập mẫu ảnh từ node bị ảnh hưởng để gán nhãn và huấn luyện lại; tạm thời có thể
   điều chỉnh ngưỡng confidence trong `config`, hoặc rollback nếu do phiên bản mới.

## Kết luận & trả lời
Bảng theo node: confidence_mean (đầu → cuối kỳ), unknown_detection_rate, class_entropy, đánh giá
(ổn định / nghi drift / do camera). Kết luận có mức độ chắc chắn và đề xuất cụ thể.

## An toàn
Quy trình chỉ đọc. Thay đổi ngưỡng hay rollback đi qua `skill_deployment_update_rollback` và cần xác nhận.
