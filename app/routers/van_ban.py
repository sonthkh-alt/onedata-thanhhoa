"""Lớp 1 — Kho văn bản, tri thức số: danh sách, xem, tải lên, tìm kiếm."""

import re
import uuid
from datetime import date
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.auth import ghi_nhat_ky, require_roles, require_user
from app.config import BASE_DIR
from app.db import get_db
from app.models import DonVi, NguoiDung, VanBan
from app.services import doc_ingest, extractor, search

router = APIRouter(prefix="/van-ban", tags=["van-ban"])

THU_MUC_UPLOAD = BASE_DIR / "uploads"

TEN_LOAI = {
    "bao_cao": "Báo cáo",
    "ke_hoach": "Kế hoạch",
    "thong_bao": "Thông báo",
    "cong_van": "Công văn",
}

quyen_tai_len = require_roles("chuyen_vien_xa")


@router.get("")
def danh_sach_van_ban(
    request: Request,
    co_quan: str | None = None,
    loai: str | None = None,
    q: str | None = None,
    nguoi_dung: NguoiDung = Depends(require_user),
    db: Session = Depends(get_db),
):
    """Danh sách văn bản (lọc cơ quan/loại) + ô tìm kiếm toàn văn FTS5."""
    from app.main import templates

    ket_qua_tim = search.tim_kiem(db, q, nguoi_dung) if q and q.strip() else None

    truy_van = db.query(VanBan).order_by(VanBan.thoi_diem_tiep_nhan.desc())
    if nguoi_dung.vai_tro != "quan_tri":
        truy_van = truy_van.filter(VanBan.mat.is_(False))
    if co_quan:
        dv = db.query(DonVi).filter_by(ma=co_quan).first()
        if dv:
            truy_van = truy_van.filter(VanBan.co_quan_id == dv.id)
    if loai in TEN_LOAI:
        truy_van = truy_van.filter(VanBan.loai == loai)

    ds_co_quan = db.query(DonVi).order_by(DonVi.ten).all()
    return templates.TemplateResponse(
        request,
        "van_ban_ds.html",
        {
            "nguoi_dung": nguoi_dung,
            "ds_van_ban": truy_van.limit(100).all(),
            "ds_co_quan": ds_co_quan,
            "ten_loai": TEN_LOAI,
            "loc_co_quan": co_quan or "",
            "loc_loai": loai or "",
            "q": q or "",
            "ket_qua_tim": ket_qua_tim,
        },
    )


@router.get("/tai-len")
def form_tai_len(
    request: Request,
    nguoi_dung: NguoiDung = Depends(quyen_tai_len),
    db: Session = Depends(get_db),
):
    """Form tiếp nhận văn bản (demo mô phỏng luồng tự động từ TD Office)."""
    from app.main import templates

    return templates.TemplateResponse(
        request, "van_ban_tai_len.html", {"nguoi_dung": nguoi_dung}
    )


@router.post("/tai-len")
async def nhan_file_tai_len(
    request: Request,
    tep: UploadFile = File(...),
    nguoi_dung: NguoiDung = Depends(quyen_tai_len),
    db: Session = Depends(get_db),
):
    """Bước 1: nhận .docx, đọc toàn văn, bóc siêu dữ liệu → cho người dùng
    RÀ VÀ SỬA trước khi lưu (không lưu thẳng)."""
    from app.main import templates

    if not (tep.filename or "").lower().endswith(".docx"):
        raise HTTPException(status_code=400, detail="Chỉ nhận file .docx.")
    THU_MUC_UPLOAD.mkdir(exist_ok=True)
    ten_tam = f"{uuid.uuid4().hex}.docx"
    duong_dan = THU_MUC_UPLOAD / ten_tam
    duong_dan.write_bytes(await tep.read())

    try:
        toan_van = doc_ingest.doc_toan_van_docx(duong_dan)
    except Exception as loi:
        duong_dan.unlink(missing_ok=True)
        raise HTTPException(
            status_code=400, detail=f"Không đọc được file .docx: {loi}"
        ) from loi

    meta = doc_ingest.boc_sieu_du_lieu(toan_van, db)
    # Chuyên viên xã: mặc định cơ quan ban hành là đơn vị mình
    if nguoi_dung.vai_tro == "chuyen_vien_xa":
        meta["co_quan_id"] = meta["co_quan_id"] or nguoi_dung.don_vi_id

    ds_co_quan = db.query(DonVi).order_by(DonVi.ten).all()
    return templates.TemplateResponse(
        request,
        "van_ban_xac_nhan_meta.html",
        {
            "nguoi_dung": nguoi_dung,
            "ten_tam": ten_tam,
            "ten_goc": tep.filename,
            "toan_van": toan_van,
            "meta": meta,
            "ds_co_quan": ds_co_quan,
            "ten_loai": TEN_LOAI,
        },
    )


