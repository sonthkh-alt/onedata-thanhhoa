"""Đăng nhập, phiên làm việc (cookie ký) và phân quyền."""

from datetime import datetime

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse, Response
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.models import NguoiDung, NhatKy

router = APIRouter(tags=["xac-thuc"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

_serializer = URLSafeTimedSerializer(settings.secret_key, salt="onedata-session")

TEN_VAI_TRO = {
    "quan_tri": "Quản trị hệ thống",
    "lanh_dao": "Lãnh đạo tỉnh/sở",
    "chuyen_vien_xa": "Chuyên viên xã/phường",
    "dai_bieu_hdnd": "Đại biểu HĐND",
}


def hash_mat_khau(mat_khau: str) -> str:
    """Băm mật khẩu bằng bcrypt."""
    return pwd_context.hash(mat_khau)


def kiem_tra_mat_khau(mat_khau: str, mat_khau_hash: str) -> bool:
    """So khớp mật khẩu người dùng nhập với chuỗi băm trong CSDL."""
    return pwd_context.verify(mat_khau, mat_khau_hash)


def ghi_nhat_ky(
    db: Session, nguoi_dung_id: int | None, hanh_dong: str, chi_tiet: str = ""
) -> None:
    """Ghi một dòng nhật ký hệ thống."""
    db.add(
        NhatKy(
            nguoi_dung_id=nguoi_dung_id,
            hanh_dong=hanh_dong,
            chi_tiet=chi_tiet,
            thoi_diem=datetime.now(),
        )
    )
    db.commit()


def tao_session_cookie(response: Response, nguoi_dung: NguoiDung) -> None:
    """Ghi cookie phiên đã ký cho người dùng vừa đăng nhập."""
    token = _serializer.dumps({"uid": nguoi_dung.id})
    response.set_cookie(
        key=settings.session_cookie,
        value=token,
        max_age=settings.session_max_age,
        httponly=True,
        samesite="lax",
    )


def get_current_user(
    request: Request, db: Session = Depends(get_db)
) -> NguoiDung | None:
    """Đọc cookie phiên, trả về người dùng hiện tại hoặc None."""
    token = request.cookies.get(settings.session_cookie)
    if not token:
        return None
    try:
        data = _serializer.loads(token, max_age=settings.session_max_age)
    except (BadSignature, SignatureExpired):
        return None
    return db.get(NguoiDung, data.get("uid"))


def require_user(request: Request, db: Session = Depends(get_db)) -> NguoiDung:
    """Bắt buộc đã đăng nhập — chưa đăng nhập thì chuyển về trang đăng nhập."""
    nguoi_dung = get_current_user(request, db)
    if nguoi_dung is None:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/dang-nhap"},
        )
    return nguoi_dung


def require_roles(*vai_tro: str):
    """Tạo dependency chỉ cho phép các vai trò liệt kê (quan_tri luôn được)."""

    def _checker(nguoi_dung: NguoiDung = Depends(require_user)) -> NguoiDung:
        if nguoi_dung.vai_tro != "quan_tri" and nguoi_dung.vai_tro not in vai_tro:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tài khoản của anh/chị không có quyền truy cập chức năng này.",
            )
        return nguoi_dung

    return _checker


@router.get("/dang-nhap")
def trang_dang_nhap(request: Request, db: Session = Depends(get_db)):
    """Hiển thị form đăng nhập; đã đăng nhập rồi thì về trang chủ."""
    from app.main import templates  # tránh import vòng

    if get_current_user(request, db) is not None:
        return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(
        request, "dang_nhap.html", {"loi": None, "nguoi_dung": None}
    )


@router.post("/dang-nhap")
def xu_ly_dang_nhap(
    request: Request,
    ten_dang_nhap: str = Form(...),
    mat_khau: str = Form(...),
    db: Session = Depends(get_db),
):
    """Kiểm tra tài khoản, tạo phiên và ghi nhật ký."""
    from app.main import templates

    nguoi_dung = (
        db.query(NguoiDung)
        .filter(NguoiDung.ten_dang_nhap == ten_dang_nhap.strip())
        .first()
    )
    if nguoi_dung is None or not kiem_tra_mat_khau(mat_khau, nguoi_dung.mat_khau_hash):
        ghi_nhat_ky(
            db,
            nguoi_dung.id if nguoi_dung else None,
            "dang_nhap_that_bai",
            f"Tên đăng nhập: {ten_dang_nhap.strip()}",
        )
        return templates.TemplateResponse(
            request,
            "dang_nhap.html",
            {
                "loi": "Tên đăng nhập hoặc mật khẩu không đúng.",
                "nguoi_dung": None,
            },
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    ghi_nhat_ky(db, nguoi_dung.id, "dang_nhap", "Đăng nhập thành công")
    response = RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
    tao_session_cookie(response, nguoi_dung)
    return response


@router.get("/dang-xuat")
def dang_xuat(request: Request, db: Session = Depends(get_db)):
    """Xóa cookie phiên và ghi nhật ký."""
    nguoi_dung = get_current_user(request, db)
    if nguoi_dung is not None:
        ghi_nhat_ky(db, nguoi_dung.id, "dang_xuat", "Đăng xuất")
    response = RedirectResponse("/dang-nhap", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(settings.session_cookie)
    return response
