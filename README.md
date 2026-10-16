# ExcelQA · AI26C0069

Giải pháp **hỏi đáp tự động trên bảng tính Excel** bằng ngôn ngữ tự nhiên — Chủ đề 2, Vòng Khu vực Bảng C, Cuộc thi Sáng tạo trẻ Quốc gia về AI 2026.

Đầu vào là một thư mục các tệp `.xlsx` và tệp `queries.json`; đầu ra là tệp `submission.csv` gồm hai cột `id,answer`.

- **Phiên bản:** 2.1.1
- **Ngôn ngữ / thư viện:** Python 3.12, chỉ phụ thuộc `openpyxl` (kèm `et_xmlfile`, `defusedxml`), cài offline từ thư mục `dependency_wheels/` có khóa hash.
- **Mô hình LLM (khi cần):** `qwen/qwen3.7-flash` qua OpenRouter — đúng mô hình thống nhất của BTC.
- **Không chứa** API key, bộ dữ liệu ẩn hay bộ đáp án.

---

## 1. Ý tưởng và đặc điểm chính

Thay vì để LLM “đoán” đáp án từ bảng, ExcelQA tách bài toán thành **hiểu cấu trúc bảng → lập kế hoạch tính toán → thực thi kế hoạch bằng Python trên ô nguồn**. Đáp án luôn được tính lại từ giá trị ô của workbook đang xử lý.

| Đặc điểm | Mô tả |
|---|---|
| **Python trước, LLM sau** | Các dạng câu hỏi đã hỗ trợ được giải trực tiếp bằng bộ chọn (selector) cục bộ: nhanh, miễn phí, tất định. Trong hybrid, chỉ câu chưa giải được cục bộ mới gọi Qwen; offline không gọi API; llm bỏ qua bộ chọn cục bộ. |
| **LLM chỉ trả kế hoạch JSON** | Mô hình không sinh mã, không `exec`/`eval`, không trả đáp án trực tiếp. Kế hoạch dùng một ngôn ngữ biểu thức nhỏ (`sum`, `mean`, `percent_change`, `age_years`, `table`, `argmax`, `rank_labels`, …) và phải có bằng chứng ô nguồn hoặc tên sheet đã xác minh. |
| **Đáp án có bằng chứng ô** | Kế hoạch phải có bằng chứng ô nguồn hoặc metadata sheet đã xác minh. Hằng số phải xuất hiện trong câu hỏi (đối chiếu không phân biệt hoa thường). Bằng chứng này giúp truy vết, không tự chứng minh đã chọn đúng phạm vi. |
| **Đọc được bảng phức tạp** | Nạp nhiều sheet, lưu ô gộp, tọa độ và thụt lề; có selector cho một số mẫu nhiều bảng và tiêu đề phân cấp. Ô thiếu được xử lý theo từng phép chọn, không mặc định bằng 0; chưa hỗ trợ mọi bố cục. |
| **Tự sửa kế hoạch** | Nếu kế hoạch của LLM sai (sai tên sheet, ô trống, biểu thức không hợp lệ), lỗi được phản hồi lại để LLM sửa, tối đa 3 lượt/câu. |
| **Kiểm soát chi phí** | Ngân sách mặc định 0,09 USD/câu (dưới ngưỡng 0,10 USD của đề), tính cả lượt thử lại. Dự trù phí **trước** mỗi request; lỗi không rõ usage vẫn giữ phần dự trù. |
| **Kiểm soát thời gian, bộ nhớ** | Giới hạn thời gian toàn lượt (mặc định 2300 giây, đề cho 40 phút), chia thời gian công bằng theo số câu còn lại; giới hạn không gian địa chỉ 3500 MiB trên Linux. |
| **Đầu ra an toàn** | Với đầu vào hợp lệ, CSV UTF-8 được ghi nguyên tử, mỗi `id` một dòng; câu chưa giải được để **trống** (không ghi `ERROR`). Lỗi đầu vào/cấu hình có thể kết thúc trước khi tạo CSV. Chương trình không lưu thay đổi workbook. |
| **Chạy lại với dữ liệu mới** | Mọi đường dẫn nhận qua tham số dòng lệnh; không gắn cứng thư mục, tên tệp, ID câu hỏi hay đáp án mẫu. |

---

## 2. Luồng xử lý

