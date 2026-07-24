"""Ứng dụng FastAPI "Một dữ liệu – Không báo cáo lại" (bản demo)."""

from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app import auth
from app.auth import TEN_VAI_TRO, get_current_user
from app.db import get_db
from app.models import NguoiDung
from app.routers import (
    ban_tin,
    bao_cao,
    cong_khai,
    dashboard,
    giam_sat,
    hoi_dap,
    kiem_ke,
    nhap_lieu,
)
from app.services import kiem_ke as kiem_ke_service

APP_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title="Một dữ liệu – Không báo cáo lại",
    description="Bản demo dự thi cải cách hành chính tỉnh Thanh Hóa 2026 "
    "— toàn bộ dữ liệu là mô phỏng.",
    version="0.1",
)

app.mount("/static", StaticFiles(directory=APP_DIR / "static"), name="static")

templates = Jinja2Templates(directory=APP_DIR / "templates")
templates.env.globals["TEN_VAI_TRO"] = TEN_VAI_TRO

app.include_router(auth.router)
app.include_router(nhap_lieu.router)
app.include_router(dashboard.router)
app.include_router(cong_khai.router)
app.include_router(giam_sat.router)
app.include_router(bao_cao.router)
app.include_router(hoi_dap.router)
app.include_router(kiem_ke.router)
app.include_router(ban_tin.router)


@app.get("/")
def trang_chu(
    request: Request,
    nguoi_dung: NguoiDung | None = Depends(get_current_user),
    db=Depends(get_db),
):
    """Trang chủ theo vai trò; chưa đăng nhập thì chuyển về trang đăng nhập."""
    if nguoi_dung is None:
        return RedirectResponse("/dang-nhap", status_code=303)
    return templates.TemplateResponse(
        request,
        "trang_chu.html",
        {"nguoi_dung": nguoi_dung, "dong_ho": kiem_ke_service.dong_ho_tiet_kiem(db)},
    )
