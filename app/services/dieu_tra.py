"""AI điều tra nguyên nhân — bấm "Vì sao?" ở điểm nóng, hệ thống tự truy vấn
nhiều bước như một chuyên viên phân tích rồi viết chuỗi lập luận + kết luận.

Cơ chế: từng "bước điều tra" là một giả thuyết → truy vấn Kho dữ liệu →
phát hiện (có/không). Kết luận xếp hạng theo bằng chứng thu được — hoàn
toàn dựa trên số liệu, minh bạch từng bước, không hộp đen.
"""

from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.models import ChiTieu, DonVi, GiaTriChiTieu
from app.services import ban_tin, tong_hop

NAM_DEMO = 2026
THANG = 7


@dataclass
class BuocDieuTra:
    """Một bước trong chuỗi điều tra."""

    gia_thuyet: str
    truy_van: str  # mô tả dữ liệu đã đối chiếu
    phat_hien: str
    la_nguyen_nhan: bool


@dataclass
class KetQuaDieuTra:
    don_vi: DonVi
    van_de: str
    tieu_de: str
    cac_buoc: list[BuocDieuTra] = field(default_factory=list)
    ket_luan: str = ""
    khuyen_nghi: str = ""


def _gia_tri(db: Session, don_vi_id: int, ma_ct: str, thang: int) -> float | None:
    ct = db.query(ChiTieu).filter_by(ma=ma_ct).one()
    kq = (
        db.query(GiaTriChiTieu.gia_tri)
        .filter_by(chi_tieu_id=ct.id, don_vi_id=don_vi_id, nam=NAM_DEMO, thang=thang)
        .scalar()
    )
    return float(kq) if kq is not None else None


def _trung_binh_tinh(db: Session, ma_ct: str, thang: int) -> float | None:
    ds = tong_hop.gia_tri_theo_xa(db, ma_ct, thang)
    if not ds:
        return None
    return sum(d["gia_tri"] for d in ds) / len(ds)