1. Đọc và kiểm tra `queries.json`, mở workbook theo `file_name`.
2. Trong offline/hybrid, thử tạo kế hoạch bằng các selector cục bộ rồi thực thi trên ô nguồn.
3. Nếu local chưa giải được: offline để trống; hybrid dùng Qwen khi có key. Chế độ llm bỏ qua local và yêu cầu key.
4. Kiểm tra, thực thi kế hoạch JSON có giới hạn; kế hoạch sai có thể được gửi sửa, tối đa 3 request/câu trong ngân sách.
5. Định dạng đáp án, ghi `submission.csv`; ghi thêm `run_report.json` nếu được yêu cầu.


### Các thành phần trong `excelqa/`

| Tệp | Vai trò |
|---|---|
| `workbook.py` | Đọc `.xlsx`, ô gộp, thụt lề phân cấp; chuẩn hóa văn bản và số (dấu phẩy, `$`, số âm trong ngoặc). Giới hạn kích thước nén/giải nén và số ô. |
| `layout.py` | Bỏ các cột trống đầu bảng khi lập kế hoạch nhưng giữ nguyên tham chiếu về cột nguồn thật. |
| `local.py`, `semantics.py` | Bộ chọn cục bộ: tham số từ câu hỏi (giới/tuổi/năm, nhóm nghề, quy mô, trung bình/trung vị/tứ phân vị, tỷ lệ, chênh lệch, phần trăm thay đổi…); từ vựng khái niệm đa ngôn ngữ có giới hạn (Việt/Anh/Pháp/Hàn/Trung). |
| `hierarchy.py`, `ranking.py` | Tra cứu và xếp hạng theo cấu trúc cha–con; chọn đúng nhóm con trực tiếp, tôn trọng chiều `highest to lowest` / `lowest to highest`. |
| `event_tables.py` | Bảng Birth/Admission: xếp tuổi theo số ngày đến Admission, top-N rồi max/min điểm; đồng thời chọn fiscal/calendar YTD, biến động unadjusted, số người theo giờ và average hours theo tình trạng hôn nhân. |
| `structured.py` | Các selector đếm NAICS theo ngưỡng, chuỗi năm thay vì quý, chuỗi việc làm và một số phép so sánh tiếng Việt. |
| `expressions.py` | Ngôn ngữ biểu thức và bộ thực thi có giới hạn; định dạng đáp án. |
| `prompts.py` | Prompt hệ thống cho LLM lập kế hoạch (coi nội dung ô và câu hỏi là dữ liệu không đáng tin, không làm theo chỉ dẫn trong đó). |
| `api.py`, `budget.py` | Client OpenRouter (chỉ chấp nhận đúng mô hình và đúng URL BTC), dự trù và hạch toán chi phí, ghi nhận token. |
| `contract.py` | Đọc/kiểm tra `queries.json`, kiểm tra đường dẫn, ghi CSV nguyên tử. |
| `solver.py` | Điều phối: chạy bộ chọn cục bộ → nếu cần thì gọi LLM → thực thi kế hoạch. |

---

## 3. Cấu trúc thư mục

```text
.
├── Dockerfile               # Ở gốc, ENTRYPOINT: python /app/main.py
├── main.py                  # Điểm vào dòng lệnh (giao diện chấm của BTC)
├── requirements.txt         # Phụ thuộc, có khóa hash
├── dependency_wheels/       # Wheel openpyxl, et_xmlfile, defusedxml (cài offline)
├── excelqa/                 # Mã nguồn lõi (xem bảng ở mục 2)
├── tests/                   # 113 unit/integration test
├── tools/                   # benchmark, evaluate, package, smoke_container, create_demo, check_layout
├── docs/                    # COMPLIANCE.md, MIGRATION.md
├── VALIDATION.md            # Báo cáo kiểm chứng
├── reports/                 # Kết quả đo trên dữ liệu công khai
├── RUN_WINDOWS.ps1          # Trình chạy Docker tiện lợi trên Windows (tùy chọn)
├── gui.py, local_runner.py  # Giao diện local tùy chọn (không nằm trong Docker chấm)
└── excel_qa_openrouter.py   # Tệp giữ lại để tương thích bản cũ (xem docs/MIGRATION.md)
```

---

## 4. Yêu cầu hệ thống

