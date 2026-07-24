# CLAUDE.md — Dự án "Một dữ liệu – Không báo cáo lại" (bản demo dự thi)

> **File này dành cho Claude Code đọc và bám sát khi lập trình.**
> Ngôn ngữ làm việc: **tiếng Việt** (tên biến/hàm bằng tiếng Anh, mọi chuỗi giao diện,
> thông báo, chú thích quan trọng bằng tiếng Việt có dấu).
> Repo dự kiến công khai trên GitHub — tuyệt đối không đưa dữ liệu thật, khóa API,
> thông tin cá nhân vào mã nguồn.

---

## 1. Bối cảnh và mục tiêu

- Đây là **sản phẩm demo** kèm bài dự thi Cuộc thi "Tìm kiếm ý tưởng, giải pháp cải
  cách hành chính tỉnh Thanh Hóa năm 2026" (hạn nộp 31/8/2026), minh họa mô hình
  **"Một dữ liệu – Không báo cáo lại"**: mỗi số liệu chỉ nhập một lần tại nguồn;
  kho dữ liệu dùng chung; báo cáo được máy tạo tự động; lãnh đạo hỏi – đáp trực tiếp
  trên dữ liệu thay vì yêu cầu cấp dưới báo cáo.
- Bối cảnh nghiệp vụ: từ 01/7/2025 Thanh Hóa vận hành chính quyền địa phương 2 cấp,
  166 xã/phường báo cáo trực tiếp các sở, ngành; cùng một số liệu phải nhập nhiều
  biểu, nhiều nơi. Demo phải làm nổi bật việc mô hình cắt được gánh nặng đó.
- **Mục tiêu demo**: chạy ổn định trên **một máy laptop, không cần Internet**
  (chế độ offline), trình diễn được trọn kịch bản 5 phút ở Mục 13, giao diện
  tiếng Việt nghiêm túc, phù hợp môi trường cơ quan nhà nước.
- Người dùng demo: lãnh đạo tỉnh/sở (xem, hỏi đáp), công chức xã (nhập liệu),
  đại biểu HĐND (giám sát), người dân (trang công khai).

## 2. Phạm vi bản demo (v0.1)

Gồm 7 phân hệ, chi tiết ở Mục 8:

1. Đăng nhập, phân quyền 4 vai trò.
2. Nhập liệu tại nguồn (webform cho cấp xã) — "nhập một lần".
3. Dashboard điều hành (tỉnh → xã, 3 lĩnh vực, biểu đồ, xếp hạng).
4. **Máy soạn báo cáo**: sinh file .docx đúng thể thức Nghị định 30/2020/NĐ-CP.
5. **Hỏi – đáp dữ liệu AI** (tiếng Việt, có kiểm soát, 2 chế độ online/offline).
6. Cảnh báo sớm theo ngưỡng.
7. Trang công khai cho người dân (không cần đăng nhập).
8. (Tùy chọn, làm sau cùng) Phân hệ "Kiểm kê báo cáo" — Bản đồ báo cáo.

**Ba lĩnh vực dữ liệu demo**: (a) giải ngân đầu tư công; (b) giải quyết thủ tục
hành chính; (c) an sinh xã hội. Dữ liệu của **15 xã/phường**, các kỳ **tháng
01–07/2026**, toàn bộ là **dữ liệu mô phỏng**.

## 3. Ràng buộc quan trọng (đọc kỹ trước khi code)

- **Offline-first**: mọi tài nguyên front-end (CSS, JS, font, Chart.js…) phải
  **vendored trong `app/static/`**, KHÔNG dùng CDN. Ứng dụng phải chạy đầy đủ
  (trừ chế độ AI online) khi rút mạng.
- **Dữ liệu mô phỏng**: footer mọi trang và mọi file báo cáo sinh ra phải có dòng
  "*Dữ liệu mô phỏng phục vụ trình diễn — không phải số liệu thống kê chính thức*".
- **AI không được bịa số liệu**: trợ lý chỉ được trả lời từ kết quả truy vấn CSDL,
  kèm nguồn và thời điểm cập nhật; nếu không truy vấn được thì nói rõ là không có
  dữ liệu. Chi tiết cơ chế ở 8.5.
- **Bảo mật tối thiểu**: mật khẩu băm (bcrypt/argon2); khóa API chỉ đọc từ `.env`;
  `.env`, `*.db` nằm trong `.gitignore`; không log dữ liệu nhạy cảm.
