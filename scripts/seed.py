"""Tạo CSDL và dữ liệu mô phỏng cho bản demo.

Chạy:  python scripts/seed.py

Toàn bộ số liệu là DỮ LIỆU MÔ PHỎNG phục vụ trình diễn, sinh ngẫu nhiên có
chủ đích (seed cố định để tái lập được), kèm các "điểm nóng" phục vụ kịch
bản demo 5 phút (xem CLAUDE.md Mục 7 và 13).

Trường thông tin, cơ quan chủ chỉ tiêu và CSDL nguồn bám theo:
- Quyết định số 2053/QĐ-UBND ngày 07/7/2026 (Danh mục dữ liệu chủ chuyên
  ngành, dữ liệu dùng chung và dữ liệu mở tỉnh Thanh Hóa);
- Quyết định số 2176/QĐ-UBND ngày 20/7/2026 (Bộ trường thông tin dữ liệu
  gốc, dữ liệu chủ, dữ liệu tham chiếu tỉnh Thanh Hóa).
"""

import json
import random
import sys
from datetime import date, datetime
from pathlib import Path

# Cho phép chạy trực tiếp `python scripts/seed.py` từ thư mục gốc
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.auth import hash_mat_khau
from app.db import Base, SessionLocal, engine
from app.models import (
    ChiTieu,
    DonVi,
    GiaTriChiTieu,
    KiemKeBaoCao,
    LinhVuc,
    MauBaoCao,
    NghiQuyetTheoDoi,
    NguoiDung,
    TrichXuatCho,
    VanBan,
    VanBanDoan,
)
from app.services import audit, van_ban_mau

NAM = 2026
CAC_THANG = list(range(1, 8))  # tháng 01–07/2026
MAT_KHAU_DEMO = "Demo@2026"

rng = random.Random(2026)  # seed cố định để dữ liệu tái lập được

# ---------------------------------------------------------------------------
# Danh mục đơn vị (lớp dữ liệu chủ)
# ---------------------------------------------------------------------------
# 15 xã/phường THẬT (chọn từ danh sách 166 đơn vị theo Nghị quyết
# 1686/NQ-UBTVQH15) với mã ĐVHC 5 chữ số thật theo danh mục Tổng cục Thống kê
# — nguồn: data/seed/donvi_hanhchinh_thanhhoa_166.json (seed tự đối chiếu).
# Trường `vung` (do_thi/dong_bang/mien_nui) là PHÂN LOẠI TẠM cho demo.
DS_XA = [
    # (mã nội bộ, tên, loại, vùng, mã ĐVHC thật)
    ("HACTHANH", "Phường Hạc Thành", "phuong", "do_thi", "14797"),
    ("CACSON", "Xã Các Sơn", "xa", "dong_bang", "16591"),
    ("NGASON", "Xã Nga Sơn", "xa", "dong_bang", "16093"),
    ("TANTHANH", "Xã Tân Thành", "xa", "mien_nui", "15661"),
    ("THANGLOC", "Xã Thắng Lộc", "xa", "mien_nui", "15643"),
    ("BIMSON", "Phường Bỉm Sơn", "phuong", "do_thi", "14812"),
    ("HAMRONG", "Phường Hàm Rồng", "phuong", "do_thi", "14758"),
    ("SAMSON", "Phường Sầm Sơn", "phuong", "do_thi", "16531"),
    ("HOANGHOA", "Xã Hoằng Hoá", "xa", "dong_bang", "15865"),
    ("HAULOC", "Xã Hậu Lộc", "xa", "dong_bang", "16012"),
    ("THOXUAN", "Xã Thọ Xuân", "xa", "dong_bang", "15499"),
    ("NONGCONG", "Xã Nông Cống", "xa", "dong_bang", "16279"),
    ("MUONGLAT", "Xã Mường Lát", "xa", "mien_nui", "14845"),
    ("BATHUOC", "Xã Bá Thước", "xa", "mien_nui", "14923"),
    ("NGOCLAC", "Xã Ngọc Lặc", "xa", "mien_nui", "15061"),
]

# 5 sở ngành đúng cơ quan chủ quản CSDL theo Danh mục QĐ 2053/QĐ-UBND
DS_SO_NGANH = [
    ("STC", "Sở Tài chính", "so_nganh"),
    ("SNV", "Sở Nội vụ", "so_nganh"),
    ("SNNMT", "Sở Nông nghiệp và Môi trường", "so_nganh"),
    ("TTPVHCC", "Trung tâm Phục vụ hành chính công tỉnh", "so_nganh"),
    ("VPUBND", "Văn phòng UBND tỉnh", "so_nganh"),
]

# Hệ số quy mô theo vùng (xã đô thị > đồng bằng > miền núi)
HE_SO_VUNG = {"do_thi": 1.6, "dong_bang": 1.0, "mien_nui": 0.65}

# Điểm nóng cài sẵn phục vụ demo (CLAUDE.md Mục 7)
XA_GIAI_NGAN_THAP = {"CACSON", "MUONGLAT"}  # tỷ lệ giải ngân tháng 7 < 30%
XA_TTHC_THAP = {"NONGCONG", "TANTHANH"}  # tỷ lệ đúng hạn TTHC tháng 7 < 90%
XA_MAU_THUAN_T6 = "HAULOC"  # lũy kế tháng 6 giảm nhẹ so tháng 5
XA_NHAP_DEMO = "HACTHANH"  # để trống vài ô tháng 7 cho kịch bản nhập liệu
XA_THIEU_SO_LIEU = "BATHUOC"  # thiếu vài chỉ tiêu tháng 7 → cảnh báo

# Ô để trống tháng 7 (chỉ tiêu, mã xã): người demo sẽ nhập tay
O_TRONG_THANG_7 = {
    ("DTC02", "HACTHANH"),
    ("DTC03", "HACTHANH"),  # tỷ lệ tính từ DTC02 nên trống theo
    ("AS04", "HACTHANH"),
    ("TTHC05", "BATHUOC"),
    ("TTHC06", "BATHUOC"),
    ("AS05", "BATHUOC"),
}

# ---------------------------------------------------------------------------
# Danh mục lĩnh vực và chỉ tiêu (lớp dữ liệu chủ/tham chiếu)
# ---------------------------------------------------------------------------
DS_LINH_VUC = [
    ("DTC", "Giải ngân vốn đầu tư công"),
    ("TTHC", "Giải quyết thủ tục hành chính"),
    ("ASXH", "An sinh xã hội"),
]

