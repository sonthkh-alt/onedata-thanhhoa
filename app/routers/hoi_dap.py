"""Router hỏi – đáp dữ liệu AI (CLAUDE.md 8.5)."""

from fastapi import APIRouter, Depends, Form, Request
from sqlalchemy.orm import Session

from app.auth import ghi_nhat_ky, require_roles
from app.config import settings
from app.db import get_db
from app.models import NguoiDung
from app.services import ai_query

router = APIRouter(prefix="/hoi-dap", tags=["hoi-dap"])

quyen_hoi_dap = require_roles("lanh_dao")


def _ngu_canh(request, nguoi_dung, ket_qua=None):
    return {
        "nguoi_dung": nguoi_dung,
        "ket_qua": ket_qua,
        "cau_hoi_goi_y": [m["cau_hoi"] for m in ai_query.tai_cau_hoi_mau()],
        "che_do_offline": bool(settings.offline or not settings.anthropic_api_key),
    }


@router.get("")
def trang_hoi_dap(
    request: Request,
    cau_hoi: str | None = None,
    nguoi_dung: NguoiDung = Depends(quyen_hoi_dap),
    db: Session = Depends(get_db),
):
    """Trang hỏi đáp; nếu có tham số ?cau_hoi= thì trả lời luôn
    (hỏi qua liên kết chia sẻ được)."""
    from app.main import templates

    ket_qua = None
    if cau_hoi and cau_hoi.strip():
        ket_qua = ai_query.hoi(cau_hoi)
        ghi_nhat_ky(
            db,
            nguoi_dung.id,
            "hoi_dap_ai",
            f"[{ket_qua.che_do}] Hỏi (GET): {cau_hoi.strip()[:300]} | "
            f"SQL: {ket_qua.sql or '(không có)'} | {ket_qua.so_dong} dòng",
        )
    return templates.TemplateResponse(
        request, "hoi_dap.html", _ngu_canh(request, nguoi_dung, ket_qua)
    )


@router.post("")
def gui_cau_hoi(
    request: Request,
    cau_hoi: str = Form(...),
    nguoi_dung: NguoiDung = Depends(quyen_hoi_dap),
    db: Session = Depends(get_db),
):
    """Nhận câu hỏi, trả lời từ Kho dữ liệu, ghi nhật ký đầy đủ."""
    from app.main import templates

    ket_qua = ai_query.hoi(cau_hoi)
    ghi_nhat_ky(
        db,
        nguoi_dung.id,
        "hoi_dap_ai",
        f"[{ket_qua.che_do}] Hỏi: {cau_hoi.strip()[:300]} | "
        f"SQL: {ket_qua.sql or '(không có)'} | {ket_qua.so_dong} dòng"
        + (f" | Lỗi: {ket_qua.loi}" if ket_qua.loi else ""),
    )
    return templates.TemplateResponse(
        request, "hoi_dap.html", _ngu_canh(request, nguoi_dung, ket_qua)
    )
