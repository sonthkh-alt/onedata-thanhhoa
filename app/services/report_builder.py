"""Máy soạn báo cáo: ghép số liệu từ CSDL vào 2 mẫu báo cáo NĐ30
(CLAUDE.md 8.4). Nhận (đơn vị, kỳ) → nhận định tự động → .docx trong outputs/.
"""

import time
from pathlib import Path

from sqlalchemy.orm import Session

from app.config import BASE_DIR
from app.models import ChiTieu, DonVi, GiaTriChiTieu
from app.services import nd30

NAM_DEMO = 2026
THU_MUC_XUAT = BASE_DIR / "outputs"

# Họ tên người ký là tên GIẢ ĐỊNH cho demo — không dùng tên người thật
NGUOI_KY_DEMO = "Nguyễn Văn Demo"


def _gia_tri(db: Session, don_vi_id: int, ma_ct: str, thang: int) -> float | None:
    ket_qua = (
        db.query(GiaTriChiTieu.gia_tri)
        .join(ChiTieu, ChiTieu.id == GiaTriChiTieu.chi_tieu_id)
        .filter(
            ChiTieu.ma == ma_ct,
            GiaTriChiTieu.don_vi_id == don_vi_id,
            GiaTriChiTieu.nam == NAM_DEMO,
            GiaTriChiTieu.thang == thang,
        )
        .scalar()
    )
    return float(ket_qua) if ket_qua is not None else None


def _xep_hang(db: Session, don_vi_id: int, ma_ct: str, thang: int) -> tuple[int, int]:
    """(thứ hạng của đơn vị, tổng số xã có số liệu) theo giá trị giảm dần."""
    dong = (
        db.query(GiaTriChiTieu.don_vi_id, GiaTriChiTieu.gia_tri)
        .join(ChiTieu, ChiTieu.id == GiaTriChiTieu.chi_tieu_id)
        .join(DonVi, DonVi.id == GiaTriChiTieu.don_vi_id)
        .filter(
            ChiTieu.ma == ma_ct,
            GiaTriChiTieu.nam == NAM_DEMO,
            GiaTriChiTieu.thang == thang,
            DonVi.loai.in_(["xa", "phuong"]),
        )
        .all()
    )
    sap_xep = sorted(dong, key=lambda d: d.gia_tri, reverse=True)
    for i, d in enumerate(sap_xep, start=1):
        if d.don_vi_id == don_vi_id:
            return i, len(sap_xep)
    return len(sap_xep), len(sap_xep)


def _so_sanh(hien_tai: float | None, truoc: float | None, don_vi: str) -> str:
    """Câu so sánh kỳ trước theo khuôn mẫu."""
    if hien_tai is None or truoc is None:
        return "chưa đủ dữ liệu để so sánh với kỳ trước"
    chenh = round(hien_tai - truoc, 1)
    if chenh > 0:
        return f"tăng {chenh:g} {don_vi} so với kỳ trước"
    if chenh < 0:
        return f"giảm {abs(chenh):g} {don_vi} so với kỳ trước"
    return "giữ nguyên so với kỳ trước"


def _ten_file_an_toan(ten: str) -> str:
    return ten.replace(" ", "-").replace("/", "-").lower()


def _mo_dau_chung(doc, don_vi: DonVi, trich_yeu: str, thang: int) -> None:
    nd30.them_phan_dau(
        doc,
        co_quan_chu_quan="UBND tỉnh Thanh Hóa",
        co_quan_ban_hanh=f"UBND {don_vi.ten}",
        so_ky_hieu="Số:        /BC-UBND",
        dia_danh=don_vi.ten.replace("Xã ", "").replace("Phường ", ""),
        ngay=f"ngày      tháng {thang} năm {NAM_DEMO}",
    )
    nd30.them_ten_loai(doc, "BÁO CÁO", trich_yeu)


def _ket_thuc_chung(doc, don_vi: DonVi) -> None:
    nd30.them_ket_thuc(
        doc,
        noi_nhan=["UBND tỉnh (để báo cáo)", "Sở, ngành liên quan", "Lãnh đạo UBND xã"],
        chuc_vu_dong_1="TM. Ủy ban nhân dân",
        chuc_vu_dong_2="Chủ tịch",
        ho_ten=NGUOI_KY_DEMO,
    )
    doc.add_paragraph()
    nd30.them_dong_mo_phong(doc)


