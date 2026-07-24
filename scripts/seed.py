"""Tạo CSDL và dữ liệu mô phỏng cho bản demo.

Chạy:  python scripts/seed.py

Toàn bộ số liệu là DỮ LIỆU MÔ PHỎNG phục vụ trình diễn, sinh ngẫu nhiên có
chủ đích (seed cố định để tái lập được), kèm các "điểm nóng" phục vụ kịch
bản demo 5 phút (xem CLAUDE.md Mục 7 và 13).
"""

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
    LinhVuc,
    MauBaoCao,
    NghiQuyetTheoDoi,
    NguoiDung,
    NhatKy,
)

NAM = 2026
CAC_THANG = list(range(1, 8))  # tháng 01–07/2026
MAT_KHAU_DEMO = "Demo@2026"

rng = random.Random(2026)  # seed cố định để dữ liệu tái lập được

# ---------------------------------------------------------------------------
# Danh mục đơn vị
# ---------------------------------------------------------------------------
# 5 tên xã/phường thật đã đối chiếu theo Nghị quyết 1686/NQ-UBTVQH15.
# TODO: thay 10 tên placeholder "Xã Demo 06"…"Xã Demo 15" bằng tên xã/phường
# thật do người dùng cung cấp — KHÔNG tự bịa tên xã.
DS_XA = [
    # (mã, tên, loại, vùng)
    ("HACTHANH", "Phường Hạc Thành", "phuong", "do_thi"),
    ("CACSON", "Xã Các Sơn", "xa", "mien_nui"),
    ("NGASON", "Xã Nga Sơn", "xa", "dong_bang"),
    ("TANTHANH", "Xã Tân Thành", "xa", "dong_bang"),
    ("THANGLOC", "Xã Thắng Lộc", "xa", "mien_nui"),
    ("DEMO06", "Xã Demo 06", "phuong", "do_thi"),
    ("DEMO07", "Xã Demo 07", "phuong", "do_thi"),
    ("DEMO08", "Xã Demo 08", "xa", "dong_bang"),
    ("DEMO09", "Xã Demo 09", "xa", "dong_bang"),
    ("DEMO10", "Xã Demo 10", "xa", "dong_bang"),
    ("DEMO11", "Xã Demo 11", "xa", "dong_bang"),
    ("DEMO12", "Xã Demo 12", "xa", "mien_nui"),
    ("DEMO13", "Xã Demo 13", "xa", "mien_nui"),
    ("DEMO14", "Xã Demo 14", "xa", "mien_nui"),
    ("DEMO15", "Xã Demo 15", "xa", "mien_nui"),
]

DS_SO_NGANH = [
    ("STC", "Sở Tài chính", "so_nganh"),
    ("SNV", "Sở Nội vụ", "so_nganh"),
    ("VPUBND", "Văn phòng UBND tỉnh", "so_nganh"),
]

# Hệ số quy mô theo vùng (xã đô thị > đồng bằng > miền núi)
HE_SO_VUNG = {"do_thi": 1.6, "dong_bang": 1.0, "mien_nui": 0.65}

# Điểm nóng cài sẵn phục vụ demo (CLAUDE.md Mục 7)
XA_GIAI_NGAN_THAP = {"CACSON", "DEMO12"}  # tỷ lệ giải ngân tháng 7 < 30%
XA_TTHC_THAP = {"DEMO09", "TANTHANH"}  # tỷ lệ đúng hạn TTHC tháng 7 < 90%
XA_MAU_THUAN_T6 = "DEMO11"  # lũy kế tháng 6 giảm nhẹ so tháng 5
XA_NHAP_DEMO = "HACTHANH"  # để trống vài ô tháng 7 cho kịch bản nhập liệu
XA_THIEU_SO_LIEU = "DEMO15"  # thiếu vài chỉ tiêu tháng 7 → cảnh báo

# Ô để trống tháng 7 (chỉ tiêu, mã xã): người demo sẽ nhập tay
O_TRONG_THANG_7 = {
    ("DTC02", "HACTHANH"),
    ("DTC03", "HACTHANH"),  # tỷ lệ tính từ DTC02 nên trống theo
    ("AS04", "HACTHANH"),
    ("TTHC05", "DEMO15"),
    ("TTHC06", "DEMO15"),
    ("AS05", "DEMO15"),
}

# ---------------------------------------------------------------------------
# Danh mục lĩnh vực và chỉ tiêu
# ---------------------------------------------------------------------------
DS_LINH_VUC = [
    ("DTC", "Giải ngân vốn đầu tư công"),
    ("TTHC", "Giải quyết thủ tục hành chính"),
    ("ASXH", "An sinh xã hội"),
]

