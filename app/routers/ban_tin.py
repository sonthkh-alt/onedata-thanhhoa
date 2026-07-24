"""Router Bản tin điều hành chủ động — máy tham mưu cho lãnh đạo."""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.auth import ghi_nhat_ky, require_roles
from app.db import get_db
from app.models import NguoiDung
from app.services import ban_tin

router = APIRouter(prefix="/ban-tin", tags=["ban-tin"])

quyen_xem = require_roles("lanh_dao", "dai_bieu_hdnd")
quyen_chi_dao = require_roles("lanh_dao")


@router.get("")
def trang_ban_tin(
    request: Request,
    nguoi_dung: NguoiDung = Depends(quyen_xem),
    db: Session = Depends(get_db),
):
    """Bản tin điều hành: dự báo, bất thường, 3 việc cần chỉ đạo hôm nay."""
    from app.main import templates

    du_lieu = ban_tin.lap_ban_tin(db)
    return templates.TemplateResponse(
        request,
        "ban_tin.html",
        {
            "nguoi_dung": nguoi_dung,
            "bt": du_lieu,
            "muc_tieu": ban_tin.MUC_TIEU_GIAI_NGAN,
        },
    )


@router.get("/du-thao-cong-van")
def tai_du_thao_cong_van(
    nguoi_dung: NguoiDung = Depends(quyen_chi_dao),
    db: Session = Depends(get_db),
):
    """Tải dự thảo công văn chỉ đạo đôn đốc giải ngân (.docx, thể thức NĐ30)."""
    duong_dan = ban_tin.tao_du_thao_cong_van(db)
    ghi_nhat_ky(
        db,
        nguoi_dung.id,
        "sinh_du_thao_chi_dao",
        f"Dự thảo công văn đôn đốc giải ngân → {duong_dan.name}",
    )
    return FileResponse(
        duong_dan,
        media_type=(
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ),
        filename=duong_dan.name,
    )
