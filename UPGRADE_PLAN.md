# Hướng cải tiến tiếp theo

1. Chạy Qwen thật trên một câu còn trống bằng key có quyền dùng; xác nhận kế hoạch, evidence, phí và thời gian.
2. Đối chiếu 13 câu public2 offline chưa giải, phân biệt chưa chọn đúng vùng/thiếu phép tính/format.
3. Bổ sung chỉ mục header cha-con, độ thụt dòng và phân nhóm tổng/con, kiểm thử số liệu và vị trí thay đổi.
4. Truy xuất vùng theo câu hỏi cho workbook vượt context; không âm thầm cắt dữ liệu.
5. Kiểm thử các ngôn ngữ khác và công thức thiếu cache. Không dùng mô hình ngoài BTC trong runtime.
6. Giữ nhánh bảo thủ: câu mơ hồ để rỗng hoặc chuyển đúng Qwen; không trả lời sẵn theo ID.

Tối ưu phí bằng tăng phép tính local và tái dùng workbook, không thay Qwen bằng mô hình free không được BTC cho phép. GUI/poster không nằm trong luồng chấm.
