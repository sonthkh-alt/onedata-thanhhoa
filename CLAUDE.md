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
- **Căn cứ chuẩn dữ liệu của tỉnh** — 2 văn bản đặt tại thư mục gốc (chỉ tham khảo
  cục bộ, KHÔNG commit lên GitHub — xem Mục 14):
  - `2053.pdf` — **Quyết định số 2053/QĐ-UBND ngày 07/7/2026** của Chủ tịch
    UBND tỉnh Thanh Hóa ban hành **Danh mục dữ liệu chủ chuyên ngành, dữ liệu
    dùng chung và dữ liệu mở tỉnh Thanh Hóa** (3 phụ lục; thay thế QĐ
    630/QĐ-UBND 2023 và QĐ 3111/QĐ-UBND 2024).
  - `2176.pdf` — **Quyết định số 2176/QĐ-UBND ngày 20/7/2026** của Chủ tịch
    UBND tỉnh Thanh Hóa ban hành **Bộ trường thông tin dữ liệu gốc, dữ liệu
    chủ, dữ liệu tham chiếu tỉnh Thanh Hóa** (từ điển dữ liệu chi tiết đến
    mức trường).
  Mọi trường thông tin, thuật ngữ, danh mục, cơ quan chủ quản trong demo phải
  bám theo hai văn bản này — bảng đối chiếu tuân thủ ở **Mục 15**. Thông điệp
  "Không báo cáo lại" có căn cứ trực tiếp tại Điều 3 khoản 3 điểm f của quyết
  định danh mục dữ liệu: các sở ngành *"phân quyền cho UBND cấp xã truy cập,
  cập nhật và khai thác dữ liệu thuộc phạm vi quản lý, **không yêu cầu báo cáo
  thủ công**"*.

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

Bảng chính (SQLAlchemy; tên bảng snake_case). Các trường đánh dấu **(chuẩn tỉnh)**
được bổ sung để tuân thủ Bộ trường thông tin trong `2176.pdf` — xem Mục 15:

- `don_vi(id, ma, ma_dinh_danh, ma_dvhc, ten, loai, loai_dvhc, vung, trang_thai,
  ngay_cap_nhat)` — `loai` ∈ {`xa`, `phuong`, `so_nganh`, `tinh`};
  `vung` ∈ {`do_thi`, `dong_bang`, `mien_nui`}.
  - `ma_dinh_danh` **(chuẩn tỉnh)**: mã định danh điện tử cơ quan theo
    QCVN 102:2016/BTTTT (demo dùng mã mô phỏng đúng cấu trúc, ghi chú rõ);
  - `ma_dvhc` **(chuẩn tỉnh)**: mã đơn vị hành chính xã/phường theo danh mục
    hành chính quốc gia (demo: mã mô phỏng 5 chữ số, TODO thay mã thật);
  - `loai_dvhc` **(chuẩn tỉnh)**: phân loại I/II/III (trường DGHC19);
  - `trang_thai` ∈ {`dang_hieu_luc`, `het_hieu_luc`} + `ngay_cap_nhat`
    **(chuẩn tỉnh)**: mẫu quản trị dữ liệu chủ/tham chiếu.
- `linh_vuc(id, ma, ten, trang_thai, ngay_cap_nhat)` — 3 bản ghi: `DTC`, `TTHC`,
  `ASXH`.
- `chi_tieu(id, ma, ten, linh_vuc_id, don_vi_tinh, tan_suat, co_quan_chu_chi_tieu,
  nguon_du_lieu, muc_chia_se, cong_thuc, rang_buoc, dinh_nghia, cong_khai,
  trang_thai, ngay_cap_nhat)` — `tan_suat` ∈ {`thang`, `quy`, `nam`};
  `cong_khai` bool (thuộc Danh mục dữ liệu mở → hiện ở trang công khai).
  - `nguon_du_lieu` **(chuẩn tỉnh)**: tên CSDL nguồn theo đúng Danh mục trong
    `2053.pdf` (ví dụ "CSDL Hệ thống thông tin giải quyết TTHC tỉnh Thanh Hóa");
    hiển thị ở tooltip nguồn trên dashboard và chân bảng công khai;
  - `muc_chia_se` **(chuẩn tỉnh)** ∈ {`chuyen_nganh`, `dung_chung`, `mo`} —
    3 lớp dữ liệu đúng theo quyết định danh mục;
  - `cong_thuc` **(chuẩn tỉnh)**: công thức tính chỉ tiêu dẫn xuất, mô phỏng
    trường `Formula` của Hệ thống thông tin báo cáo tỉnh (ví dụ DTC03 =
    `DTC02/DTC01*100`); hệ thống tự tính, không cho nhập tay chỉ tiêu dẫn xuất;
  - `rang_buoc` **(chuẩn tỉnh)**: quy tắc kiểm tra dữ liệu, mô phỏng
    `Content.Rule.Formula` (ví dụ `0 <= gia_tri <= 100`; `DTC02 không giảm
    so kỳ trước`).
