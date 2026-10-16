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
