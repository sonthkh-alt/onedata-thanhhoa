"""Xuất các báo cáo .docx mô phỏng (thể thức NĐ30) từ văn bản Lớp 1 —
đầu vào cho demo kênh 2 và tủ hồ sơ data/seed/van_ban_mau/.

Chạy SAU khi seed:  python scripts/make_sample_docs.py

Đặc biệt sinh thêm file "bao-cao-hacthanh-202607.docx" — báo cáo THÁNG 7
của phường Hạc Thành CHƯA có trong Kho, để người demo tải lên theo kịch
bản Mục 13 (máy trích số → người xác nhận → số hiện lên dashboard).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db import SessionLocal
from app.models import ChiTieu, DonVi, GiaTriChiTieu, VanBan
from app.services import nd30, van_ban_mau
from app.services.report_builder import NGUOI_KY_DEMO

THU_MUC = Path(__file__).resolve().parent.parent / "data" / "seed" / "van_ban_mau"
NAM = 2026


def xuat_docx_bao_cao(vb: VanBan, duong_dan: Path) -> None:
    """Dựng file .docx thể thức NĐ30 từ một văn bản báo cáo ở Lớp 1."""
    ten_dv = vb.co_quan.ten if vb.co_quan else "UBND xã"
    doc = nd30.tao_van_ban()
    nd30.them_phan_dau(
        doc,
        co_quan_chu_quan="UBND tỉnh Thanh Hóa",
        co_quan_ban_hanh=f"UBND {ten_dv}",
        so_ky_hieu=f"Số: {vb.so}/{vb.ky_hieu}",
        dia_danh=ten_dv.replace("Xã ", "").replace("Phường ", ""),
        ngay=(
            f"ngày {vb.ngay_ban_hanh.day} tháng {vb.ngay_ban_hanh.month} "
            f"năm {vb.ngay_ban_hanh.year}"
            if vb.ngay_ban_hanh
            else f"ngày      tháng      năm {NAM}"
        ),
    )
    nd30.them_ten_loai(doc, "BÁO CÁO", vb.trich_yeu)
    for doan in vb.toan_van.split("\n\n"):
        nd30.them_doan(doc, doan)
    nd30.them_ket_thuc(
        doc,
        noi_nhan=["UBND tỉnh (để báo cáo)", "Sở, ngành liên quan"],
        chuc_vu_dong_1="TM. Ủy ban nhân dân",
        chuc_vu_dong_2="Chủ tịch",
        ho_ten=NGUOI_KY_DEMO,
    )
    doc.add_paragraph()
    nd30.them_dong_mo_phong(doc)
    doc.save(duong_dan)


def sinh_bao_cao_hacthanh_thang7(db) -> Path:
    """File báo cáo tháng 7 của Hạc Thành để TẢI LÊN trong demo (chưa có
    trong Kho). Số liệu DTC02/DTC03/AS04 là số 'mới phát hành' hợp lý."""
    dv = db.query(DonVi).filter_by(ma="HACTHANH").one()
    so: dict[str, float] = {}
    for ct in db.query(ChiTieu).all():
        gt = (
            db.query(GiaTriChiTieu.gia_tri)
            .filter_by(chi_tieu_id=ct.id, don_vi_id=dv.id, nam=NAM, thang=7)
            .scalar()
        )
        if gt is None:  # ô trống chờ kênh 2 → sinh số hợp lý cho file demo
            thang6 = (
                db.query(GiaTriChiTieu.gia_tri)
                .filter_by(chi_tieu_id=ct.id, don_vi_id=dv.id, nam=NAM, thang=6)
                .scalar()
            ) or 0
            if ct.ma == "DTC02":
                ke_hoach = (
                    db.query(GiaTriChiTieu.gia_tri)
                    .join(ChiTieu, ChiTieu.id == GiaTriChiTieu.chi_tieu_id)
                    .filter(
                        ChiTieu.ma == "DTC01",
                        GiaTriChiTieu.don_vi_id == dv.id,
                        GiaTriChiTieu.thang == 7,
                    )
                    .scalar()
                )
                gt = round(thang6 + 0.08 * float(ke_hoach or 0), 0)
                so["DTC01_ke_hoach"] = float(ke_hoach or 0)
            elif ct.ma == "AS04":
                gt = round(thang6 * 1.02, 1)
            else:
                gt = thang6
        so[ct.ma] = float(gt)
    if "DTC01" in so and so.get("DTC01"):
        so["DTC03"] = round(so["DTC02"] / so["DTC01"] * 100, 1)

    cac_doan = van_ban_mau.noi_dung_bao_cao(dv.ten, 7, NAM, so)
    vb_tam = VanBan(
        so="58",
        ky_hieu="BC-UBND-HACTHANH",
        loai="bao_cao",
        trich_yeu=van_ban_mau.trich_yeu_bao_cao(7, NAM),
        toan_van="\n\n".join(cac_doan),
    )
    vb_tam.co_quan = dv
    from datetime import date

    vb_tam.ngay_ban_hanh = date(NAM, 7, 24)
    duong_dan = THU_MUC / "bao-cao-hacthanh-202607-TAI-LEN-DEMO.docx"
    xuat_docx_bao_cao(vb_tam, duong_dan)
    return duong_dan


def main() -> None:
    THU_MUC.mkdir(parents=True, exist_ok=True)
    db = SessionLocal()
    try:
        ds_bao_cao = db.query(VanBan).filter_by(loai="bao_cao", mat=False).all()
        so_file = 0
        for vb in ds_bao_cao:
            if not vb.duong_dan_file:
                continue
            duong_dan = Path(vb.duong_dan_file)
            if not duong_dan.is_absolute():
                duong_dan = THU_MUC.parent.parent.parent / vb.duong_dan_file
            duong_dan.parent.mkdir(parents=True, exist_ok=True)
            xuat_docx_bao_cao(vb, duong_dan)
            so_file += 1
        file_demo = sinh_bao_cao_hacthanh_thang7(db)
    finally:
        db.close()
    print(f"Đã xuất {so_file} báo cáo .docx vào {THU_MUC}")
    print(f"File dùng cho kịch bản TẢI LÊN demo: {file_demo.name}")


if __name__ == "__main__":
    main()