# Cơ quan chủ chỉ tiêu và CSDL nguồn — bám Danh mục QĐ 2053/QĐ-UBND
CQ_STC = "Sở Tài chính"
CQ_TTPVHCC = "Trung tâm Phục vụ hành chính công tỉnh"
CQ_SNNMT = "Sở Nông nghiệp và Môi trường"
CQ_SNV = "Sở Nội vụ"

NGUON_DTC = (
    "CSDL thông tin Dự án Đầu tư công (vốn ngân sách tỉnh); "
    "CSDL quản lý ngân sách dự án đầu tư — Sở Tài chính"
)
NGUON_TTHC = "CSDL Hệ thống thông tin giải quyết TTHC tỉnh Thanh Hóa"
NGUON_HO_NGHEO = (
    "CSDL quản lý hộ nghèo, hộ cận nghèo toàn tỉnh "
    "(dữ liệu mở do UBND cấp xã cung cấp)"
)
NGUON_BTXH = "CSDL về Bảo trợ xã hội (chi trả trợ cấp)"

RB_PHAN_TRAM = "0 <= gia_tri <= 100"
RB_KHONG_AM = "gia_tri >= 0"
RB_LUY_KE = "gia_tri >= 0; canh_bao_neu_giam_so_ky_truoc"

# Kênh 2 (v0.2): cụm từ giúp máy nhận diện chỉ tiêu trong câu văn của văn bản
# — phải khớp với mẫu câu trong app/services/van_ban_mau.py
TU_KHOA_TRICH_XUAT = {
    "DTC01": ["kế hoạch vốn giao", "kế hoạch vốn"],
    "DTC02": ["giải ngân lũy kế", "đã giải ngân", "giá trị giải ngân"],
    "DTC03": ["tỷ lệ giải ngân"],
    "DTC04": ["dự án đang triển khai"],
    "DTC05": ["dự án chậm tiến độ", "dự án chậm"],
    "TTHC01": ["tiếp nhận"],
    "TTHC02": ["giải quyết đúng hạn", "đúng hạn"],
    "TTHC03": ["quá hạn"],
    "TTHC04": ["tỷ lệ đúng hạn"],
    "TTHC05": ["nộp trực tuyến"],
    "TTHC06": ["tỷ lệ hồ sơ trực tuyến"],
    "AS01": ["hộ nghèo"],
    "AS02": ["hộ cận nghèo"],
    "AS03": ["đối tượng bảo trợ", "bảo trợ xã hội đang hưởng"],
    "AS04": ["kinh phí chi trả"],
    "AS05": ["không dùng tiền mặt", "không tiền mặt"],
}

# Tháng có báo cáo điện tử trong Kho (nguồn kênh 2); các tháng trước lấy từ
# hệ thống nghiệp vụ (DTC/TTHC) hoặc nhập tại nguồn (ASXH) → trộn ~40/40/20
CAC_THANG_CO_VAN_BAN = (5, 6, 7)

# (mã, tên, lĩnh vực, đơn vị tính, cơ quan chủ, nguồn CSDL,
#  công thức, ràng buộc, công khai, định nghĩa bổ sung)
DS_CHI_TIEU = [
    (
        "DTC01",
        "Kế hoạch vốn giao",
        "DTC",
        "triệu đồng",
        CQ_STC,
        NGUON_DTC,
        None,
        RB_KHONG_AM,
        False,
        "Kế hoạch vốn đầu tư công giao đầu năm (quy ước demo: không đổi trong năm).",
    ),
    (
        "DTC02",
        "Giải ngân lũy kế",
        "DTC",
        "triệu đồng",
        CQ_STC,
        NGUON_DTC,
        None,
        RB_LUY_KE,
        False,
        "Giải ngân lũy kế từ đầu năm đến hết kỳ báo cáo; không vượt kế hoạch vốn.",
    ),
    (
        "DTC03",
        "Tỷ lệ giải ngân",
        "DTC",
        "%",
        CQ_STC,
        NGUON_DTC,
        "DTC02/DTC01*100",
        RB_PHAN_TRAM,
        True,
        "Chỉ tiêu dẫn xuất, hệ thống tự tính theo công thức — không nhập tay.",
    ),
    (
        "DTC04",
        "Số dự án đang triển khai",
        "DTC",
        "dự án",
        CQ_STC,
        NGUON_DTC,
        None,
        RB_KHONG_AM,
        False,
        "",
    ),
    (
        "DTC05",
        "Số dự án chậm tiến độ",
        "DTC",
        "dự án",
        CQ_STC,
        NGUON_DTC,
        None,
        RB_KHONG_AM,
        False,
        "",
    ),
    (
        "TTHC01",
        "Hồ sơ tiếp nhận",
        "TTHC",
        "hồ sơ",
        CQ_TTPVHCC,
        NGUON_TTHC,
        None,
        RB_KHONG_AM,
        False,
        "Hồ sơ TTHC tiếp nhận trong kỳ; mã TTHC theo CSDL quốc gia về TTHC.",
    ),
    (
        "TTHC02",
        "Hồ sơ giải quyết đúng hạn",
        "TTHC",
        "hồ sơ",
        CQ_TTPVHCC,
        NGUON_TTHC,
        None,
        RB_KHONG_AM,
        False,
        "",
    ),
    (
        "TTHC03",
        "Hồ sơ quá hạn",
        "TTHC",
        "hồ sơ",
        CQ_TTPVHCC,
        NGUON_TTHC,
        None,
        RB_KHONG_AM,
        False,
        "",
    ),
    (
        "TTHC04",
        "Tỷ lệ giải quyết đúng hạn",
        "TTHC",
        "%",
        CQ_TTPVHCC,
        NGUON_TTHC,
        "TTHC02/TTHC01*100",
        RB_PHAN_TRAM,
        True,
        "Chỉ tiêu dẫn xuất, hệ thống tự tính theo công thức — không nhập tay.",
    ),
    (
        "TTHC05",
        "Hồ sơ nộp trực tuyến",
        "TTHC",
        "hồ sơ",
        CQ_TTPVHCC,
        NGUON_TTHC,
        None,
        RB_KHONG_AM,
        False,
        "Đếm hồ sơ theo hình thức nộp/trả kết quả trực tuyến "
        "(trường HTTKQ ∈ {trực tuyến, trực tiếp, bưu chính}).",
    ),
    (
        "TTHC06",
        "Tỷ lệ hồ sơ trực tuyến",
        "TTHC",
        "%",
        CQ_TTPVHCC,
        NGUON_TTHC,
        "TTHC05/TTHC01*100",
        RB_PHAN_TRAM,
        True,
        "Chỉ tiêu dẫn xuất, hệ thống tự tính theo công thức — không nhập tay.",
    ),
    (
        "AS01",
        "Số hộ nghèo",
        "ASXH",
        "hộ",
        CQ_SNNMT,
        NGUON_HO_NGHEO,
        None,
        RB_KHONG_AM,
        False,
        "",
    ),
    (
        "AS02",
        "Số hộ cận nghèo",
        "ASXH",
        "hộ",
        CQ_SNNMT,
        NGUON_HO_NGHEO,
        None,
        RB_KHONG_AM,
        False,
        "",
    ),
    (
        "AS03",
        "Đối tượng bảo trợ xã hội hưởng trợ cấp",
        "ASXH",
        "người",
        CQ_SNV,
        NGUON_BTXH,
        None,
        RB_KHONG_AM,
        False,
        "Số đối tượng đang hưởng trợ cấp xã hội hằng tháng.",
    ),
    (
        "AS04",
        "Kinh phí chi trả tháng",
        "ASXH",
        "triệu đồng",
        CQ_SNV,
        NGUON_BTXH,
        None,
        RB_KHONG_AM,
        False,
        "Tổng kinh phí chi trả trợ cấp trong kỳ (trường KyChiTra).",
    ),
    (
        "AS05",
        "Tỷ lệ chi trả không dùng tiền mặt",
        "ASXH",
        "%",
        CQ_SNV,
        NGUON_BTXH,
        None,
        RB_PHAN_TRAM,
        True,
        "Không dùng tiền mặt = kỳ chi trả có hình thức chi trả qua tài khoản "
        "(các trường MaHinhThucChiTra, SoTaiKhoanNguoiNhan, MaNganHang).",
    ),
]