# (mã, tên, lĩnh vực, đơn vị tính, cơ quan chủ chỉ tiêu, công khai)
DS_CHI_TIEU = [
    ("DTC01", "Kế hoạch vốn giao", "DTC", "triệu đồng", "Sở Tài chính", False),
    ("DTC02", "Giải ngân lũy kế", "DTC", "triệu đồng", "Sở Tài chính", False),
    ("DTC03", "Tỷ lệ giải ngân", "DTC", "%", "Sở Tài chính", True),
    ("DTC04", "Số dự án đang triển khai", "DTC", "dự án", "Sở Tài chính", False),
    ("DTC05", "Số dự án chậm tiến độ", "DTC", "dự án", "Sở Tài chính", False),
    ("TTHC01", "Hồ sơ tiếp nhận", "TTHC", "hồ sơ", "Sở Nội vụ", False),
    ("TTHC02", "Hồ sơ giải quyết đúng hạn", "TTHC", "hồ sơ", "Sở Nội vụ", False),
    ("TTHC03", "Hồ sơ quá hạn", "TTHC", "hồ sơ", "Sở Nội vụ", False),
    ("TTHC04", "Tỷ lệ giải quyết đúng hạn", "TTHC", "%", "Sở Nội vụ", True),
    ("TTHC05", "Hồ sơ nộp trực tuyến", "TTHC", "hồ sơ", "Sở Nội vụ", False),
    ("TTHC06", "Tỷ lệ hồ sơ trực tuyến", "TTHC", "%", "Sở Nội vụ", True),
    ("AS01", "Số hộ nghèo", "ASXH", "hộ", "Sở Nội vụ", False),
    ("AS02", "Số hộ cận nghèo", "ASXH", "hộ", "Sở Nội vụ", False),
    (
        "AS03",
        "Đối tượng bảo trợ xã hội hưởng trợ cấp",
        "ASXH",
        "người",
        "Sở Nội vụ",
        False,
    ),
    ("AS04", "Kinh phí chi trả tháng", "ASXH", "triệu đồng", "Sở Nội vụ", False),
    (
        "AS05",
        "Tỷ lệ chi trả không dùng tiền mặt",
        "ASXH",
        "%",
        "Sở Nội vụ",
        True,
    ),
]


