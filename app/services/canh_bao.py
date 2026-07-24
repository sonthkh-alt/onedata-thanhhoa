"""Cảnh báo sớm theo ngưỡng — bảng "Điểm nóng" (CLAUDE.md 8.6).

4 luật demo:
1. Tỷ lệ giải ngân (DTC03) kỳ mới nhất < 30%.
2. Tỷ lệ giải quyết đúng hạn TTHC (TTHC04) kỳ mới nhất < 90%.
3. Đơn vị chưa nhập đủ số liệu kỳ hiện tại.
4. Giải ngân lũy kế (DTC02) giảm so kỳ trước — nghi sai số liệu.
"""

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models import ChiTieu, DonVi, GiaTriChiTieu

NGUONG_GIAI_NGAN = 30.0  # %
NGUONG_TTHC_DUNG_HAN = 90.0  # %


@dataclass
class DiemNong:
    """Một dòng trong bảng điểm nóng."""

    don_vi: str
    ma_don_vi: str
    chi_tieu: str
    gia_tri: str
    luat: str
    muc_do: str  # "cao" | "trung_binh"


def _gia_tri_theo_xa(
    db: Session, ma_chi_tieu: str, thang: int, nam: int = 2026
) -> list[tuple[DonVi, float]]:
    """Danh sách (đơn vị xã, giá trị) của một chỉ tiêu trong kỳ."""
    return (
        db.query(DonVi, GiaTriChiTieu.gia_tri)
        .join(GiaTriChiTieu, GiaTriChiTieu.don_vi_id == DonVi.id)
        .join(ChiTieu, ChiTieu.id == GiaTriChiTieu.chi_tieu_id)
        .filter(
            ChiTieu.ma == ma_chi_tieu,
            GiaTriChiTieu.nam == nam,
            GiaTriChiTieu.thang == thang,
            DonVi.loai.in_(["xa", "phuong"]),
        )
        .all()
    )


def tim_diem_nong(db: Session, thang: int = 7, nam: int = 2026) -> list[DiemNong]:
    """Chạy 4 luật cảnh báo, trả về danh sách điểm nóng (mức cao trước)."""
    ket_qua: list[DiemNong] = []

    # Luật 1: tỷ lệ giải ngân < 30%
    for dv, gia_tri in _gia_tri_theo_xa(db, "DTC03", thang, nam):
        if gia_tri < NGUONG_GIAI_NGAN:
            ket_qua.append(
                DiemNong(
                    don_vi=dv.ten,
                    ma_don_vi=dv.ma,
                    chi_tieu="DTC03 — Tỷ lệ giải ngân",
                    gia_tri=f"{gia_tri:g}%",
                    luat=f"Tỷ lệ giải ngân kỳ {nam}{thang:02d} dưới "
                    f"{NGUONG_GIAI_NGAN:g}%",
                    muc_do="cao",
                )
            )

    # Luật 2: tỷ lệ đúng hạn TTHC < 90%
    for dv, gia_tri in _gia_tri_theo_xa(db, "TTHC04", thang, nam):
        if gia_tri < NGUONG_TTHC_DUNG_HAN:
            ket_qua.append(
                DiemNong(
                    don_vi=dv.ten,
                    ma_don_vi=dv.ma,
                    chi_tieu="TTHC04 — Tỷ lệ giải quyết đúng hạn",
                    gia_tri=f"{gia_tri:g}%",
                    luat=f"Tỷ lệ đúng hạn TTHC kỳ {nam}{thang:02d} dưới "
                    f"{NGUONG_TTHC_DUNG_HAN:g}%",
                    muc_do="cao",
                )
            )

    # Luật 3: chưa nhập đủ số liệu kỳ hiện tại
    tong_chi_tieu = db.query(ChiTieu).count()
    ds_xa = db.query(DonVi).filter(DonVi.loai.in_(["xa", "phuong"])).all()
    for dv in ds_xa:
        so_da_nhap = (
            db.query(GiaTriChiTieu)
            .filter_by(don_vi_id=dv.id, nam=nam, thang=thang)
            .count()
        )
        if so_da_nhap < tong_chi_tieu:
            ket_qua.append(
                DiemNong(
                    don_vi=dv.ten,
                    ma_don_vi=dv.ma,
                    chi_tieu=f"Đã nhập {so_da_nhap}/{tong_chi_tieu} chỉ tiêu",
                    gia_tri=f"thiếu {tong_chi_tieu - so_da_nhap}",
                    luat=f"Chưa nhập đủ số liệu kỳ {nam}{thang:02d}",
                    muc_do="trung_binh",
                )
            )

    # Luật 4: giải ngân lũy kế giảm so kỳ trước (nghi sai số liệu)
    ct_dtc02 = db.query(ChiTieu).filter_by(ma="DTC02").one()
    for dv in ds_xa:
        gia_tri_cac_thang = dict(
            db.query(GiaTriChiTieu.thang, GiaTriChiTieu.gia_tri)
            .filter_by(chi_tieu_id=ct_dtc02.id, don_vi_id=dv.id, nam=nam)
            .all()
        )
        for t in range(2, thang + 1):
            truoc, sau = gia_tri_cac_thang.get(t - 1), gia_tri_cac_thang.get(t)
            if truoc is not None and sau is not None and sau < truoc:
                ket_qua.append(
                    DiemNong(
                        don_vi=dv.ten,
                        ma_don_vi=dv.ma,
                        chi_tieu="DTC02 — Giải ngân lũy kế",
                        gia_tri=f"{sau:g} < {truoc:g} (tr.đ)",
                        luat=f"Lũy kế tháng {t} giảm so tháng {t - 1} — "
                        "nghi sai số liệu",
                        muc_do="trung_binh",
                    )
                )

    ket_qua.sort(key=lambda d: (d.muc_do != "cao", d.don_vi))
    return ket_qua