- Không thêm thư viện ngoài danh sách Mục 4 khi chưa hỏi lại người dùng.
- Mỗi milestone hoàn thành phải chạy được (`uvicorn` lên, `pytest` xanh) rồi mới
  chuyển milestone tiếp theo.

## 4. Công nghệ và thư viện

| Thành phần | Lựa chọn | Ghi chú |
|---|---|---|
| Ngôn ngữ | Python ≥ 3.11 | |
| Web framework | FastAPI + Uvicorn | |
| Giao diện | Jinja2 + HTMX + Chart.js (vendored) | Server-rendered, không cần build step |
| CSDL | SQLite (file `data/onedata.db`) qua SQLAlchemy 2.x | Thiết kế để sau đổi được sang PostgreSQL |
| Sinh .docx | python-docx | Lõi thể thức NĐ30 ở 8.4 |
| Xử lý dữ liệu/seed | pandas, openpyxl | |
| AI (chế độ online) | SDK `anthropic` | Model đặt trong `.env`, ví dụ `claude-sonnet-4-6` |
| Kiểm soát SQL | sqlglot | Parse/validate truy vấn do AI sinh |
| Auth | passlib[bcrypt], itsdangerous (session cookie) | Đơn giản, đủ cho demo |
| Kiểm thử | pytest, httpx | |
| Chất lượng mã | ruff, black | |

## 5. Cấu trúc thư mục

```
onedata-thanhhoa/
├── CLAUDE.md                # file này
├── README.md                # giới thiệu repo (M6)
├── LICENSE                  # MIT
├── .gitignore               # .env, *.db, __pycache__, .venv, outputs/
├── .env.example
├── requirements.txt
├── app/
│   ├── main.py              # FastAPI app, mount router + static
│   ├── config.py            # đọc .env (pydantic-settings)
│   ├── db.py                # engine, session, Base
│   ├── models.py            # SQLAlchemy models (Mục 6)
│   ├── auth.py              # đăng nhập, phân quyền
│   ├── routers/
│   │   ├── dashboard.py
│   │   ├── nhap_lieu.py
│   │   ├── bao_cao.py
│   │   ├── hoi_dap.py
│   │   ├── giam_sat.py      # trang HĐND
│   │   ├── cong_khai.py
│   │   └── kiem_ke.py       # tùy chọn (M6)
│   ├── services/
│   │   ├── nd30.py          # lõi sinh .docx chuẩn NĐ30 (8.4)
│   │   ├── report_builder.py# ghép số liệu vào mẫu báo cáo
│   │   ├── ai_query.py      # text→SQL có kiểm soát + chế độ offline
│   │   ├── canh_bao.py
│   │   └── audit.py         # ghi nhật ký
│   ├── templates/           # Jinja2 (base.html, ...)
│   └── static/              # css, js (htmx.min.js, chart.umd.js), logo
├── data/
│   └── seed/                # file nguồn sinh dữ liệu mẫu
├── scripts/
│   ├── seed.py              # tạo CSDL + dữ liệu mô phỏng
│   └── make_demo_reports.py # sinh sẵn vài báo cáo mẫu ra outputs/
├── outputs/                 # file .docx sinh ra (gitignore)
└── tests/
```

## 6. Mô hình dữ liệu

Bảng chính (SQLAlchemy; tên bảng snake_case):

- `don_vi(id, ma, ten, loai, vung)` — `loai` ∈ {`xa`, `phuong`, `so_nganh`, `tinh`};
  `vung` ∈ {`do_thi`, `dong_bang`, `mien_nui`}.
- `linh_vuc(id, ma, ten)` — 3 bản ghi: `DTC`, `TTHC`, `ASXH`.
- `chi_tieu(id, ma, ten, linh_vuc_id, don_vi_tinh, tan_suat, co_quan_chu_chi_tieu,
  dinh_nghia, cong_khai)` — `tan_suat` ∈ {`thang`, `quy`}; `cong_khai` bool
  (được hiện ở trang công khai hay không).
- `gia_tri_chi_tieu(id, chi_tieu_id, don_vi_id, nam, thang, gia_tri, nguon,
  nguoi_cap_nhat_id, thoi_diem_cap_nhat)` — `nguon` ∈ {`he_thong`, `nhap_tay`};
  ràng buộc UNIQUE(chi_tieu_id, don_vi_id, nam, thang) — đúng tinh thần
  "một số liệu chỉ có một bản ghi".