- **Chạy bằng Docker (khuyến nghị, đúng cách BTC chấm):** Docker Engine/Desktop, nền tảng `linux/amd64`, CPU (không cần GPU). Build cần mạng để tải image `python:3.12-slim`; các phụ thuộc Python được cài từ `dependency_wheels/`, không tải từ PyPI.
- **Chạy trực tiếp bằng Python:** Python 3.12.
- **Khi dùng LLM:** truy cập `https://openrouter.ai/api/v1` và một API key hợp lệ (do BTC cung cấp khi chấm).

---

## 5. Hướng dẫn cài đặt và chạy

### 5.1. Chạy bằng Docker (Linux / macOS / WSL)

Chuẩn bị thư mục dữ liệu có đúng cấu trúc:

```text
data/
├── queries.json     # [{"id":1,"file_name":"a.xlsx","query":"..."}, ...]
└── xlsx_files/      # chứa các tệp .xlsx; tên tệp khớp file_name
```

Tạo thư mục đầu ra trước khi bind mount và build image:

```bash
mkdir -p out
docker build --platform linux/amd64 -t excelqa2026:local .
```

**Chế độ offline** (không dùng API, không cần key, chặn mạng trong container):

```bash
docker run --rm --platform linux/amd64 --memory=4g --cpus=4 --network=none \
  --read-only --tmpfs /tmp:rw,size=64m \
  --mount type=bind,source="$PWD/data",target=/input,readonly \
  --mount type=bind,source="$PWD/out",target=/output \
  excelqa2026:local \
  --xlsx-dir /input/xlsx_files \
  --queries /input/queries.json \
  --output /output/submission.csv \
  --solver offline \
  --report /output/run_report.json
```

Ví dụ dùng 4 CPU, phù hợp máy bạn hiện có. Giảm nếu Docker cấp ít hơn; môi trường BTC có 6 vCPU.

**Chế độ hybrid** (mặc định của chương trình khi BTC không truyền `--solver`): Python trước, Qwen cho câu còn lại. Nhập key ẩn trong Bash để không ghi giá trị key trực tiếp vào lịch sử lệnh:

```bash
read -r -s -p "OpenRouter API key: " OPENROUTER_API_KEY
printf '\n'
export OPENROUTER_API_KEY
docker run --rm --platform linux/amd64 --memory=4g --cpus=4 \
  --read-only --tmpfs /tmp:rw,size=64m \
  -e OPENROUTER_API_KEY \
  --mount type=bind,source="$PWD/data",target=/input,readonly \
  --mount type=bind,source="$PWD/out",target=/output \
  excelqa2026:local \
  --xlsx-dir /input/xlsx_files \
  --queries /input/queries.json \
  --output /output/submission.csv \
  --openrouter-model qwen/qwen3.7-flash \
  --openrouter-base-url https://openrouter.ai/api/v1 \
  --report /output/run_report.json
```

Sau khi thử, có thể chạy `unset OPENROUTER_API_KEY`. Biến môi trường không bảo vệ key trước người có quyền truy cập Docker/máy. Khi tự thử, key và phí API thuộc tài khoản của bạn; không giả định BTC thanh toán.

Cũng có thể truyền khóa bằng `--openrouter-key <khóa>` đúng như giao diện chấm của BTC (xem mục 6).

### 5.2. Chạy bằng Docker trên Windows

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\RUN_WINDOWS.ps1 `
  -DataDir "D:\duong\dan\data" -OutputDir "D:\duong\dan\out" -Solver offline -Cpus 4
```

Script tự kiểm tra Docker, build image, chạy container với giới hạn 4 GB RAM, hệ thống tệp chỉ đọc và mount dữ liệu vào ở chế độ `readonly`. Với `-Solver hybrid`, script dùng `OPENROUTER_API_KEY` đang có hoặc hỏi key bằng ô nhập ẩn nếu chưa có. Thêm `-SkipBuild` khi mã nguồn không đổi kể từ lần build trước.

### 5.3. Chạy trực tiếp bằng Python (không Docker)

```bash
python3.12 -m venv .venv
source .venv/bin/activate            # Windows: .\.venv\Scripts\Activate.ps1
pip install --no-index --find-links dependency_wheels --require-hashes -r requirements.txt

python main.py \
  --xlsx-dir data/xlsx_files \
  --queries  data/queries.json \
  --output   out/submission.csv \
  --solver offline \
  --report   out/run_report.json
```

### 5.4. Chạy thử nhanh bằng dữ liệu mẫu tự tạo

```bash
python tools/create_demo.py --out demo_data
python main.py --xlsx-dir demo_data/xlsx_files --queries demo_data/queries.json \
  --output output/submission.csv --solver offline --report output/run_report.json
```