def tao_bao_cao_giai_ngan(db: Session, don_vi: DonVi, thang: int) -> Path:
    """Mẫu 1: Báo cáo tình hình giải ngân vốn đầu tư công tháng M/2026."""
    ke_hoach = _gia_tri(db, don_vi.id, "DTC01", thang)
    giai_ngan = _gia_tri(db, don_vi.id, "DTC02", thang)
    ty_le = _gia_tri(db, don_vi.id, "DTC03", thang)
    ty_le_truoc = _gia_tri(db, don_vi.id, "DTC03", thang - 1) if thang > 1 else None
    du_an = _gia_tri(db, don_vi.id, "DTC04", thang)
    du_an_cham = _gia_tri(db, don_vi.id, "DTC05", thang)
    hang, tong_xa = _xep_hang(db, don_vi.id, "DTC03", thang)

    doc = nd30.tao_van_ban()
    _mo_dau_chung(
        doc,
        don_vi,
        f"Tình hình giải ngân vốn đầu tư công tháng {thang}/{NAM_DEMO}",
        thang,
    )

    nd30.them_muc(doc, "1.", "Kết quả giải ngân")
    nd30.them_doan(
        doc,
        (
            f"Kế hoạch vốn đầu tư công năm {NAM_DEMO} giao cho đơn vị là "
            f"{ke_hoach:,.0f} triệu đồng. Lũy kế giải ngân đến hết tháng "
            f"{thang}/{NAM_DEMO} đạt {giai_ngan:,.0f} triệu đồng, bằng "
            f"{ty_le:g}% kế hoạch, {_so_sanh(ty_le, ty_le_truoc, 'điểm %')}."
            if ke_hoach and giai_ngan is not None and ty_le is not None
            else "Đơn vị chưa cập nhật đủ số liệu giải ngân của kỳ báo cáo trên "
            "Kho dữ liệu dùng chung."
        ),
    )
    if ty_le is not None:
        nd30.them_doan(
            doc,
            f"So với {tong_xa} xã, phường có số liệu trong toàn tỉnh, đơn vị "
            f"xếp thứ {hang} về tỷ lệ giải ngân.",
        )
    if du_an is not None:
        nd30.them_doan(
            doc,
            f"Toàn xã đang triển khai {du_an:g} dự án, trong đó "
            f"{du_an_cham:g} dự án chậm tiến độ.",
        )

    nd30.them_muc(doc, "2.", "Nhận định và kiến nghị")
    if ty_le is not None and ty_le < 30:
        nd30.them_doan(
            doc,
            "Tỷ lệ giải ngân của đơn vị đang ở mức THẤP so với mặt bằng chung "
            "của tỉnh (dưới 30%). UBND xã kiến nghị các chủ đầu tư đẩy nhanh "
            "hoàn thiện hồ sơ, nghiệm thu khối lượng; cam kết giải ngân đạt "
            "kế hoạch được giao trong các tháng còn lại của năm.",
        )
    else:
        nd30.them_doan(
            doc,
            "Đơn vị tiếp tục đôn đốc các chủ đầu tư đẩy nhanh tiến độ thi công, "
            "nghiệm thu và giải ngân; phấn đấu hoàn thành kế hoạch vốn được "
            "giao trong năm.",
        )
    nd30.them_doan(
        doc,
        "Số liệu tại báo cáo này được tổng hợp tự động từ Kho dữ liệu dùng "
        "chung của tỉnh — đơn vị không phải lập biểu, nhập lại số liệu./.",
    )

    _ket_thuc_chung(doc, don_vi)

    THU_MUC_XUAT.mkdir(exist_ok=True)
    duong_dan = THU_MUC_XUAT / (
        f"bao-cao-giai-ngan-{_ten_file_an_toan(don_vi.ma)}-{NAM_DEMO}{thang:02d}.docx"
    )
    doc.save(duong_dan)
    return duong_dan