- `mau_bao_cao(id, ma, ten, linh_vuc_id, mo_ta)` + cấu trúc mẫu đặt trong code
  (`report_builder.py`), không cần bảng JSON phức tạp ở bản demo.
- `nguoi_dung(id, ten_dang_nhap, mat_khau_hash, ho_ten, vai_tro, don_vi_id)` —
  `vai_tro` ∈ {`quan_tri`, `lanh_dao`, `chuyen_vien_xa`, `dai_bieu_hdnd`}.
- `nhat_ky(id, nguoi_dung_id, hanh_dong, chi_tiet, thoi_diem)` — ghi mọi lần
  đăng nhập, nhập/sửa số liệu, sinh báo cáo, câu hỏi AI.
- `nghi_quyet_theo_doi(id, so_ky_hieu, trich_yeu, chi_tieu_id, gia_tri_muc_tieu,
  han_hoan_thanh)` — phục vụ trang giám sát HĐND (demo 3–5 bản ghi).

Tạo thêm **view chỉ đọc** cho AI truy vấn (8.5): `v_so_lieu` (join đủ tên chỉ tiêu,
tên đơn vị, kỳ, giá trị, nguồn, thời điểm cập nhật) và `v_don_vi`, `v_chi_tieu`.

## 7. Danh mục chỉ tiêu và dữ liệu mẫu (seed)

`scripts/seed.py` phải tạo:

**15 đơn vị cấp xã** — dùng tên thật sau sắp xếp theo Nghị quyết
1686/NQ-UBTVQH15, ví dụ: phường Hạc Thành, xã Các Sơn, xã Nga Sơn, xã Tân Thành,
xã Thắng Lộc… (5 tên này đã đối chiếu; **11 tên còn lại lấy placeholder
`Xã Demo 06`…`Xã Demo 15` và ghi TODO để người dùng thay bằng tên thật** — không
tự bịa tên xã). Phân bổ đủ 3 vùng. Thêm 3 `so_nganh`: Sở Tài chính, Sở Nội vụ,
Văn phòng UBND tỉnh; 1 bản ghi `tinh`.

**Chỉ tiêu** (mã gợi ý — có thể tinh chỉnh):

- DTC: `DTC01` kế hoạch vốn giao (triệu đồng, quy ước giao đầu năm);
  `DTC02` giải ngân lũy kế (triệu đồng); `DTC03` tỷ lệ giải ngân (%; tính =
  DTC02/DTC01, lưu sẵn để truy vấn nhanh); `DTC04` số dự án đang triển khai;
  `DTC05` số dự án chậm tiến độ.
- TTHC: `TTHC01` hồ sơ tiếp nhận; `TTHC02` giải quyết đúng hạn; `TTHC03` quá hạn;
  `TTHC04` tỷ lệ đúng hạn (%); `TTHC05` hồ sơ nộp trực tuyến; `TTHC06` tỷ lệ hồ
  sơ trực tuyến (%).
- ASXH: `AS01` số hộ nghèo; `AS02` số hộ cận nghèo; `AS03` đối tượng bảo trợ xã
  hội hưởng trợ cấp; `AS04` kinh phí chi trả tháng (triệu đồng); `AS05` tỷ lệ chi
  trả không dùng tiền mặt (%).

**Giá trị**: sinh ngẫu nhiên có chủ đích cho tháng 01–07/2026, hợp lý về nghiệp vụ
(giải ngân lũy kế tăng dần, không vượt kế hoạch; tỷ lệ 0–100%; quy mô xã đô thị >
miền núi), và **cài sẵn vài "điểm nóng" phục vụ demo**: 2–3 xã tỷ lệ giải ngân
tháng 7 dưới 30%, 1–2 xã tỷ lệ đúng hạn TTHC dưới 90%, 1 xã có số liệu tháng 6
mâu thuẫn nhẹ để demo chức năng cảnh báo. `nguon` trộn `he_thong`/`nhap_tay`;
`thoi_diem_cap_nhat` rải trong tháng.

**Người dùng mẫu** (mật khẩu ghi rõ trong README, chỉ dùng demo):
`lanhdao/Demo@2026`, `xa.hacthanh/Demo@2026` (vai trò chuyên viên xã, gắn
phường Hạc Thành), `daibieu/Demo@2026`, `admin/Demo@2026`.

