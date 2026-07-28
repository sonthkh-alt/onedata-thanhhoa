"""Phân hệ nhập liệu tại nguồn — "nhập MỘT LẦN" (CLAUDE.md 8.2).

- Chuyên viên xã chỉ nhập/sửa số liệu của đơn vị mình; quản trị chọn đơn vị.
- Quy tắc kiểm tra đọc từ `chi_tieu.rang_buoc` (mô phỏng Content.Rule của
  Hệ thống thông tin báo cáo tỉnh).
- Chỉ tiêu dẫn xuất (có `cong_thuc`) khóa nhập tay, hệ thống tự tính lại.
"""

import re
from datetime import datetime

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.auth import ghi_nhat_ky, require_roles
from app.db import get_db
from app.models import ChiTieu, DonVi, GiaTriChiTieu, NguoiDung
from app.services import ban_tin, tong_hop

router = APIRouter(prefix="/nhap-lieu", tags=["nhap-lieu"])

NAM_DEMO = 2026
CAC_THANG = list(range(1, 8))

MAU_CONG_THUC = re.compile(r"^(\w+)/(\w+)\*100$")


def _don_vi_lam_viec(
    nguoi_dung: NguoiDung, db: Session, ma_don_vi: str | None
) -> DonVi | None:
    """Xác định đơn vị mà người dùng được nhập số liệu.

    Chuyên viên xã: luôn là đơn vị của mình (bỏ qua tham số).
    Quản trị: chọn qua tham số `don_vi`, mặc định xã đầu tiên.
    """
    if nguoi_dung.vai_tro == "chuyen_vien_xa":
        return db.get(DonVi, nguoi_dung.don_vi_id)
    truy_van = db.query(DonVi).filter(DonVi.loai.in_(["xa", "phuong"]))
    if ma_don_vi:
        return truy_van.filter(DonVi.ma == ma_don_vi).first()
    return truy_van.order_by(DonVi.ten).first()


def _gia_tri_ky(db: Session, don_vi_id: int, thang: int) -> dict[int, GiaTriChiTieu]:
    """Map chi_tieu_id → bản ghi giá trị của đơn vị trong kỳ."""
    ds = (
        db.query(GiaTriChiTieu)
        .filter_by(don_vi_id=don_vi_id, nam=NAM_DEMO, thang=thang)
        .all()
    )
    return {gt.chi_tieu_id: gt for gt in ds}


def _upsert_gia_tri(
    db: Session,
    chi_tieu: ChiTieu,
    don_vi: DonVi,
    thang: int,
    gia_tri: float,
    nguon: str,
    nguoi_dung: NguoiDung,
    van_ban_id: int | None = None,
) -> str:
    """Ghi giá trị một chỉ tiêu (một số liệu chỉ có MỘT bản ghi).

    Kênh 2 truyền `van_ban_id` để giữ liên kết về văn bản gốc ở Lớp 1.
    Trả về "nhap" nếu tạo mới, "sua" nếu ghi đè.
    """
    ban_ghi = (
        db.query(GiaTriChiTieu)
        .filter_by(
            chi_tieu_id=chi_tieu.id, don_vi_id=don_vi.id, nam=NAM_DEMO, thang=thang
        )
        .first()
    )
    if ban_ghi is None:
        db.add(
            GiaTriChiTieu(
                chi_tieu_id=chi_tieu.id,
                don_vi_id=don_vi.id,
                nam=NAM_DEMO,
                thang=thang,
                gia_tri=gia_tri,
                nguon=nguon,
                van_ban_id=van_ban_id,
                nguoi_xac_nhan_id=nguoi_dung.id,
                thoi_diem_cap_nhat=datetime.now(),
            )
        )
        return "nhap"
    ban_ghi.gia_tri = gia_tri
    ban_ghi.nguon = nguon
    ban_ghi.van_ban_id = van_ban_id
    ban_ghi.nguoi_xac_nhan_id = nguoi_dung.id
    ban_ghi.thoi_diem_cap_nhat = datetime.now()
    return "sua"