DUONG_DAN_DANH_MUC_DVHC = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "seed"
    / "donvi_hanhchinh_thanhhoa_166.json"
)


def kiem_tra_danh_muc_dvhc() -> None:
    """Đối chiếu 15 đơn vị demo với danh mục 166 xã/phường thật của tỉnh
    (mã ĐVHC 5 chữ số + tên phải khớp tuyệt đối) — chặn sai sót thủ công."""
    with open(DUONG_DAN_DANH_MUC_DVHC, encoding="utf-8") as f:
        danh_muc = {d["ma_dvhc"]: d["ten_day_du"] for d in json.load(f)["don_vi"]}
    for _ma, ten, _loai, _vung, ma_dvhc in DS_XA:
        if ma_dvhc not in danh_muc:
            raise SystemExit(
                f"Seed lỗi: mã ĐVHC {ma_dvhc} ({ten}) không có trong danh mục "
                "166 đơn vị hành chính."
            )
        if danh_muc[ma_dvhc] != ten:
            raise SystemExit(
                f"Seed lỗi: tên không khớp danh mục — '{ten}' ≠ "
                f"'{danh_muc[ma_dvhc]}' (mã {ma_dvhc})."
            )


def _ma_dinh_danh(so_thu_tu: int) -> str:
    """Sinh mã định danh điện tử cơ quan MÔ PHỎNG theo cấu trúc
    QCVN 102:2016/BTTTT (H56 = mã tỉnh Thanh Hóa).

    TODO: thay bằng mã định danh thật theo Danh mục Mã định danh điện tử
    của tỉnh (Sở Khoa học và Công nghệ) khi người dùng cung cấp.
    """
    return f"000.00.{so_thu_tu:02d}.H56"


def reset_db() -> None:
    """Xóa và tạo lại toàn bộ bảng + FTS5 + view chỉ đọc cho AI."""
    with engine.begin() as conn:
        for view in ("v_so_lieu", "v_don_vi", "v_chi_tieu", "v_van_ban"):
            conn.execute(text(f"DROP VIEW IF EXISTS {view}"))
        conn.execute(text("DROP TABLE IF EXISTS van_ban_fts"))
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with engine.begin() as conn:
        # Chỉ mục toàn văn FTS5 cho Lớp 1 (mỗi dòng = một đoạn văn bản)
        conn.execute(text("""
                CREATE VIRTUAL TABLE van_ban_fts USING fts5(
                    noi_dung,
                    van_ban_id UNINDEXED,
                    doan_id UNINDEXED
                )
                """))
        conn.execute(text("""
                CREATE VIEW v_so_lieu AS
                SELECT g.id,
                       c.ma  AS ma_chi_tieu,
                       c.ten AS ten_chi_tieu,
                       c.don_vi_tinh,
                       l.ma  AS ma_linh_vuc,
                       l.ten AS ten_linh_vuc,
                       d.ma  AS ma_don_vi,
                       d.ten AS ten_don_vi,
                       d.loai AS loai_don_vi,
                       d.vung AS vung,
                       g.nam,
                       g.thang,
                       (g.nam * 100 + g.thang) AS ky,
                       g.gia_tri,
                       g.nguon,
                       g.van_ban_id,
                       g.thoi_diem_cap_nhat
                FROM gia_tri_chi_tieu g
                JOIN chi_tieu c ON c.id = g.chi_tieu_id
                JOIN linh_vuc l ON l.id = c.linh_vuc_id
                JOIN don_vi d   ON d.id = g.don_vi_id
                """))
        conn.execute(text("""
                CREATE VIEW v_van_ban AS
                SELECT v.id, v.so, v.ky_hieu, v.loai, v.trich_yeu,
                       d.ten AS ten_co_quan, v.ngay_ban_hanh
                FROM van_ban v
                LEFT JOIN don_vi d ON d.id = v.co_quan_id
                WHERE v.mat = 0
                """))
        conn.execute(text("""
                CREATE VIEW v_don_vi AS
                SELECT id, ma, ma_dinh_danh, ma_dvhc, ten, loai, loai_dvhc,
                       vung, trang_thai
                FROM don_vi
                """))
        conn.execute(text("""
                CREATE VIEW v_chi_tieu AS
                SELECT c.id, c.ma, c.ten, c.don_vi_tinh, c.tan_suat,
                       c.co_quan_chu_chi_tieu, c.nguon_du_lieu, c.muc_chia_se,
                       c.cong_thuc, c.cong_khai,
                       l.ma AS ma_linh_vuc, l.ten AS ten_linh_vuc
                FROM chi_tieu c
                JOIN linh_vuc l ON l.id = c.linh_vuc_id
                """))


