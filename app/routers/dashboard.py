"""Dashboard điều hành: trang tỉnh và trang chi tiết đơn vị (CLAUDE.md 8.3)."""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.auth import require_roles, require_user
from app.db import get_db
from app.models import ChiTieu, DonVi, GiaTriChiTieu, NguoiDung, NhatKy
from app.services import canh_bao, tong_hop

router = APIRouter(tags=["dashboard"])

NAM_DEMO = 2026
CAC_THANG = list(range(1, 8))

TEN_VUNG = {"do_thi": "Đô thị", "dong_bang": "Đồng bằng", "mien_nui": "Miền núi"}

xem_dashboard = require_roles("lanh_dao", "dai_bieu_hdnd")


@router.get("/dashboard")
def trang_dashboard(
    request: Request,
    thang: int = 7,
    vung: str | None = None,
    nguoi_dung: NguoiDung = Depends(xem_dashboard),
    db: Session = Depends(get_db),
):
    """Trang tỉnh: thẻ tổng hợp 3 lĩnh vực, xếp hạng, diễn biến, điểm nóng."""
    from app.main import templates

    if thang not in CAC_THANG:
        thang = 7
    if vung not in TEN_VUNG:
        vung = None

    # Thẻ tổng hợp 3 lĩnh vực (kỳ đã chọn)
    the_dtc = {
        "ke_hoach": tong_hop.tong_theo_tinh(db, "DTC01", thang),
        "giai_ngan": tong_hop.tong_theo_tinh(db, "DTC02", thang),
        "ty_le": tong_hop.ty_le_toan_tinh(db, "DTC02", "DTC01", thang),
        "du_an_cham": tong_hop.tong_theo_tinh(db, "DTC05", thang),
    }
    the_tthc = {
        "tiep_nhan": tong_hop.tong_theo_tinh(db, "TTHC01", thang),
        "ty_le_dung_han": tong_hop.ty_le_toan_tinh(db, "TTHC02", "TTHC01", thang),
        "ty_le_truc_tuyen": tong_hop.ty_le_toan_tinh(db, "TTHC05", "TTHC01", thang),
    }
    the_asxh = {
        "ho_ngheo": tong_hop.tong_theo_tinh(db, "AS01", thang),
        "doi_tuong_btxh": tong_hop.tong_theo_tinh(db, "AS03", thang),
        "kinh_phi": tong_hop.tong_theo_tinh(db, "AS04", thang),
        "ty_le_ktm": tong_hop.trung_binh_toan_tinh(db, "AS05", thang),
    }

    # Biểu đồ cột: xếp hạng tỷ lệ giải ngân theo xã
    xep_hang = tong_hop.gia_tri_theo_xa(db, "DTC03", thang, vung)

    # Biểu đồ đường: diễn biến 7 tháng toàn tỉnh
    dien_bien = {
        "nhan": [f"T{t}" for t in CAC_THANG],
        "giai_ngan": tong_hop.chuoi_ty_le_theo_thang(db, "DTC02", "DTC01"),
        "dung_han": tong_hop.chuoi_ty_le_theo_thang(db, "TTHC02", "TTHC01"),
        "truc_tuyen": tong_hop.chuoi_ty_le_theo_thang(db, "TTHC05", "TTHC01"),
    }

    diem_nong = canh_bao.tim_diem_nong(db, thang, NAM_DEMO)

    ds_chi_tieu = db.query(ChiTieu).order_by(ChiTieu.ma).all()
    nguon_dtc03 = next((ct.nguon_du_lieu for ct in ds_chi_tieu if ct.ma == "DTC03"), "")

    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "nguoi_dung": nguoi_dung,
            "thang": thang,
            "nam": NAM_DEMO,
            "ky": NAM_DEMO * 100 + thang,
            "cac_thang": CAC_THANG,
            "vung": vung,
            "ten_vung": TEN_VUNG,
            "the_dtc": the_dtc,
            "the_tthc": the_tthc,
            "the_asxh": the_asxh,
            "xep_hang": xep_hang,
            "dien_bien": dien_bien,
            "diem_nong": diem_nong,
            "ds_chi_tieu": ds_chi_tieu,
            "nguon_dtc03": nguon_dtc03,
        },
    )