## 8. Yêu cầu chức năng từng phân hệ

### 8.1 Đăng nhập, phân quyền
- Form đăng nhập tiếng Việt; session cookie ký (itsdangerous); đăng xuất.
- Quyền: `chuyen_vien_xa` chỉ nhập/sửa số liệu của đơn vị mình; `lanh_dao` xem
  toàn bộ + hỏi đáp + sinh báo cáo; `dai_bieu_hdnd` xem toàn bộ + trang giám sát
  (chỉ đọc); `quan_tri` tất cả. Mọi hành động ghi vào `nhat_ky`.

### 8.2 Nhập liệu tại nguồn
- Trang "Nhập số liệu kỳ tháng M/2026": bảng các chỉ tiêu thuộc xã của người dùng,
  ô nào đã có giá trị thì hiển thị kèm thời điểm cập nhật; sửa thì ghi đè + log.
- Kiểm tra dữ liệu: đúng kiểu số, % trong [0;100], cảnh báo nếu giải ngân lũy kế
  giảm so tháng trước (cho phép lưu nhưng gắn cờ).
- Thông điệp chủ đạo hiển thị trên trang: "*Anh/chị chỉ phải nhập MỘT LẦN — mọi
  báo cáo, bảng biểu sẽ được hệ thống tự tổng hợp từ số liệu này.*"

### 8.3 Dashboard điều hành
- Trang tỉnh: thẻ tổng hợp 3 lĩnh vực (kỳ mới nhất), biểu đồ cột xếp hạng tỷ lệ
  giải ngân theo xã, biểu đồ đường diễn biến 7 tháng, bảng "điểm nóng" (từ 8.6).
- Trang chi tiết đơn vị: mọi chỉ tiêu 7 tháng, biểu đồ, nút "Tạo báo cáo" (8.4).
- Bộ lọc kỳ, lĩnh vực, vùng. Mọi con số kèm tooltip: nguồn + thời điểm cập nhật.

### 8.4 Máy soạn báo cáo — lõi thể thức Nghị định 30/2020/NĐ-CP
- `services/nd30.py`: module dựng file .docx đúng thể thức văn bản hành chính.
  **Nếu người dùng đã bổ sung sẵn file `nd30.py` vào repo thì dùng nguyên, không
  viết lại.** Nếu chưa có, tự cài đặt với đặc tả tối thiểu:
  - Khổ A4; phông Times New Roman; cỡ chữ nội dung 14 (cho demo);
    lề trên 20 mm, dưới 20 mm, trái 30 mm, phải 15 mm; giãn dòng ~1,4.
  - Đầu văn bản 2 cột: trái = tên cơ quan chủ quản (in hoa) + tên cơ quan ban
    hành (in hoa, đậm, có đường kẻ ngắn bên dưới) + dòng "Số:  /BC-UBND";
    phải = "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM" (in hoa, đậm) + "Độc lập - Tự do -
    Hạnh phúc" (đậm, có đường kẻ) + dòng địa danh, ngày tháng (nghiêng).
  - Tên loại "BÁO CÁO" in hoa đậm canh giữa; trích yếu đậm, đường kẻ ngắn dưới.
  - Kết thúc: khối "Nơi nhận:" (nghiêng đậm, danh sách cỡ 11) bên trái; khối chữ
    ký bên phải ("TM. ỦY BAN NHÂN DÂN / CHỦ TỊCH" in hoa đậm, họ tên đậm);
    kết thúc phần nội dung bằng "./.".
- `services/report_builder.py`: 2 mẫu báo cáo demo, nhận (đơn vị, kỳ) → lấy số
  liệu từ CSDL → sinh đoạn văn nhận định tự động (câu khuôn mẫu: so sánh kỳ
  trước, xếp hạng trong tỉnh) → xuất .docx vào `outputs/` và trả về link tải:
  1. "Báo cáo tình hình giải ngân vốn đầu tư công tháng M/2026" của UBND xã X.
  2. "Báo cáo kết quả giải quyết thủ tục hành chính tháng M/2026" của UBND xã X.
- Trên dashboard có nút "Tạo báo cáo tháng này cho tất cả 15 xã" → sinh loạt file,
  đo và hiển thị thời gian chạy (phục vụ câu chốt khi demo: "15 báo cáo trong X giây").