def seed_don_vi(db: Session) -> dict[str, DonVi]:
    """Tạo 15 xã/phường + 5 sở ngành + 1 tỉnh; trả về map mã → đơn vị."""
    ket_qua: dict[str, DonVi] = {}
    so_thu_tu = 10  # phần mã cơ quan trong mã định danh mô phỏng
    for ma, ten, loai, vung, ma_dvhc in DS_XA:
        dv = DonVi(
            ma=ma,
            ma_dinh_danh=_ma_dinh_danh(so_thu_tu),
            ma_dvhc=ma_dvhc,
            ten=ten,
            loai=loai,
            loai_dvhc=rng.choice(["I", "II", "III"]),
            vung=vung,
        )
        db.add(dv)
        ket_qua[ma] = dv
        so_thu_tu += 1
    for i, (ma, ten, loai) in enumerate(DS_SO_NGANH, start=1):
        dv = DonVi(
            ma=ma,
            ma_dinh_danh=_ma_dinh_danh(i),
            ten=ten,
            loai=loai,
            vung=None,
        )
        db.add(dv)
        ket_qua[ma] = dv
    tinh = DonVi(
        ma="TINH",
        ma_dinh_danh="000.00.00.H56",
        ten="UBND tỉnh Thanh Hóa",
        loai="tinh",
        vung=None,
    )
    db.add(tinh)
    ket_qua["TINH"] = tinh
    db.flush()
    return ket_qua


def seed_danh_muc(db: Session) -> dict[str, ChiTieu]:
    """Tạo lĩnh vực, chỉ tiêu và mẫu báo cáo; trả về map mã → chỉ tiêu."""
    map_lv: dict[str, LinhVuc] = {}
    for ma, ten in DS_LINH_VUC:
        lv = LinhVuc(ma=ma, ten=ten)
        db.add(lv)
        map_lv[ma] = lv
    db.flush()

    map_ct: dict[str, ChiTieu] = {}
    for (
        ma,
        ten,
        ma_lv,
        dvt,
        co_quan,
        nguon_du_lieu,
        cong_thuc,
        rang_buoc,
        cong_khai,
        dinh_nghia,
    ) in DS_CHI_TIEU:
        ct = ChiTieu(
            ma=ma,
            ten=ten,
            linh_vuc_id=map_lv[ma_lv].id,
            don_vi_tinh=dvt,
            tan_suat="thang",
            co_quan_chu_chi_tieu=co_quan,
            nguon_du_lieu=nguon_du_lieu,
            muc_chia_se="mo" if cong_khai else "dung_chung",
            cong_thuc=cong_thuc,
            rang_buoc=rang_buoc,
            tu_khoa_trich_xuat=json.dumps(
                TU_KHOA_TRICH_XUAT.get(ma, []), ensure_ascii=False
            ),
            dinh_nghia=dinh_nghia
            or f"Chỉ tiêu {ten.lower()} theo kỳ báo cáo tháng (dữ liệu mô phỏng).",
            cong_khai=cong_khai,
        )
        db.add(ct)
        map_ct[ma] = ct

    db.add_all(
        [
            MauBaoCao(
                ma="BC-DTC",
                ten="Báo cáo tình hình giải ngân vốn đầu tư công tháng",
                linh_vuc_id=map_lv["DTC"].id,
                mo_ta="Mẫu báo cáo tháng về giải ngân vốn đầu tư công của UBND cấp xã.",
            ),
            MauBaoCao(
                ma="BC-TTHC",
                ten="Báo cáo kết quả giải quyết thủ tục hành chính tháng",
                linh_vuc_id=map_lv["TTHC"].id,
                mo_ta="Mẫu báo cáo tháng về giải quyết TTHC của UBND cấp xã.",
            ),
        ]
    )
    db.flush()
    return map_ct


def seed_nguoi_dung(db: Session, map_dv: dict[str, DonVi]) -> dict[str, NguoiDung]:
    """Tạo 4 tài khoản demo (mật khẩu ghi trong README, chỉ dùng demo).

    Email công vụ dạng @thanhhoa.gov.vn là MÔ PHỎNG (nguồn chuẩn thực tế:
    CSDL cán bộ, công chức, viên chức tỉnh Thanh Hóa).
    """
    hash_chung = hash_mat_khau(MAT_KHAU_DEMO)
    ds = [
        NguoiDung(
            ten_dang_nhap="admin",
            mat_khau_hash=hash_chung,
            ho_ten="Quản trị hệ thống",
            email="admin.demo@thanhhoa.gov.vn",
            vai_tro="quan_tri",
            don_vi_id=map_dv["VPUBND"].id,
        ),
        NguoiDung(
            ten_dang_nhap="lanhdao",
            mat_khau_hash=hash_chung,
            ho_ten="Lãnh đạo UBND tỉnh",
            email="lanhdao.demo@thanhhoa.gov.vn",
            vai_tro="lanh_dao",
            don_vi_id=map_dv["TINH"].id,
        ),
        NguoiDung(
            ten_dang_nhap="xa.hacthanh",
            mat_khau_hash=hash_chung,
            ho_ten="Chuyên viên phường Hạc Thành",
            email="hacthanh.demo@thanhhoa.gov.vn",
            vai_tro="chuyen_vien_xa",
            don_vi_id=map_dv["HACTHANH"].id,
        ),
        NguoiDung(
            ten_dang_nhap="daibieu",
            mat_khau_hash=hash_chung,
            ho_ten="Đại biểu HĐND tỉnh",
            email="daibieu.demo@thanhhoa.gov.vn",
            vai_tro="dai_bieu_hdnd",
            don_vi_id=map_dv["TINH"].id,
        ),
    ]
    db.add_all(ds)
    db.flush()
    return {nd.ten_dang_nhap: nd for nd in ds}