def tao_bao_cao_tthc(db: Session, don_vi: DonVi, thang: int) -> Path:
    """Mẫu 2: Báo cáo kết quả giải quyết TTHC tháng M/2026."""
    tiep_nhan = _gia_tri(db, don_vi.id, "TTHC01", thang)
    dung_han = _gia_tri(db, don_vi.id, "TTHC02", thang)
    qua_han = _gia_tri(db, don_vi.id, "TTHC03", thang)
    ty_le = _gia_tri(db, don_vi.id, "TTHC04", thang)
    ty_le_truoc = _gia_tri(db, don_vi.id, "TTHC04", thang - 1) if thang > 1 else None
    truc_tuyen = _gia_tri(db, don_vi.id, "TTHC05", thang)
    ty_le_tt = _gia_tri(db, don_vi.id, "TTHC06", thang)
    hang, tong_xa = _xep_hang(db, don_vi.id, "TTHC04", thang)

    doc = nd30.tao_van_ban()
    _mo_dau_chung(
        doc,
        don_vi,
        f"Kết quả giải quyết thủ tục hành chính tháng {thang}/{NAM_DEMO}",
        thang,
    )

    nd30.them_muc(doc, "1.", "Kết quả tiếp nhận, giải quyết hồ sơ")
    if tiep_nhan is not None and ty_le is not None:
        nd30.them_doan(
            doc,
            f"Trong tháng {thang}/{NAM_DEMO}, đơn vị tiếp nhận {tiep_nhan:,.0f} "
            f"hồ sơ thủ tục hành chính; giải quyết đúng hạn {dung_han:,.0f} hồ sơ "
            f"(đạt {ty_le:g}%, {_so_sanh(ty_le, ty_le_truoc, 'điểm %')}); "
            f"quá hạn {qua_han:,.0f} hồ sơ.",
        )
        nd30.them_doan(
            doc,
            f"Hồ sơ nộp trực tuyến đạt {truc_tuyen:,.0f} hồ sơ, chiếm "
            f"{ty_le_tt:g}% tổng số tiếp nhận. So với {tong_xa} xã, phường có "
            f"số liệu, đơn vị xếp thứ {hang} về tỷ lệ giải quyết đúng hạn.",
        )
    else:
        nd30.them_doan(
            doc,
            "Đơn vị chưa cập nhật đủ số liệu TTHC của kỳ báo cáo trên Kho dữ "
            "liệu dùng chung.",
        )

    nd30.them_muc(doc, "2.", "Nhận định và kiến nghị")
    if ty_le is not None and ty_le < 90:
        nd30.them_doan(
            doc,
            "Tỷ lệ giải quyết đúng hạn dưới 90%, chưa đạt yêu cầu của tỉnh. "
            "UBND xã chỉ đạo bộ phận một cửa rà soát các hồ sơ quá hạn, làm rõ "
            "nguyên nhân, tổ chức xin lỗi tổ chức, công dân theo quy định và "
            "chấn chỉnh kỷ luật, kỷ cương hành chính.",
        )
    else:
        nd30.them_doan(
            doc,
            "Đơn vị duy trì tỷ lệ giải quyết đúng hạn ở mức cao; tiếp tục đẩy "
            "mạnh tiếp nhận hồ sơ trực tuyến, số hóa kết quả giải quyết theo "
            "chỉ đạo của tỉnh.",
        )
    nd30.them_doan(
        doc,
        "Số liệu tại báo cáo này được tổng hợp tự động từ Kho dữ liệu dùng "
        "chung của tỉnh — đơn vị không phải lập biểu, nhập lại số liệu./.",
    )

    _ket_thuc_chung(doc, don_vi)

    THU_MUC_XUAT.mkdir(exist_ok=True)
    duong_dan = THU_MUC_XUAT / (
        f"bao-cao-tthc-{_ten_file_an_toan(don_vi.ma)}-{NAM_DEMO}{thang:02d}.docx"
    )
    doc.save(duong_dan)
    return duong_dan


MAU_BAO_CAO = {
    "BC-DTC": tao_bao_cao_giai_ngan,
    "BC-TTHC": tao_bao_cao_tthc,
}


def tao_bao_cao(db: Session, don_vi: DonVi, ma_mau: str, thang: int) -> Path:
    """Tạo một báo cáo theo mã mẫu."""
    ham = MAU_BAO_CAO.get(ma_mau)
    if ham is None:
        raise ValueError(f"Không có mẫu báo cáo {ma_mau}")
    return ham(db, don_vi, thang)


def tao_bao_cao_hang_loat(
    db: Session, ma_mau: str, thang: int
) -> tuple[list[Path], float]:
    """Sinh báo cáo cho TẤT CẢ 15 xã; trả về (danh sách file, số giây chạy)."""
    ds_xa = (
        db.query(DonVi)
        .filter(DonVi.loai.in_(["xa", "phuong"]))
        .order_by(DonVi.ten)
        .all()
    )
    bat_dau = time.perf_counter()
    ds_file = [tao_bao_cao(db, dv, ma_mau, thang) for dv in ds_xa]
    thoi_gian = time.perf_counter() - bat_dau
    return ds_file, round(thoi_gian, 2)
