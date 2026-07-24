"""Máy tham mưu — Bản tin điều hành chủ động (tính năng vượt IOC).

IOC hiển thị "chuyện gì đã xảy ra". Bản tin này trả lời:
1. Sắp xảy ra chuyện gì — DỰ BÁO tỷ lệ giải ngân đến 31/12 theo nhịp hiện
   tại của từng xã (hồi quy tuyến tính trên chuỗi lũy kế), đối chiếu mục
   tiêu 95% của Nghị quyết HĐND.
2. Có gì bất thường — số liệu kỳ mới lệch mạnh so với trung bình 6 tháng.
3. Hôm nay cần chỉ đạo gì — 3 việc xếp theo mức độ, kèm DỰ THẢO CÔNG VĂN
   chỉ đạo đúng thể thức NĐ 30/2020/NĐ-CP sẵn để ký.
"""

from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.orm import Session

from app.models import ChiTieu, DonVi, GiaTriChiTieu
from app.services import canh_bao, nd30
from app.services.report_builder import NGUOI_KY_DEMO, THU_MUC_XUAT

NAM_DEMO = 2026
THANG_HIEN_TAI = 7
MUC_TIEU_GIAI_NGAN = 95.0  # % — Nghị quyết 12/NQ-HĐND
NGUONG_BAT_THUONG = 0.4  # lệch >40% so trung bình 6 tháng đầu năm


@dataclass
class DuBaoXa:
    """Dự báo giải ngân cả năm của một xã."""

    ma: str
    ten: str
    ke_hoach: float
    luy_ke_hien_tai: float
    ty_le_hien_tai: float
    ty_le_du_bao: float  # đến 31/12 nếu giữ nhịp hiện tại
    dat_muc_tieu: bool
    can_tang_toc_thang: float  # triệu đồng/tháng cần thêm để đạt 95%


@dataclass
class BatThuong:
    """Một số liệu kỳ mới lệch mạnh so với chính lịch sử của xã."""

    don_vi: str
    ma_don_vi: str
    chi_tieu: str
    gia_tri_ky_nay: float
    trung_binh_6_thang: float
    lech_phan_tram: float  # dương = tăng vọt, âm = giảm sâu


def _hoi_quy_tuyen_tinh(diem: list[tuple[int, float]]) -> tuple[float, float]:
    """Hồi quy tuyến tính nhỏ nhất bình phương: trả về (hệ số góc, chặn)."""
    n = len(diem)
    if n < 2:
        return 0.0, diem[0][1] if diem else 0.0
    tong_x = sum(x for x, _ in diem)
    tong_y = sum(y for _, y in diem)
    tong_xy = sum(x * y for x, y in diem)
    tong_x2 = sum(x * x for x, _ in diem)
    mau = n * tong_x2 - tong_x * tong_x
    if mau == 0:
        return 0.0, tong_y / n
    goc = (n * tong_xy - tong_x * tong_y) / mau
    chan = (tong_y - goc * tong_x) / n
    return goc, chan


def _chuoi_gia_tri(db: Session, don_vi_id: int, ma_ct: str) -> dict[int, float]:
    ct = db.query(ChiTieu).filter_by(ma=ma_ct).one()
    return dict(
        db.query(GiaTriChiTieu.thang, GiaTriChiTieu.gia_tri)
        .filter_by(chi_tieu_id=ct.id, don_vi_id=don_vi_id, nam=NAM_DEMO)
        .all()
    )


def du_bao_giai_ngan(db: Session) -> list[DuBaoXa]:
    """Dự báo tỷ lệ giải ngân 31/12 của từng xã theo nhịp 7 tháng đầu năm."""
    ket_qua: list[DuBaoXa] = []
    ds_xa = (
        db.query(DonVi)
        .filter(DonVi.loai.in_(["xa", "phuong"]))
        .order_by(DonVi.ten)
        .all()
    )
    for xa in ds_xa:
        ke_hoach_chuoi = _chuoi_gia_tri(db, xa.id, "DTC01")
        luy_ke = _chuoi_gia_tri(db, xa.id, "DTC02")
        if not ke_hoach_chuoi or not luy_ke:
            continue
        ke_hoach = next(iter(ke_hoach_chuoi.values()))
        diem = sorted(luy_ke.items())
        goc, chan = _hoi_quy_tuyen_tinh(diem)
        du_bao_12 = min(max(goc * 12 + chan, 0.0), ke_hoach)
        thang_cuoi, gia_tri_cuoi = diem[-1]
        ty_le_hien_tai = round(gia_tri_cuoi / ke_hoach * 100, 1)
        ty_le_du_bao = round(du_bao_12 / ke_hoach * 100, 1)
        dat = ty_le_du_bao >= MUC_TIEU_GIAI_NGAN
        con_lai_thang = max(12 - thang_cuoi, 1)
        can_moi_thang = (ke_hoach * MUC_TIEU_GIAI_NGAN / 100 - gia_tri_cuoi) / (
            con_lai_thang
        )
        ket_qua.append(
            DuBaoXa(
                ma=xa.ma,
                ten=xa.ten,
                ke_hoach=ke_hoach,
                luy_ke_hien_tai=gia_tri_cuoi,
                ty_le_hien_tai=ty_le_hien_tai,
                ty_le_du_bao=ty_le_du_bao,
                dat_muc_tieu=dat,
                can_tang_toc_thang=round(max(can_moi_thang, 0.0), 0),
            )
        )
    ket_qua.sort(key=lambda d: d.ty_le_du_bao)
    return ket_qua


