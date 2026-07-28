# CLAUDE.md — Dự án "Một dữ liệu – Không báo cáo lại" (bản demo dự thi, v0.2)

> **File này dành cho Claude Code đọc và bám sát khi lập trình.**
> Ngôn ngữ làm việc: **tiếng Việt** (tên biến/hàm bằng tiếng Anh; mọi chuỗi giao diện,
> thông báo, chú thích quan trọng bằng tiếng Việt có dấu).
> Repo dự kiến công khai trên GitHub — tuyệt đối không đưa dữ liệu thật, khóa API,
> thông tin cá nhân vào mã nguồn.
>
> **v0.2 thay đổi lớn so với v0.1**: Kho dữ liệu nay có **hai lớp** (văn bản – tri thức
> số; chỉ tiêu có cấu trúc) và **ba kênh thu nhận**, trong đó kênh trọng tâm để trình
> diễn là **"máy trích xuất – người xác nhận"**: dữ liệu hình thành từ chính văn bản,
> báo cáo điện tử được xử lý hằng ngày, thay vì bắt công chức gõ lại vào biểu mẫu.

---

## 1. Bối cảnh và mục tiêu

- Đây là **sản phẩm demo** kèm bài dự thi Cuộc thi "Tìm kiếm ý tưởng, giải pháp cải
  cách hành chính tỉnh Thanh Hóa năm 2026" (hạn nộp 31/8/2026), minh họa mô hình
  **"Một dữ liệu – Không báo cáo lại"**.
- **Nguyên tắc nghiệp vụ cốt lõi** (phải hiện rõ trên giao diện): *"Mỗi số liệu chỉ
  được thu nhận một lần từ nguồn chính thống — hệ thống nghiệp vụ, văn bản điện tử
  đã ban hành hoặc nhập tại nguồn; số liệu đã có trong Kho thì không cơ quan nào được
  yêu cầu báo cáo lại."* "Một lần" không có nghĩa là gõ tay một lần, mà là dữ liệu vào
  Kho một lần từ đúng nguồn.
- Bối cảnh: từ 01/7/2025 Thanh Hóa vận hành chính quyền hai cấp, 166 xã/phường báo cáo
  trực tiếp các sở, ngành qua nhiều kênh (chính quyền, Đảng, Mặt trận). Demo phải làm
  bật việc mô hình cắt gánh nặng đó **mà không tạo thêm thao tác mới cho cấp xã**.
- **Mục tiêu demo**: chạy ổn định trên **một laptop, không cần Internet** (chế độ
  offline), trình diễn trọn kịch bản 6 phút ở Mục 13, giao diện tiếng Việt nghiêm túc,
  phù hợp môi trường cơ quan nhà nước.
- Vai trò người dùng: lãnh đạo tỉnh/sở (xem, hỏi đáp), công chức xã (phát hành văn
  bản, xác nhận số liệu máy trích), đại biểu HĐND (giám sát), người dân (trang công khai).

## 2. Kiến trúc mà phần mềm phải thể hiện

```
        NGUỒN CHÍNH THỐNG                    KHO DỮ LIỆU (2 lớp)            KHAI THÁC
┌────────────────────────────┐        ┌──────────────────────────┐   ┌──────────────────┐
│ Kênh 1: hệ thống nghiệp vụ │──API──▶│ LỚP 2 — CHỈ TIÊU         │──▶│ Dashboard        │
│ (dịch vụ công, tài chính…) │        │ có cấu trúc              │   │ Máy soạn báo cáo │
├────────────────────────────┤        │ (số liệu + nguồn + kỳ)   │   │ Cảnh báo sớm     │
│ Kênh 2: VĂN BẢN ĐIỆN TỬ    │        └──────────▲───────────────┘   │ Giám sát HĐND    │
│ (TD Office) → máy trích    │─trích─▶ (vùng chờ) │ người xác nhận    │ Trang công khai  │
│   xuất – người xác nhận    │───────▶┌──────────┴───────────────┐   │ HỎI–ĐÁP AI       │
├────────────────────────────┤ lưu    │ LỚP 1 — VĂN BẢN,         │──▶│  xuyên hai lớp   │
│ Kênh 3: nhập tại nguồn     │───────▶│ TRI THỨC SỐ (toàn văn)   │   └──────────────────┘
│ (chỉ phần còn thiếu)       │        └──────────────────────────┘
└────────────────────────────┘
```