def dieu_tra_giai_ngan(db: Session, don_vi: DonVi) -> KetQuaDieuTra:
    """Điều tra: vì sao xã này giải ngân thấp?"""
    kq = KetQuaDieuTra(
        don_vi=don_vi,
        van_de="giai_ngan",
        tieu_de=f"Vì sao {don_vi.ten} giải ngân thấp?",
    )
    ty_le = _gia_tri(db, don_vi.id, "DTC03", THANG)
    tb_tinh = _trung_binh_tinh(db, "DTC03", THANG)
    nguyen_nhan: list[str] = []

    # Bước 1: xác nhận hiện trạng so mặt bằng tỉnh
    kq.cac_buoc.append(
        BuocDieuTra(
            gia_thuyet="Hiện trạng có thật sự thấp so mặt bằng tỉnh?",
            truy_van=f"DTC03 kỳ {NAM_DEMO}{THANG:02d} của xã so trung bình 15 xã",
            phat_hien=(
                f"Tỷ lệ giải ngân {ty_le:g}% so trung bình tỉnh {tb_tinh:.1f}% — "
                f"thấp hơn {tb_tinh - ty_le:.1f} điểm %."
                if ty_le is not None and tb_tinh is not None
                else "Xã chưa có số liệu tỷ lệ giải ngân kỳ này."
            ),
            la_nguyen_nhan=False,
        )
    )

    # Bước 2: giả thuyết dự án chậm tiến độ
    du_an = _gia_tri(db, don_vi.id, "DTC04", THANG) or 0
    du_an_cham = _gia_tri(db, don_vi.id, "DTC05", THANG) or 0
    ty_le_cham = du_an_cham / du_an * 100 if du_an else 0
    tb_cham = _trung_binh_tinh(db, "DTC05", THANG) or 0
    la_nn_cham = du_an_cham >= 2 and du_an_cham > tb_cham
    if la_nn_cham:
        nguyen_nhan.append(
            f"{du_an_cham:g}/{du_an:g} dự án chậm tiến độ "
            f"({ty_le_cham:.0f}% số dự án, cao hơn mức chung toàn tỉnh)"
        )
    kq.cac_buoc.append(
        BuocDieuTra(
            gia_thuyet="Do nhiều dự án chậm tiến độ?",
            truy_van="DTC05 (dự án chậm) và DTC04 (đang triển khai) của xã, "
            "đối chiếu trung bình tỉnh",
            phat_hien=f"{du_an_cham:g}/{du_an:g} dự án chậm tiến độ "
            f"(trung bình tỉnh: {tb_cham:.1f} dự án chậm/xã).",
            la_nguyen_nhan=la_nn_cham,
        )
    )

    # Bước 3: giả thuyết vốn giao lớn (mẫu số lớn)
    ke_hoach = _gia_tri(db, don_vi.id, "DTC01", THANG)
    tb_von = _trung_binh_tinh(db, "DTC01", THANG)
    la_nn_von = ke_hoach is not None and tb_von is not None and ke_hoach > tb_von * 1.3
    if la_nn_von:
        nguyen_nhan.append(
            f"kế hoạch vốn được giao lớn ({ke_hoach:,.0f} tr.đ, gấp "
            f"{ke_hoach / tb_von:.1f} lần trung bình tỉnh) nên tỷ lệ phần trăm "
            "tăng chậm dù giá trị tuyệt đối không nhỏ"
        )
    kq.cac_buoc.append(
        BuocDieuTra(
            gia_thuyet="Do được giao vốn quá lớn (mẫu số lớn)?",
            truy_van="DTC01 (kế hoạch vốn) của xã so trung bình tỉnh",
            phat_hien=(
                f"Kế hoạch vốn {ke_hoach:,.0f} tr.đ so trung bình tỉnh "
                f"{tb_von:,.0f} tr.đ."
                if ke_hoach is not None and tb_von is not None
                else "Thiếu số liệu kế hoạch vốn."
            ),
            la_nguyen_nhan=bool(la_nn_von),
        )
    )

    # Bước 4: nhịp giải ngân — tháng nào chững lại?
    ct_dtc02 = db.query(ChiTieu).filter_by(ma="DTC02").one()
    chuoi = dict(
        db.query(GiaTriChiTieu.thang, GiaTriChiTieu.gia_tri)
        .filter_by(chi_tieu_id=ct_dtc02.id, don_vi_id=don_vi.id, nam=NAM_DEMO)
        .all()
    )
    thang_chung: list[str] = []
    for t in range(2, THANG + 1):
        truoc, sau = chuoi.get(t - 1), chuoi.get(t)
        if truoc is not None and sau is not None and ke_hoach:
            tang = (sau - truoc) / ke_hoach * 100
            if tang < 2:  # tăng dưới 2 điểm %/tháng coi là chững
                thang_chung.append(f"T{t} (+{tang:.1f}đ%)")
    la_nn_chung = len(thang_chung) >= 2
    if la_nn_chung:
        nguyen_nhan.append(
            f"nhịp giải ngân chững lại kéo dài ({', '.join(thang_chung)})"
        )
    kq.cac_buoc.append(
        BuocDieuTra(
            gia_thuyet="Nhịp giải ngân có bị chững lại kéo dài?",
            truy_van="Mức tăng lũy kế DTC02 từng tháng (điểm % kế hoạch/tháng)",
            phat_hien=(
                f"Các tháng tăng dưới 2 điểm %: {', '.join(thang_chung)}."
                if thang_chung
                else "Nhịp giải ngân đều, không có tháng nào chững bất thường."
            ),
            la_nguyen_nhan=la_nn_chung,
        )
    )

    # Bước 5: chất lượng dữ liệu
    so_da_nhap = (
        db.query(GiaTriChiTieu)
        .filter_by(don_vi_id=don_vi.id, nam=NAM_DEMO, thang=THANG)
        .count()
    )
    tong_ct = db.query(ChiTieu).count()
    thieu = so_da_nhap < tong_ct
    kq.cac_buoc.append(
        BuocDieuTra(
            gia_thuyet="Hay chỉ là do thiếu/sai số liệu?",
            truy_van=f"Đếm số chỉ tiêu đã nhập kỳ {NAM_DEMO}{THANG:02d}",
            phat_hien=f"Đã nhập {so_da_nhap}/{tong_ct} chỉ tiêu kỳ này"
            + (" — CHƯA đủ, kết luận cần thận trọng." if thieu else " — đủ."),
            la_nguyen_nhan=thieu,
        )
    )
    if thieu:
        nguyen_nhan.append("số liệu kỳ này chưa nhập đủ (kết luận cần thận trọng)")

    # Dự báo để định lượng hệ quả
    du_bao = {d.ma: d for d in ban_tin.du_bao_giai_ngan(db)}.get(don_vi.ma)

    if nguyen_nhan:
        kq.ket_luan = (
            f"Nguyên nhân chính (theo bằng chứng số liệu): {'; '.join(nguyen_nhan)}."
        )
    else:
        kq.ket_luan = (
            "Không tìm thấy nguyên nhân nổi bật trong dữ liệu hiện có — "
            "cần làm việc trực tiếp với đơn vị."
        )
    if du_bao is not None:
        kq.ket_luan += (
            f" Nếu giữ nhịp hiện tại, dự báo cả năm chỉ đạt {du_bao.ty_le_du_bao:g}%."
        )
    kq.khuyen_nghi = (
        "Khuyến nghị: yêu cầu xã cam kết mốc giải ngân từng tháng còn lại"
        + (
            f" (cần bình quân {du_bao.can_tang_toc_thang:,.0f} tr.đ/tháng để đạt 95%)"
            if du_bao is not None and not du_bao.dat_muc_tieu
            else ""
        )
        + "; giao Sở Tài chính theo dõi trên Kho dữ liệu, họp kiểm điểm nếu "
        "2 tháng liên tiếp không đạt mốc."
    )
    return kq


