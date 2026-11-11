---
name: weekly
description: Báo cáo an toàn PPE theo tuần cho quản lý công trường, có so sánh tuần trước và khuyến nghị. Dùng khi user xin báo cáo tuần, tổng kết 7 ngày, báo cáo định kỳ. Không dùng cho báo cáo ngày hoặc báo cáo sự cố.
metadata:
  inputs: tuần cần báo cáo, phạm vi
  output: báo cáo Word (.docx) có link
---

# Báo cáo tuần

## Cần có
- Tuần cần báo cáo và phạm vi. Mặc định 7 ngày gần nhất, toàn bộ phạm vi user được xem.

## Các bước
1. Lấy dữ liệu: tổng vi phạm 7 ngày và theo loại; cùng chỉ số cho 7 ngày liền trước; xu hướng theo ngày; top 5 camera và top 3 cụm nhiều vi phạm nhất.
2. Điền khung dưới đây rồi gọi export_safety_report.

## Khung đầu ra

```
# Báo cáo an toàn PPE: tuần {từ} – {đến}
Phạm vi: {toàn hệ thống | cụm X}

## 1. Tóm tắt
Tổng vi phạm, tăng hay giảm so với tuần trước (số và %), loại nổi bật nhất. 2–3 câu.

## 2. So với tuần trước
| Loại | Tuần này | Tuần trước | Thay đổi |

## 3. Xu hướng theo ngày
7 ngày; nêu ngày cao nhất và thấp nhất.

## 4. Điểm nóng
| Camera / cụm | Số vi phạm | Loại chính |

## 5. Khuyến nghị
Tối đa 3 ý, mỗi ý dựa vào một số liệu ở trên. Bỏ mục này nếu user không cần.
```

## Quy tắc
- Tuần trước bằng 0: không tính %, ghi "không có kỳ trước để so sánh".
- Khuyến nghị chỉ dựa trên số liệu có trong báo cáo hoặc điều khoản quy định đã tra.