def tim_bat_thuong(db: Session, thang: int = THANG_HIEN_TAI) -> list[BatThuong]:
    """Số liệu kỳ mới lệch >40% so trung bình 6 tháng trước của chính xã đó
    (áp cho các chỉ tiêu biến động: hồ sơ tiếp nhận, đối tượng BTXH, kinh phí)."""
    cac_chi_tieu = ["TTHC01", "AS03", "AS04"]
    ket_qua: list[BatThuong] = []
    ds_xa = db.query(DonVi).filter(DonVi.loai.in_(["xa", "phuong"])).all()
    for xa in ds_xa:
        for ma_ct in cac_chi_tieu:
            chuoi = _chuoi_gia_tri(db, xa.id, ma_ct)
            lich_su = [v for t, v in chuoi.items() if t < thang]
            ky_nay = chuoi.get(thang)
            if ky_nay is None or len(lich_su) < 3:
                continue
            trung_binh = sum(lich_su) / len(lich_su)
            if trung_binh == 0:
                continue
            lech = (ky_nay - trung_binh) / trung_binh
            if abs(lech) > NGUONG_BAT_THUONG:
                ct = db.query(ChiTieu).filter_by(ma=ma_ct).one()
                ket_qua.append(
                    BatThuong(
                        don_vi=xa.ten,
                        ma_don_vi=xa.ma,
                        chi_tieu=f"{ct.ma} — {ct.ten}",
                        gia_tri_ky_nay=ky_nay,
                        trung_binh_6_thang=round(trung_binh, 1),
                        lech_phan_tram=round(lech * 100, 1),
                    )
                )
    ket_qua.sort(key=lambda b: -abs(b.lech_phan_tram))
    return ket_qua


def lap_ban_tin(db: Session, thang: int = THANG_HIEN_TAI) -> dict:
    """Lập bản tin điều hành: dự báo + bất thường + điểm nóng + việc cần
    chỉ đạo hôm nay."""
    du_bao = du_bao_giai_ngan(db)
    xa_hut = [d for d in du_bao if not d.dat_muc_tieu]
    bat_thuong = tim_bat_thuong(db, thang)
    diem_nong = canh_bao.tim_diem_nong(db, thang, NAM_DEMO)

    xa_thieu = sorted({d.don_vi for d in diem_nong if "Chưa nhập đủ" in d.luat})
    xa_tthc = sorted({d.don_vi for d in diem_nong if "đúng hạn TTHC" in d.luat})
    xa_nghi_sai = sorted({d.don_vi for d in diem_nong if "nghi sai số liệu" in d.luat})

    viec_can_chi_dao: list[dict] = []
    if xa_hut:
        ten_3_xa = ", ".join(d.ten for d in xa_hut[:3])
        viec_can_chi_dao.append(
            {
                "tieu_de": f"Đôn đốc giải ngân {len(xa_hut)} xã dự báo hụt "
                f"mục tiêu {MUC_TIEU_GIAI_NGAN:g}%",
                "noi_dung": f"Nếu giữ nhịp hiện tại, {len(xa_hut)} xã sẽ không "
                f"đạt mục tiêu giải ngân cả năm (thấp nhất: {ten_3_xa}). "
                "Yêu cầu chủ tịch các xã cam kết mốc giải ngân từng tháng "
                "còn lại — dự thảo công văn đã soạn sẵn bên dưới.",
                "muc_do": "cao",
            }
        )
    if xa_tthc:
        viec_can_chi_dao.append(
            {
                "tieu_de": f"Chấn chỉnh giải quyết TTHC tại {len(xa_tthc)} xã "
                "dưới ngưỡng 90%",
                "noi_dung": f"{', '.join(xa_tthc)} có tỷ lệ đúng hạn dưới 90% "
                "trong kỳ — yêu cầu rà soát hồ sơ quá hạn và xin lỗi công dân "
                "theo quy định.",
                "muc_do": "cao",
            }
        )
    if xa_thieu or xa_nghi_sai:
        chi_tiet = []
        if xa_thieu:
            chi_tiet.append(f"chưa nhập đủ số liệu kỳ này: {', '.join(xa_thieu)}")
        if xa_nghi_sai:
            chi_tiet.append(f"số liệu nghi sai cần xác minh: {', '.join(xa_nghi_sai)}")
        viec_can_chi_dao.append(
            {
                "tieu_de": "Làm sạch dữ liệu trên Kho dùng chung",
                "noi_dung": "Nhắc các đơn vị " + "; ".join(chi_tiet) + ". "
                "Hệ thống tự nhắc qua bảng điểm nóng — không cần công văn giấy.",
                "muc_do": "trung_binh",
            }
        )

    return {
        "thang": thang,
        "nam": NAM_DEMO,
        "ky": NAM_DEMO * 100 + thang,
        "du_bao": du_bao,
        "xa_hut": xa_hut,
        "bat_thuong": bat_thuong,
        "diem_nong": diem_nong,
        "viec_can_chi_dao": viec_can_chi_dao[:3],
    }


