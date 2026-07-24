"""Kiểm chứng toàn vẹn chuỗi nhật ký (tamper-evident ledger)."""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.auth import require_user
from app.db import get_db
from app.models import NguoiDung, NhatKy
from app.services import audit

router = APIRouter(tags=["kiem-chung"])


@router.get("/kiem-chung")
def trang_kiem_chung(
    request: Request,
    nguoi_dung: NguoiDung = Depends(require_user),
    db: Session = Depends(get_db),
):
    """Chạy kiểm chứng toàn bộ chuỗi hash của nhật ký và hiển thị kết quả."""
    from app.main import templates

    ket_qua = audit.kiem_chung_chuoi(db)
    nhat_ky_moi_nhat = db.query(NhatKy).order_by(NhatKy.id.desc()).limit(10).all()
    return templates.TemplateResponse(
        request,
        "kiem_chung.html",
        {
            "nguoi_dung": nguoi_dung,
            "kq": ket_qua,
            "nhat_ky": nhat_ky_moi_nhat,
        },
    )
