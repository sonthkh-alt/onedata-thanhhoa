"""Trang công khai cho người dân — mô hình "Cổng dữ liệu mở thu nhỏ"
(CLAUDE.md 8.7, theo cấu trúc Phụ lục 3 QĐ 2053/QĐ-UBND).

Không cần đăng nhập. Chỉ hiển thị chỉ tiêu thuộc Danh mục dữ liệu mở
(cong_khai=true). Tải xuống Excel/JSON; tiếp nhận góp ý nhu cầu dữ liệu.
"""

import io
from datetime import datetime

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import JSONResponse, RedirectResponse, StreamingResponse
from openpyxl import Workbook
from sqlalchemy.orm import Session

from app.auth import get_current_user, ghi_nhat_ky
from app.db import get_db
from app.models import ChiTieu, DonVi, GiaTriChiTieu, NguoiDung

router = APIRouter(prefix="/cong-khai", tags=["cong-khai"])

NAM_DEMO = 2026
THANG_MOI_NHAT = 7


def _du_lieu_cong_khai(db: Session) -> list[dict]:
    """Các chỉ tiêu thuộc Danh mục dữ liệu mở, kỳ mới nhất, theo xã.

    Mỗi tập kèm metadata đúng cột Phụ lục 3: Cơ quan chủ trì cung cấp,
    Kỳ nhập liệu, Định dạng - hình thức chia sẻ, thời điểm cập nhật.
    """
    ds_chi_tieu = db.query(ChiTieu).filter_by(cong_khai=True).order_by(ChiTieu.ma).all()
    ket_qua = []
    for ct in ds_chi_tieu:
        dong = (
            db.query(DonVi, GiaTriChiTieu)
            .join(GiaTriChiTieu, GiaTriChiTieu.don_vi_id == DonVi.id)
            .filter(
                GiaTriChiTieu.chi_tieu_id == ct.id,
                GiaTriChiTieu.nam == NAM_DEMO,
                GiaTriChiTieu.thang == THANG_MOI_NHAT,
                DonVi.loai.in_(["xa", "phuong"]),
            )
            .order_by(DonVi.ten)
            .all()
        )
        cap_nhat_max = max((gt.thoi_diem_cap_nhat for _, gt in dong), default=None)
        ket_qua.append(
            {
                "chi_tieu": ct,
                "so_lieu": [
                    {"ten_don_vi": dv.ten, "ma_dvhc": dv.ma_dvhc, "gia_tri": gt.gia_tri}
                    for dv, gt in dong
                ],
                "cap_nhat": (
                    cap_nhat_max.strftime("%Y-%m-%d %H:%M") if cap_nhat_max else "—"
                ),
            }
        )
    return ket_qua


@router.get("")
def trang_cong_khai(
    request: Request,
    gop_y: str | None = None,
    db: Session = Depends(get_db),
):
    """Trang công khai "Dân biết – dân giám sát" (không cần đăng nhập)."""
    from app.main import templates

    du_lieu = _du_lieu_cong_khai(db)
    # Biểu đồ: tỷ lệ giải ngân (DTC03) theo xã
    bieu_do = next(
        (
            [{"ten": d["ten_don_vi"], "gia_tri": d["gia_tri"]} for d in tap["so_lieu"]]
            for tap in du_lieu
            if tap["chi_tieu"].ma == "DTC03"
        ),
        [],
    )
    bieu_do.sort(key=lambda d: d["gia_tri"], reverse=True)
    return templates.TemplateResponse(
        request,
        "cong_khai.html",
        {
            "nguoi_dung": None,
            "du_lieu": du_lieu,
            "bieu_do": bieu_do,
            "thang": THANG_MOI_NHAT,
            "nam": NAM_DEMO,
            "ky": NAM_DEMO * 100 + THANG_MOI_NHAT,
            "da_gop_y": gop_y == "ok",
        },
    )


@router.get("/tai-xuong")
def tai_xuong(dinh_dang: str = "json", db: Session = Depends(get_db)):
    """Tải dữ liệu mở: Excel (.xlsx) hoặc JSON — cột "Định dạng, hình thức
    chia sẻ: API, Excel" của Danh mục dữ liệu mở."""
    du_lieu = _du_lieu_cong_khai(db)

    if dinh_dang == "xlsx":
        wb = Workbook()
        ws = wb.active
        ws.title = f"Du lieu mo {NAM_DEMO}{THANG_MOI_NHAT:02d}"
        ws.append(
            [
                "Mã chỉ tiêu",
                "Tên chỉ tiêu",
                "Đơn vị tính",
                "Cơ quan chủ trì cung cấp",
                "Kỳ",
                "Đơn vị hành chính",
                "Mã ĐVHC",
                "Giá trị",
            ]
        )
        for tap in du_lieu:
            ct = tap["chi_tieu"]
            for d in tap["so_lieu"]:
                ws.append(
                    [
                        ct.ma,
                        ct.ten,
                        ct.don_vi_tinh,
                        ct.co_quan_chu_chi_tieu,
                        f"{NAM_DEMO}{THANG_MOI_NHAT:02d}",
                        d["ten_don_vi"],
                        d["ma_dvhc"],
                        d["gia_tri"],
                    ]
                )
        ws.append([])
        ws.append(
            ["Dữ liệu mô phỏng phục vụ trình diễn — không phải số liệu chính thức."]
        )
        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)
        ten_file = f"du-lieu-mo-{NAM_DEMO}{THANG_MOI_NHAT:02d}.xlsx"
        return StreamingResponse(
            buf,
            media_type=(
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ),
            headers={"Content-Disposition": f'attachment; filename="{ten_file}"'},
        )

    # JSON (minh họa hình thức chia sẻ API)
    return JSONResponse(
        {
            "nguon": "Kho dữ liệu dùng chung tỉnh Thanh Hóa (bản demo)",
            "ky": f"{NAM_DEMO}{THANG_MOI_NHAT:02d}",
            "luu_y": "Dữ liệu mô phỏng phục vụ trình diễn.",
            "tap_du_lieu": [
                {
                    "ma_chi_tieu": tap["chi_tieu"].ma,
                    "ten_chi_tieu": tap["chi_tieu"].ten,
                    "don_vi_tinh": tap["chi_tieu"].don_vi_tinh,
                    "co_quan_chu_tri": tap["chi_tieu"].co_quan_chu_chi_tieu,
                    "ky_nhap_lieu": tap["chi_tieu"].tan_suat,
                    "cap_nhat": tap["cap_nhat"],
                    "so_lieu": tap["so_lieu"],
                }
                for tap in du_lieu
            ],
        }
    )


@router.post("/gop-y")
def gop_y_du_lieu_mo(
    request: Request,
    noi_dung: str = Form(...),
    email: str = Form(""),
    db: Session = Depends(get_db),
):
    """Tiếp nhận góp ý nhu cầu dữ liệu mở của người dân (Điều 3.3.g QĐ 2053)."""
    nguoi_dung: NguoiDung | None = get_current_user(request, db)
    chi_tiet = f"Góp ý dữ liệu mở: {noi_dung.strip()[:500]}"
    if email.strip():
        chi_tiet += f" (liên hệ: {email.strip()[:100]})"
    chi_tiet += f" — lúc {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    ghi_nhat_ky(db, nguoi_dung.id if nguoi_dung else None, "gop_y_du_lieu_mo", chi_tiet)
    return RedirectResponse("/cong-khai?gop_y=ok", status_code=303)
