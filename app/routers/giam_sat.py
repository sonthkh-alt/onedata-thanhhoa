"""Trang giám sát nghị quyết HĐND (chỉ đọc) — phục vụ đại biểu HĐND."""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.auth import require_roles
from app.db import get_db
from app.models import NghiQuyetTheoDoi, NguoiDung
from app.services import tong_hop

router = APIRouter(tags=["giam-sat"])

THANG_MOI_NHAT = 7
NAM_DEMO = 2026

# Cách gộp giá trị toàn tỉnh cho từng chỉ tiêu theo dõi (đều là chỉ tiêu dẫn
# xuất %): tử/mẫu để tính đúng, hoặc trung bình cộng theo xã.
CACH_GOP = {
    "DTC03": ("ty_le", "DTC02", "DTC01"),
    "TTHC04": ("ty_le", "TTHC02", "TTHC01"),
    "TTHC06": ("ty_le", "TTHC05", "TTHC01"),
    "AS05": ("trung_binh", None, None),
}


def _gia_tri_toan_tinh(db: Session, ma_chi_tieu: str) -> float | None:
    cach = CACH_GOP.get(ma_chi_tieu)
    if cach is None:
        return None
    loai, ma_tu, ma_mau = cach
    if loai == "ty_le":
        return tong_hop.ty_le_toan_tinh(db, ma_tu, ma_mau, THANG_MOI_NHAT)
    return tong_hop.trung_binh_toan_tinh(db, ma_chi_tieu, THANG_MOI_NHAT)


@router.get("/giam-sat")
def trang_giam_sat(
    request: Request,
    nguoi_dung: NguoiDung = Depends(require_roles("dai_bieu_hdnd", "lanh_dao")),
    db: Session = Depends(get_db),
):
    """Bảng theo dõi nghị quyết: mục tiêu — hiện trạng — tiến độ."""
    from app.main import templates

    ds_nghi_quyet = db.query(NghiQuyetTheoDoi).order_by(NghiQuyetTheoDoi.id).all()
    bang = []
    for nq in ds_nghi_quyet:
        hien_tai = _gia_tri_toan_tinh(db, nq.chi_tieu.ma)
        tien_do = (
            round(hien_tai / nq.gia_tri_muc_tieu * 100, 1)
            if hien_tai is not None and nq.gia_tri_muc_tieu
            else None
        )
        bang.append(
            {
                "nq": nq,
                "hien_tai": hien_tai,
                "tien_do": min(tien_do, 100.0) if tien_do is not None else None,
                "dat": hien_tai is not None and hien_tai >= nq.gia_tri_muc_tieu,
            }
        )

    return templates.TemplateResponse(
        request,
        "giam_sat.html",
        {
            "nguoi_dung": nguoi_dung,
            "bang": bang,
            "thang": THANG_MOI_NHAT,
            "nam": NAM_DEMO,
            "ky": NAM_DEMO * 100 + THANG_MOI_NHAT,
        },
    )
