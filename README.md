# ExcelQA · AI26C0069

Giải pháp hỏi đáp Excel cho Vòng Khu vực Bảng C, Cuộc thi Sáng tạo trẻ Quốc gia về AI 2026.

**Bản 2.0.0**: đọc nhiều sheet và ô gộp, bảo toàn tọa độ ô/tiêu đề, tính bằng Python trước; câu chưa hỗ trợ dùng đúng `qwen/qwen3.7-flash` qua OpenRouter. Mô hình trả kế hoạch JSON, không sinh mã để `exec`. Không chứa API key hoặc bộ đáp án.

**Kết quả thực đo, offline**: public 1 đúng 14/20, 6 rỗng; public 2 đúng 17/30, 13 rỗng; 0 đáp án sai không rỗng trong cả hai lượt. 72 test đạt. Không diễn giải kết quả này thành chất lượng Qwen hoặc điểm bộ ẩn. Xem [VALIDATION.md](VALIDATION.md).

## Chạy nhanh trên Windows, không phát sinh phí API

Giải nén source vào `G:\BC\AI2026\AI26C0069-main`. Nếu chọn vị trí khác, thay đường dẫn tương ứng. Giữ nguyên Docker/Python đã cài; không cần pandas, OpenAI SDK hay Node.

```powershell
cd "G:\BC\AI2026\AI26C0069-main"
```

Nếu dữ liệu BTC của bạn ở `G:\BC\AI2026\Publicdata2`, kiểm tra:

```powershell
Test-Path "G:\BC\AI2026\Publicdata2\queries.json"
Test-Path "G:\BC\AI2026\Publicdata2\xlsx_files"
```

Cả hai phải True. Chạy Docker:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\RUN_WINDOWS.ps1 -DataDir "G:\BC\AI2026\Publicdata2" -OutputDir "G:\BC\AI2026\KetQua_AI26C0069" -Solver offline -Cpus 4
```

Không hỏi API key; container offline bị chặn mạng. Script kiểm tra số CPU; tối đa 6, RAM 4 GB. Build ban đầu có thể tải base image, không gọi API AI. Sửa mã xong phải build lại; các lần thử không thay mã có thể thêm `-SkipBuild`.

Đọc báo cáo:

```powershell
Get-Content "G:\BC\AI2026\KetQua_AI26C0069\run_report.json" -Raw -Encoding UTF8 | ConvertFrom-Json | Select-Object version,questions,solved,unanswered,llm_calls,seconds,peak_rss_mb
```

`solved` là số câu có đáp án, chưa phải số đúng. `llm_calls=0` khi offline. Đáp án chưa có để rỗng theo FAQ, không ghi ERROR vào CSV.

## Chạy bằng Python và giao diện local

Dùng Python 3.12 đã cài:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --no-index --find-links dependency_wheels --require-hashes -r requirements.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Nếu đã có `.venv` đúng Python và thư viện thì không cần tạo lại.

Mở giao diện:

```powershell
.\.venv\Scripts\python.exe gui.py
```

1. Chọn thư mục có `queries.json` và `xlsx_files`.
2. Chọn thư mục kết quả ở ngoài dữ liệu.
3. Giữ chế độ `offline` để không gọi API.
4. Nhấn **Chạy bộ câu hỏi**. Xem tiến độ, nhật ký, bảng kết quả.
5. Chỉ khi muốn thử API được phép sử dụng mới chọn `hybrid`, nhập key vào ô ẩn hoặc cấp qua biến môi trường. Key không được lưu vào source/tệp cấu hình; giao diện không đưa key vào argv.

GUI là công cụ local tùy chọn, không chạy trong Docker chấm và không được đưa vào ZIP nộp do công cụ package tạo. Windows Python bản đầy đủ thường có Tkinter; trên Linux thiếu Tkinter chỉ ảnh hưởng GUI, không ảnh hưởng CLI/Docker.

Giao diện đã có mã thực thi; hình trong `assets/gui_preview.png` là **bản minh họa**, không phải ảnh chụp lượt chạy GUI trên Windows. [Poster](assets/poster.png) / [SVG chỉnh sửa](assets/poster.svg).

Thử dữ liệu tự tạo nếu chưa có public data:

```powershell
.\.venv\Scripts\python.exe tools\create_demo.py --out demo_data
.\.venv\Scripts\python.exe main.py --xlsx-dir demo_data\xlsx_files --queries demo_data\queries.json --output output\submission.csv --solver offline --report output\run_report.json
```

## Thử Qwen thật với chi phí được kiểm soát

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\RUN_WINDOWS.ps1 -DataDir "G:\BC\AI2026\Publicdata2" -OutputDir "G:\BC\AI2026\KetQua_Hybrid" -Solver hybrid -Cpus 4
```

Nhập khóa khi script hỏi (ẩn). **Hybrid có thể phát sinh phí.** Không có cơ chế “Qwen miễn phí” trong sản phẩm này. Không đổi sang mô hình khác hoặc `openrouter/free` trong bản thi. Google AI Studio/Gemini/Antigravity chỉ dùng hỗ trợ phát triển, không phải API runtime.