Kết quả mong đợi: tệp `output/submission.csv` có dòng `1,1`.

---

## 6. Giao diện dòng lệnh

### Sáu tham số theo giao diện chấm của BTC

| Tham số | Ý nghĩa |
|---|---|
| `--xlsx-dir` | Thư mục chứa các tệp `.xlsx` |
| `--queries` | Đường dẫn `queries.json` |
| `--output` | Đường dẫn `submission.csv` cần tạo |
| `--openrouter-key` | API key OpenRouter (mặc định đọc từ biến môi trường `OPENROUTER_API_KEY`) |
| `--openrouter-model` | Phải là `qwen/qwen3.7-flash`; giá trị khác bị từ chối |
| `--openrouter-base-url` | Phải là `https://openrouter.ai/api/v1` |

ENTRYPOINT là `python /app/main.py`, chế độ mặc định là **hybrid**. BTC không cần truyền thêm tham số nào khác.

### Tham số tùy chọn

| Tham số | Mặc định | Ý nghĩa |
|---|---|---|
| `--solver` | `hybrid` | `hybrid`: Python trước rồi Qwen; `offline`: chỉ Python, không gọi API; `llm`: buộc dùng Qwen (chỉ để thử nghiệm) |
| `--question-budget` | `0.09` | Ngân sách USD/câu, tối đa 0,10 |
| `--time-limit` | `2300` | Tổng thời gian chạy (giây), tối đa 2350 |
| `--question-timeout` | `110` | Ngân sách thời gian cho bước solver/API mỗi câu; có thể giảm theo thời gian còn lại. Không phải timeout cứng riêng cho toàn bộ bước đọc Excel/local |
| `--max-context-bytes` | `200000` | Kích thước tối đa ngữ cảnh workbook gửi cho LLM (1.000–1.000.000) |
| `--report` | — | Ghi báo cáo JSON; nên đặt ngoài thư mục dữ liệu, không trùng CSV, queries hay workbook đầu vào |

### Định dạng đầu vào và đầu ra

- `queries.json`: danh sách không rỗng; mỗi phần tử có `id` (số hoặc chuỗi, không trùng), `file_name` (tên tệp `.xlsx`) và `query`.
- `submission.csv`: UTF-8, tiêu đề `id,answer`, mỗi `id` đúng một dòng, sắp xếp tăng dần theo giá trị số nếu toàn bộ ID là số hoặc chuỗi chữ số; FAQ quy định bộ chấm dùng ID số tự nhiên; cột `answer` chỉ chứa đáp án cuối cùng, không giải thích.
- `run_report.json` (tùy chọn): số câu, số câu có đáp án, số câu để trống, số lần gọi LLM, token (input, completion, reasoning), chi phí hạch toán, thời gian, RSS tối đa và vết xử lý từng câu.

---

## 7. Đối chiếu yêu cầu của đề

| Yêu cầu | Cách đáp ứng |
|---|---|
| Nhận thư mục `.xlsx` + `queries.json`, xuất `submission.csv` đúng mẫu | `main.py`; `contract.py` kiểm tra đầu vào và xác thực lại CSV sau khi ghi |
| Mỗi `id` đúng một dòng; `answer` chỉ là đáp án | Kiểm tra trùng/thiếu `id`; không ghi giải thích hay thông báo lỗi vào CSV |
| Nộp `.zip` có mã nguồn, cấu hình/phụ thuộc, README | `tools/package.py` tạo `dist/AI26C0069.zip` có `Dockerfile` ở gốc |
| Chạy lại với dữ liệu mới, không phụ thuộc đường dẫn mẫu | Mọi đường dẫn qua tham số; không dùng tên tệp, ID hay đáp án mẫu |
| LLM là Qwen3.7 Flash qua OpenRouter | `api.py` chỉ chấp nhận đúng model ID và URL; key cấu hình bên ngoài, không có trong mã nguồn |
| Chi phí ≤ 0,10 USD/câu, tính cả retry | Ngân sách 0,09 USD/câu; dự trù trước request; giới hạn giá nhà cung cấp trong payload; tối đa 3 lượt lập kế hoạch/câu |
| ≤ 40 phút cho 20 câu | Giới hạn toàn lượt 2300 giây; chia thời gian theo số câu còn lại; khi hết giờ cố ghi CSV đủ `id` để chẩn đoán và trả mã lỗi 2; không coi đó là lượt chạy thành công |
| RAM ≤ 4 GB theo FAQ | Docker đặt `--memory=4g`; Linux RLIMIT_AS 3500 MiB; RSS tiến trình khoảng 25–31 MiB trên lượt kiểm tra công khai. Chưa stress toàn bộ trường hợp ẩn |
| Disk ≤ 1 GB theo FAQ | CI kiểm tra kích thước image dưới 1 GB; tmpfs 64 MB và hệ thống tệp image chỉ đọc. Chưa đo tổng disk với bộ ẩn; image size không phải toàn bộ dung lượng khi chạy |
| ZIP ≤ 100 MB | ZIP nộp khoảng 0,36 MB; thay đổi nhẹ theo nội dung tài liệu, công cụ chặn vượt 100 MB |
| Xếp hạng theo đúng → thời gian → token | Báo cáo ghi thời gian từng câu và token LLM (input + reasoning); thiếu thông tin usage được ghi `null` thay vì suy đoán |