def _tinh_chi_tieu_dan_xuat(
    db: Session,
    ds_chi_tieu: list[ChiTieu],
    don_vi: DonVi,
    thang: int,
    nguoi_dung: NguoiDung,
) -> list[str]:
    """Tự tính các chỉ tiêu có công thức dạng A/B*100; trả về danh sách mã đã tính."""
    map_ct = {ct.ma: ct for ct in ds_chi_tieu}
    gia_tri_ky = _gia_tri_ky(db, don_vi.id, thang)
    da_tinh: list[str] = []
    for ct in ds_chi_tieu:
        if not ct.cong_thuc:
            continue
        khop = MAU_CONG_THUC.match(ct.cong_thuc.replace(" ", ""))
        if not khop:
            continue
        ma_tu, ma_mau = khop.group(1), khop.group(2)
        ct_tu, ct_mau = map_ct.get(ma_tu), map_ct.get(ma_mau)
        if ct_tu is None or ct_mau is None:
            continue
        gt_tu = gia_tri_ky.get(ct_tu.id)
        gt_mau = gia_tri_ky.get(ct_mau.id)
        if gt_tu is None or gt_mau is None or not gt_mau.gia_tri:
            continue
        ket_qua = round(gt_tu.gia_tri / gt_mau.gia_tri * 100, 1)
        _upsert_gia_tri(db, ct, don_vi, thang, ket_qua, "he_thong", nguoi_dung)
        da_tinh.append(ct.ma)
    return da_tinh


def _kiem_tra_gia_tri(
    chi_tieu: ChiTieu, gia_tri: float, gia_tri_thang_truoc: float | None
) -> tuple[str | None, str | None]:
    """Áp quy tắc trong `chi_tieu.rang_buoc`.

    Trả về (lỗi chặn lưu, cảnh báo cho phép lưu).
    """
    rb = chi_tieu.rang_buoc or ""
    if "0 <= gia_tri <= 100" in rb and not 0 <= gia_tri <= 100:
        return (
            f"{chi_tieu.ma}: giá trị phần trăm phải nằm trong [0; 100] "
            f"(đã nhập {gia_tri:g}).",
            None,
        )
    if "gia_tri >= 0" in rb and gia_tri < 0:
        return (f"{chi_tieu.ma}: giá trị không được âm (đã nhập {gia_tri:g}).", None)
    if (
        "canh_bao_neu_giam_so_ky_truoc" in rb
        and gia_tri_thang_truoc is not None
        and gia_tri < gia_tri_thang_truoc
    ):
        return (
            None,
            f"{chi_tieu.ma}: giá trị lũy kế {gia_tri:g} GIẢM so với kỳ trước "
            f"({gia_tri_thang_truoc:g}) — đã lưu nhưng gắn cờ nghi sai số liệu.",
        )
    return (None, None)


def _duoc_nhap_tay(ct: ChiTieu, gt: GiaTriChiTieu | None) -> bool:
    """Kênh 3 (v0.2) CHỈ nhập chỉ tiêu chưa có giá trị từ kênh 1/kênh 2.

    Được nhập khi: chưa có giá trị kỳ này, hoặc giá trị hiện có vốn là
    nhập tay (sửa lại chính kênh 3). Chỉ tiêu dẫn xuất không bao giờ nhập.
    """
    if ct.cong_thuc:
        return False
    return gt is None or gt.nguon == "nhap_tay"