Thử ít câu cần LLM trước khi chạy toàn bộ. Mỗi câu dự trù tối đa 0.09 USD, bao gồm các lần thử lại, dưới mức đề 0.10 USD. Client kiểm tra metadata giá, giới hạn giá provider và `max_tokens`, dự trù phí trước khi gửi; thất bại không rõ usage được giữ dự trù thay vì xem bằng 0. Tối đa 3 lượt lập kế hoạch/câu; giới hạn toàn lượt mặc định 2300 giây. Không đồng nghĩa đảm bảo dịch vụ ngoài luôn trả lời đúng hạn/đúng đáp án.

402: kiểm tra quyền sử dụng/hạn mức/credit của khóa; không lặp chạy cả bộ hoặc tự đổi mô hình. 401: khóa không hợp lệ. Key BTC cung cấp khi chấm được truyền qua tham số; bài nộp không mang key cá nhân.

**Lượt Qwen thật chưa được kiểm chứng trong môi trường tạo bản này.** Không dùng khóa đã lộ trong ZIP cũ; nếu còn hoạt động, thu hồi và cấp lại.

## Đánh giá public data

```powershell
.\.venv\Scripts\python.exe tools\benchmark.py --data-dir "G:\BC\AI2026\Publicdata2" --output-dir "G:\BC\AI2026\DanhGia_AI26C0069" --solver offline
```

Công cụ chạy lời giải trước rồi đọc `answers.json` để đánh giá bên ngoài. Bản giải bài không đọc file đáp án. Nếu không có answers.json, công cụ dùng sample_submission.csv: chỉ có ý nghĩa khi tệp đó thực sự chứa đáp án tham chiếu. Exit 1 ở công cụ đánh giá là có câu khác đáp án; không phải mặc định lỗi thực thi. Đối chiếu chuỗi chính xác, không mô phỏng toàn bộ chuẩn hóa BTC.

## Đóng gói bài nộp

```powershell
.\.venv\Scripts\python.exe tools\package.py --team AI26C0069 --out dist
```

Tệp `dist\AI26C0069.zip` có Dockerfile ở gốc, không kèm GUI, poster, dữ liệu, kết quả hay môi trường ảo. Tên đội đang lấy từ kho do người dùng chỉ định; kiểm tra lại đúng tên/mã đội trên hệ thống trước khi nộp. Giải nén ZIP sang thư mục mới và build/chạy lại chính thư mục đó.

### Giao diện chấm BTC

```text
--xlsx-dir /input/xlsx_files
--queries /input/queries.json
--output /output/submission.csv
--openrouter-key <key BTC cung cấp>
--openrouter-model qwen/qwen3.7-flash
--openrouter-base-url https://openrouter.ai/api/v1
```

ENTRYPOINT là `python /app/main.py`; mặc định **hybrid** khi BTC chấm. Windows launcher mặc định **offline** chỉ phục vụ thử local. Không bắt buộc BTC mở GUI hoặc truyền cờ ngoài sáu cờ trên.

Build Linux amd64:

```powershell
docker build --platform linux/amd64 -t ai26c0069:local .
```

Kiểm tra Docker với dữ liệu tổng hợp, không gọi API:

```powershell
.\.venv\Scripts\python.exe tools\smoke_container.py
```

Workflow GitHub Actions thực hiện unit test, build Linux amd64, chạy container không mạng với đủ sáu cờ và tạo ZIP. Đọc trạng thái Actions; không mặc định push thành công là test thành công.

## Giới hạn và tuân thủ

- Không giới hạn cứng 2/20/30 câu; đọc danh sách JSON, xử lý tuần tự trong ngân sách thời gian. Mỗi câu một workbook có thể nhiều sheet; cùng workbook liên tiếp được tái dùng bộ nhớ.
- Giới hạn bảo vệ: queries 8 MB; mỗi workbook nén 40 MB, tổng giải nén 180 MB, tối đa 150.000 ô có dữ liệu, mỗi sheet tối đa 1.000.000 ô trong khung kích thước. Đây là giới hạn ứng dụng, không phải số liệu BTC hứa cấp.
- Không cắt còn 80 dòng/6 dòng preview. Context đầy đủ đến 200 KB mặc định; vượt giới hạn thì từ chối thay vì âm thầm bỏ dữ liệu. Có tùy chọn đến 1 MB, vẫn phải giữ ngân sách token/thời gian. Chưa triển khai truy xuất ngữ nghĩa để xử lý workbook vượt context.
- Bộ tính table tối đa 3.000 dòng/phép, range tối đa 5.000 ô/phép, biểu thức giới hạn độ sâu/nút. Không tuyên bố xử lý mọi workbook lớn.
- UTF-8 CSV `id,answer`, ID số tăng dần, đủ ID, không giải thích trong cột answer. Dữ liệu input chỉ đọc.
- RAM container 4 GB; main giới hạn không gian địa chỉ Linux 3500 MiB. Disk 1 GB theo FAQ: workflow kiểm tra bảo thủ kích thước image và tmpfs 64 MB; phạm vi tính disk chưa rõ cần xác nhận BTC. Không tuyên bố đã chứng minh mọi tập đầu vào nằm trong giới hạn.
- Thời gian đề 40 phút/20 câu. Build/install ngoài thời gian chạy; runtime chỉ dùng OpenRouter nếu cần.
- Token BTC: input + reasoning, không thay reasoning bằng completion. Thiếu usage ghi unknown.

Xem [docs/COMPLIANCE.md](docs/COMPLIANCE.md), [docs/MIGRATION.md](docs/MIGRATION.md) và [VALIDATION.md](VALIDATION.md).