def _thoi_diem_cap_nhat(thang: int) -> datetime:
    """Thời điểm cập nhật rải trong tháng: số liệu tháng M chốt đầu tháng M+1;
    riêng tháng 7 (kỳ hiện tại) cập nhật giữa tháng 7."""
    if thang < 7:
        return datetime(NAM, thang + 1, rng.randint(2, 10), rng.randint(8, 17))
    return datetime(NAM, 7, rng.randint(18, 23), rng.randint(8, 17))


def _sinh_giai_ngan(ma_xa: str, he_so: float) -> dict[str, list[float]]:
    """Sinh chuỗi 7 tháng cho nhóm chỉ tiêu DTC của một xã."""
    ke_hoach = round(he_so * rng.uniform(30_000, 60_000), 0)

    # Tỷ lệ giải ngân đích ở tháng 7
    if ma_xa in XA_GIAI_NGAN_THAP:
        ty_le_t7 = rng.uniform(0.18, 0.28)  # điểm nóng: dưới 30%
    else:
        ty_le_t7 = rng.uniform(0.38, 0.72)

    # Lũy kế tăng dần: cộng dồn trọng số ngẫu nhiên rồi quy về tỷ lệ tháng 7
    trong_so = [rng.uniform(0.5, 1.5) for _ in CAC_THANG]
    tong = sum(trong_so)
    luy_ke: list[float] = []
    cong_don = 0.0
    for w in trong_so:
        cong_don += w
        luy_ke.append(round(ke_hoach * ty_le_t7 * cong_don / tong, 0))

    # Điểm nóng: xã có lũy kế tháng 6 giảm nhẹ so tháng 5 (nghi sai số liệu)
    if ma_xa == XA_MAU_THUAN_T6:
        luy_ke[5] = round(luy_ke[4] * 0.97, 0)

    ty_le = [round(gn / ke_hoach * 100, 1) for gn in luy_ke]
    so_du_an = rng.randint(4, 8) + int(he_so * 6)
    du_an_cham_max = 4 if ma_xa in XA_GIAI_NGAN_THAP else 2
    return {
        "DTC01": [ke_hoach] * 7,
        "DTC02": luy_ke,
        "DTC03": ty_le,
        "DTC04": [so_du_an + rng.randint(-1, 1) for _ in CAC_THANG],
        "DTC05": [
            rng.randint(1 if ma_xa in XA_GIAI_NGAN_THAP else 0, du_an_cham_max)
            for _ in CAC_THANG
        ],
    }


def _sinh_tthc(ma_xa: str, he_so: float, vung: str) -> dict[str, list[float]]:
    """Sinh chuỗi 7 tháng cho nhóm chỉ tiêu TTHC của một xã."""
    tiep_nhan = [int(he_so * rng.uniform(150, 400)) for _ in CAC_THANG]
    ty_le_dung_han, dung_han, qua_han = [], [], []
    for i, tn in enumerate(tiep_nhan):
        if ma_xa in XA_TTHC_THAP and i == 6:  # tháng 7: điểm nóng dưới 90%
            ty_le = rng.uniform(0.84, 0.895)
        else:
            ty_le = rng.uniform(0.92, 0.995)
        dh = int(tn * ty_le)
        dung_han.append(dh)
        qua_han.append(tn - dh)
        ty_le_dung_han.append(round(dh / tn * 100, 1))

    # Hồ sơ trực tuyến: đô thị cao hơn, xu hướng tăng dần theo tháng
    muc_truc_tuyen = {"do_thi": 0.65, "dong_bang": 0.5, "mien_nui": 0.35}[vung]
    truc_tuyen, ty_le_tt = [], []
    for i, tn in enumerate(tiep_nhan):
        ty_le = min(0.95, muc_truc_tuyen + 0.02 * i + rng.uniform(-0.05, 0.05))
        tt = int(tn * ty_le)
        truc_tuyen.append(tt)
        ty_le_tt.append(round(tt / tn * 100, 1))

    return {
        "TTHC01": tiep_nhan,
        "TTHC02": dung_han,
        "TTHC03": qua_han,
        "TTHC04": ty_le_dung_han,
        "TTHC05": truc_tuyen,
        "TTHC06": ty_le_tt,
    }


def _sinh_asxh(he_so: float, vung: str) -> dict[str, list[float]]:
    """Sinh chuỗi 7 tháng cho nhóm chỉ tiêu ASXH của một xã."""
    # Hộ nghèo/cận nghèo: miền núi cao hơn, giảm nhẹ qua các tháng
    muc_ngheo = {"do_thi": 40, "dong_bang": 90, "mien_nui": 220}[vung]
    ho_ngheo_dau = int(muc_ngheo * rng.uniform(0.8, 1.3))
    ho_can_ngheo_dau = int(ho_ngheo_dau * rng.uniform(1.1, 1.5))
    ho_ngheo = [max(0, ho_ngheo_dau - rng.randint(0, 3) * i) for i in range(7)]
    ho_can_ngheo = [max(0, ho_can_ngheo_dau - rng.randint(0, 4) * i) for i in range(7)]

    bao_tro = int(he_so * rng.uniform(250, 500))
    doi_tuong = [bao_tro + rng.randint(-10, 10) for _ in CAC_THANG]
    kinh_phi = [round(dt * rng.uniform(0.54, 0.62), 1) for dt in doi_tuong]

    muc_ktm = {"do_thi": 55, "dong_bang": 38, "mien_nui": 22}[vung]
    khong_tien_mat = [
        round(min(95.0, muc_ktm + 2.5 * i + rng.uniform(-3, 3)), 1) for i in range(7)
    ]
    return {
        "AS01": ho_ngheo,
        "AS02": ho_can_ngheo,
        "AS03": doi_tuong,
        "AS04": kinh_phi,
        "AS05": khong_tien_mat,
    }


def _sinh_chuoi_xa(ma_xa: str, vung: str) -> dict[str, list[float]]:
    """Chuỗi 7 tháng của toàn bộ 16 chỉ tiêu cho một xã."""
    he_so = HE_SO_VUNG[vung] * rng.uniform(0.85, 1.15)
    chuoi: dict[str, list[float]] = {}
    chuoi.update(_sinh_giai_ngan(ma_xa, he_so))
    chuoi.update(_sinh_tthc(ma_xa, he_so, vung))
    chuoi.update(_sinh_asxh(he_so, vung))
    return chuoi


