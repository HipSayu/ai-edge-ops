---
name: report-writing
description: Cách viết báo cáo an toàn PPE theo từng loại (ngày, tuần, sự cố, tuân thủ quy định). Dùng khi user xin báo cáo, tổng kết hoặc tài liệu có cấu trúc để gửi người khác. Không dùng khi user chỉ hỏi một con số hay một câu hỏi nhanh.
metadata:
  inputs: loại báo cáo, kỳ thời gian, phạm vi (toàn hệ thống hoặc một cụm)
  output: báo cáo Word (.docx) có link
---

# Viết báo cáo

## Cần có
- Loại báo cáo, kỳ thời gian và phạm vi. Thiếu cái nào thì hỏi user trước khi lấy dữ liệu.
- Kỳ mặc định khi user không nói: ngày = 24 giờ gần nhất, tuần = 7 ngày gần nhất. Nói rõ mặc định này trong báo cáo.

## Các bước
1. Chọn đúng một template theo bảng dưới. Chỉ cần đọc header của các template để chọn, rồi đọc đầy đủ template đã chọn.
2. Lấy dữ liệu theo mục "Các bước" của template: dùng các tool dữ liệu (và search_knowledge nếu template cần quy định).
3. Viết báo cáo theo cấu trúc template, chỉ dùng số liệu đã lấy, rồi gọi export_safety_report đúng một lần với toàn văn.
4. Trả link báo cáo cho user.

## Khung đầu ra

| Template | Dùng khi |
|---|---|
| `assets/daily.md` | báo cáo ngày hoặc ca làm việc |
| `assets/weekly.md` | báo cáo tuần, tổng kết định kỳ |
| `assets/incident.md` | một sự kiện hoặc cụm sự kiện cụ thể |
| `assets/compliance.md` | đối chiếu vi phạm với quy định của khách |

Loại báo cáo chưa có template (tháng, theo khu vực, tình trạng hệ thống): nói với user là chưa có mẫu, đề nghị dùng template gần nhất và nêu rõ chỗ khác.

## Quy tắc
- Chỉ dùng số mà dữ liệu trả về. Thiếu thì ghi "Không có dữ liệu", không ước lượng.
- Mọi con số kèm kỳ và phạm vi. Dùng tên gọi tiếng Việt của các loại vi phạm (xem skill `ppe-classes`).
- Báo cáo viết bằng tiếng Việt, markdown: `##` cho mục, bảng `| a | b |`, danh sách `- `.
- Kỳ trước bằng 0 thì không tính phần trăm, ghi "không có kỳ trước để so sánh".