Điểm phải đúng khi lập trình: **mỗi giá trị chỉ tiêu trong Lớp 2 luôn mang thông tin
nguồn** (`he_thong` | `van_ban` | `nhap_tay`); nếu nguồn là `van_ban` thì phải có
liên kết về đúng văn bản gốc ở Lớp 1 và người đã xác nhận.

## 3. Phạm vi bản demo (v0.2)

1. Đăng nhập, phân quyền 4 vai trò.
2. **Lớp 1 — Kho văn bản, tri thức số**: tiếp nhận/tải lên văn bản, lưu toàn văn +
   siêu dữ liệu, tìm kiếm (từ khóa + ngữ nghĩa đơn giản).
3. **Kênh 2 — Máy trích xuất & màn hình xác nhận** (điểm nhấn mới, phải trau chuốt nhất).
4. **Kênh 3 — Nhập tại nguồn**: chỉ cho chỉ tiêu chưa có ở kênh 1, kênh 2.
5. Dashboard điều hành (tỉnh → xã, 3 lĩnh vực, biểu đồ, điểm nóng).
6. Máy soạn báo cáo: sinh .docx đúng thể thức Nghị định 30/2020/NĐ-CP.
7. **Hỏi – đáp AI xuyên hai lớp** (số liệu / văn bản / câu hỏi lai).
8. Cảnh báo sớm theo ngưỡng.
9. Trang công khai cho người dân (không cần đăng nhập).
10. (Tùy chọn, sau cùng) Kiểm kê báo cáo — "Bản đồ báo cáo".

**Ba lĩnh vực dữ liệu demo**: (a) giải ngân đầu tư công; (b) giải quyết thủ tục hành
chính; (c) an sinh xã hội. Dữ liệu **15 xã/phường**, kỳ **tháng 01–07/2026**, toàn bộ
là **dữ liệu mô phỏng**.

## 4. Ràng buộc quan trọng (đọc kỹ trước khi code)

- **Offline-first**: mọi tài nguyên front-end (CSS, JS, font, Chart.js…) **vendored
  trong `app/static/`**, KHÔNG dùng CDN. Ứng dụng chạy đầy đủ khi rút mạng (trừ chế
  độ AI online).
- **Dữ liệu mô phỏng**: footer mọi trang và mọi file sinh ra phải có dòng
  "*Dữ liệu mô phỏng phục vụ trình diễn — không phải số liệu thống kê chính thức*".
- **AI không được bịa**: trả lời số liệu chỉ từ kết quả truy vấn CSDL; trả lời về văn
  bản chỉ từ đoạn văn bản truy xuất được, **bắt buộc dẫn nguồn** (số, ký hiệu, ngày
  ban hành). Không có dữ liệu thì nói rõ "Không tìm thấy trong Kho".
- **Phân quyền xuyên suốt cả tầng AI**: truy vấn và tìm kiếm ngữ nghĩa phải lọc theo
  quyền của người đang đăng nhập trước khi đưa cho mô hình.
- **Không dữ liệu mật**: có cờ `mat` trên văn bản; văn bản gắn cờ này bị chặn khỏi
  Kho và khỏi mọi kết quả tìm kiếm/AI. Demo cần 1 bản ghi minh họa việc chặn.
- **Bảo mật tối thiểu**: mật khẩu băm (bcrypt); khóa API chỉ đọc từ `.env`; `.env`,
  `*.db`, `outputs/`, `uploads/` trong `.gitignore`.
- Không thêm thư viện ngoài Mục 5 khi chưa hỏi lại người dùng.
- Mỗi milestone hoàn thành phải chạy được (`uvicorn` lên, `pytest` xanh) rồi mới sang
  milestone kế tiếp.

## 5. Công nghệ và thư viện