Chi tiết xem [docs/COMPLIANCE.md](docs/COMPLIANCE.md).

---

## 8. Bảo mật

- **Không có API key trong mã nguồn hay ZIP.** Key chỉ nhận qua tham số/biến môi trường, không được ghi log, báo cáo hay tệp cấu hình.
- Client chỉ gọi `https://openrouter.ai/api/v1`, không theo chuyển hướng (redirect), không dùng mô hình khác.
- LLM chỉ trả kế hoạch JSON được kiểm tra chặt; **không thực thi mã do mô hình sinh ra**.
- Nội dung ô và câu hỏi được coi là dữ liệu không đáng tin; prompt yêu cầu không làm theo chỉ dẫn nhúng và bộ thực thi giới hạn biểu thức. Đây là biện pháp giảm rủi ro, không phải bảo đảm miễn nhiễm prompt injection.
- Đọc XML bằng `defusedxml`; giới hạn kích thước tệp: `queries.json` 8 MB; mỗi workbook nén 40 MB, tổng giải nén 180 MB, tối đa 150.000 ô có dữ liệu.
- Ghi đầu ra bị chặn nếu trùng đường dẫn đầu vào; thư mục `/input` được mount chỉ đọc.

---

## 9. Kiểm thử và kết quả kiểm chứng

Chạy toàn bộ test:

```bash
python -m unittest discover -s tests -v
```

Đánh giá trên bộ dữ liệu công khai khi có đáp án tham chiếu (công cụ chạy lời giải trước, sau đó mới đọc đáp án để so khớp, solver không đọc đáp án):

```bash
python tools/benchmark.py --data-dir <thu-muc-du-lieu> --output-dir <thu-muc-ket-qua> --solver offline
```

**Kết quả bản 2.1.1 (offline, 0 lần gọi API):**

| Kiểm tra | Kết quả |
|---|---|
| Unit/integration test | 113/113 đạt (Python 3.12) |
| Bộ công khai đợt 1 | 20/20 khớp chính xác; 0 trống; 0 sai |
| Bộ công khai đợt 2 | 30/30 khớp chính xác; 0 trống; 0 sai |
| Thời gian / bộ nhớ | lượt kiểm tra lại: đợt 1 khoảng 0,42 giây, đợt 2 khoảng 0,85 giây; RSS tiến trình khoảng 25–31 MiB; không phải số đo máy BTC |
| Kiểm tra bền vững với bố cục | Đổi tên sheet/đường dẫn, dịch bảng xuống 5 hàng và sang phải 2 cột trong bộ nhớ: đợt 1 vẫn 20/20, đợt 2 vẫn 30/30; đáp án hỏi tên sheet theo tên mới. Đây là kiểm tra engine trong bộ nhớ, không phải ghi lại XLSX rồi chạy đầu-cuối (`tools/check_layout.py`) |

**Lưu ý trung thực về phạm vi kết quả:**

