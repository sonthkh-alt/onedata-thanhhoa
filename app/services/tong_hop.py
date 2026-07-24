"""Hàm tổng hợp số liệu dùng chung cho dashboard, giám sát, công khai."""

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import ChiTieu, DonVi, GiaTriChiTieu

NAM_DEMO = 2026
CAC_THANG = list(range(1, 8))


def tong_theo_tinh(db: Session, ma_chi_tieu: str, thang: int) -> float | None:
    """Tổng giá trị một chỉ tiêu của tất cả xã/phường trong kỳ."""
    ket_qua = (
        db.query(func.sum(GiaTriChiTieu.gia_tri))
        .join(ChiTieu, ChiTieu.id == GiaTriChiTieu.chi_tieu_id)
        .join(DonVi, DonVi.id == GiaTriChiTieu.don_vi_id)
        .filter(
            ChiTieu.ma == ma_chi_tieu,
            GiaTriChiTieu.nam == NAM_DEMO,
            GiaTriChiTieu.thang == thang,
            DonVi.loai.in_(["xa", "phuong"]),
        )
        .scalar()
    )
    return float(ket_qua) if ket_qua is not None else None


def ty_le_toan_tinh(db: Session, ma_tu: str, ma_mau: str, thang: int) -> float | None:
    """Tỷ lệ toàn tỉnh = sum(tử)/sum(mẫu)*100 (đúng cách gộp chỉ tiêu dẫn xuất)."""
    tu = tong_theo_tinh(db, ma_tu, thang)
    mau = tong_theo_tinh(db, ma_mau, thang)
    if tu is None or not mau:
        return None
    return round(tu / mau * 100, 1)


def trung_binh_toan_tinh(db: Session, ma_chi_tieu: str, thang: int) -> float | None:
    """Trung bình cộng giá trị chỉ tiêu (%) của các xã trong kỳ."""
    ket_qua = (
        db.query(func.avg(GiaTriChiTieu.gia_tri))
        .join(ChiTieu, ChiTieu.id == GiaTriChiTieu.chi_tieu_id)
        .join(DonVi, DonVi.id == GiaTriChiTieu.don_vi_id)
        .filter(
            ChiTieu.ma == ma_chi_tieu,
            GiaTriChiTieu.nam == NAM_DEMO,
            GiaTriChiTieu.thang == thang,
            DonVi.loai.in_(["xa", "phuong"]),
        )
        .scalar()
    )
    return round(float(ket_qua), 1) if ket_qua is not None else None


def gia_tri_theo_xa(
    db: Session, ma_chi_tieu: str, thang: int, vung: str | None = None
) -> list[dict]:
    """[{ma, ten, vung, gia_tri, nguon, thoi_diem}] của một chỉ tiêu trong kỳ,
    sắp xếp giảm dần theo giá trị."""
    truy_van = (
        db.query(DonVi, GiaTriChiTieu)
        .join(GiaTriChiTieu, GiaTriChiTieu.don_vi_id == DonVi.id)
        .join(ChiTieu, ChiTieu.id == GiaTriChiTieu.chi_tieu_id)
        .filter(
            ChiTieu.ma == ma_chi_tieu,
            GiaTriChiTieu.nam == NAM_DEMO,
            GiaTriChiTieu.thang == thang,
            DonVi.loai.in_(["xa", "phuong"]),
        )
    )
    if vung:
        truy_van = truy_van.filter(DonVi.vung == vung)
    ket_qua = [
        {
            "id": gt.id,
            "ma": dv.ma,
            "ten": dv.ten,
            "vung": dv.vung,
            "gia_tri": gt.gia_tri,
            "nguon": gt.nguon,
            "thoi_diem": gt.thoi_diem_cap_nhat.strftime("%Y-%m-%d %H:%M"),
        }
        for dv, gt in truy_van.all()
    ]
    ket_qua.sort(key=lambda d: d["gia_tri"], reverse=True)
    return ket_qua


def chuoi_ty_le_theo_thang(db: Session, ma_tu: str, ma_mau: str) -> list[float | None]:
    """Chuỗi tỷ lệ toàn tỉnh theo 7 tháng (cho biểu đồ đường)."""
    return [ty_le_toan_tinh(db, ma_tu, ma_mau, t) for t in CAC_THANG]


def chuoi_gia_tri_don_vi(
    db: Session, don_vi_id: int, ma_chi_tieu: str
) -> list[float | None]:
    """Chuỗi giá trị 7 tháng của một chỉ tiêu tại một đơn vị."""
    ct = db.query(ChiTieu).filter_by(ma=ma_chi_tieu).one()
    gia_tri = dict(
        db.query(GiaTriChiTieu.thang, GiaTriChiTieu.gia_tri)
        .filter_by(chi_tieu_id=ct.id, don_vi_id=don_vi_id, nam=NAM_DEMO)
        .all()
    )
    return [gia_tri.get(t) for t in CAC_THANG]
