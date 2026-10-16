# Đối chiếu yêu cầu BTC

Căn cứ: đề Chủ đề 2; Hướng dẫn nộp bài Vòng Khu vực Bảng C; Giải đáp thắc mắc của BTC đã được người dùng cung cấp. Không tự thay đổi quy định theo tài liệu của nền tảng API.

| Yêu cầu | Cách thực hiện | Trạng thái kiểm chứng |
|---|---|---|
| ZIP <=100 MB, Dockerfile gốc | package allowlist + manifest SHA256 | Kiểm tra ZIP tự động |
| Linux amd64 CPU | build --platform linux/amd64; không GPU | Có workflow Docker, cần xem kết quả thực tế |
| Sáu tham số | argparse main.py, ENTRYPOINT | Test tích hợp API HTTP giả lập |
| Không API key trong source | env/CLI, không lưu/in key | Quét source/ZIP; không dùng khóa ZIP cũ |
| Chỉ Qwen BTC | exact model và URL validation | Unit test từ chối mô hình khác |
| Không sửa /input | kiểm tra đường dẫn + mount readonly | Byte comparison trong integration test |
| CSV UTF8 đủ ID | output atomic; số ID tăng dần; không ghi ERROR | Test CSV/ID |
| Chưa giải được để rỗng | SolveError giữ empty | Test FAQ |
| RAM <=4 GB | Docker --memory=4g, Linux RLIMIT_AS 3500 MiB | Đo RSS offline public; chưa stress tất cả đầu vào |
| Disk <=1 GB | image size smoke check, tmpfs64MB, source nhẹ | Cần xem CI và làm rõ phạm vi tính disk |
| 40 phút/20 câu | 2300 giây + guard, chia thời gian theo câu | Offline đã đo; API thật chưa đo |
| 0.10 USD/câu gồm retries | cap nội bộ0.09; preflight và max_price | Test giả lập; chưa đo phí thật |
| Internet install/OpenRouter | runtime chỉ client OpenRouter; không GUI trong image | Static inspection + mock |
| Input + reasoning tokens | trường riêng, unknown nếu thiếu | Unit test |
| Công cụ AI phát triển | GUI không thêm AI/runtime khác | Phù hợp FAQ7 theo tài liệu đã cung cấp |

Không có khẳng định “đáp ứng toàn bộ” khi chưa có lượt chạy API thật và Docker/CI thành công. Public data đúng nhiều câu là chỉ báo phát triển; không bảo đảm điểm tập ẩn. Không cần đạt 100% public để cấu trúc bài nộp hợp lệ; độ đúng ảnh hưởng thứ hạng.