| Thành phần | Lựa chọn | Ghi chú |
|---|---|---|
| Ngôn ngữ | Python ≥ 3.11 | |
| Web framework | FastAPI + Uvicorn | |
| Giao diện | Jinja2 + HTMX + Chart.js (vendored) | Server-rendered, không build step |
| CSDL | SQLite (`data/onedata.db`) qua SQLAlchemy 2.x | Thiết kế để đổi được sang PostgreSQL |
| Tìm kiếm toàn văn | SQLite FTS5 | Lớp 1, chạy offline, không cần dịch vụ ngoài |
| Tìm kiếm ngữ nghĩa | sentence-transformers (mô hình đa ngữ nhỏ, tải sẵn về `models/`) + numpy | Nếu tải mô hình thất bại → tự lùi về FTS5, ghi log, KHÔNG làm sập app |
| Đọc .docx đầu vào | python-docx | Kênh 2 |
| Sinh .docx | python-docx qua `services/nd30.py` | **Đã có sẵn — xem Mục 9** |
| Xử lý dữ liệu/seed | pandas, openpyxl | |
| AI (chế độ online) | SDK `anthropic` | Model đặt trong `.env`, ví dụ `claude-sonnet-4-6` |
| Kiểm soát SQL | sqlglot | Validate truy vấn AI sinh |
| Auth | passlib[bcrypt], itsdangerous | |
| Kiểm thử | pytest, httpx | |
| Chất lượng mã | ruff, black | |

## 6. Cấu trúc thư mục

```
onedata-thanhhoa/
├── CLAUDE.md                # file này
├── README.md                # (M7)
├── LICENSE                  # MIT — Hà Ngọc Sơn
├── .gitignore               # .env, *.db, __pycache__, .venv, outputs/, uploads/, models/
├── .env.example
├── requirements.txt
├── app/
│   ├── main.py
│   ├── config.py            # pydantic-settings đọc .env
│   ├── db.py
│   ├── models.py            # Mục 7
│   ├── auth.py
│   ├── routers/
│   │   ├── dashboard.py
│   │   ├── van_ban.py       # Lớp 1: danh sách, xem, tải lên, tìm kiếm
│   │   ├── trich_xuat.py    # Kênh 2: hàng chờ + màn hình xác nhận
│   │   ├── nhap_lieu.py     # Kênh 3
│   │   ├── bao_cao.py
│   │   ├── hoi_dap.py
│   │   ├── giam_sat.py
│   │   ├── cong_khai.py
│   │   └── kiem_ke.py       # tùy chọn
│   ├── services/
│   │   ├── nd30.py          # ĐÃ CÓ — không viết lại
│   │   ├── report_builder.py
│   │   ├── doc_ingest.py    # đọc .docx → toàn văn + siêu dữ liệu → Lớp 1
│   │   ├── extractor.py     # Kênh 2: trích chỉ tiêu từ văn bản
│   │   ├── search.py        # FTS5 + embedding, lọc theo quyền
│   │   ├── ai_query.py      # định tuyến 2 lớp + text→SQL + offline
│   │   ├── canh_bao.py
│   │   └── audit.py
│   ├── templates/
│   └── static/
├── data/
│   ├── seed/
│   │   ├── donvi_hanhchinh_thanhhoa_166.json   # ĐÃ CÓ — xem Mục 8
│   │   ├── cau_hoi_mau.json                    # chế độ offline
│   │   └── van_ban_mau/                        # 20-30 báo cáo .docx mô phỏng
│   └── onedata.db
├── models/                  # mô hình embedding tải sẵn (gitignore)
├── scripts/
│   ├── seed.py
│   ├── make_sample_docs.py  # sinh các .docx báo cáo mô phỏng bằng nd30.py
│   └── make_demo_reports.py
├── outputs/                 # .docx sinh ra (gitignore)
├── uploads/                 # văn bản tải lên (gitignore)
└── tests/
```

## 7. Mô hình dữ liệu

**Danh mục & Lớp 2 (chỉ tiêu):**

- `don_vi(id, ma, ten, loai, vung)` — `ma` là mã đơn vị hành chính 5 chữ số lấy từ
  file JSON ở Mục 8; `loai` ∈ {`xa`, `phuong`, `so_nganh`, `tinh`};
  `vung` ∈ {`do_thi`, `dong_bang`, `mien_nui`}.
- `linh_vuc(id, ma, ten)` — `DTC`, `TTHC`, `ASXH`.
- `chi_tieu(id, ma, ten, linh_vuc_id, don_vi_tinh, tan_suat, co_quan_chu_chi_tieu,
  dinh_nghia, tu_khoa_trich_xuat, cong_khai)` — `tu_khoa_trich_xuat` là danh sách cụm
  từ giúp máy nhận diện chỉ tiêu trong văn bản (kênh 2).