def _tao_van_ban_bao_cao(
    db: Session, dv: DonVi, thang: int, so_lieu_ky: dict[str, float]
) -> VanBan:
    """Tạo một báo cáo tháng ở Lớp 1 (toàn văn + đoạn + chỉ mục FTS5)."""
    cac_doan = van_ban_mau.noi_dung_bao_cao(dv.ten, thang, NAM, so_lieu_ky)
    vb = VanBan(
        so=f"{rng.randint(30, 99)}",
        ky_hieu=f"BC-UBND-{dv.ma}",
        loai="bao_cao",
        trich_yeu=van_ban_mau.trich_yeu_bao_cao(thang, NAM),
        co_quan_id=dv.id,
        ngay_ban_hanh=date(NAM, thang, min(28, rng.randint(18, 26))),
        duong_dan_file=f"data/seed/van_ban_mau/bao-cao-{dv.ma.lower()}-{NAM}"
        f"{thang:02d}.docx",
        toan_van="\n\n".join(cac_doan),
        mat=False,
        thoi_diem_tiep_nhan=datetime(NAM, thang, min(28, rng.randint(18, 26)), 9),
    )
    db.add(vb)
    db.flush()
    for i, doan in enumerate(cac_doan):
        db.add(VanBanDoan(van_ban_id=vb.id, thu_tu=i, noi_dung=doan))
    db.flush()
    for doan in vb.cac_doan:
        db.execute(
            text(
                "INSERT INTO van_ban_fts (noi_dung, van_ban_id, doan_id) "
                "VALUES (:nd, :vb, :d)"
            ),
            {"nd": doan.noi_dung, "vb": vb.id, "d": doan.id},
        )
    return vb


def seed_van_ban_khac(db: Session, map_dv: dict[str, DonVi]) -> None:
    """2 văn bản khác loại (kế hoạch, thông báo) + 1 văn bản MẬT minh họa."""
    ds = [
        VanBan(
            so="12",
            ky_hieu="KH-STC",
            loai="ke_hoach",
            trich_yeu="Kế hoạch đôn đốc giải ngân vốn đầu tư công những tháng "
            f"cuối năm {NAM}",
            co_quan_id=map_dv["STC"].id,
            ngay_ban_hanh=date(NAM, 7, 10),
            toan_van="Sở Tài chính xây dựng kế hoạch đôn đốc giải ngân vốn đầu "
            f"tư công những tháng cuối năm {NAM}. Mục tiêu: toàn tỉnh đạt tối "
            "thiểu 95% kế hoạch vốn; các xã có tỷ lệ giải ngân dưới 30% phải "
            "cam kết mốc giải ngân từng tháng. Nguyên nhân chậm chủ yếu do "
            "vướng mắc giải phóng mặt bằng và năng lực một số nhà thầu hạn "
            "chế; yêu cầu các chủ đầu tư khẩn trương hoàn thiện hồ sơ nghiệm "
            "thu, thanh toán ngay khi có khối lượng./.",
            mat=False,
            thoi_diem_tiep_nhan=datetime(NAM, 7, 10, 14),
        ),
        VanBan(
            so="45",
            ky_hieu="TB-VPUBND",
            loai="thong_bao",
            trich_yeu="Thông báo kết luận của Chủ tịch UBND tỉnh tại hội nghị "
            "đẩy nhanh giải ngân và chuyển đổi số dữ liệu báo cáo",
            co_quan_id=map_dv["VPUBND"].id,
            ngay_ban_hanh=date(NAM, 7, 15),
            toan_van="Chủ tịch UBND tỉnh kết luận: các sở, ngành khai thác số "
            "liệu trực tiếp trên Kho dữ liệu dùng chung, không yêu cầu UBND "
            "cấp xã báo cáo lại số liệu đã có trong Kho. Giao Sở Tài chính "
            "theo dõi các xã giải ngân chậm, báo cáo Chủ tịch UBND tỉnh qua "
            "bản tin điều hành hằng tuần./.",
            mat=False,
            thoi_diem_tiep_nhan=datetime(NAM, 7, 15, 16),
        ),
        VanBan(
            so="07",
            ky_hieu="CV-MAT",
            loai="cong_van",
            trich_yeu="Văn bản MẬT minh họa — nội dung không được đưa vào Kho",
            co_quan_id=map_dv["VPUBND"].id,
            ngay_ban_hanh=date(NAM, 7, 5),
            toan_van="NỘI DUNG MẬT MÔ PHỎNG — văn bản này phải bị chặn khỏi "
            "tìm kiếm, AI và máy trích xuất. Cụm từ nhận diện: bi-mat-demo.",
            mat=True,
            thoi_diem_tiep_nhan=datetime(NAM, 7, 5, 10),
        ),
    ]
    db.add_all(ds)
    db.flush()
    # Chia đoạn + FTS cho văn bản KHÔNG mật (văn bản mật không được lập chỉ mục)
    for vb in ds:
        if vb.mat:
            continue
        for i, doan in enumerate(vb.toan_van.split("\n\n")):
            d = VanBanDoan(van_ban_id=vb.id, thu_tu=i, noi_dung=doan)
            db.add(d)
            db.flush()
            db.execute(
                text(
                    "INSERT INTO van_ban_fts (noi_dung, van_ban_id, doan_id) "
                    "VALUES (:nd, :vb, :d)"
                ),
                {"nd": doan, "vb": vb.id, "d": d.id},
            )


