# Thay đổi so với excel_qa.zip đã kiểm tra

Bản ZIP cũ thiếu requirements.txt, Dockerfile trong thư mục bọc, hardcode đường dẫn/key, tách sai tiêu đề, cắt dữ liệu còn 80 dòng và chỉ gửi preview 6 dòng. Kết quả lưu sẵn hai câu đều khác đáp án BTC.

Bản 2.0 dùng lại nền lõi ExcelQA trước đây của cùng dự án, thay cơ chế sinh/chạy Python bằng kế hoạch JSON có kiểm tra tham chiếu ô. Không sao chép key, file đáp án, output hay data công khai từ ZIP vào repo. Không có lệnh eval/exec của nội dung mô hình trong runtime.

Thêm phép điều kiện để chọn nhãn đã có nguyên văn trong câu hỏi và phép lấy tên sheet từ metadata; kết quả vẫn cần bằng chứng dữ liệu. Thêm xử lý nhóm hoạt động theo header cha/con, chênh lệch chỉ số, so sánh số tiền và tổng doanh thu giữa các sheet. Các quy tắc nhận diện dựa câu hỏi/header, không dựa ID hoặc tên file.

GUI local và hình giới thiệu không thuộc bài chấm. GUI không đòi hỏi mô hình thứ hai hoặc nền tảng ngoài OpenRouter.
