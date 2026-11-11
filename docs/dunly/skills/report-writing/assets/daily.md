---
name: daily
description: Báo cáo an toàn PPE theo ngày hoặc ca làm việc cho chỉ huy trưởng và giám sát. Dùng khi user xin báo cáo ngày, ca, hôm nay, hôm qua. Không dùng cho báo cáo tuần hoặc báo cáo một sự cố.
metadata:
  inputs: ngày hoặc ca, phạm vi
  output: báo cáo Word (.docx) có link
---

# Báo cáo ngày

## Cần có
- Ngày hoặc khoảng giờ của ca, và phạm vi. Mặc định 24 giờ gần nhất, toàn bộ phạm vi user được xem.

## Các bước
1. Lấy dữ liệu: tổng vi phạm trong kỳ và theo từng loại; so với 24 giờ liền trước; phân bố theo giờ; top 5 camera nhiều vi phạm nhất; vài sự kiện mới nhất.
2. Điền khung dưới đây rồi gọi export_safety_report.

## Khung đầu ra

```
# Báo cáo an toàn PPE: {ngày / ca}
Phạm vi: {toàn hệ thống | cụm X}. Kỳ: {từ giờ} – {đến giờ}

## 1. Tóm tắt
Tổng vi phạm, tăng hay giảm so với kỳ trước, loại vi phạm nhiều nhất. 2–3 câu.

## 2. Theo loại vi phạm
| Loại | Kỳ này | Kỳ trước |

## 3. Theo giờ
Giờ cao điểm và giờ thấp nhất. Bảng hoặc danh sách.

## 4. Camera cần chú ý
| Camera | Cụm | Số vi phạm | Loại chính |

## 5. Sự kiện gần nhất
Tối đa 5 dòng: giờ, camera, loại.
```

## Quy tắc
- Kỳ không có vi phạm: nói rõ và giữ các mục còn lại, các bảng ghi "Không có dữ liệu".
- Không thêm khuyến nghị nếu user không yêu cầu.