@router.get("/so-lieu/{so_lieu_id}")
def ho_chieu_so_lieu(
    request: Request,
    so_lieu_id: int,
    nguoi_dung: NguoiDung = Depends(require_user),
    db: Session = Depends(get_db),
):
    """Hộ chiếu số liệu: một con số — đầy đủ nguồn gốc, không thể chối cãi.

    Ai nhập, lúc nào, từ CSDL nguồn nào (theo QĐ 2053), tính bằng công thức
    gì, lịch sử thay đổi và cờ cảnh báo — điều IOC không truy được vì số
    liệu IOC đến từ báo cáo tổng hợp thủ công.
    """
    from app.main import templates

    gt = db.get(GiaTriChiTieu, so_lieu_id)
    if gt is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy số liệu.")

    chi_tieu = db.get(ChiTieu, gt.chi_tieu_id)
    don_vi = db.get(DonVi, gt.don_vi_id)
    nguoi_cap_nhat = (
        db.get(NguoiDung, gt.nguoi_cap_nhat_id) if gt.nguoi_cap_nhat_id else None
    )
    lich_su = (
        db.query(NhatKy)
        .filter(
            NhatKy.hanh_dong.in_(
                [
                    "nhap_so_lieu",
                    "sua_so_lieu",
                    "canh_bao_du_lieu",
                    "tinh_chi_tieu_dan_xuat",
                ]
            ),
            NhatKy.chi_tiet.like(f"%{don_vi.ten}%"),
            NhatKy.chi_tiet.like(f"%{chi_tieu.ma}%"),
        )
        .order_by(NhatKy.thoi_diem.desc())
        .limit(20)
        .all()
    )
    return templates.TemplateResponse(
        request,
        "so_lieu.html",
        {
            "nguoi_dung": nguoi_dung,
            "gt": gt,
            "chi_tieu": chi_tieu,
            "don_vi": don_vi,
            "nguoi_cap_nhat": nguoi_cap_nhat,
            "lich_su": lich_su,
            "ky": gt.nam * 100 + gt.thang,
        },
    )


@router.get("/don-vi/{ma_don_vi}")
def trang_chi_tiet_don_vi(
    request: Request,
    ma_don_vi: str,
    nguoi_dung: NguoiDung = Depends(xem_dashboard),
    db: Session = Depends(get_db),
):
    """Trang chi tiết một đơn vị: mọi chỉ tiêu 7 tháng + biểu đồ."""
    from app.main import templates

    don_vi = (
        db.query(DonVi)
        .filter(DonVi.ma == ma_don_vi, DonVi.loai.in_(["xa", "phuong"]))
        .first()
    )
    if don_vi is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn vị.")

    ds_chi_tieu = db.query(ChiTieu).order_by(ChiTieu.ma).all()
    bang_so_lieu = []
    for ct in ds_chi_tieu:
        ban_ghi = {
            gt.thang: gt
            for gt in db.query(GiaTriChiTieu)
            .filter_by(chi_tieu_id=ct.id, don_vi_id=don_vi.id, nam=NAM_DEMO)
            .all()
        }
        bang_so_lieu.append(
            {"chi_tieu": ct, "gia_tri": [ban_ghi.get(t) for t in CAC_THANG]}
        )

    bieu_do = {
        "nhan": [f"T{t}" for t in CAC_THANG],
        "giai_ngan": tong_hop.chuoi_gia_tri_don_vi(db, don_vi.id, "DTC03"),
        "dung_han": tong_hop.chuoi_gia_tri_don_vi(db, don_vi.id, "TTHC04"),
        "khong_tien_mat": tong_hop.chuoi_gia_tri_don_vi(db, don_vi.id, "AS05"),
    }

    return templates.TemplateResponse(
        request,
        "don_vi.html",
        {
            "nguoi_dung": nguoi_dung,
            "don_vi": don_vi,
            "cac_thang": CAC_THANG,
            "nam": NAM_DEMO,
            "bang_so_lieu": bang_so_lieu,
            "bieu_do": bieu_do,
        },
    )
