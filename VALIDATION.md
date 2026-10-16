# Kiểm chứng bản 2.1.0 — ngữ nghĩa và phạm vi bảng

- 103/103 unit/integration tests đạt trong môi trường Python 3.12 sạch, thư viện khóa hash.
- Public 2: 30/30 exact match, 0 trống, 0 sai; offline, 0 request API.
- Public 1: 14/20 exact match, 6 trống, 0 đáp án sai không rỗng; không giảm so với bản trước.
- Kiểm tra biến đổi trên đối tượng workbook trong bộ nhớ: đổi tên sheet, thay Book.path, dịch dữ liệu/merged ranges xuống 5 hàng và sang phải 2 cột. Public 2 vẫn 30/30; câu hỏi tên sheet trả theo tên mới. Không phải lượt serialize lại XLSX hoặc chấm API.
- 26 test mới không dựa số liệu/ID/filename công khai: nhóm/năm/nhãn mới; số liệu mới; vị trí hàng/cột mới; quartile thiếu; tổng gây nhiễu; số phần trăm đã báo cáo; từ vựng Pháp/Hàn/Trung/Việt; cách hỏi equivalent; xếp hạng bằng nhau từ chối.
- Test có fail trước sửa cho chức năng mới và phép chọn sai phạm vi; sau sửa các test cũ vẫn đạt.
- Selector mới có phạm vi ngôn ngữ/layout hữu hạn. 100% public 2 không phải 100% public 1, không bảo đảm tập ẩn hoặc mọi cách diễn đạt.
- Bản này chưa chạy Qwen thật. Giữ hybrid để hỗ trợ câu mới, đúng mô hình BTC; không có bảng tra đáp án runtime.
- Xem workflow của commit mới để xác nhận Docker; bản trước đã build/run thành công trên GitHub Actions.

## Kiểm chứng lịch sử

# Kiểm chứng bản 2.0.1 — sửa từ log API người dùng

- 77/77 unit/integration tests đạt.
- Public 1 offline: 14/20 đúng, 6 trống, không đáp án sai không rỗng.
- Public 2 offline: 19/30 đúng, 11 trống, không đáp án sai không rỗng.
- Hai dạng được bổ sung: xếp hạng con trực tiếp đúng chiều; mức tăng theo nhóm/giới/tuổi/năm. Test dùng tên nhóm, số liệu, năm khác công khai và có nhóm gây nhiễu.
- Giữ last_plan và tọa độ ô lỗi cho việc sửa kế hoạch; không kết luận nguyên nhân chính xác của kế hoạch câu 10 cũ vì log chưa có plan đó.
- Người dùng đối chiếu API thật ở bản 2.0.0: 3/5 đúng (11,12,13), 1 sai thứ tự (5), 1 trống (10), 8 request. Tổng mức hạch toán từ log: 0.003665027 USD. Đây là bằng chứng người dùng cung cấp, không phải lượt API tôi tự chạy.
- Chưa chạy lại API thật ở 2.0.1. Hai câu lỗi đã được kiểm chứng offline; không cần gọi API cho hai câu đó trong hybrid.
- Docker 2.0.0 đã build/run thành công trên Actions sau bản sửa quyền CSV; xem workflow mới cho bản vá này.

## Kiểm chứng lịch sử 2.0.0

# Kiểm chứng bản 2.0.0 — 17/10/2026

Môi trường sạch Python 3.12, cài offline từ ba wheel đã khóa hash. Không dùng API key thật.

| Kiểm tra | Kết quả |
|---|---|
| Unit/integration | 73 test đạt |
| Public 1 offline | 14/20 đúng; 6 rỗng; 0 đáp án sai không rỗng |
| Public 2 offline | 17/30 đúng; 13 rỗng; 0 đáp án sai không rỗng |
| Hai câu của ZIP gốc | Đều đúng trong lượt public 2, tính từ workbook |
| API thật | Chưa chạy; không dùng khóa hardcode của ZIP gốc |
| API HTTP giả lập | Nhận sáu tham số; không thay đổi input; không in key |
| GUI command builder | Offline loại key kế thừa; hybrid chỉ truyền key qua env; chặn output trong input |
| Giao diện Tkinter trên Windows | Chưa chạy tương tác; đã kiểm tra cú pháp và logic điều phối |
| Poster/ảnh GUI | Đã xem ảnh render; GUI preview được ghi rõ là minh họa |
| Docker trong môi trường tạo bản | Không có Docker; có workflow build/run smoke để kiểm tra sau push |

Test mới dùng số liệu/năm/vị trí/tên sheet khác dữ liệu công khai cho: tiền tệ, điều kiện chọn nhãn từ câu hỏi, cộng doanh thu nhiều sheet, lấy sheet có giá trị lớn nhất, nhóm trẻ em và tiêu đề nhiều tầng, tỷ lệ số cuối năm so với bình quân, chênh lệch cột relative importance, phần trăm thay đổi đã báo cáo, total fair value. Test workbook dài xác nhận không cắt tại 80 dòng.

Số đo offline public 1 khoảng 0.32 giây/23.75 MiB RSS; public 2 khoảng 0.69 giây/30.11 MiB RSS. Không dùng số này làm thời gian/RAM dự đoán cho Qwen thật hoặc mọi bộ ẩn. Báo cáo chi tiết tóm tắt ở reports/public_results.json; không đưa đáp án tham chiếu vào runtime.

Đánh giá exact-string, không mô phỏng đầy đủ chuẩn hóa BTC. Còn câu chưa hỗ trợ và giới hạn context/dòng/phép tính, xem README. Chưa thể khẳng định toàn bộ giới hạn tài nguyên/chi phí trên mọi dữ liệu hoặc điểm tập ẩn.
