---
name: incident
description: Báo cáo một sự kiện vi phạm hoặc cụm sự kiện cụ thể kèm ảnh khung hình, cho bộ phận an toàn lao động. Dùng khi user xin báo cáo về một sự kiện, một camera trong một khoảng giờ, hoặc điều tra một vi phạm. Không dùng cho báo cáo định kỳ.
metadata:
  inputs: mã sự kiện, hoặc camera và khoảng giờ
  output: báo cáo Word (.docx) có link
---

# Báo cáo sự cố

## Cần có
- Mã sự kiện, hoặc camera và khoảng giờ. Thiếu thì hỏi user, không tự đoán sự kiện.

## Các bước
1. Lấy dữ liệu: chi tiết sự kiện (loại, giờ, camera, cụm), ảnh khung hình, các sự kiện cùng camera trong 1 giờ quanh đó, số lần loại vi phạm này lặp lại trong 7 ngày gần nhất.
2. Nếu user muốn đối chiếu quy định, dùng search_knowledge tìm quy định về loại vi phạm này (kèm file và điều khoản).
3. Điền khung dưới đây rồi gọi export_safety_report.

## Khung đầu ra

```
# Báo cáo sự cố: {loại vi phạm}, {camera}, {giờ}

## 1. Mô tả
Điều gì được ghi nhận: loại, giờ, camera, cụm.

## 2. Hình ảnh
Link ảnh khung hình của sự kiện.

## 3. Bối cảnh
Các sự kiện khác cùng camera quanh thời điểm đó; mức lặp lại trong 7 ngày.

## 4. Quy định liên quan
Điều khoản kèm file và mục. Bỏ mục nếu không tra quy định.

## 5. Đề xuất xử lý
Tối đa 3 ý, dựa vào dữ liệu và quy định ở trên.
```

## Quy tắc
- Chỉ mô tả điều mô hình ghi nhận. Không kết luận danh tính hay lỗi của cá nhân.
- Sự kiện không có ảnh thì ghi "Không có ảnh khung hình".
- Nhắc đây là phát hiện tự động, cần người xác nhận trên ảnh trước khi xử lý.
