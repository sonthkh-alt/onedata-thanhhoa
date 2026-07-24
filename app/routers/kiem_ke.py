"""Phân hệ kiểm kê báo cáo (8.8): khai báo chế độ báo cáo, thống kê gánh
nặng, danh sách nghi trùng lặp — "Bản đồ báo cáo" của tỉnh."""

from datetime import datetime

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.auth import ghi_nhat_ky, require_roles, require_user
from app.db import get_db
from app.models import KiemKeBaoCao, NguoiDung
from app.services import kiem_ke

router = APIRouter(prefix="/kiem-ke", tags=["kiem-ke"])


@router.get("")
def trang_kiem_ke(
    request: Request,
    khai_bao: str | None = None,
    nguoi_dung: NguoiDung = Depends(require_user),
    db: Session = Depends(get_db),
):
    """Trang thống kê gánh nặng báo cáo + danh sách nghi trùng lặp."""
    from app.main import templates

    thong_ke = kiem_ke.thong_ke_ganh_nang(db)
    return templates.TemplateResponse(
        request,
        "kiem_ke.html",
        {
            "nguoi_dung": nguoi_dung,
            "tk": thong_ke,
            "ten_tan_suat": kiem_ke.TEN_TAN_SUAT,
            "so_ky": kiem_ke.SO_KY_MOT_NAM,
            "da_khai_bao": khai_bao == "ok",
            "duoc_khai_bao": nguoi_dung.vai_tro in ("lanh_dao", "quan_tri"),
        },
    )


@router.post("")
def khai_bao_bao_cao(
    ten_bao_cao: str = Form(...),
    co_quan_yeu_cau: str = Form(...),
    tan_suat: str = Form("thang"),
    can_cu: str = Form(""),
    nguoi_dung: NguoiDung = Depends(require_roles("lanh_dao")),
    db: Session = Depends(get_db),
):
    """Khai báo thêm một chế độ báo cáo vào bản kiểm kê."""
    if tan_suat not in kiem_ke.SO_KY_MOT_NAM:
        tan_suat = "thang"
    db.add(
        KiemKeBaoCao(
            ten_bao_cao=ten_bao_cao.strip()[:300],
            co_quan_yeu_cau=co_quan_yeu_cau.strip()[:200],
            tan_suat=tan_suat,
            can_cu=can_cu.strip()[:300],
            nguoi_khai_id=nguoi_dung.id,
            thoi_diem_khai=datetime.now(),
        )
    )
    ghi_nhat_ky(
        db,
        nguoi_dung.id,
        "khai_bao_kiem_ke",
        f"Khai báo chế độ báo cáo: {ten_bao_cao.strip()[:200]} "
        f"({co_quan_yeu_cau.strip()[:100]}, {tan_suat})",
    )
    return RedirectResponse("/kiem-ke?khai_bao=ok", status_code=303)
