---
name: ppe-classes
description: Các loại vi phạm PPE hệ thống phát hiện và cách đọc số liệu. Dùng khi cần giải thích một loại vi phạm, diễn giải con số, hoặc viết nhận xét về dữ liệu. Không dùng khi chỉ cần lấy số liệu thô hoặc tra cứu quy định.
metadata:
  inputs: loại vi phạm hoặc con số cần giải thích
  output: giải thích ngắn, đúng phạm vi dữ liệu
---

# Các loại vi phạm PPE

## Cần có
- Số liệu hoặc loại vi phạm cần giải thích. Không có thì hỏi lại user đang hỏi về loại nào.

## Các bước
1. Đối chiếu loại vi phạm với bảng dưới để dùng đúng tên gọi tiếng Việt.
2. Diễn giải con số theo mục "Quy tắc".
3. Nếu user hỏi vì sao một loại bị coi là vi phạm, hoặc mức xử lý, chuyển sang tra cứu quy định của khách. Không tự suy diễn.

## Khung đầu ra

| Mã trong hệ thống | Gọi là | Nghĩa |
|---|---|---|
| `no_helmet` | Thiếu mũ bảo hộ | Người trong khung hình không đội mũ bảo hộ |
| `no_vest` | Thiếu áo phản quang | Người trong khung hình không mặc áo phản quang |
| `no_gloves` | Thiếu găng tay | Người trong khung hình không đeo găng tay |
| `no_safety_boots` | Thiếu giày/ủng bảo hộ | Người trong khung hình không đi giày hoặc ủng bảo hộ |

Danh sách này lấy từ mô hình phát hiện đang chạy. Loại nào ngoài bảng thì nói là hệ thống không ghi nhận.

## Quy tắc
- Một vi phạm là một lần mô hình phát hiện trên một khung hình, không phải một người cụ thể và không phải một sự cố đã xác nhận.
- Một người vi phạm kéo dài có thể tạo nhiều sự kiện. Không nói "có N người vi phạm" khi dữ liệu chỉ có số sự kiện.
- Mỗi con số phải kèm khoảng thời gian và phạm vi (camera, cụm) mà nó áp dụng.
- Hệ thống không xếp hạng mức nghiêm trọng giữa các loại. Không tự nói loại nào nặng hơn; nếu user hỏi, dẫn từ tài liệu quy định của khách hoặc nói chưa có căn cứ.
- Mô hình có thể nhầm khi bị che khuất, thiếu sáng hoặc người ở xa. Khi số liệu bất thường, gợi ý xem ảnh khung hình trước khi kết luận.
- Không có vi phạm nào trong kỳ thì nói rõ là không có.