def tao_du_thao_cong_van(db: Session, thang: int = THANG_HIEN_TAI) -> Path:
    """Dự thảo CÔNG VĂN chỉ đạo đôn đốc giải ngân (thể thức NĐ30) từ kết quả
    dự báo — lãnh đạo chỉ việc rà và ký."""
    ban_tin = lap_ban_tin(db, thang)
    xa_hut: list[DuBaoXa] = ban_tin["xa_hut"]

    doc = nd30.tao_van_ban()
    nd30.them_phan_dau(
        doc,
        co_quan_chu_quan="",
        co_quan_ban_hanh="UBND tỉnh Thanh Hóa",
        so_ky_hieu="Số:        /UBND-THKH",
        dia_danh="Thanh Hóa",
        ngay=f"ngày      tháng {thang} năm {NAM_DEMO}",
    )
    nd30.them_trich_yeu_cong_van(
        doc,
        "V/v đôn đốc đẩy nhanh tiến độ giải ngân vốn đầu tư công "
        f"những tháng cuối năm {NAM_DEMO}",
    )
    doc.add_paragraph()
    nd30.them_kinh_gui(doc, "Chủ tịch UBND các xã, phường")

    nd30.them_doan(
        doc,
        "Theo số liệu trên Kho dữ liệu dùng chung của tỉnh (cập nhật đến kỳ "
        f"{NAM_DEMO}{thang:02d}), hệ thống dự báo nếu giữ tốc độ giải ngân "
        f"hiện tại thì {len(xa_hut)} xã, phường sẽ KHÔNG đạt mục tiêu giải "
        f"ngân tối thiểu {MUC_TIEU_GIAI_NGAN:g}% kế hoạch năm theo Nghị quyết "
        "của HĐND tỉnh, cụ thể:",
    )
    for d in xa_hut:
        nd30.them_doan(
            doc,
            f"- {d.ten}: đã giải ngân {d.luy_ke_hien_tai:,.0f}/{d.ke_hoach:,.0f} "
            f"triệu đồng ({d.ty_le_hien_tai:g}%); dự báo cả năm chỉ đạt "
            f"{d.ty_le_du_bao:g}%; cần giải ngân thêm bình quân "
            f"{d.can_tang_toc_thang:,.0f} triệu đồng/tháng để đạt mục tiêu.",
        )
    nd30.them_doan(
        doc,
        "Chủ tịch UBND tỉnh yêu cầu Chủ tịch UBND các xã, phường nêu trên "
        "khẩn trương rà soát từng dự án, cam kết mốc giải ngân từng tháng "
        "còn lại của năm; cập nhật kết quả lên Kho dữ liệu dùng chung để "
        "tỉnh theo dõi trực tiếp, không yêu cầu báo cáo giấy./.",
    )
    nd30.them_ket_thuc(
        doc,
        noi_nhan=["Như trên", "Chủ tịch, các PCT UBND tỉnh", "Sở Tài chính"],
        chuc_vu_dong_1="TM. Ủy ban nhân dân",
        chuc_vu_dong_2="Chủ tịch",
        ho_ten=NGUOI_KY_DEMO,
    )
    doc.add_paragraph()
    nd30.them_dong_mo_phong(doc)

    THU_MUC_XUAT.mkdir(exist_ok=True)
    duong_dan = THU_MUC_XUAT / f"du-thao-cong-van-don-doc-{NAM_DEMO}{thang:02d}.docx"
    doc.save(duong_dan)
    return duong_dan