def _du_lieu_trang(
    db: Session,
    nguoi_dung: NguoiDung,
    don_vi: DonVi,
    thang: int,
) -> dict:
    """Chuẩn bị dữ liệu chung cho template nhập liệu."""
    ds_chi_tieu = db.query(ChiTieu).order_by(ChiTieu.ma).all()
    gia_tri_ky = _gia_tri_ky(db, don_vi.id, thang)
    ds_xa = (
        db.query(DonVi)
        .filter(DonVi.loai.in_(["xa", "phuong"]))
        .order_by(DonVi.ten)
        .all()
        if nguoi_dung.vai_tro == "quan_tri"
        else []
    )
    duoc_nhap = {ct.id: _duoc_nhap_tay(ct, gia_tri_ky.get(ct.id)) for ct in ds_chi_tieu}
    return {
        "nguoi_dung": nguoi_dung,
        "don_vi": don_vi,
        "thang": thang,
        "nam": NAM_DEMO,
        "ky": NAM_DEMO * 100 + thang,
        "cac_thang": CAC_THANG,
        "ds_chi_tieu": ds_chi_tieu,
        "gia_tri_ky": gia_tri_ky,
        "duoc_nhap": duoc_nhap,
        "so_o_duoc_nhap": sum(1 for v in duoc_nhap.values() if v),
        "ds_xa": ds_xa,
    }


@router.get("")
def trang_nhap_lieu(
    request: Request,
    thang: int = 7,
    don_vi: str | None = None,
    nguoi_dung: NguoiDung = Depends(require_roles("chuyen_vien_xa")),
    db: Session = Depends(get_db),
):
    """Trang "Nhập số liệu kỳ tháng M/2026" của đơn vị người dùng."""
    from app.main import templates

    if thang not in CAC_THANG:
        thang = 7
    dv = _don_vi_lam_viec(nguoi_dung, db, don_vi)
    if dv is None:
        return RedirectResponse("/", status_code=303)
    ctx = _du_lieu_trang(db, nguoi_dung, dv, thang)
    ctx.update({"thong_bao": None, "ds_loi": [], "ds_canh_bao": []})
    return templates.TemplateResponse(request, "nhap_lieu.html", ctx)


