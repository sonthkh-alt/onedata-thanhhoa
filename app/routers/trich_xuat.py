"""Kênh 2 — Màn hình "Xác nhận số liệu máy trích" (ĐIỂM NHẤN v0.2).

Hàng chờ từng dòng: chỉ tiêu, giá trị máy đọc (sửa được), câu trích dẫn
(bôi đậm con số), link văn bản gốc; nút Xác nhận / Sửa & xác nhận / Từ chối;
nút "Xác nhận tất cả dòng độ tin cậy cao". Xác nhận xong → ghi Lớp 2 với
nguon='van_ban', van_ban_id, nguoi_xac_nhan_id.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from markupsafe import Markup, escape
from sqlalchemy.orm import Session

from app.auth import ghi_nhat_ky, require_roles
from app.db import get_db
from app.models import ChiTieu, DonVi, NguoiDung, TrichXuatCho
from app.routers.nhap_lieu import _tinh_chi_tieu_dan_xuat, _upsert_gia_tri
from app.services.extractor import MAU_SO

router = APIRouter(prefix="/trich-xuat", tags=["trich-xuat"])

quyen_xac_nhan = require_roles("chuyen_vien_xa")

TEN_TIN_CAY = {"cao": "Cao", "trung_binh": "Trung bình", "thap": "Thấp"}


def _boi_dam_so(doan: str) -> Markup:
    """Bôi đậm các con số trong câu trích dẫn (an toàn HTML)."""
    an_toan = str(escape(doan))
    return Markup(MAU_SO.sub(r"<strong>\g<0></strong>", an_toan))


def _hang_cho_theo_quyen(db: Session, nguoi_dung: NguoiDung, van_ban_id: int | None):
    truy_van = (
        db.query(TrichXuatCho)
        .filter(TrichXuatCho.trang_thai == "cho_xac_nhan")
        .order_by(TrichXuatCho.van_ban_id, TrichXuatCho.chi_tieu_id)
    )
    if nguoi_dung.vai_tro == "chuyen_vien_xa":
        truy_van = truy_van.filter(TrichXuatCho.don_vi_id == nguoi_dung.don_vi_id)
    if van_ban_id:
        truy_van = truy_van.filter(TrichXuatCho.van_ban_id == van_ban_id)
    return truy_van.all()


def _ghi_vao_lop_2(db: Session, dong: TrichXuatCho, nguoi_dung: NguoiDung) -> None:
    """Ghi một dòng đã xác nhận vào Lớp 2 + tự tính chỉ tiêu dẫn xuất."""
    chi_tieu = db.get(ChiTieu, dong.chi_tieu_id)
    don_vi = db.get(DonVi, dong.don_vi_id)
    _upsert_gia_tri(
        db,
        chi_tieu,
        don_vi,
        dong.thang,
        dong.gia_tri_may_doc,
        "van_ban",
        nguoi_dung,
        van_ban_id=dong.van_ban_id,
    )
    ds_chi_tieu = db.query(ChiTieu).order_by(ChiTieu.ma).all()
    _tinh_chi_tieu_dan_xuat(db, ds_chi_tieu, don_vi, dong.thang, nguoi_dung)
    db.commit()


@router.get("")
def man_hinh_xac_nhan(
    request: Request,
    van_ban_id: int | None = None,
    nguoi_dung: NguoiDung = Depends(quyen_xac_nhan),
    db: Session = Depends(get_db),
):
    """Bảng hàng chờ xác nhận số liệu máy trích."""
    from app.main import templates

    ds = _hang_cho_theo_quyen(db, nguoi_dung, van_ban_id)
    hang_cho = [
        {
            "dong": d,
            "doan_dam": _boi_dam_so(d.doan_trich),
            "ten_tin_cay": TEN_TIN_CAY.get(d.do_tin_cay, d.do_tin_cay),
        }
        for d in ds
    ]
    so_tin_cay_cao = sum(1 for d in ds if d.do_tin_cay == "cao")
    return templates.TemplateResponse(
        request,
        "trich_xuat.html",
        {
            "nguoi_dung": nguoi_dung,
            "hang_cho": hang_cho,
            "so_tin_cay_cao": so_tin_cay_cao,
            "van_ban_id": van_ban_id,
        },
    )


def _lay_dong(db: Session, dong_id: int, nguoi_dung: NguoiDung) -> TrichXuatCho:
    dong = db.get(TrichXuatCho, dong_id)
    if dong is None or dong.trang_thai != "cho_xac_nhan":
        raise HTTPException(status_code=404, detail="Không tìm thấy dòng hàng chờ.")
    if (
        nguoi_dung.vai_tro == "chuyen_vien_xa"
        and dong.don_vi_id != nguoi_dung.don_vi_id
    ):
        raise HTTPException(
            status_code=403, detail="Chỉ xác nhận được số liệu của đơn vị mình."
        )
    return dong


@router.post("/{dong_id}/xac-nhan")
def xac_nhan_mot_dong(
    dong_id: int,
    gia_tri: str = Form(...),
    nguoi_dung: NguoiDung = Depends(quyen_xac_nhan),
    db: Session = Depends(get_db),
):
    """Xác nhận (hoặc Sửa & xác nhận nếu người dùng đổi giá trị)."""
    dong = _lay_dong(db, dong_id, nguoi_dung)
    try:
        gia_tri_moi = float(gia_tri.replace(",", "."))
    except ValueError as loi:
        raise HTTPException(status_code=400, detail="Giá trị không hợp lệ.") from loi

    da_sua = abs(gia_tri_moi - dong.gia_tri_may_doc) > 1e-9
    dong.gia_tri_may_doc = gia_tri_moi
    dong.trang_thai = "da_sua" if da_sua else "da_xac_nhan"
    dong.nguoi_xu_ly_id = nguoi_dung.id
    dong.thoi_diem = datetime.now()
    _ghi_vao_lop_2(db, dong, nguoi_dung)
    ghi_nhat_ky(
        db,
        nguoi_dung.id,
        "xac_nhan_trich_xuat",
        f"{'Sửa & xác nhận' if da_sua else 'Xác nhận'} {dong.chi_tieu.ma} "
        f"tháng {dong.thang}/{dong.nam} = {gia_tri_moi:g} "
        f"(văn bản #{dong.van_ban_id})",
    )
    return RedirectResponse("/trich-xuat", status_code=303)


@router.post("/{dong_id}/tu-choi")
def tu_choi_mot_dong(
    dong_id: int,
    nguoi_dung: NguoiDung = Depends(quyen_xac_nhan),
    db: Session = Depends(get_db),
):
    dong = _lay_dong(db, dong_id, nguoi_dung)
    dong.trang_thai = "tu_choi"
    dong.nguoi_xu_ly_id = nguoi_dung.id
    dong.thoi_diem = datetime.now()
    db.commit()
    ghi_nhat_ky(
        db,
        nguoi_dung.id,
        "tu_choi_trich_xuat",
        f"Từ chối {dong.chi_tieu.ma} tháng {dong.thang}/{dong.nam} "
        f"(máy đọc {dong.gia_tri_may_doc:g}, văn bản #{dong.van_ban_id})",
    )
    return RedirectResponse("/trich-xuat", status_code=303)


@router.post("/xac-nhan-tin-cay-cao")
def xac_nhan_tat_ca_tin_cay_cao(
    van_ban_id: int | None = Form(None),
    nguoi_dung: NguoiDung = Depends(quyen_xac_nhan),
    db: Session = Depends(get_db),
):
    """Nút demo: "Xác nhận tất cả dòng độ tin cậy cao"."""
    ds = [
        d
        for d in _hang_cho_theo_quyen(db, nguoi_dung, van_ban_id)
        if d.do_tin_cay == "cao"
    ]
    for dong in ds:
        dong.trang_thai = "da_xac_nhan"
        dong.nguoi_xu_ly_id = nguoi_dung.id
        dong.thoi_diem = datetime.now()
        _ghi_vao_lop_2(db, dong, nguoi_dung)
    ghi_nhat_ky(
        db,
        nguoi_dung.id,
        "xac_nhan_trich_xuat",
        f"Xác nhận hàng loạt {len(ds)} dòng độ tin cậy cao"
        + (f" (văn bản #{van_ban_id})" if van_ban_id else ""),
    )
    return RedirectResponse("/trich-xuat", status_code=303)