def dieu_tra_tthc(db: Session, don_vi: DonVi) -> KetQuaDieuTra:
    """Điều tra: vì sao tỷ lệ giải quyết TTHC đúng hạn thấp?"""
    kq = KetQuaDieuTra(
        don_vi=don_vi,
        van_de="tthc",
        tieu_de=f"Vì sao {don_vi.ten} giải quyết TTHC đúng hạn thấp?",
    )
    ty_le = _gia_tri(db, don_vi.id, "TTHC04", THANG)
    tb_tinh = _trung_binh_tinh(db, "TTHC04", THANG)
    nguyen_nhan: list[str] = []

    kq.cac_buoc.append(
        BuocDieuTra(
            gia_thuyet="Hiện trạng so mặt bằng tỉnh?",
            truy_van=f"TTHC04 kỳ {NAM_DEMO}{THANG:02d} so trung bình 15 xã",
            phat_hien=(
                f"Đúng hạn {ty_le:g}% so trung bình tỉnh {tb_tinh:.1f}%."
                if ty_le is not None and tb_tinh is not None
                else "Thiếu số liệu."
            ),
            la_nguyen_nhan=False,
        )
    )

    # Khối lượng hồ sơ tăng đột biến?
    ct = db.query(ChiTieu).filter_by(ma="TTHC01").one()
    chuoi = dict(
        db.query(GiaTriChiTieu.thang, GiaTriChiTieu.gia_tri)
        .filter_by(chi_tieu_id=ct.id, don_vi_id=don_vi.id, nam=NAM_DEMO)
        .all()
    )
    lich_su = [v for t, v in chuoi.items() if t < THANG]
    ky_nay = chuoi.get(THANG)
    tang_vot = False
    if lich_su and ky_nay:
        tb = sum(lich_su) / len(lich_su)
        tang_vot = ky_nay > tb * 1.3
        if tang_vot:
            nguyen_nhan.append(
                f"khối lượng hồ sơ tăng vọt ({ky_nay:g} so trung bình {tb:.0f}/tháng "
                "— quá tải bộ phận một cửa)"
            )
        kq.cac_buoc.append(
            BuocDieuTra(
                gia_thuyet="Do khối lượng hồ sơ tăng đột biến?",
                truy_van="TTHC01 kỳ này so trung bình 6 tháng trước",
                phat_hien=f"Tiếp nhận {ky_nay:g} hồ sơ, trung bình trước đó "
                f"{tb:.0f}/tháng ({(ky_nay - tb) / tb * 100:+.0f}%).",
                la_nguyen_nhan=tang_vot,
            )
        )

    # Tỷ lệ trực tuyến thấp?
    ty_le_tt = _gia_tri(db, don_vi.id, "TTHC06", THANG)
    tb_tt = _trung_binh_tinh(db, "TTHC06", THANG)
    tt_thap = ty_le_tt is not None and tb_tt is not None and ty_le_tt < tb_tt - 10
    if tt_thap:
        nguyen_nhan.append(
            f"tỷ lệ hồ sơ trực tuyến thấp ({ty_le_tt:g}% so trung bình "
            f"{tb_tt:.1f}%) — xử lý giấy tốn thời gian hơn"
        )
    kq.cac_buoc.append(
        BuocDieuTra(
            gia_thuyet="Do ít dùng dịch vụ công trực tuyến?",
            truy_van="TTHC06 của xã so trung bình tỉnh",
            phat_hien=(
                f"Trực tuyến {ty_le_tt:g}% so trung bình tỉnh {tb_tt:.1f}%."
                if ty_le_tt is not None and tb_tt is not None
                else "Thiếu số liệu hồ sơ trực tuyến."
            ),
            la_nguyen_nhan=bool(tt_thap),
        )
    )

    qua_han = _gia_tri(db, don_vi.id, "TTHC03", THANG) or 0
    kq.ket_luan = f"Kỳ này còn {qua_han:g} hồ sơ quá hạn. " + (
        f"Nguyên nhân chính: {'; '.join(nguyen_nhan)}."
        if nguyen_nhan
        else "Chưa thấy nguyên nhân nổi bật trong dữ liệu — có thể do "
        "tổ chức nhân lực tại bộ phận một cửa."
    )
    kq.khuyen_nghi = (
        "Khuyến nghị: rà soát từng hồ sơ quá hạn và tổ chức xin lỗi công dân "
        "theo quy định; đẩy mạnh tiếp nhận trực tuyến qua điểm hỗ trợ dịch vụ "
        "công tại thôn/tổ dân phố; theo dõi tỷ lệ đúng hạn hằng tuần trên Kho."
    )
    return kq


def dieu_tra(db: Session, don_vi: DonVi, van_de: str) -> KetQuaDieuTra:
    if van_de == "tthc":
        return dieu_tra_tthc(db, don_vi)
    return dieu_tra_giai_ngan(db, don_vi)
