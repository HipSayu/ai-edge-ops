---
name: compliance
description: Báo cáo đối chiếu vi phạm PPE với tài liệu quy định mà khách cung cấp, có trích dẫn file và điều khoản. Dùng khi user hỏi mức độ tuân thủ, vi phạm trái điều khoản nào, hoặc cần báo cáo cho kiểm tra an toàn. Không dùng cho báo cáo số liệu thuần.
metadata:
  inputs: kỳ, phạm vi, quy định cần đối chiếu (nếu có)
  output: báo cáo Word (.docx) có link
---

# Báo cáo tuân thủ quy định

## Cần có
- Kỳ và phạm vi. Mặc định 7 ngày gần nhất.
- Hệ thống phải có tài liệu quy định của khách. Không có thì dừng và nói với user, không dùng kiến thức bên ngoài.

## Các bước
1. Lấy dữ liệu: tổng vi phạm theo loại trong kỳ và phạm vi.
2. Với từng loại có vi phạm, dùng search_knowledge tìm điều khoản liên quan, kèm file và mục.
3. Điền khung dưới đây rồi gọi export_safety_report.

## Khung đầu ra

```
# Báo cáo tuân thủ quy định: {kỳ}
Phạm vi: {toàn hệ thống | cụm X}

## 1. Tóm tắt
Số loại vi phạm, loại nhiều nhất, số điều khoản liên quan.

## 2. Đối chiếu
| Loại vi phạm | Số lần | Điều khoản | Nguồn (file, mục) |

## 3. Loại không tìm thấy quy định
Loại có vi phạm nhưng tài liệu không đề cập. Ghi rõ là chưa có căn cứ.

## 4. Đề xuất
Tối đa 3 ý, mỗi ý gắn với một điều khoản đã trích.
```

## Quy tắc
- Chỉ trích điều khoản mà search_knowledge trả về, nguyên văn và kèm nguồn. Không diễn giải rộng hơn.
- Không tự nói mức phạt hay trách nhiệm pháp lý nếu tài liệu không nêu.