def seed_gia_tri(
    db: Session,
    map_dv: dict[str, DonVi],
    map_ct: dict[str, ChiTieu],
    map_nd: dict[str, NguoiDung],
) -> int:
    """Sinh giá trị tháng 01–07/2026 cho 15 xã, TRỘN ĐỦ 3 NGUỒN (v0.2):

    - Tháng 1–4: DTC/TTHC từ `he_thong` (kênh 1), ASXH `nhap_tay` (kênh 3);
    - Tháng 5–7: toàn bộ từ `van_ban` (kênh 2) — mỗi xã mỗi tháng có một
      báo cáo điện tử ở Lớp 1, giá trị liên kết van_ban_id + người xác nhận.
    - Riêng phường Hạc Thành KHÔNG có báo cáo tháng 7 trong Kho (file .docx
      để người demo tải lên theo kịch bản Mục 13); các ô DTC02/DTC03/AS04
      tháng 7 để trống chờ kênh 2.
    """
    so_ban_ghi = 0
    id_xa_hacthanh = map_nd["xa.hacthanh"].id
    id_admin = map_nd["admin"].id

    for ma_xa, _ten, _loai, vung, _ma_dvhc in DS_XA:
        dv = map_dv[ma_xa]
        chuoi = _sinh_chuoi_xa(ma_xa, vung)

        # Văn bản báo cáo tháng 5–7 của xã (Hạc Thành: bỏ tháng 7 — chờ tải lên)
        van_ban_theo_thang: dict[int, VanBan] = {}
        for thang in CAC_THANG_CO_VAN_BAN:
            if ma_xa == XA_NHAP_DEMO and thang == 7:
                continue
            so_lieu_ky = {ma: chuoi[ma][thang - 1] for ma in chuoi}
            van_ban_theo_thang[thang] = _tao_van_ban_bao_cao(db, dv, thang, so_lieu_ky)

        for ma_ct, gia_tri_7_thang in chuoi.items():
            for i, thang in enumerate(CAC_THANG):
                if thang == 7 and (ma_ct, ma_xa) in O_TRONG_THANG_7:
                    continue  # để trống cho kịch bản kênh 2 / cảnh báo
                vb = van_ban_theo_thang.get(thang)
                if thang in CAC_THANG_CO_VAN_BAN and vb is not None:
                    nguon, van_ban_id = "van_ban", vb.id
                    nguoi_xac_nhan = (
                        id_xa_hacthanh if ma_xa == XA_NHAP_DEMO else id_admin
                    )
                elif thang in CAC_THANG_CO_VAN_BAN:
                    # Hạc Thành tháng 7: chưa có văn bản → tạm từ hệ thống
                    nguon, van_ban_id, nguoi_xac_nhan = "he_thong", None, None
                elif ma_ct.startswith("AS"):
                    nguon, van_ban_id = "nhap_tay", None
                    nguoi_xac_nhan = id_xa_hacthanh if ma_xa == XA_NHAP_DEMO else None
                else:
                    nguon, van_ban_id, nguoi_xac_nhan = "he_thong", None, None
                db.add(
                    GiaTriChiTieu(
                        chi_tieu_id=map_ct[ma_ct].id,
                        don_vi_id=dv.id,
                        nam=NAM,
                        thang=thang,
                        gia_tri=float(gia_tri_7_thang[i]),
                        nguon=nguon,
                        van_ban_id=van_ban_id,
                        nguoi_xac_nhan_id=nguoi_xac_nhan,
                        thoi_diem_cap_nhat=_thoi_diem_cap_nhat(thang),
                    )
                )
                so_ban_ghi += 1
    db.flush()
    return so_ban_ghi


def seed_hang_cho_ton_dong(db: Session, map_dv: dict[str, DonVi]) -> None:
    """2 dòng hàng chờ xác nhận TỒN ĐỌNG QUÁ 3 NGÀY (luật cảnh báo 8.8 v0.2):
    báo cáo tháng 7 của Xã Ngọc Lặc có 2 số máy đọc chưa ai xác nhận."""
    dv = map_dv["NGOCLAC"]
    vb = (
        db.query(VanBan)
        .filter(VanBan.co_quan_id == dv.id, VanBan.loai == "bao_cao")
        .order_by(VanBan.ngay_ban_hanh.desc())
        .first()
    )
    if vb is None:
        return
    ct_dtc04 = db.query(ChiTieu).filter_by(ma="DTC04").one()
    ct_dtc05 = db.query(ChiTieu).filter_by(ma="DTC05").one()
    ngay_cu = datetime(NAM, 7, 19, 8)  # ~5 ngày trước "hôm nay" của demo
    db.add_all(
        [
            TrichXuatCho(
                van_ban_id=vb.id,
                chi_tieu_id=ct_dtc04.id,
                don_vi_id=dv.id,
                nam=NAM,
                thang=7,
                gia_tri_may_doc=12,
                doan_trich="Toàn địa bàn có 12 dự án đang triển khai, trong "
                "đó có 2 dự án chậm tiến độ.",
                do_tin_cay="trung_binh",
                trang_thai="cho_xac_nhan",
                thoi_diem=ngay_cu,
            ),
            TrichXuatCho(
                van_ban_id=vb.id,
                chi_tieu_id=ct_dtc05.id,
                don_vi_id=dv.id,
                nam=NAM,
                thang=7,
                gia_tri_may_doc=2,
                doan_trich="Toàn địa bàn có 12 dự án đang triển khai, trong "
                "đó có 2 dự án chậm tiến độ.",
                do_tin_cay="cao",
                trang_thai="cho_xac_nhan",
                thoi_diem=ngay_cu,
            ),
        ]
    )


def seed_nghi_quyet(db: Session, map_ct: dict[str, ChiTieu]) -> None:
    """Tạo các nghị quyết HĐND theo dõi (demo 4 bản ghi)."""
    db.add_all(
        [
            NghiQuyetTheoDoi(
                so_ky_hieu="12/NQ-HĐND",
                trich_yeu="Phấn đấu tỷ lệ giải ngân vốn đầu tư công toàn tỉnh "
                "đạt tối thiểu 95% kế hoạch năm 2026.",
                chi_tieu_id=map_ct["DTC03"].id,
                gia_tri_muc_tieu=95.0,
                han_hoan_thanh=date(2026, 12, 31),
            ),
            NghiQuyetTheoDoi(
                so_ky_hieu="15/NQ-HĐND",
                trich_yeu="Tỷ lệ hồ sơ thủ tục hành chính giải quyết đúng hạn "
                "đạt tối thiểu 98%.",
                chi_tieu_id=map_ct["TTHC04"].id,
                gia_tri_muc_tieu=98.0,
                han_hoan_thanh=date(2026, 12, 31),
            ),
            NghiQuyetTheoDoi(
                so_ky_hieu="18/NQ-HĐND",
                trich_yeu="Tỷ lệ hồ sơ nộp trực tuyến toàn tỉnh đạt tối thiểu 70%.",
                chi_tieu_id=map_ct["TTHC06"].id,
                gia_tri_muc_tieu=70.0,
                han_hoan_thanh=date(2026, 12, 31),
            ),
            NghiQuyetTheoDoi(
                so_ky_hieu="21/NQ-HĐND",
                trich_yeu="Tỷ lệ chi trả an sinh xã hội không dùng tiền mặt "
                "đạt tối thiểu 60%.",
                chi_tieu_id=map_ct["AS05"].id,
                gia_tri_muc_tieu=60.0,
                han_hoan_thanh=date(2026, 12, 31),
            ),
        ]
    )


