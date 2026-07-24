"""Router AI điều tra nguyên nhân + Phòng lab chính sách What-if."""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.auth import ghi_nhat_ky, require_roles
from app.db import get_db
from app.models import DonVi, NguoiDung
from app.services import ban_tin, dieu_tra
from app.services.ban_tin import _chuoi_gia_tri, _hoi_quy_tuyen_tinh

router = APIRouter(tags=["dieu-tra"])

quyen_xem = require_roles("lanh_dao", "dai_bieu_hdnd")


@router.get("/dieu-tra")
def trang_dieu_tra(
    request: Request,
    don_vi: str,
    van_de: str = "giai_ngan",
    nguoi_dung: NguoiDung = Depends(quyen_xem),
    db: Session = Depends(get_db),
):
    """Chuỗi điều tra nguyên nhân nhiều bước cho một xã."""
    from app.main import templates

    dv = (
        db.query(DonVi)
        .filter(DonVi.ma == don_vi, DonVi.loai.in_(["xa", "phuong"]))
        .first()
    )
    if dv is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn vị.")
    if van_de not in ("giai_ngan", "tthc"):
        van_de = "giai_ngan"

    ket_qua = dieu_tra.dieu_tra(db, dv, van_de)
    ghi_nhat_ky(
        db,
        nguoi_dung.id,
        "dieu_tra_nguyen_nhan",
        f"{ket_qua.tieu_de} — {len(ket_qua.cac_buoc)} bước điều tra",
    )
    return templates.TemplateResponse(
        request, "dieu_tra.html", {"nguoi_dung": nguoi_dung, "kq": ket_qua}
    )


@router.get("/lab")
def phong_lab_chinh_sach(
    request: Request,
    nguoi_dung: NguoiDung = Depends(quyen_xem),
    db: Session = Depends(get_db),
):
    """Phòng lab What-if: thử quyết định trước khi ký — kéo thanh trượt,
    hệ thống mô phỏng ngay kết cục 31/12 toàn tỉnh."""
    from app.main import templates

    du_lieu_xa = []
    ds_xa = (
        db.query(DonVi)
        .filter(DonVi.loai.in_(["xa", "phuong"]))
        .order_by(DonVi.ten)
        .all()
    )
    for xa in ds_xa:
        ke_hoach_chuoi = _chuoi_gia_tri(db, xa.id, "DTC01")
        luy_ke = _chuoi_gia_tri(db, xa.id, "DTC02")
        if not ke_hoach_chuoi or not luy_ke:
            continue
        diem = sorted(luy_ke.items())
        goc, _chan = _hoi_quy_tuyen_tinh(diem)
        thang_cuoi, gia_tri_cuoi = diem[-1]
        du_lieu_xa.append(
            {
                "ma": xa.ma,
                "ten": xa.ten,
                "ke_hoach": next(iter(ke_hoach_chuoi.values())),
                "luy_ke": gia_tri_cuoi,
                "toc_do": max(goc, 0.0),  # triệu đồng/tháng theo nhịp hiện tại
                "thang_cuoi": thang_cuoi,
            }
        )

    return templates.TemplateResponse(
        request,
        "lab.html",
        {
            "nguoi_dung": nguoi_dung,
            "du_lieu_xa": du_lieu_xa,
            "muc_tieu": ban_tin.MUC_TIEU_GIAI_NGAN,
        },
    )