- Kết quả 100% chỉ áp dụng cho hai bộ công khai hiện có; **không phải cam kết cho bộ kiểm thử ẩn**. Bộ ẩn có thể dùng cách hỏi, cấu trúc bảng hoặc phép tính chưa có bộ chọn hỗ trợ.
- Ở chế độ offline, câu chưa hỗ trợ được để trống. Ở chế độ hybrid, các câu này chuyển sang Qwen và có thể phát sinh chi phí.
- Đánh giá dùng so khớp chuỗi chính xác, không mô phỏng toàn bộ bước chuẩn hóa của BTC.
- Chưa có lượt chạy Qwen thật sau các bản vá 2.0.1–2.1.1. Lượt thử thật gần nhất (bản 2.0.0, 5 câu) cho 3 đúng, 1 sai, 1 trống, tổng chi phí hạch toán khoảng 0,0037 USD; các lỗi đó đã được xử lý bằng bộ chọn cục bộ và kiểm chứng offline.
- Chưa kiểm thử giao diện đồ họa trên Windows. GUI là công cụ tùy chọn, không nằm trong Docker chấm.

Báo cáo chi tiết: [VALIDATION.md](VALIDATION.md), [reports/public_results.json](reports/public_results.json).

---

## 10. Hạn chế đã biết

- Bộ chọn cục bộ phủ một số dạng câu hỏi và bố cục bảng hữu hạn; ngoài phạm vi đó phụ thuộc vào chất lượng kế hoạch của Qwen.
- Hỗ trợ đa ngôn ngữ dựa trên từ vựng khái niệm có giới hạn, không phải hiểu ngôn ngữ tự do.
- Khi cần LLM, ngữ cảnh workbook vượt giới hạn mặc định 200.000 byte bị từ chối thay vì cắt bớt âm thầm; local không chịu giới hạn ngữ cảnh gửi LLM này; chưa có truy xuất ngữ nghĩa cho workbook rất lớn.
- Không có engine tính lại toàn bộ công thức Excel. Ưu tiên giá trị cache và một số tham chiếu công thức đơn giản; công thức thiếu cache/không hỗ trợ có thể khiến câu bị để trống.
- Bộ tính toán bảng giới hạn 3.000 dòng/phép, range tối đa 5.000 ô/phép.
- Nhiều selector từ chối khi không đủ ngữ cảnh, tiêu đề trùng hoặc đồng hạng; chưa thể khẳng định mọi selector đều phát hiện mọi dạng mơ hồ. Khi local không tạo được lời giải hợp lệ, chương trình chuyển cho LLM (hybrid) hoặc để trống (offline).
- Tuổi trong bảng Birth/Admission được tính theo ngày từ ngày sinh đến ngày nhập học của từng người; không dùng ngày hiện tại.
- Phạm vi tính dung lượng đĩa (1 GB) cần BTC xác nhận; image được kiểm tra kích thước bảo thủ trong quy trình CI.

---

## 11. Đóng gói bài nộp

**Không nộp trực tiếp ZIP “Download ZIP” của GitHub:** có thư mục bao ngoài. Gói `submission/AI26C0069.zip` được tạo sẵn có Dockerfile ở gốc; nếu vừa cập nhật tài liệu/mã, chạy lệnh dưới để tạo lại gói mới nhất.

```bash
python tools/package.py --team AI26C0069 --out dist
```

Tạo `dist/AI26C0069.zip` gồm `Dockerfile` ở gốc, mã nguồn, wheel phụ thuộc, README; **không** kèm dữ liệu, kết quả chạy, môi trường ảo, GUI hay poster. Giải nén ZIP sang thư mục mới, build và chạy lại để xác nhận trước khi nộp. Workflow GitHub Actions (`.github/workflows/check.yml`) chạy unit test, smoke test container và đóng gói ZIP.

Kiểm tra container với dữ liệu tổng hợp, không gọi API:

```bash
python tools/smoke_container.py
```

---

## 12. Lịch sử phiên bản (tóm tắt)

| Bản | Nội dung chính |
|---|---|
| 2.1.1 | Bổ sung bộ chọn cho bảng Birth/Admission, YTD, cực đại trị tuyệt đối; 113 test. |
| 2.1.0 | Bộ chọn theo ngữ nghĩa (giới/tuổi/năm, nhóm nghề, quy mô, thống kê), từ vựng đa ngôn ngữ, loại cột trống đầu bảng, từ chối khi mơ hồ. |
| 2.0.1 | Sửa xếp hạng con trực tiếp đúng chiều; tính mức tăng theo nhóm/giới/tuổi/năm; ghi `cost_usd=null` khi request thất bại. |
| 2.0.0 | Kiến trúc kế hoạch JSON + bộ thực thi có giới hạn; client OpenRouter có dự trù ngân sách; Docker và CI. |