- `gia_tri_chi_tieu(id, chi_tieu_id, don_vi_id, nam, thang, gia_tri, nguon,
  van_ban_id, nguoi_xac_nhan_id, thoi_diem_cap_nhat)` — `nguon` ∈ {`he_thong`,
  `van_ban`, `nhap_tay`}; UNIQUE(chi_tieu_id, don_vi_id, nam, thang) — "một số liệu,
  một bản ghi".

**Lớp 1 (văn bản) và hàng chờ kênh 2:**

- `van_ban(id, so, ky_hieu, loai, trich_yeu, co_quan_id, ngay_ban_hanh, duong_dan_file,
  toan_van, mat, thoi_diem_tiep_nhan)` — `mat` bool; văn bản `mat=true` không được đưa
  vào tìm kiếm, AI, hay trích xuất.
- `van_ban_doan(id, van_ban_id, thu_tu, noi_dung, embedding)` — chia văn bản thành
  đoạn để tìm kiếm ngữ nghĩa; `embedding` lưu BLOB (nullable nếu chạy chế độ FTS5).
- `trich_xuat_cho(id, van_ban_id, chi_tieu_id, don_vi_id, nam, thang, gia_tri_may_doc,
  doan_trich, do_tin_cay, trang_thai, nguoi_xu_ly_id, thoi_diem)` — `trang_thai` ∈
  {`cho_xac_nhan`, `da_xac_nhan`, `da_sua`, `tu_choi`}.

**Khác:**

- `nguoi_dung(id, ten_dang_nhap, mat_khau_hash, ho_ten, vai_tro, don_vi_id)` —
  `vai_tro` ∈ {`quan_tri`, `lanh_dao`, `chuyen_vien_xa`, `dai_bieu_hdnd`}.
- `nhat_ky(id, nguoi_dung_id, hanh_dong, chi_tiet, thoi_diem)`.
- `nghi_quyet_theo_doi(id, so_ky_hieu, trich_yeu, chi_tieu_id, gia_tri_muc_tieu,
  han_hoan_thanh)` — trang giám sát HĐND, 3–5 bản ghi.

View chỉ đọc cho AI: `v_so_lieu` (join tên chỉ tiêu, tên đơn vị, kỳ, giá trị, nguồn,
thời điểm), `v_don_vi`, `v_chi_tieu`, `v_van_ban` (không chứa cột `toan_van`).

## 8. Dữ liệu mẫu (seed)

**Đơn vị hành chính**: đọc từ `data/seed/donvi_hanhchinh_thanhhoa_166.json` (file đã
có sẵn, chứa đủ 166 xã/phường kèm mã 5 chữ số). Chọn **15 đơn vị** đại diện đủ 3 vùng
để seed; lưu `ma_dvhc` vào `don_vi.ma`. **Không tự bịa tên xã.** Thêm 3 `so_nganh`
(Sở Tài chính, Sở Nội vụ, Văn phòng UBND tỉnh) và 1 bản ghi `tinh`.

**Chỉ tiêu** (mã gợi ý):
- DTC: `DTC01` kế hoạch vốn giao (triệu đồng); `DTC02` giải ngân lũy kế (triệu đồng);
  `DTC03` tỷ lệ giải ngân (%); `DTC04` số dự án đang triển khai; `DTC05` số dự án chậm.
- TTHC: `TTHC01` hồ sơ tiếp nhận; `TTHC02` giải quyết đúng hạn; `TTHC03` quá hạn;
  `TTHC04` tỷ lệ đúng hạn (%); `TTHC05` hồ sơ trực tuyến; `TTHC06` tỷ lệ trực tuyến (%).
- ASXH: `AS01` hộ nghèo; `AS02` hộ cận nghèo; `AS03` đối tượng bảo trợ hưởng trợ cấp;
  `AS04` kinh phí chi trả tháng (triệu đồng); `AS05` tỷ lệ chi trả không tiền mặt (%).