- `gia_tri_chi_tieu(id, chi_tieu_id, don_vi_id, nam, thang, gia_tri, nguon,
  nguoi_cap_nhat_id, thoi_diem_cap_nhat)` — `nguon` ∈ {`he_thong`, `nhap_tay`};
  ràng buộc UNIQUE(chi_tieu_id, don_vi_id, nam, thang) — đúng tinh thần
  "một số liệu chỉ có một bản ghi". Đây là lớp **dữ liệu gốc** (nhập một lần
  tại nguồn). Kỳ hiển thị/xuất dữ liệu dùng định dạng chuẩn **`YYYYMM`**
  (tháng), `YYYYQ` (quý), `YYYY` (năm) theo Hệ thống thông tin báo cáo tỉnh.
- `mau_bao_cao(id, ma, ten, linh_vuc_id, mo_ta)` + cấu trúc mẫu đặt trong code
  (`report_builder.py`), không cần bảng JSON phức tạp ở bản demo.
- `nguoi_dung(id, ten_dang_nhap, mat_khau_hash, ho_ten, email, vai_tro,
  don_vi_id)` — `vai_tro` ∈ {`quan_tri`, `lanh_dao`, `chuyen_vien_xa`,
  `dai_bieu_hdnd`}; `email` **(chuẩn tỉnh)** dạng `ten@thanhhoa.gov.vn`
  (mô phỏng — nguồn chuẩn thực tế là CSDL cán bộ, công chức, viên chức tỉnh).
- `nhat_ky(id, nguoi_dung_id, hanh_dong, chi_tiet, thoi_diem)` — ghi mọi lần
  đăng nhập, nhập/sửa số liệu, sinh báo cáo, câu hỏi AI.
- `nghi_quyet_theo_doi(id, so_ky_hieu, trich_yeu, chi_tieu_id, gia_tri_muc_tieu,
  han_hoan_thanh)` — phục vụ trang giám sát HĐND (demo 3–5 bản ghi).

Tạo thêm **view chỉ đọc** cho AI truy vấn (8.5): `v_so_lieu` (join đủ tên chỉ tiêu,
tên đơn vị, kỳ, giá trị, nguồn, thời điểm cập nhật) và `v_don_vi`, `v_chi_tieu`.

**Chuẩn trường thông tin áp dụng toàn hệ thống** (theo `2176.pdf`):

- Ngày: hiển thị/lưu trao đổi theo **`YYYY-MM-DD`**; thời điểm:
  **`YYYY-MM-DD HH:MM:SS`** (giao diện tiếng Việt có thể hiển thị kèm dạng
  `dd/mm/yyyy` cho thân thiện, nhưng dữ liệu xuất API/Excel dùng chuẩn ISO).
- Kỳ báo cáo: `YYYYMM` / `YYYYQ` / `YYYY`.
- Số tiền: kiểu số thập phân (Float/Decimal), đơn vị tính ghi rõ trong
  `chi_tieu.don_vi_tinh` (tương ứng `Content.Indicator.Unit`).
- Phân lớp dữ liệu dùng đúng thuật ngữ của tỉnh: **dữ liệu gốc**
  (`gia_tri_chi_tieu`), **dữ liệu chủ/tham chiếu** (`don_vi`, `linh_vuc`,
  `chi_tieu`), lớp **chia sẻ** (các view `v_*` — tinh thần kết nối qua nền
  tảng trung gian LGSP, chỉ đọc, có kiểm soát).
- Bảng danh mục mới (nếu phát sinh) theo mẫu danh mục tham chiếu chuẩn:
  `ma` (bất biến), `ten`, `ma_cha`, `mo_ta`, `thu_tu`, `ngay_hl`, `ngay_hhl`,
  `trang_thai`.

## 7. Danh mục chỉ tiêu và dữ liệu mẫu (seed)

`scripts/seed.py` phải tạo:

**15 đơn vị cấp xã** — dùng **tên thật + mã ĐVHC 5 chữ số thật**, chọn từ danh
mục 166 xã/phường theo Nghị quyết 1686/NQ-UBTVQH15 trong file
`data/seed/donvi_hanhchinh_thanhhoa_166.json` (người dùng cung cấp, seed phải
tự đối chiếu mã + tên với file này khi chạy — hàm `kiem_tra_danh_muc_dvhc`).
15 đơn vị đã chốt: phường Hạc Thành, Bỉm Sơn, Hàm Rồng, Sầm Sơn; xã Các Sơn,
Nga Sơn, Hoằng Hoá, Hậu Lộc, Thọ Xuân, Nông Cống, Tân Thành, Thắng Lộc,
Mường Lát, Bá Thước, Ngọc Lặc. Phân bổ đủ 3 vùng (phân vùng là gán tạm cho
demo; trường `vung` trong file JSON để trống). Thêm 5 `so_nganh` (đúng cơ quan chủ quản
theo Danh mục dữ liệu `2053.pdf`): **Sở Tài chính, Sở Nội vụ, Sở Nông nghiệp
và Môi trường, Trung tâm Phục vụ hành chính công tỉnh, Văn phòng UBND tỉnh**;
1 bản ghi `tinh`. Mỗi đơn vị có `ma_dinh_danh` (mô phỏng cấu trúc QCVN
102:2016/BTTTT) và xã/phường có `ma_dvhc` (mô phỏng 5 chữ số, TODO thay mã thật).

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

**Cơ quan chủ chỉ tiêu và CSDL nguồn** (bắt buộc bám Danh mục `2053.pdf` —
đây là giá trị các cột `co_quan_chu_chi_tieu` và `nguon_du_lieu`):

| Nhóm chỉ tiêu | Cơ quan chủ chỉ tiêu | CSDL nguồn (`nguon_du_lieu`) |
|---|---|---|
| DTC01–DTC05 | Sở Tài chính | CSDL thông tin Dự án Đầu tư công (vốn ngân sách tỉnh); CSDL quản lý ngân sách dự án đầu tư |
| TTHC01–TTHC06 | Trung tâm Phục vụ hành chính công tỉnh | CSDL Hệ thống thông tin giải quyết TTHC tỉnh Thanh Hóa |
| AS01, AS02 | Sở Nông nghiệp và Môi trường | CSDL quản lý hộ nghèo, hộ cận nghèo toàn tỉnh (dữ liệu mở do UBND cấp xã cung cấp) |
| AS03–AS05 | Sở Nội vụ | CSDL về Bảo trợ xã hội (chi trả trợ cấp) |

Ghi chú định nghĩa theo Bộ trường thông tin `2176.pdf` (đưa vào
`chi_tieu.dinh_nghia`): TTHC05/TTHC06 đếm hồ sơ theo hình thức nộp/trả kết quả
∈ {trực tuyến, trực tiếp, bưu chính} (trường `HTTKQ`); AS05 "không dùng tiền
mặt" = kỳ chi trả có hình thức chi trả qua tài khoản (các trường `KyChiTra`,
`MaHinhThucChiTra`, `SoTaiKhoanNguoiNhan`, `MaNganHang`); DTC03 khai báo bằng
`cong_thuc` = `DTC02/DTC01*100` (hệ thống tự tính).

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
  giảm so tháng trước (cho phép lưu nhưng gắn cờ). Quy tắc kiểm tra đọc từ
  `chi_tieu.rang_buoc` (cơ chế mô phỏng `Content.Rule` của Hệ thống thông tin
  báo cáo tỉnh) — không hard-code rải rác trong view.
- Chỉ tiêu dẫn xuất (có `cong_thuc`, ví dụ DTC03, TTHC04, TTHC06) **khóa ô nhập
  tay** và hệ thống tự tính lại ngay khi lưu chỉ tiêu gốc — thể hiện đúng nguyên
  tắc mỗi số liệu chỉ có một nguồn sự thật.
- Thông điệp chủ đạo hiển thị trên trang: "*Anh/chị chỉ phải nhập MỘT LẦN — mọi
  báo cáo, bảng biểu sẽ được hệ thống tự tổng hợp từ số liệu này.*"
- Chân trang khu nhập liệu hiển thị nguyên tắc chất lượng dữ liệu của tỉnh:
  "*Đúng - Đủ - Sạch - Sống - Liên thông - Thống nhất - Dùng chung*"
  (đủ 7 vế, đúng thứ tự).

### 8.3 Dashboard điều hành
- Trang tỉnh: thẻ tổng hợp 3 lĩnh vực (kỳ mới nhất), biểu đồ cột xếp hạng tỷ lệ
  giải ngân theo xã, biểu đồ đường diễn biến 7 tháng, bảng "điểm nóng" (từ 8.6).
