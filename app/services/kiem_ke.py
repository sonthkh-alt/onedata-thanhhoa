"""Kiểm kê chế độ báo cáo — thống kê gánh nặng và tìm báo cáo nghi trùng lặp
(phân hệ tùy chọn 8.8, CLAUDE.md).
"""

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models import KiemKeBaoCao
from app.services.ai_query import chuan_hoa

# Số kỳ phải nộp trong một năm theo tần suất (quy ước demo)
SO_KY_MOT_NAM = {"thang": 12, "quy": 4, "6_thang": 2, "nam": 1, "dot_xuat": 6}
TEN_TAN_SUAT = {
    "thang": "Hằng tháng",
    "quy": "Hằng quý",
    "6_thang": "6 tháng/lần",
    "nam": "Hằng năm",
    "dot_xuat": "Đột xuất (ước tính 6 lần/năm)",
}
SO_XA_TOAN_TINH = 166
NGUONG_TRUNG_LAP = 0.6

# Từ chung chung trong tên báo cáo — loại ra trước khi so khớp để tên
# "tình hình..." và "kết quả..." của cùng một nội dung vẫn bắt được nhau
TU_BO_QUA = {
    "bao",
    "cao",
    "tinh",
    "hinh",
    "ket",
    "qua",
    "cong",
    "tac",
    "ve",
    "viec",
    "thuc",
    "hien",
    "trien",
    "khai",
}


@dataclass
class CapTrungLap:
    """Một cặp báo cáo nghi trùng lặp nội dung."""

    bao_cao_1: KiemKeBaoCao
    bao_cao_2: KiemKeBaoCao
    do_giong: float  # 0..1


def _bo_tu(ten: str) -> set[str]:
    """Tập từ khóa đặc trưng của tên báo cáo (bỏ dấu, bỏ từ chung chung)."""
    return {t for t in chuan_hoa(ten).split() if t not in TU_BO_QUA}


def do_giong_nhau(ten_1: str, ten_2: str) -> float:
    """Độ giống Jaccard giữa hai tên báo cáo trên tập từ khóa đặc trưng."""
    tap_1, tap_2 = _bo_tu(ten_1), _bo_tu(ten_2)
    if not tap_1 or not tap_2:
        return 0.0
    giao = len(tap_1 & tap_2)
    hop = len(tap_1 | tap_2)
    return round(giao / hop, 2)


def tim_nghi_trung_lap(ds_bao_cao: list[KiemKeBaoCao]) -> list[CapTrungLap]:
    """So khớp gần đúng từng cặp tên; trả về các cặp vượt ngưỡng, giống nhất
    xếp trước."""
    ket_qua: list[CapTrungLap] = []
    for i, bc1 in enumerate(ds_bao_cao):
        for bc2 in ds_bao_cao[i + 1 :]:
            giong = do_giong_nhau(bc1.ten_bao_cao, bc2.ten_bao_cao)
            if giong >= NGUONG_TRUNG_LAP:
                ket_qua.append(CapTrungLap(bc1, bc2, giong))
    ket_qua.sort(key=lambda c: c.do_giong, reverse=True)
    return ket_qua


def thong_ke_ganh_nang(db: Session) -> dict:
    """Thống kê gánh nặng báo cáo của MỘT xã và quy đổi toàn tỉnh 166 xã."""
    ds = db.query(KiemKeBaoCao).order_by(KiemKeBaoCao.ten_bao_cao).all()
    luot_mot_xa_nam = sum(SO_KY_MOT_NAM.get(bc.tan_suat, 12) for bc in ds)
    cap_trung = tim_nghi_trung_lap(ds)
    # Ước tính số lượt cắt được nếu gộp mỗi cặp trùng về một báo cáo
    luot_cat_duoc = sum(
        min(
            SO_KY_MOT_NAM.get(c.bao_cao_1.tan_suat, 12),
            SO_KY_MOT_NAM.get(c.bao_cao_2.tan_suat, 12),
        )
        for c in cap_trung
    )
    return {
        "ds_bao_cao": ds,
        "so_loai": len(ds),
        "luot_mot_xa_nam": luot_mot_xa_nam,
        "luot_mot_xa_thang": round(luot_mot_xa_nam / 12, 1),
        "luot_toan_tinh_nam": luot_mot_xa_nam * SO_XA_TOAN_TINH,
        "cap_trung": cap_trung,
        "luot_cat_duoc_toan_tinh": luot_cat_duoc * SO_XA_TOAN_TINH,
    }