def reset_db() -> None:
    """Xóa và tạo lại toàn bộ bảng + view chỉ đọc cho AI."""
    with engine.begin() as conn:
        for view in ("v_so_lieu", "v_don_vi", "v_chi_tieu"):
            conn.execute(text(f"DROP VIEW IF EXISTS {view}"))
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with engine.begin() as conn:
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
                       g.gia_tri,
                       g.nguon,
                       g.thoi_diem_cap_nhat
                FROM gia_tri_chi_tieu g
                JOIN chi_tieu c ON c.id = g.chi_tieu_id
                JOIN linh_vuc l ON l.id = c.linh_vuc_id
                JOIN don_vi d   ON d.id = g.don_vi_id
                """))
        conn.execute(
            text("CREATE VIEW v_don_vi AS SELECT id, ma, ten, loai, vung FROM don_vi")
        )
        conn.execute(text("""
                CREATE VIEW v_chi_tieu AS
                SELECT c.id, c.ma, c.ten, c.don_vi_tinh, c.tan_suat, c.cong_khai,
                       l.ma AS ma_linh_vuc, l.ten AS ten_linh_vuc
                FROM chi_tieu c
                JOIN linh_vuc l ON l.id = c.linh_vuc_id
                """))


def seed_don_vi(db: Session) -> dict[str, DonVi]:
    """Tạo 15 xã/phường + 3 sở ngành + 1 tỉnh; trả về map mã → đơn vị."""
    ket_qua: dict[str, DonVi] = {}
    for ma, ten, loai, vung in DS_XA:
        dv = DonVi(ma=ma, ten=ten, loai=loai, vung=vung)
        db.add(dv)
        ket_qua[ma] = dv
    for ma, ten, loai in DS_SO_NGANH:
        dv = DonVi(ma=ma, ten=ten, loai=loai, vung=None)
        db.add(dv)
        ket_qua[ma] = dv
    tinh = DonVi(ma="TINH", ten="UBND tỉnh Thanh Hóa", loai="tinh", vung=None)
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
    for ma, ten, ma_lv, dvt, co_quan, cong_khai in DS_CHI_TIEU:
        ct = ChiTieu(
            ma=ma,
            ten=ten,
            linh_vuc_id=map_lv[ma_lv].id,
            don_vi_tinh=dvt,
            tan_suat="thang",
            co_quan_chu_chi_tieu=co_quan,
            dinh_nghia=f"Chỉ tiêu {ten.lower()} theo kỳ báo cáo tháng (dữ liệu mô phỏng).",
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
    """Tạo 4 tài khoản demo (mật khẩu ghi trong README, chỉ dùng demo)."""
    hash_chung = hash_mat_khau(MAT_KHAU_DEMO)
    ds = [
        NguoiDung(
            ten_dang_nhap="admin",
            mat_khau_hash=hash_chung,
            ho_ten="Quản trị hệ thống",
            vai_tro="quan_tri",
            don_vi_id=map_dv["VPUBND"].id,
        ),
        NguoiDung(
            ten_dang_nhap="lanhdao",
            mat_khau_hash=hash_chung,
            ho_ten="Lãnh đạo UBND tỉnh",
            vai_tro="lanh_dao",
            don_vi_id=map_dv["TINH"].id,
        ),
        NguoiDung(
            ten_dang_nhap="xa.hacthanh",
            mat_khau_hash=hash_chung,
            ho_ten="Chuyên viên phường Hạc Thành",
            vai_tro="chuyen_vien_xa",
            don_vi_id=map_dv["HACTHANH"].id,
        ),
        NguoiDung(
            ten_dang_nhap="daibieu",
            mat_khau_hash=hash_chung,
            ho_ten="Đại biểu HĐND tỉnh",
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


def seed_gia_tri(
    db: Session,
    map_dv: dict[str, DonVi],
    map_ct: dict[str, ChiTieu],
    map_nd: dict[str, NguoiDung],
) -> int:
    """Sinh giá trị chỉ tiêu tháng 01–07/2026 cho 15 xã; trả về số bản ghi."""
    so_ban_ghi = 0
    id_chuyen_vien_hacthanh = map_nd["xa.hacthanh"].id

    for ma_xa, _ten, _loai, vung in DS_XA:
        dv = map_dv[ma_xa]
        he_so = HE_SO_VUNG[vung] * rng.uniform(0.85, 1.15)

        chuoi: dict[str, list[float]] = {}
        chuoi.update(_sinh_giai_ngan(ma_xa, he_so))
        chuoi.update(_sinh_tthc(ma_xa, he_so, vung))
        chuoi.update(_sinh_asxh(he_so, vung))

        for ma_ct, gia_tri_7_thang in chuoi.items():
            for i, thang in enumerate(CAC_THANG):
                if thang == 7 and (ma_ct, ma_xa) in O_TRONG_THANG_7:
                    continue  # để trống cho kịch bản nhập liệu / cảnh báo
                # Nhóm ASXH nhập tay tại xã; DTC/TTHC chủ yếu từ hệ thống
                nhap_tay = ma_ct.startswith("AS") or rng.random() < 0.15
                nguon = "nhap_tay" if nhap_tay else "he_thong"
                nguoi_cap_nhat = (
                    id_chuyen_vien_hacthanh
                    if nhap_tay and ma_xa == "HACTHANH"
                    else None
                )
                db.add(
                    GiaTriChiTieu(
                        chi_tieu_id=map_ct[ma_ct].id,
                        don_vi_id=dv.id,
                        nam=NAM,
                        thang=thang,
                        gia_tri=float(gia_tri_7_thang[i]),
                        nguon=nguon,
                        nguoi_cap_nhat_id=nguoi_cap_nhat,
                        thoi_diem_cap_nhat=_thoi_diem_cap_nhat(thang),
                    )
                )
                so_ban_ghi += 1
    db.flush()
    return so_ban_ghi


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


def seed_all(db: Session) -> dict[str, int]:
    """Chạy toàn bộ các bước seed trên một phiên CSDL; trả về thống kê."""
    map_dv = seed_don_vi(db)
    map_ct = seed_danh_muc(db)
    map_nd = seed_nguoi_dung(db, map_dv)
    so_gia_tri = seed_gia_tri(db, map_dv, map_ct, map_nd)
    seed_nghi_quyet(db, map_ct)
    db.add(
        NhatKy(
            nguoi_dung_id=map_nd["admin"].id,
            hanh_dong="khoi_tao_du_lieu",
            chi_tiet=f"Seed dữ liệu mô phỏng: {so_gia_tri} bản ghi giá trị chỉ tiêu.",
            thoi_diem=datetime.now(),
        )
    )
    db.commit()
    return {
        "don_vi": len(map_dv),
        "chi_tieu": len(map_ct),
        "nguoi_dung": len(map_nd),
        "gia_tri": so_gia_tri,
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
        f"  - Người dùng:        {thong_ke['nguoi_dung']} (mật khẩu demo: {MAT_KHAU_DEMO})"
    )
    print(f"  - Giá trị chỉ tiêu:  {thong_ke['gia_tri']} bản ghi (tháng 01–07/{NAM})")
    print("Lưu ý: toàn bộ là DỮ LIỆU MÔ PHỎNG phục vụ trình diễn.")


if __name__ == "__main__":
    main()
