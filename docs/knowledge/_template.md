---
# Mẫu tài liệu kiến thức cho AI assistant (skill / runbook / doc).
# Chỉ `name` + `summary` được embed để tìm kiếm; phần thân chỉ được đọc khi agent gọi get_document.
# File thiếu `summary` sẽ bị bỏ qua khi ingest. File mẫu này nằm ngoài skill/ runbook/ doc/ nên không được ingest.
# Ingest (từ thư mục app/):
#   python -m apps.assistant.ingest docs/knowledge/skill --kind skill
#   python -m apps.assistant.ingest docs/knowledge/runbook --kind runbook
#   python -m apps.assistant.ingest docs/knowledge/doc --kind doc
id: skill_example_slug            # duy nhất, snake_case, tiền tố theo loại: skill_ / runbook_ / doc_
name: Tên quy trình ngắn gọn       # dùng làm tiêu đề khi trả kết quả tìm kiếm
category: edge_operations         # edge_operations | deployment | monitoring | model_quality | reference
version: 1.0.0
tools: [get_node, get_latest_telemetry, get_node_events]   # tool MCP THẬT mà quy trình phối hợp
# summary: tối đa ~250 token sau khi tách từ (~150 từ). dangvantuan/vietnamese-embedding (PhoBERT) chỉ đọc
#          256 token: phần vượt quá bị cắt và không tìm được. Đưa từ khóa quan trọng nhất lên đầu.
summary: >-
  Một đoạn 3-6 câu, tự đủ nghĩa, để câu hỏi của người dùng khớp được với tài liệu này.
  Nêu: mục đích; khi nào dùng (triệu chứng, câu hỏi điển hình); các đối tượng và metric liên quan
  (tên field thật, ví dụ gpu_temperature_c, effective_fps_ratio); các từ khóa đồng nghĩa tiếng Việt
  và tiếng Anh (quá nhiệt / overheating / throttling); các tool được phối hợp. Không viết chung chung.
---

# Tên quy trình

## Khi nào dùng
- Tình huống / câu hỏi kích hoạt (kèm 2-3 câu hỏi mẫu của người dùng).
- Khi nào KHÔNG dùng và dùng tài liệu nào thay thế.

## Dữ liệu cần có
- Tham số đầu vào (node, runtime, deployment...): tool nhận thẳng tên, mã hoặc id.

## Quy trình
1. Bước → tool gọi (tham số) → đọc field nào → điều kiện rẽ nhánh.
2. ...
Mỗi bước ghi rõ ngưỡng quyết định; ngưỡng chung lấy theo `doc_metrics_thresholds`.

## Kết luận & trả lời
- Mẫu kết luận theo từng nhánh (nguyên nhân khả dĩ, bằng chứng là số liệu cụ thể).

## An toàn
- Tool ghi (create_/update_/remove_/register_/control_) chỉ gọi sau khi người dùng xác nhận rõ ràng.