@router.post("/luu")
def luu_van_ban(
    ten_tam: str = Form(...),
    so: str = Form(""),
    ky_hieu: str = Form(""),
    loai: str = Form("bao_cao"),
    trich_yeu: str = Form(""),
    co_quan_id: int = Form(...),
    ngay_ban_hanh: str = Form(""),
    mat: bool = Form(False),
    nguoi_dung: NguoiDung = Depends(quyen_tai_len),
    db: Session = Depends(get_db),
):
    """Bước 2: lưu văn bản vào Lớp 1 rồi chạy MÁY TRÍCH XUẤT (kênh 2)."""
    if "/" in ten_tam or "\\" in ten_tam or ".." in ten_tam:
        raise HTTPException(status_code=400, detail="Tên file không hợp lệ.")
    duong_dan = THU_MUC_UPLOAD / ten_tam
    if not duong_dan.is_file():
        raise HTTPException(status_code=404, detail="File tạm không còn tồn tại.")

    # Chuyên viên xã chỉ được tiếp nhận văn bản của đơn vị mình
    if nguoi_dung.vai_tro == "chuyen_vien_xa" and co_quan_id != nguoi_dung.don_vi_id:
        raise HTTPException(
            status_code=403, detail="Chỉ được tiếp nhận văn bản của đơn vị mình."
        )

    ngay: date | None = None
    if ngay_ban_hanh:
        try:
            ngay = date.fromisoformat(ngay_ban_hanh)
        except ValueError:
            ngay = None

    toan_van = doc_ingest.doc_toan_van_docx(duong_dan)
    vb = doc_ingest.luu_van_ban(
        db,
        toan_van=toan_van,
        so=so,
        ky_hieu=ky_hieu,
        loai=loai if loai in TEN_LOAI else "bao_cao",
        trich_yeu=trich_yeu,
        co_quan_id=co_quan_id,
        ngay_ban_hanh=ngay,
        duong_dan_file=f"uploads/{ten_tam}",
        mat=mat,
    )
    ghi_nhat_ky(
        db,
        nguoi_dung.id,
        "tiep_nhan_van_ban",
        f"Văn bản #{vb.id} {vb.so}/{vb.ky_hieu} — {vb.trich_yeu[:150]}"
        + (" [MẬT — chặn khỏi Kho tìm kiếm/AI/trích xuất]" if mat else ""),
    )

    if vb.mat:
        return RedirectResponse(f"/van-ban/{vb.id}", status_code=303)

    ds_trich = extractor.trich_xuat(db, vb)
    ghi_nhat_ky(
        db,
        nguoi_dung.id,
        "may_trich_xuat",
        f"Văn bản #{vb.id}: máy đọc được {len(ds_trich)} chỉ tiêu, "
        "đã đưa vào hàng chờ xác nhận.",
    )
    return RedirectResponse(f"/trich-xuat?van_ban_id={vb.id}", status_code=303)


@router.get("/{van_ban_id}")
def xem_van_ban(
    request: Request,
    van_ban_id: int,
    nguoi_dung: NguoiDung = Depends(require_user),
    db: Session = Depends(get_db),
):
    """Trang chi tiết: siêu dữ liệu + toàn văn + link tải file gốc."""
    from app.main import templates

    vb = db.get(VanBan, van_ban_id)
    if vb is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy văn bản.")
    if vb.mat and nguoi_dung.vai_tro != "quan_tri":
        # Văn bản mật bị chặn khỏi Kho với mọi vai trò thường
        raise HTTPException(status_code=404, detail="Không tìm thấy văn bản.")

    co_file = False
    if vb.duong_dan_file:
        co_file = (BASE_DIR / vb.duong_dan_file).is_file()
    return templates.TemplateResponse(
        request,
        "van_ban_xem.html",
        {
            "nguoi_dung": nguoi_dung,
            "vb": vb,
            "ten_loai": TEN_LOAI,
            "co_file": co_file,
        },
    )


@router.get("/{van_ban_id}/tai-file")
def tai_file_goc(
    van_ban_id: int,
    nguoi_dung: NguoiDung = Depends(require_user),
    db: Session = Depends(get_db),
):
    """Tải file .docx gốc của văn bản."""
    vb = db.get(VanBan, van_ban_id)
    if vb is None or (vb.mat and nguoi_dung.vai_tro != "quan_tri"):
        raise HTTPException(status_code=404, detail="Không tìm thấy văn bản.")
    if not vb.duong_dan_file:
        raise HTTPException(status_code=404, detail="Văn bản không có file gốc.")
    duong_dan = BASE_DIR / vb.duong_dan_file
    if not duong_dan.is_file():
        raise HTTPException(
            status_code=404,
            detail="File gốc chưa được sinh — chạy scripts/make_sample_docs.py.",
        )
    ten = re.sub(r"[^\w.-]", "-", Path(vb.duong_dan_file).name)
    return FileResponse(
        duong_dan,
        media_type=(
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ),
        filename=ten,
    )