Mỗi chỉ tiêu phải có `tu_khoa_trich_xuat` (ví dụ `DTC02`: "giải ngân lũy kế", "đã giải
ngân", "giá trị giải ngân").

**Giá trị**: sinh hợp lý về nghiệp vụ cho tháng 01–07/2026 (giải ngân lũy kế tăng dần,
không vượt kế hoạch; tỷ lệ 0–100%; xã đô thị quy mô lớn hơn miền núi), **trộn đủ ba
nguồn** để demo thấy được sự khác biệt (`he_thong` ~40%, `van_ban` ~40%, `nhap_tay`
~20%). Cài sẵn "điểm nóng": 2–3 xã tỷ lệ giải ngân tháng 7 dưới 30%; 1–2 xã tỷ lệ đúng
hạn TTHC dưới 90%; 1 xã có số liệu tháng 6 mâu thuẫn nhẹ.

**Văn bản mẫu** (`scripts/make_sample_docs.py`): dùng chính `nd30.py` sinh 20–30 báo
cáo .docx mô phỏng của các xã (báo cáo tháng về đầu tư công, TTHC, an sinh) có chứa
số liệu trong câu văn — đây là đầu vào cho kênh 2 và Lớp 1. Thêm 2–3 văn bản khác loại
(kế hoạch, thông báo) để tìm kiếm phong phú, và 1 văn bản gắn `mat=true` để demo việc chặn.

**Người dùng mẫu** (mật khẩu ghi trong README, chỉ dùng demo): `lanhdao/Demo@2026`,
`xa.hacthanh/Demo@2026`, `daibieu/Demo@2026`, `admin/Demo@2026`.

## 9. Yêu cầu chức năng từng phân hệ

### 9.1 Đăng nhập, phân quyền
Session cookie ký (itsdangerous). `chuyen_vien_xa` chỉ thao tác dữ liệu đơn vị mình;
`lanh_dao` xem toàn bộ + hỏi đáp + sinh báo cáo; `dai_bieu_hdnd` xem toàn bộ + trang
giám sát (chỉ đọc); `quan_tri` tất cả. Mọi hành động ghi `nhat_ky`.

### 9.2 Lớp 1 — Kho văn bản, tri thức số
- Trang danh sách văn bản (lọc theo cơ quan, loại, thời gian), trang xem chi tiết
  (siêu dữ liệu + toàn văn + link tải file gốc).
- Form "Tiếp nhận văn bản": tải lên .docx → `doc_ingest.py` đọc toàn văn, cố gắng bóc
  siêu dữ liệu (số, ký hiệu, trích yếu, ngày, cơ quan) bằng biểu thức chính quy trên
  phần đầu văn bản; cho người dùng sửa lại trước khi lưu. *(Trong thực tế đây là luồng
  tự động từ TD Office; demo mô phỏng bằng tải lên — ghi rõ điều này trên giao diện.)*
- Chia đoạn, tạo embedding nếu có mô hình; luôn đánh chỉ mục FTS5.
- Ô tìm kiếm: trả về đoạn văn khớp + tên văn bản + số ký hiệu + ngày ban hành.

### 9.3 Kênh 2 — Máy trích xuất & màn hình xác nhận (ĐIỂM NHẤN)
- Ngay khi một văn bản vào Lớp 1, `extractor.py` chạy: với mỗi chỉ tiêu, dò
  `tu_khoa_trich_xuat` trong các câu; bắt số kèm đơn vị tính bằng biểu thức chính quy
  (xử lý được "45.000 triệu đồng", "27,0%", "1.250 hồ sơ"); suy ra kỳ báo cáo từ trích
  yếu; tạo bản ghi `trich_xuat_cho` với `do_tin_cay` (cao/trung bình/thấp) và
  `doan_trich` là câu chứa số.
  - Chế độ online: gửi văn bản + danh mục chỉ tiêu cho mô hình, yêu cầu trả JSON
    `[{ma_chi_tieu, gia_tri, doan_trich, do_tin_cay}]`; **giá trị phải xuất hiện
    nguyên văn trong `doan_trich`**, nếu không thì loại bỏ bản ghi đó.
  - Chế độ offline: chỉ dùng biểu thức chính quy — vẫn đủ để demo.
- **Màn hình "Xác nhận số liệu máy trích"**: bảng hàng chờ, mỗi dòng gồm chỉ tiêu, giá
  trị máy đọc (ô sửa được), câu trích dẫn (bôi đậm con số), link mở văn bản gốc, nút
  **Xác nhận** / **Sửa & xác nhận** / **Từ chối**; có nút "Xác nhận tất cả dòng độ tin
  cậy cao". Xác nhận xong → ghi vào `gia_tri_chi_tieu` với `nguon='van_ban'`,
  `van_ban_id`, `nguoi_xac_nhan_id`.
- Thông điệp trên trang: *"Anh/chị không phải nhập lại — chỉ xác nhận số liệu hệ thống
  đã đọc từ chính báo cáo vừa phát hành."*

### 9.4 Kênh 3 — Nhập tại nguồn
Chỉ hiển thị các chỉ tiêu của kỳ hiện tại **chưa có giá trị từ kênh 1 hoặc 2** (đây là
minh chứng trực quan cho việc thu hẹp dần việc nhập tay). Kiểm tra kiểu số, % trong
[0;100], cảnh báo nếu lũy kế giảm so kỳ trước.

### 9.5 Dashboard điều hành
Thẻ tổng hợp 3 lĩnh vực; biểu đồ cột xếp hạng tỷ lệ giải ngân theo xã; biểu đồ đường
7 tháng; bảng "điểm nóng". **Mỗi con số kèm nhãn nguồn** (biểu tượng/tooltip: hệ thống
/ trích từ văn bản số… / nhập tại nguồn) và thời điểm cập nhật — bấm vào số có nguồn
`van_ban` thì mở đúng văn bản gốc. Trang chi tiết đơn vị có nút "Tạo báo cáo".

### 9.6 Máy soạn báo cáo (Nghị định 30/2020/NĐ-CP)
- `services/nd30.py` **đã có sẵn trong repo — dùng nguyên, không viết lại**. API:
  `VanBan(co_quan_chu_quan, co_quan_ban_hanh, so, ky_hieu, dia_danh, ngay, thang, nam,
  loai_van_ban, trich_yeu)`, các phương thức `doan()`, `khoan(n, text)`, `dieu()`,
  `nguoi_ky(chuc_vu, ho_ten, chuc_vu_thuc=…)`, `noi_nhan([...])`, `luu(path)`.
  Lưu ý: `khoan`/`diem` tự đánh số — **không tự chèn "1." hay "a)" vào chuỗi text**.
- `report_builder.py`: 2 mẫu báo cáo demo (đầu tư công; thủ tục hành chính) — lấy số
  liệu từ Lớp 2, sinh câu nhận định tự động (so sánh kỳ trước, xếp hạng trong tỉnh),
  xuất .docx vào `outputs/`.
- Nút "Tạo báo cáo tháng này cho tất cả 15 xã" → sinh loạt, hiển thị thời gian chạy.

### 9.7 Hỏi – đáp AI xuyên hai lớp
- `ai_query.py` có **tầng định tuyến**: phân loại câu hỏi thành `so_lieu` |
  `van_ban` | `lai` (offline: theo từ khóa; online: hỏi mô hình).
  - `so_lieu` → sinh SQL, validate bằng sqlglot: một statement, chỉ `SELECT`, bảng/cột
    thuộc allowlist (`v_so_lieu`, `v_don_vi`, `v_chi_tieu`), cấm `;`, `ATTACH`,
    `PRAGMA`; tự thêm `LIMIT 200`; timeout 5 giây; chạy trên kết nối chỉ đọc.
  - `van_ban` → `search.py` lấy 5–8 đoạn liên quan (đã lọc quyền, loại bỏ `mat=true`)
    → mô hình tổng hợp trả lời **chỉ dựa trên các đoạn đó**, kèm số/ký hiệu/ngày.
  - `lai` → chạy cả hai, ghép thành một câu trả lời (số liệu + trích dẫn văn bản).
- Giao diện hiển thị: câu trả lời + bảng số liệu (nếu có) + danh sách văn bản dẫn
  nguồn + câu SQL đã chạy (thu gọn). Kết quả rỗng → "Không tìm thấy trong Kho dữ liệu".
- **Chế độ offline** (`OFFLINE=1`, mặc định): ~25 câu hỏi mẫu trong
  `data/seed/cau_hoi_mau.json` — đủ cả 3 loại — ánh xạ sẵn sang SQL hoặc sang truy vấn
  FTS5; so khớp gần đúng (chuẩn hóa không dấu + từ khóa); có dropdown "Câu hỏi gợi ý".
  Luồng hiển thị giống hệt chế độ online.
- Mọi câu hỏi, SQL, số dòng kết quả ghi `nhat_ky`.

### 9.8 Cảnh báo sớm
Luật demo: tỷ lệ giải ngân kỳ mới nhất < 30%; tỷ lệ đúng hạn TTHC < 90%; đơn vị chưa
đủ số liệu kỳ hiện tại; lũy kế giảm so kỳ trước; **có bản ghi trong hàng chờ xác nhận
quá 3 ngày**. Hiển thị bảng "Điểm nóng" trên dashboard.

### 9.9 Trang giám sát HĐND
Danh sách `nghi_quyet_theo_doi` với chỉ tiêu gắn kèm: giá trị hiện tại vs mục tiêu,
tiến độ, cảnh báo chậm; mỗi dòng có link tới văn bản gốc ở Lớp 1. Chỉ đọc.

### 9.10 Trang công khai
`/cong-khai`, không đăng nhập: các chỉ tiêu `cong_khai=true` theo xã, kỳ mới nhất, kèm
biểu đồ; banner "Dân biết – dân giám sát" + dòng dữ liệu mô phỏng.

### 9.11 (Tùy chọn) Kiểm kê báo cáo
Form khai báo báo cáo định kỳ; thống kê số báo cáo/xã/tháng; danh sách nghi trùng lặp.

## 10. Kế hoạch thực hiện theo milestone

| MS | Nội dung | Hoàn thành khi (DoD) |
|---|---|---|
| M1 | Khung dự án: cấu trúc, config, models đầy đủ 2 lớp, `seed.py` (đơn vị + chỉ tiêu + giá trị), auth | `python scripts/seed.py` tạo DB đầy đủ; đăng nhập 4 tài khoản; `pytest` xanh |
| M2 | Lớp 1: `make_sample_docs.py`, `doc_ingest.py`, danh sách/xem/tải lên văn bản, FTS5 | Tải lên .docx → toàn văn vào Kho, tìm kiếm từ khóa ra kết quả; văn bản `mat` bị chặn |
| M3 | **Kênh 2**: `extractor.py` + màn hình xác nhận + ghi vào Lớp 2 kèm `van_ban_id` | Tải báo cáo mẫu → hàng chờ có bản ghi đúng; xác nhận → số hiện trên dashboard, bấm vào mở được văn bản gốc |
| M4 | Kênh 3 + dashboard + nhãn nguồn + cảnh báo + trang công khai + giám sát HĐND | Biểu đồ chạy offline; mọi số có nhãn nguồn; điểm nóng đúng dữ liệu cài sẵn |
| M5 | Máy soạn báo cáo NĐ30 (dùng `nd30.py` sẵn có) | 2 mẫu .docx đúng thể thức; sinh loạt 15 xã kèm đo thời gian |
| M6 | Hỏi – đáp AI xuyên lớp: offline trước, online sau; tìm kiếm ngữ nghĩa | 25 câu mẫu chạy đúng offline (đủ 3 loại); validator SQL có test chặn UPDATE/DELETE/bảng ngoài allowlist; phân quyền áp dụng trong tìm kiếm |
| M7 | Đóng gói: README (ảnh chụp màn hình, hướng dẫn cài), LICENSE, rà soát theo kịch bản Mục 13, tag `v0.2-demo` | Người mới clone làm theo README chạy được demo trong ≤ 10 phút |

Trình tự bắt buộc: xong, chạy thử và commit từng milestone rồi mới sang milestone kế
tiếp. M3 là milestone quan trọng nhất — đừng rút gọn.

## 11. Kiểm thử và chất lượng

- `pytest` tối thiểu: seed tạo đủ bản ghi; UNIQUE trên `gia_tri_chi_tieu`; phân quyền
  (xã A không thao tác được dữ liệu xã B); `extractor` bắt đúng số từ câu mẫu (gồm ca
  "45.000 triệu đồng" và "27,0%"); giá trị AI trả về không nằm trong `doan_trich` thì
  bị loại; validator SQL chặn các ca tấn công; văn bản `mat=true` không xuất hiện
  trong tìm kiếm và AI; báo cáo sinh ra mở lại được và chứa "BÁO CÁO", "./.".
- `ruff check .` và `black --check .` sạch trước mỗi commit.
- Chạy: `uvicorn app.main:app --reload` → http://127.0.0.1:8000

## 12. Git, GitHub và quy ước commit

- Repo `onedata-thanhhoa` (public). Nhánh `main`; mỗi milestone một nhánh
  `feat/m3-kenh-trich-xuat`… rồi merge.
- Commit: `feat(m3): may trich xuat va man hinh xac nhan` (không dấu ở tiêu đề).
- `.gitignore`: `.env`, `.venv/`, `__pycache__/`, `*.db`, `outputs/`, `uploads/`,
  `models/`, `.pytest_cache/`.
- LICENSE: MIT, tác giả "Hà Ngọc Sơn".
- README: giới thiệu mô hình (kèm sơ đồ 2 lớp – 3 kênh ở Mục 2), ảnh chụp màn hình
  (ưu tiên màn hình xác nhận số liệu), cài đặt, tài khoản demo, tuyên bố dữ liệu mô
  phỏng, liên hệ (Hà Ngọc Sơn – 0904818886 – sonthkh@gmail.com).
- Hoàn tất M7: tag `v0.2-demo`. Đẩy lên GitHub (người dùng tự chạy):
  `gh repo create onedata-thanhhoa --public --source=. --push`.

## 13. Biến môi trường — `.env.example`

```
# 1 = offline (mặc định, dùng khi trình diễn), 0 = gọi Claude API
OFFLINE=1
ANTHROPIC_API_KEY=
ANTHROPIC_MODEL=claude-sonnet-4-6
DATABASE_URL=sqlite:///data/onedata.db
SECRET_KEY=doi-chuoi-nay-khi-chay-that
# Để trống nếu chưa tải mô hình embedding — hệ thống tự lùi về FTS5
EMBEDDING_MODEL_PATH=
```

## 14. Kịch bản demo 6 phút (mọi chức năng phải phục vụ kịch bản này)

1. Đăng nhập `xa.hacthanh` → **tải lên báo cáo tháng 7 vừa phát hành** (.docx) →
   nhấn mạnh: đây là việc công chức vẫn làm hằng ngày, không thêm thao tác.
2. Hệ thống hiện ngay hàng chờ: đã đọc được 5–6 chỉ tiêu, kèm câu trích dẫn → bấm
   **"Xác nhận tất cả dòng độ tin cậy cao"** → *"Anh/chị không phải nhập lại."*
3. Đăng nhập `lanhdao` → dashboard đã có số vừa xác nhận; **bấm vào con số** → mở đúng
   báo cáo gốc → chốt ý "mỗi số liệu đều truy được về nguồn".
4. Hỏi AI ba câu, mỗi loại một câu: *"Những xã nào giải ngân dưới 30% trong tháng 7?"*
   → *"Báo cáo mới nhất của xã X nói gì về nguyên nhân chậm giải ngân?"* → *"Tỷ lệ
   đúng hạn TTHC của phường Hạc Thành hiện là bao nhiêu và đã có báo cáo nào giải
   trình chưa?"*
5. Bấm **"Tạo báo cáo tháng 7 cho tất cả 15 xã"** → mở một file .docx xem thể thức
   chuẩn NĐ30 → nêu "15 báo cáo trong X giây".
6. Chuyển `daibieu` → trang giám sát nghị quyết; mở `/cong-khai` không đăng nhập →
   chốt "dân biết – dân giám sát".

## 15. Việc KHÔNG được làm

- Không dùng dữ liệu thật, tên người thật, số liệu thống kê chính thức.
- Không tự bịa tên xã/phường — lấy từ file JSON ở Mục 8.
- Không để AI trả lời số liệu không có trong Kho; không bỏ phần dẫn nguồn.
- Không cho văn bản `mat=true` lọt vào tìm kiếm, AI, hay trích xuất.
- Không ghi thẳng số liệu máy trích vào Lớp 2 khi chưa qua bước người xác nhận.
- Không viết lại `nd30.py`.
- Không commit `.env`, `*.db`, file .docx sinh ra, thư mục `models/`.
- Không đổi stack, không thêm docker/k8s/microservice — demo một máy.
- Không dùng CDN, không yêu cầu Internet cho bất kỳ trang nào (trừ AI online).