- Trang chi tiết đơn vị: mọi chỉ tiêu 7 tháng, biểu đồ, nút "Tạo báo cáo" (8.4).
- Bộ lọc kỳ, lĩnh vực, vùng. Mọi con số kèm tooltip: **CSDL nguồn theo Danh mục
  của tỉnh** (`chi_tieu.nguon_du_lieu`) + nguồn bản ghi (`he_thong`/`nhap_tay`)
  + thời điểm cập nhật — người xem luôn trả lời được "số này từ đâu ra".
- Kỳ hiển thị kèm mã kỳ chuẩn (ví dụ "Tháng 7/2026 — kỳ 202607").

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

### 8.7 Trang công khai — mô hình "Cổng dữ liệu mở thu nhỏ"
- `/cong-khai`, không đăng nhập: các chỉ tiêu có `cong_khai=true` (tỷ lệ giải
  ngân, tỷ lệ đúng hạn TTHC, tỷ lệ hồ sơ trực tuyến, tỷ lệ chi trả không tiền
  mặt) theo xã, kỳ mới nhất, kèm biểu đồ; banner "Dân biết – dân giám sát" +
  dòng dữ liệu mô phỏng.
- Trình bày theo đúng cấu trúc Danh mục dữ liệu mở của tỉnh (Phụ lục 3,
  `2053.pdf`): mỗi tập số liệu ghi rõ **Cơ quan chủ trì cung cấp – Kỳ nhập
  liệu – Định dạng, hình thức chia sẻ – Thời điểm cập nhật**.
- Nút **tải xuống Excel (.xlsx) và JSON** cho từng bảng số liệu công khai —
  tương ứng cột "Định dạng, hình thức chia sẻ: API, Excel" của danh mục
  (JSON đóng vai trò minh họa API; không cần xây API công khai riêng ở demo).
- Khối "**Góp ý nhu cầu dữ liệu mở**": form đơn giản (nội dung + email tùy
  chọn, lưu vào `nhat_ky`, không cần xử lý) — thể hiện quy định tiếp nhận
  phản hồi của tổ chức, cá nhân để ưu tiên công bố dữ liệu mở.

### 8.8 (Tùy chọn — chỉ làm khi M1–M5 xong) Kiểm kê báo cáo
- Form khai báo: tên báo cáo, cơ quan yêu cầu, tần suất, căn cứ; trang thống kê
  tổng số báo cáo/xã/tháng và danh sách nghi trùng lặp (trùng gần đúng theo tên).

## 9. Kế hoạch thực hiện theo milestone

| MS | Nội dung | Hoàn thành khi (DoD) |
|---|---|---|
| M1 | Khung dự án: cấu trúc thư mục, config, models, `scripts/seed.py`, auth cơ bản | `python scripts/seed.py` tạo DB đầy đủ; đăng nhập được 4 tài khoản; `pytest` xanh |
| M2 | **Cập nhật schema/seed theo chuẩn tỉnh (Mục 6, 7 bản mới)** + Nhập liệu tại nguồn + nhật ký | Models/seed có đủ trường (chuẩn tỉnh); tài khoản xã nhập/sửa được số liệu, chỉ tiêu dẫn xuất tự tính, ràng buộc UNIQUE hoạt động, log ghi đủ |
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
- **Không commit 2 file `2053.pdf`, `2176.pdf`** (văn bản của tỉnh, chỉ dùng
  tham khảo cục bộ) — `*.pdf` phải nằm trong `.gitignore`.
- Không tự bịa tên xã/phường ngoài 5 tên đã nêu — dùng placeholder + TODO.
- Không gọi API AI ở chế độ offline; không để lỗi API làm sập trang.
- Không commit `.env`, file `.db`, file .docx sinh ra.
- Không đổi stack công nghệ, không thêm docker/k8s/microservice — demo một máy.
- Không dùng CDN, không yêu cầu Internet cho bất kỳ trang nào (trừ AI online).

## 15. Đối chiếu tuân thủ hai quyết định của tỉnh Thanh Hóa

Bảng tra nhanh khi lập trình — chi tiết nằm trong 2 file PDF ở thư mục gốc:

### 15.1 Theo Quyết định số 2053/QĐ-UBND ngày 07/7/2026 — Danh mục dữ liệu (`2053.pdf`)