### 8.5 Hỏi – đáp dữ liệu AI (trọng tâm demo)
- Ô hỏi tiếng Việt trên dashboard, ví dụ: "Những xã nào giải ngân dưới 30% trong
  tháng 7?", "So sánh tỷ lệ đúng hạn TTHC của phường Hạc Thành 3 tháng gần nhất".
- **Chế độ online** (`OFFLINE=0`, có `ANTHROPIC_API_KEY`):
  1. Gửi cho model: schema các view `v_*` (chỉ view, không bảng gốc) + câu hỏi +
     yêu cầu trả về DUY NHẤT một câu `SELECT`.
  2. Validate bằng sqlglot: chỉ một statement; chỉ `SELECT`; bảng/cột nằm trong
     allowlist (`v_so_lieu`, `v_don_vi`, `v_chi_tieu`); cấm `;`, `ATTACH`,
     `PRAGMA`, subquery ghi; tự thêm `LIMIT 200` nếu thiếu; timeout 5 giây.
  3. Thực thi trên kết nối chỉ đọc; đưa kết quả (bảng) cho model viết 2–4 câu
     trả lời tiếng Việt **chỉ dựa trên bảng kết quả**; giao diện hiển thị: câu
     trả lời + bảng số liệu + câu SQL đã chạy (thu gọn) + nguồn/thời điểm cập nhật.
  4. Nếu validate thất bại hoặc kết quả rỗng: trả lời "Không có dữ liệu phù hợp
     trong Kho" — tuyệt đối không để model tự trả lời từ trí nhớ.
- **Chế độ offline** (`OFFLINE=1` — mặc định cho demo): bộ ~20 câu hỏi mẫu ánh xạ
  sẵn sang SQL (file `data/seed/cau_hoi_mau.json`), so khớp gần đúng (chuẩn hóa
  không dấu + từ khóa); giao diện có dropdown "Câu hỏi gợi ý". Luồng hiển thị
  giống hệt chế độ online để kịch bản demo không đổi.
- Mọi câu hỏi + SQL + số dòng kết quả ghi `nhat_ky`.

### 8.6 Cảnh báo sớm
- `services/canh_bao.py` — luật demo: tỷ lệ giải ngân kỳ mới nhất < 30%; tỷ lệ
  đúng hạn TTHC < 90%; đơn vị chưa nhập đủ số liệu kỳ hiện tại; giải ngân lũy kế
  giảm so kỳ trước (nghi sai số liệu). Hiện thành bảng "Điểm nóng" trên dashboard,
  mỗi dòng ghi rõ đơn vị – chỉ tiêu – giá trị – luật cảnh báo.

### 8.7 Trang công khai
- `/cong-khai`, không đăng nhập: các chỉ tiêu có `cong_khai=true` (tỷ lệ giải
  ngân, tỷ lệ đúng hạn TTHC, tỷ lệ chi trả không tiền mặt) theo xã, kỳ mới nhất,
  kèm biểu đồ; banner "Dân biết – dân giám sát" + dòng dữ liệu mô phỏng.

### 8.8 (Tùy chọn — chỉ làm khi M1–M5 xong) Kiểm kê báo cáo
- Form khai báo: tên báo cáo, cơ quan yêu cầu, tần suất, căn cứ; trang thống kê
  tổng số báo cáo/xã/tháng và danh sách nghi trùng lặp (trùng gần đúng theo tên).

## 9. Kế hoạch thực hiện theo milestone

| MS | Nội dung | Hoàn thành khi (DoD) |
|---|---|---|
| M1 | Khung dự án: cấu trúc thư mục, config, models, `scripts/seed.py`, auth cơ bản | `python scripts/seed.py` tạo DB đầy đủ; đăng nhập được 4 tài khoản; `pytest` xanh |
| M2 | Nhập liệu tại nguồn + nhật ký | Tài khoản xã nhập/sửa được số liệu, ràng buộc UNIQUE hoạt động, log ghi đủ |
| M3 | Dashboard + trang chi tiết + trang công khai + cảnh báo | Biểu đồ chạy offline; bảng điểm nóng đúng với dữ liệu cài sẵn |
| M4 | Máy soạn báo cáo NĐ30 | Sinh 2 mẫu báo cáo .docx đúng thể thức; nút sinh loạt 15 xã kèm đo thời gian |
| M5 | Hỏi – đáp AI: offline trước, online sau | 20 câu mẫu chạy đúng ở chế độ offline; chế độ online qua validator sqlglot; test cho validator (chặn UPDATE/DELETE/bảng ngoài allowlist) |
| M6 | Đóng gói: README (ảnh chụp màn hình, hướng dẫn cài), LICENSE, `make_demo_reports.py`, rà soát demo theo Mục 13, tag `v0.1-demo` | Người mới clone repo làm theo README chạy được demo trong ≤ 10 phút |