@router.post("")
async def luu_nhap_lieu(
    request: Request,
    nguoi_dung: NguoiDung = Depends(require_roles("chuyen_vien_xa")),
    db: Session = Depends(get_db),
):
    """Lưu số liệu người dùng nhập: kiểm tra, ghi đè có log, tự tính dẫn xuất."""
    from app.main import templates

    form = await request.form()
    try:
        thang = int(form.get("thang", 7))
    except ValueError:
        thang = 7
    if thang not in CAC_THANG:
        thang = 7

    dv = _don_vi_lam_viec(nguoi_dung, db, form.get("don_vi") or None)
    if dv is None:
        return RedirectResponse("/", status_code=303)

    ds_chi_tieu = db.query(ChiTieu).order_by(ChiTieu.ma).all()
    gia_tri_thang_truoc = _gia_tri_ky(db, dv.id, thang - 1) if thang > 1 else {}

    ds_loi: list[str] = []
    ds_canh_bao: list[str] = []
    so_da_luu = 0
    da_luu: list[tuple[ChiTieu, float, float | None]] = []

    gia_tri_ky_hien_tai = _gia_tri_ky(db, dv.id, thang)
    for ct in ds_chi_tieu:
        # Kênh 3 chỉ nhận chỉ tiêu CHƯA có từ kênh 1/kênh 2 (v0.2 — 9.4)
        if not _duoc_nhap_tay(ct, gia_tri_ky_hien_tai.get(ct.id)):
            continue
        gia_tri_tho = (form.get(f"gt_{ct.ma}") or "").strip()
        if gia_tri_tho == "":
            continue
        try:
            gia_tri = float(gia_tri_tho.replace(",", "."))
        except ValueError:
            ds_loi.append(f"{ct.ma}: “{gia_tri_tho}” không phải là số hợp lệ.")
            continue

        gt_truoc = gia_tri_thang_truoc.get(ct.id)
        loi, canh_bao = _kiem_tra_gia_tri(
            ct, gia_tri, gt_truoc.gia_tri if gt_truoc else None
        )
        if loi:
            ds_loi.append(loi)
            continue
        if canh_bao:
            ds_canh_bao.append(canh_bao)
            ghi_nhat_ky(
                db,
                nguoi_dung.id,
                "canh_bao_du_lieu",
                f"{dv.ten} — {canh_bao}",
            )

        gt_hien_tai = (
            db.query(GiaTriChiTieu)
            .filter_by(chi_tieu_id=ct.id, don_vi_id=dv.id, nam=NAM_DEMO, thang=thang)
            .first()
        )
        gia_tri_cu = gt_hien_tai.gia_tri if gt_hien_tai else None
        if gia_tri_cu is not None and gia_tri_cu == gia_tri:
            continue  # không đổi thì không ghi

        hanh_dong = _upsert_gia_tri(db, ct, dv, thang, gia_tri, "nhap_tay", nguoi_dung)
        so_da_luu += 1
        da_luu.append((ct, gia_tri, gt_truoc.gia_tri if gt_truoc else None))
        chi_tiet = f"{dv.ten} — {ct.ma} tháng {thang}/{NAM_DEMO} = {gia_tri:g}" + (
            f" (giá trị cũ: {gia_tri_cu:g})" if gia_tri_cu is not None else ""
        )
        ghi_nhat_ky(
            db,
            nguoi_dung.id,
            "nhap_so_lieu" if hanh_dong == "nhap" else "sua_so_lieu",
            chi_tiet,
        )

    da_tinh = _tinh_chi_tieu_dan_xuat(db, ds_chi_tieu, dv, thang, nguoi_dung)
    db.commit()
    if da_tinh:
        ghi_nhat_ky(
            db,
            nguoi_dung.id,
            "tinh_chi_tieu_dan_xuat",
            f"{dv.ten} — tự tính {', '.join(da_tinh)} tháng {thang}/{NAM_DEMO}",
        )

    thong_bao = None
    if so_da_luu:
        thong_bao = (
            f"Đã lưu {so_da_luu} số liệu tháng {thang}/{NAM_DEMO}"
            + (f", hệ thống tự tính {', '.join(da_tinh)}" if da_tinh else "")
            + ". Anh/chị KHÔNG phải báo cáo lại số liệu này ở bất kỳ đâu."
        )
    elif not ds_loi:
        thong_bao = "Không có số liệu nào thay đổi."

    # PHÂN TÍCH TỨC THÌ: vừa cập nhật dữ liệu, hệ thống tự phân tích ngay —
    # so kỳ trước, vị trí mới trong tỉnh, dự báo cả năm thay đổi thế nào.
    phan_tich_nhanh: list[dict] = []
    du_bao_moi = None
    if da_luu:
        for ct, gia_tri, gia_tri_truoc in da_luu:
            xep_hang = tong_hop.gia_tri_theo_xa(db, ct.ma, thang)
            hang = next(
                (i + 1 for i, d in enumerate(xep_hang) if d["ma"] == dv.ma), None
            )
            phan_tich_nhanh.append(
                {
                    "ma": ct.ma,
                    "ten": ct.ten,
                    "gia_tri": gia_tri,
                    "don_vi_tinh": ct.don_vi_tinh,
                    "so_ky_truoc": (
                        round(gia_tri - gia_tri_truoc, 1)
                        if gia_tri_truoc is not None
                        else None
                    ),
                    "hang": hang,
                    "tong_xa": len(xep_hang),
                }
            )
        if any(ct.ma.startswith("DTC") for ct, _, _ in da_luu):
            du_bao_moi = next(
                (d for d in ban_tin.du_bao_giai_ngan(db) if d.ma == dv.ma), None
            )

    ctx = _du_lieu_trang(db, nguoi_dung, dv, thang)
    ctx.update(
        {
            "thong_bao": thong_bao,
            "ds_loi": ds_loi,
            "ds_canh_bao": ds_canh_bao,
            "phan_tich_nhanh": phan_tich_nhanh,
            "du_bao_moi": du_bao_moi,
        }
    )
    return templates.TemplateResponse(request, "nhap_lieu.html", ctx)