| Quy định của tỉnh | Demo thể hiện tại |
|---|---|
| 3 lớp: dữ liệu chủ chuyên ngành (PL1) / dùng chung (PL2) / mở (PL3) | `chi_tieu.muc_chia_se`; `cong_khai` ⇔ thuộc Danh mục dữ liệu mở |
| Điều 3.3.f: phân quyền cấp xã cập nhật dữ liệu, "không yêu cầu báo cáo thủ công" | Thông điệp trung tâm của demo; trích dẫn ở trang giới thiệu/README |
| Nguyên tắc "Đúng - Đủ - Sạch - Sống - Liên thông - Thống nhất - Dùng chung" | Hiển thị ở khu nhập liệu (8.2); tiêu chí phần cảnh báo (8.6) |
| Kết nối qua LGSP, không kết nối riêng lẻ; chia sẻ có kiểm soát | AI chỉ truy vấn view `v_*` chỉ đọc, allowlist (8.5) |
| Cột PL3: Cơ quan chủ trì – Kỳ nhập liệu – Định dạng, hình thức chia sẻ | Cấu trúc trang công khai (8.7); metadata chỉ tiêu (Mục 6) |
| Cơ quan chủ quản đúng danh mục: TTHC → Trung tâm Phục vụ hành chính công tỉnh; hộ nghèo/cận nghèo → Sở NN&MT; bảo trợ xã hội → Sở Nội vụ; đầu tư công/ngân sách → Sở Tài chính | Bảng cơ quan chủ chỉ tiêu (Mục 7) |
| CSDL về chỉ tiêu kinh tế - xã hội (VP UBND tỉnh, PL2) phục vụ chỉ đạo điều hành | Chính là "kho chỉ tiêu dùng chung" mà demo mô phỏng |
| Tiếp nhận phản hồi dân về nhu cầu dữ liệu mở (Điều 3.3.g) | Form góp ý trên trang công khai (8.7) |

### 15.2 Theo Quyết định số 2176/QĐ-UBND ngày 20/7/2026 — Bộ trường thông tin (`2176.pdf`)

| Chuẩn của tỉnh | Demo áp dụng |
|---|---|
| Mã cơ quan theo QCVN 102:2016/BTTTT | `don_vi.ma_dinh_danh` (mã mô phỏng đúng cấu trúc) |
| Mã xã/phường theo danh mục hành chính quốc gia (DGHC12, `ma_dvhc`) | `don_vi.ma_dvhc` (TODO thay mã thật) |
| Phân loại ĐVHC I/II/III (DGHC19); thuộc vùng miền (DGHC20) | `don_vi.loai_dvhc`, `don_vi.vung` |
| Ngày `YYYY-MM-DD`; thời điểm `YYYY-MM-DD HH:MM:SS` | Mọi API/Excel xuất ra; hiển thị thân thiện dd/mm/yyyy |
| Kỳ báo cáo `YYYYMM`/`YYYYQ`/`YYYY` (HTTT báo cáo cấp tỉnh) | Mã kỳ trên dashboard, tên file báo cáo, dữ liệu xuất |
| Chỉ tiêu có công thức (`Formula`) và ràng buộc (`Content.Rule`) | `chi_tieu.cong_thuc`, `chi_tieu.rang_buoc`; chỉ tiêu dẫn xuất khóa nhập tay |
| Danh mục tham chiếu chuẩn: ma, ten, ma_cha, thu_tu, ngay_hl, ngay_hhl, trang_thai | Mẫu cho mọi bảng danh mục mới; `trang_thai`+`ngay_cap_nhat` trên bảng dữ liệu chủ |
| Hồ sơ TTHC: mã TTHC theo CSDL quốc gia; hình thức trả kết quả {trực tuyến, trực tiếp, bưu chính} | Định nghĩa TTHC05/TTHC06 trong `chi_tieu.dinh_nghia` |
| Chi trả trợ cấp: `KyChiTra`, `MaHinhThucChiTra`, tài khoản/ngân hàng | Định nghĩa AS04/AS05 ("không tiền mặt" = chi trả qua tài khoản) |
| Email công vụ `@thanhhoa.gov.vn`; nguồn chuẩn là CSDL CBCCVC tỉnh | `nguoi_dung.email` (mô phỏng) |

**Ghi chú triển khai**: M1 đã hoàn thành trước khi bổ sung chuẩn này — phần đầu
M2 phải cập nhật `models.py`, `scripts/seed.py`, view `v_*` và test theo Mục 6,
Mục 7 bản mới rồi mới làm phân hệ nhập liệu. Khi trích dẫn trong giao diện,
báo cáo hoặc README, dùng đúng số hiệu: **Quyết định số 2053/QĐ-UBND ngày
07/7/2026** và **Quyết định số 2176/QĐ-UBND ngày 20/7/2026** của Chủ tịch
UBND tỉnh Thanh Hóa.