Trình tự bắt buộc: làm xong, chạy thử và commit từng milestone rồi mới sang
milestone kế tiếp. Không gộp M4 và M5 vào một commit.

## 10. Kiểm thử và chất lượng

- `pytest`: tối thiểu — seed tạo đủ bản ghi; ràng buộc UNIQUE; phân quyền (xã A
  không sửa được số liệu xã B); validator SQL (các ca tấn công cơ bản); sinh
  báo cáo trả về file .docx mở được (python-docx đọc lại, kiểm tra có chuỗi
  "BÁO CÁO" và "./.").
- `ruff check .` và `black --check .` sạch trước mỗi commit.
- Chạy nhanh: `uvicorn app.main:app --reload` → http://127.0.0.1:8000

## 11. Git, GitHub và quy ước commit

- Repo: `onedata-thanhhoa` (public). Nhánh chính `main`; mỗi milestone một nhánh
  `feat/m1-khung-du-an`… rồi merge.
- Commit message: `feat(m2): nhap lieu tai nguon + nhat ky` (không dấu cho an
  toàn; thân commit có thể tiếng Việt có dấu).
- `.gitignore`: `.env`, `.venv/`, `__pycache__/`, `*.db`, `outputs/`, `.pytest_cache/`.
- LICENSE: MIT, tác giả "Hà Ngọc Sơn".
- README.md gồm: giới thiệu mô hình (3–5 dòng), ảnh chụp màn hình, cài đặt
  (`python -m venv` → `pip install -r requirements.txt` → seed → chạy), tài khoản
  demo, tuyên bố dữ liệu mô phỏng, liên hệ.
- Khi hoàn tất M6: tag `v0.1-demo`. Lệnh đẩy lên GitHub (người dùng tự chạy khi
  sẵn sàng): `gh repo create onedata-thanhhoa --public --source=. --push`
  hoặc `git remote add origin … && git push -u origin main`.

## 12. Biến môi trường — `.env.example`

```
# Chế độ demo không cần mạng: 1 = offline (mặc định), 0 = dùng Claude API
OFFLINE=1
ANTHROPIC_API_KEY=
ANTHROPIC_MODEL=claude-sonnet-4-6
DATABASE_URL=sqlite:///data/onedata.db
SECRET_KEY=doi-chuoi-nay-khi-chay-that
```

## 13. Kịch bản demo 5 phút (mọi chức năng phải phục vụ kịch bản này)

1. Đăng nhập `xa.hacthanh` → nhập 2 số liệu tháng 7 → nhấn mạnh "chỉ nhập một lần".
2. Đăng nhập `lanhdao` → dashboard thấy ngay số vừa nhập; bảng "điểm nóng" nêu
   2 xã giải ngân dưới 30%.
3. Hỏi AI: "Những xã nào giải ngân dưới 30% trong tháng 7?" → câu trả lời + bảng
   + nguồn.
4. Bấm "Tạo báo cáo tháng 7 cho tất cả 15 xã" → mở 1 file .docx cho khán giả xem
   thể thức chuẩn NĐ30 → nêu con số "15 báo cáo trong X giây".
5. Chuyển tài khoản `daibieu` → trang giám sát nghị quyết; mở trang công khai
   không đăng nhập → chốt thông điệp "dân biết – dân giám sát".

## 14. Việc KHÔNG được làm

- Không dùng dữ liệu thật, tên người thật, số liệu thống kê chính thức.
- Không tự bịa tên xã/phường ngoài 5 tên đã nêu — dùng placeholder + TODO.
- Không gọi API AI ở chế độ offline; không để lỗi API làm sập trang.
- Không commit `.env`, file `.db`, file .docx sinh ra.
- Không đổi stack công nghệ, không thêm docker/k8s/microservice — demo một máy.
- Không dùng CDN, không yêu cầu Internet cho bất kỳ trang nào (trừ AI online).
