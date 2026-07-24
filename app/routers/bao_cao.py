"""Router máy soạn báo cáo NĐ30: tạo 1 báo cáo, tạo loạt 15 xã, tải file."""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.auth import ghi_nhat_ky, require_roles
from app.db import get_db
from app.models import DonVi, NguoiDung
from app.services import report_builder
from app.services.report_builder import MAU_BAO_CAO, THU_MUC_XUAT

router = APIRouter(prefix="/bao-cao", tags=["bao-cao"])

CAC_THANG = list(range(1, 8))

TEN_MAU = {
    "BC-DTC": "Báo cáo tình hình giải ngân vốn đầu tư công",
    "BC-TTHC": "Báo cáo kết quả giải quyết thủ tục hành chính",
}

quyen_tao_bao_cao = require_roles("lanh_dao")


@router.get("/tao")
def tao_mot_bao_cao(
    don_vi: str,
    mau: str = "BC-DTC",
    thang: int = 7,
    nguoi_dung: NguoiDung = Depends(quyen_tao_bao_cao),
    db: Session = Depends(get_db),
):
    """Tạo 1 báo cáo cho một xã và trả về file .docx để tải."""
    if mau not in MAU_BAO_CAO:
        raise HTTPException(status_code=400, detail="Mẫu báo cáo không hợp lệ.")
    if thang not in CAC_THANG:
        thang = 7
    dv = (
        db.query(DonVi)
        .filter(DonVi.ma == don_vi, DonVi.loai.in_(["xa", "phuong"]))
        .first()
    )
    if dv is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn vị.")

    duong_dan = report_builder.tao_bao_cao(db, dv, mau, thang)
    ghi_nhat_ky(
        db,
        nguoi_dung.id,
        "sinh_bao_cao",
        f"{TEN_MAU[mau]} tháng {thang}/2026 — {dv.ten} → {duong_dan.name}",
    )
    return FileResponse(
        duong_dan,
        media_type=(
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ),
        filename=duong_dan.name,
    )


@router.get("/tao-tat-ca")
def tao_bao_cao_tat_ca(
    request: Request,
    mau: str = "BC-DTC",
    thang: int = 7,
    nguoi_dung: NguoiDung = Depends(quyen_tao_bao_cao),
    db: Session = Depends(get_db),
):
    """Nút demo: "Tạo báo cáo tháng này cho tất cả 15 xã" + đo thời gian."""
    from app.main import templates

    if mau not in MAU_BAO_CAO:
        raise HTTPException(status_code=400, detail="Mẫu báo cáo không hợp lệ.")
    if thang not in CAC_THANG:
        thang = 7

    ds_file, thoi_gian = report_builder.tao_bao_cao_hang_loat(db, mau, thang)
    ghi_nhat_ky(
        db,
        nguoi_dung.id,
        "sinh_bao_cao_hang_loat",
        f"{TEN_MAU[mau]} tháng {thang}/2026 — {len(ds_file)} xã "
        f"trong {thoi_gian} giây",
    )
    return templates.TemplateResponse(
        request,
        "bao_cao_ket_qua.html",
        {
            "nguoi_dung": nguoi_dung,
            "ten_mau": TEN_MAU[mau],
            "mau": mau,
            "thang": thang,
            "so_file": len(ds_file),
            "thoi_gian": thoi_gian,
            "ds_file": [f.name for f in ds_file],
        },
    )


@router.get("/tai/{ten_file}")
def tai_bao_cao(
    ten_file: str,
    nguoi_dung: NguoiDung = Depends(quyen_tao_bao_cao),
):
    """Tải một file báo cáo đã sinh trong outputs/ (chặn vượt thư mục)."""
    if "/" in ten_file or "\\" in ten_file or ".." in ten_file:
        raise HTTPException(status_code=400, detail="Tên file không hợp lệ.")
    duong_dan = THU_MUC_XUAT / ten_file
    if not duong_dan.is_file() or duong_dan.suffix != ".docx":
        raise HTTPException(status_code=404, detail="Không tìm thấy file báo cáo.")
    return FileResponse(
        duong_dan,
        media_type=(
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ),
        filename=ten_file,
    )