Xem thêm: [docs/MIGRATION.md](docs/MIGRATION.md), [UPGRADE_PLAN.md](UPGRADE_PLAN.md).

---

## Khi BTC cung cấp bộ dữ liệu mới

### Tìm và chuẩn bị dữ liệu công khai

Kiểm tra thông báo trên [hệ thống thi](https://ai.tainangviet.vn) và kênh chính thức của BTC để lấy đường dẫn tải. Chưa xác nhận rằng đợt tiếp theo sẽ nằm trong thư mục Drive cũ; luôn dùng đường dẫn BTC thông báo cho đợt đó. Chương trình không tự theo dõi hoặc tải dữ liệu từ Drive.

Tải và giải nén vào một thư mục riêng, giữ nguyên các bộ cũ để đối chiếu. Thư mục truyền cho `-DataDir` phải chứa trực tiếp:

- `queries.json`: danh sách câu hỏi, mỗi câu có `id`, `file_name`, `query`.
- `xlsx_files`: chứa các tệp Excel; tên tệp phải khớp `file_name` trong JSON.

Nếu ZIP có nhiều lớp thư mục, chọn thư mục trong cùng chứa đủ hai mục trên. Không cần chép dữ liệu vào mã nguồn hoặc Docker image. Các tệp đáp án tham chiếu, nếu BTC cung cấp, chỉ phục vụ đánh giá riêng; solver không cần và không đọc chúng để trả lời.

### Chạy thử trên Windows, không phí API

Mở PowerShell trong thư mục dự án hiện tại. Ví dụ:

```powershell
cd "C:\Users\PC\Downloads\AI26C0069"
$dataMoi = Read-Host "Nhap duong dan thu muc du lieu moi"
Test-Path "$dataMoi\queries.json"
Test-Path "$dataMoi\xlsx_files"
```

Khi được hỏi, chỉ nhập đường dẫn thư mục, không nhập thêm câu lệnh. Cả hai kiểm tra phải hiện `True`. Sau đó chạy:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\RUN_WINDOWS.ps1 `
  -DataDir "$dataMoi" `
  -OutputDir "$env:USERPROFILE\Downloads\KetQua_DuLieuMoi" `
  -Solver offline `
  -Cpus 4
```

Chọn thư mục kết quả riêng cho mỗi lượt nếu muốn giữ kết quả cũ. Khi chỉ thay dữ liệu và đã build thành công image từ đúng mã hiện tại, có thể thêm `-SkipBuild`. Nếu vừa cập nhật mã nguồn, phải build lại, không thêm cờ này. Không cần cài lại Docker.

Đọc báo cáo:

```powershell
Get-Content "$env:USERPROFILE\Downloads\KetQua_DuLieuMoi\run_report.json" -Raw -Encoding UTF8 |
  ConvertFrom-Json |
  Select-Object version,questions,solved,unanswered,llm_calls,seconds,peak_rss_mb
```

`llm_calls=0` trong offline; không phí API. `solved` chỉ đếm câu có đáp án, không xác nhận đáp án đúng. Nếu có đáp án chuẩn đi kèm, dùng công cụ đánh giá riêng như hướng dẫn bên dưới. Nếu chưa có đáp án chuẩn, cần kiểm tra lại bằng Excel trước khi kết luận độ chính xác.

### Dữ liệu ẩn khi chấm

Bộ ẩn thuộc môi trường chấm của BTC. Bài nộp nhận đường dẫn qua `--xlsx-dir`, `--queries` và ghi kết quả theo `--output`; không gắn cứng thư mục trên máy đội thi. Không đóng gói bộ dữ liệu ẩn hoặc bộ đáp án vào bài nộp. Các tham số OpenRouter vẫn được tiếp nhận theo giao diện chấm đã mô tả trong README.

### Giới hạn cần hiểu đúng

Bản 2.1.1 đã đối chiếu đúng 20/20 đợt 1 và 30/30 đợt 2 offline. Bộ mới có thể dùng cách hỏi, cấu trúc bảng hoặc phép tính chưa được selector hỗ trợ; không thể suy ra chắc chắn đúng 100% bộ mới. Offline để trống câu chưa hỗ trợ. Hybrid có thể chuyển câu chưa hỗ trợ sang đúng mô hình Qwen qua OpenRouter, có thể phát sinh phí; không tự chuyển sang Gemini hoặc mô hình khác. Không cần huấn luyện lại chỉ để đổi thư mục dữ liệu.

