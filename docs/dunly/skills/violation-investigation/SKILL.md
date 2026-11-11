---
name: violation-investigation
description: Quy trình điều tra vì sao một camera, khu vực hoặc loại vi phạm có nhiều vi phạm bất thường. Dùng khi user hỏi "tại sao camera X nhiều vi phạm", muốn tìm nguyên nhân, giờ cao điểm hoặc xem bằng chứng. Không dùng khi chỉ hỏi một con số, hoặc khi cần xuất báo cáo (dùng report-writing).
metadata:
  inputs: camera, cụm hoặc loại vi phạm cần điều tra; khoảng thời gian
  output: kết luận ngắn kèm số liệu và ảnh khung hình làm bằng chứng
---

# Điều tra vi phạm

## Cần có
- Đối tượng điều tra (camera, cụm hoặc loại vi phạm) và khoảng thời gian. Thiếu thì hỏi user; mặc định 7 ngày gần nhất.

## Các bước
1. Lấy mức vi phạm của đối tượng so với kỳ liền trước và so với các camera/cụm khác cùng phạm vi, để biết có thực sự bất thường không.
2. Lấy xu hướng theo giờ và theo ngày: tăng đột ngột hay kéo dài, tập trung ở khung giờ nào.
3. Lấy phân rã theo loại vi phạm: một loại chiếm đa số hay đều các loại.
4. Lấy ảnh khung hình của vài sự kiện tiêu biểu (mới nhất và giờ cao điểm) để kiểm tra bằng mắt.
5. Nếu cần căn cứ, dùng search_knowledge tìm điều khoản liên quan đến loại vi phạm chiếm đa số.
6. Tổng hợp theo khung đầu ra.

## Khung đầu ra
- **Kết luận**: một câu, nói rõ chắc chắn đến đâu.
- **Số liệu**: kỳ này và kỳ trước, kèm khoảng thời gian và phạm vi.
- **Mô hình**: giờ cao điểm, loại vi phạm chủ yếu, các camera liên quan.
- **Bằng chứng**: link ảnh khung hình, mô tả điều thấy được trên ảnh.
- **Điều chưa biết**: dữ liệu còn thiếu để xác định nguyên nhân.

## Quy tắc
- Số liệu cho thấy dấu hiệu, không chứng minh nguyên nhân. Chỉ nêu giả thuyết khi có số liệu hoặc ảnh ủng hộ, và gọi đúng là giả thuyết.
- Mô hình có thể nhầm khi bị che khuất hoặc thiếu sáng (xem skill `ppe-classes`); nhiều sự kiện từ cùng một người kéo dài không phải nhiều người vi phạm.
- Không quy lỗi cho cá nhân hay nhóm cụ thể.
- Không có dữ liệu thì nói là không có.
