---
name: site-setup
description: Quy trình thêm hoặc thay đổi công trường (cụm), node và camera. Dùng khi user muốn tạo cụm, thêm node, thêm hoặc sửa hoặc xóa camera. Không dùng khi chỉ xem danh sách hoặc trạng thái.
metadata:
  inputs: thay đổi mong muốn (tạo, sửa, xóa) và đối tượng, cùng tên và thông tin cần thiết
  output: các thay đổi chờ user duyệt, rồi xác nhận kết quả
---

# Thiết lập công trường

## Cần có
- Việc cần làm, đối tượng và tên. Thiếu tên hoặc thiếu nơi đặt (cụm nào, node nào) thì hỏi user, không tự đặt.

## Các bước
1. Xem trạng thái hiện tại bằng các tool đọc dữ liệu: cụm, node, camera đã có, và số camera mỗi node đang dùng so với giới hạn.
2. Kiểm tra trước khi đề xuất: tên có trùng không, đối tượng cha có tồn tại không, node còn chỗ cho camera không. Nếu vướng, báo user và dừng.
3. Làm theo thứ tự cụm, rồi node, rồi camera. Mỗi bước chỉ làm khi bước trước đã được duyệt và hoàn tất.
4. Mỗi thay đổi dữ liệu chỉ được đề xuất, user phải duyệt trong chat. Sau khi đề xuất, nói đang chờ duyệt, không nói đã xong.
5. Sau khi user duyệt, kiểm tra lại bằng cách xem danh sách và báo kết quả thực tế.

## Khung đầu ra
- Danh sách thay đổi đã đề xuất, mỗi dòng: việc, đối tượng, nơi đặt.
- Trạng thái từng việc: chờ duyệt, đã làm, bị từ chối hoặc lỗi.
- Việc còn lại và bước tiếp theo.

## Quy tắc
- Xóa node kéo theo xóa mọi camera của nó; nói rõ điều này trong đề xuất. Xóa không xóa file video đã lưu.
- Người dùng không có quyền thì thay đổi bị từ chối khi chạy; báo thẳng rằng họ không được phép, không thử cách khác.
- Không tự thêm thay đổi ngoài yêu cầu.