def seed_kiem_ke(db: Session) -> None:
    """Danh sách chế độ báo cáo cấp xã đang phải làm (phân hệ 8.8) —
    cài sẵn 3 cặp nghi trùng lặp để demo chức năng phát hiện."""
    ds = [
        # (tên báo cáo, cơ quan yêu cầu, tần suất, căn cứ)
        (
            "Báo cáo tình hình giải ngân vốn đầu tư công",
            "Sở Tài chính",
            "thang",
            "Công văn đôn đốc giải ngân hằng tháng",
        ),
        (
            "Báo cáo kết quả giải ngân vốn đầu tư công",
            "Văn phòng UBND tỉnh",
            "thang",
            "Phục vụ họp giao ban kinh tế - xã hội",
        ),  # trùng với trên
        (
            "Báo cáo kết quả giải quyết thủ tục hành chính",
            "Trung tâm Phục vụ hành chính công tỉnh",
            "thang",
            "Chế độ báo cáo định kỳ về kiểm soát TTHC",
        ),
        (
            "Báo cáo tình hình giải quyết thủ tục hành chính",
            "Sở Nội vụ",
            "quy",
            "Phục vụ chấm chỉ số cải cách hành chính",
        ),  # trùng với trên
        (
            "Báo cáo rà soát hộ nghèo, hộ cận nghèo",
            "Sở Nông nghiệp và Môi trường",
            "6_thang",
            "Quy trình rà soát hộ nghèo định kỳ",
        ),
        (
            "Báo cáo tình hình rà soát hộ nghèo, cận nghèo trên địa bàn",
            "Văn phòng UBND tỉnh",
            "nam",
            "Tổng hợp an sinh cuối năm",
        ),  # trùng
        (
            "Báo cáo chi trả trợ cấp bảo trợ xã hội",
            "Sở Nội vụ",
            "thang",
            "Theo dõi chi trả trợ cấp hằng tháng",
        ),
        (
            "Báo cáo tình hình kinh tế - xã hội",
            "Văn phòng UBND tỉnh",
            "thang",
            "Phục vụ phiên họp thường kỳ UBND tỉnh",
        ),
        (
            "Báo cáo công tác chuyển đổi số",
            "Sở Khoa học và Công nghệ",
            "quy",
            "Kế hoạch chuyển đổi số của tỉnh",
        ),
        (
            "Báo cáo công tác tiếp công dân, giải quyết khiếu nại, tố cáo",
            "Thanh tra tỉnh",
            "thang",
            "Luật Tiếp công dân",
        ),
        (
            "Báo cáo phòng, chống thiên tai và tìm kiếm cứu nạn",
            "Sở Nông nghiệp và Môi trường",
            "dot_xuat",
            "Theo mùa mưa bão, khi có tình huống",
        ),
        (
            "Báo cáo kết quả thực hiện chương trình nông thôn mới",
            "Sở Nông nghiệp và Môi trường",
            "quy",
            "Chương trình mục tiêu quốc gia",
        ),
    ]
    db.add_all(
        KiemKeBaoCao(
            ten_bao_cao=ten,
            co_quan_yeu_cau=co_quan,
            tan_suat=tan_suat,
            can_cu=can_cu,
        )
        for ten, co_quan, tan_suat, can_cu in ds
    )


def seed_all(db: Session) -> dict[str, int]:
    """Chạy toàn bộ các bước seed trên một phiên CSDL; trả về thống kê."""
    kiem_tra_danh_muc_dvhc()
    map_dv = seed_don_vi(db)
    map_ct = seed_danh_muc(db)
    map_nd = seed_nguoi_dung(db, map_dv)
    so_gia_tri = seed_gia_tri(db, map_dv, map_ct, map_nd)
    seed_van_ban_khac(db, map_dv)
    seed_hang_cho_ton_dong(db, map_dv)
    seed_nghi_quyet(db, map_ct)
    seed_kiem_ke(db)
    db.commit()
    so_van_ban = db.query(VanBan).count()
    # Bản ghi mở đầu chuỗi nhật ký chống sửa lén (hash chain)
    audit.ghi_nhat_ky(
        db,
        map_nd["admin"].id,
        "khoi_tao_du_lieu",
        f"Seed dữ liệu mô phỏng: {so_gia_tri} giá trị chỉ tiêu (Lớp 2), "
        f"{so_van_ban} văn bản (Lớp 1).",
    )
    return {
        "don_vi": len(map_dv),
        "chi_tieu": len(map_ct),
        "nguoi_dung": len(map_nd),
        "gia_tri": so_gia_tri,
        "van_ban": so_van_ban,
    }


def main() -> None:
    reset_db()
    db = SessionLocal()
    try:
        thong_ke = seed_all(db)
    finally:
        db.close()
    print("Đã tạo xong CSDL dữ liệu mô phỏng:")
    print(f"  - Đơn vị:            {thong_ke['don_vi']}")
    print(f"  - Chỉ tiêu:          {thong_ke['chi_tieu']}")
    print(
        f"  - Người dùng:        {thong_ke['nguoi_dung']} "
        f"(mật khẩu demo: {MAT_KHAU_DEMO})"
    )
    print(f"  - Giá trị chỉ tiêu:  {thong_ke['gia_tri']} bản ghi (tháng 01–07/{NAM})")
    print(f"  - Văn bản Lớp 1:     {thong_ke['van_ban']} (kèm đoạn + chỉ mục FTS5)")
    print("Lưu ý: toàn bộ là DỮ LIỆU MÔ PHỎNG phục vụ trình diễn.")
    print("Chạy tiếp: python scripts/make_sample_docs.py để xuất file .docx mẫu.")


if __name__ == "__main__":
    main()
