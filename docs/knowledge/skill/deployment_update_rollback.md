---
id: skill_deployment_update_rollback
name: Cập nhật phiên bản runtime và rollback khi lỗi
category: deployment
version: 1.0.0
tools: [list_deployments, get_deployment, update_deployment, get_runtime, get_latest_telemetry, get_telemetry_history, get_node_events]
summary: >-
  Quy trình cập nhật (update, nâng cấp, đổi phiên bản) một deployment đang chạy trên edge node: đổi
  image_tag, image_uri, model_uri, config (target_fps, ngưỡng), environment hoặc resource_limits; so sánh
  hiệu năng trước và sau (effective_fps_ratio, inference_p95_ms, inference_error_rate, confidence_mean) và
  rollback (quay lại, hoàn tác về phiên bản cũ) nếu phiên bản mới lỗi hoặc kém hơn. Dùng khi người dùng nói
  "nâng model lên v3", "đổi config FPS", "update runtime", "rollback về bản trước", "bản mới chạy tệ hơn".
  Phối hợp get_deployment, update_deployment, get_runtime, get_telemetry_history, get_node_events.
---

# Cập nhật phiên bản runtime và rollback khi lỗi

## Khi nào dùng
- "Cập nhật ppe-detector ở node A lên tag v3", "Tăng target_fps lên 20", "Rollback bản vừa deploy".
- KHÔNG dùng để deploy runtime chưa tồn tại → `skill_safe_deploy`.

## Dữ liệu cần có
tên deployment (= tên runtime, vd `ppe-detector`, kèm `node` nếu nhiều node cùng tên) và các trường cần đổi.
Chỉ các trường được truyền mới thay đổi.

## Quy trình
1. **Chụp trạng thái cũ** – `get_deployment(deployment)`: lưu lại `spec` hiện tại (image_uri, image_tag,
   model_uri, config, environment, resource_limits). **Đây là điểm rollback**; ghi rõ trong câu trả lời.
2. **Baseline hiệu năng** – `get_telemetry_history(node, "runtime", limit=120)` lọc theo runtime:
   trung bình `effective_fps_ratio`, `inference_p95_ms`, `inference_error_rate`, `confidence_mean`.
3. **Xác nhận** – trình bày diff cũ → mới và hỏi người dùng. Lưu ý: update sẽ tạo lại container, runtime
   gián đoạn vài giây đến vài phút (tải image mới).
4. **Cập nhật** – `update_deployment(deployment, <chỉ các trường đổi>)`.
5. **Theo dõi** – `get_deployment` mỗi ~15 giây tới `SUCCEEDED`/`FAILED` (tối đa ~5 phút);
   sau đó `get_runtime` phải `RUNNING`.
6. **So sánh sau 2-5 phút** – lấy lại telemetry runtime, so với baseline theo `doc_metrics_thresholds`:
   - Tốt hơn hoặc tương đương → giữ.
   - `effective_fps_ratio` giảm > 10 %, `inference_p95_ms` tăng > 50 %, `inference_error_rate` ≥ 0.01,
     `confidence_mean` giảm > 15 %, hoặc runtime FAILED/crash-loop → đề xuất rollback.
7. **Rollback (cần xác nhận)** – `update_deployment(deployment, ...)` với đúng các giá trị `spec` cũ
   đã lưu ở bước 1. Theo dõi như bước 5 và xác nhận chỉ số trở lại baseline.

## Kết luận & trả lời
Bảng trước / sau cho các chỉ số chính, kết luận giữ hay rollback, và spec cũ để người dùng có thể quay lại.

## An toàn
`update_deployment` là thao tác ghi. Luôn giữ spec cũ trước khi đổi. Cập nhật từng node một khi áp dụng
cho nhiều node; dừng lại ngay khi node đầu tiên xấu đi.
