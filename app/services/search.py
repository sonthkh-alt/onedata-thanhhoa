"""Tìm kiếm Lớp 1: FTS5 (offline, mặc định) + tùy chọn ngữ nghĩa.

- Luôn LOẠI văn bản mật (không nằm trong chỉ mục, và lọc lại lần nữa khi join).
- LỌC THEO QUYỀN trước khi trả kết quả (kể cả cho tầng AI): chuyên viên xã
  chỉ thấy văn bản của đơn vị mình + văn bản cấp sở/tỉnh; các vai trò khác
  thấy toàn bộ văn bản không mật.
- Nếu có mô hình embedding trong `models/` thì có thể bổ sung xếp hạng ngữ
  nghĩa; tải thất bại → tự lùi về FTS5, KHÔNG làm sập ứng dụng.
"""

import re

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models import DonVi, NguoiDung, VanBan

SO_DOAN_TOI_DA = 8


def _dieu_kien_quyen(nguoi_dung: NguoiDung | None, db: Session) -> list[int] | None:
    """Trả về danh sách co_quan_id được phép xem, hoặc None = không giới hạn."""
    if nguoi_dung is None or nguoi_dung.vai_tro != "chuyen_vien_xa":
        return None
    ds_so_nganh = [
        dv.id
        for dv in db.query(DonVi).filter(DonVi.loai.in_(["so_nganh", "tinh"])).all()
    ]
    return [nguoi_dung.don_vi_id, *ds_so_nganh]


def _chuoi_fts(tu_khoa: str) -> str:
    """Chuyển câu người dùng gõ thành truy vấn FTS5 an toàn (OR các từ)."""
    cac_tu = [t for t in re.findall(r"\w+", tu_khoa, flags=re.UNICODE) if len(t) > 1]
    if not cac_tu:
        return '""'
    return " OR ".join(f'"{t}"' for t in cac_tu[:12])


def tim_kiem(
    db: Session,
    tu_khoa: str,
    nguoi_dung: NguoiDung | None = None,
    gioi_han: int = SO_DOAN_TOI_DA,
) -> list[dict]:
    """Tìm đoạn văn bản khớp từ khóa; trả về đoạn + siêu dữ liệu văn bản.

    Kết quả đã lọc mật + lọc quyền — dùng chung cho ô tìm kiếm và tầng AI.
    """
    truy_van = _chuoi_fts(tu_khoa)
    dong = db.execute(
        text(
            "SELECT f.noi_dung, f.van_ban_id, f.doan_id, bm25(van_ban_fts) AS diem "
            "FROM van_ban_fts f WHERE van_ban_fts MATCH :q "
            "ORDER BY diem LIMIT :lim"
        ),
        {"q": truy_van, "lim": gioi_han * 3},
    ).fetchall()

    duoc_phep = _dieu_kien_quyen(nguoi_dung, db)
    ket_qua: list[dict] = []
    for noi_dung, van_ban_id, doan_id, _diem in dong:
        vb = db.get(VanBan, van_ban_id)
        if vb is None or vb.mat:
            continue  # phòng thủ 2 lớp: văn bản mật không bao giờ lọt ra
        if duoc_phep is not None and vb.co_quan_id not in duoc_phep:
            continue
        ket_qua.append(
            {
                "doan": noi_dung,
                "van_ban_id": vb.id,
                "so_ky_hieu": f"{vb.so}/{vb.ky_hieu}" if vb.so else vb.ky_hieu,
                "trich_yeu": vb.trich_yeu,
                "ten_co_quan": vb.co_quan.ten if vb.co_quan else "",
                "ngay_ban_hanh": (
                    vb.ngay_ban_hanh.strftime("%Y-%m-%d") if vb.ngay_ban_hanh else ""
                ),
            }
        )
        if len(ket_qua) >= gioi_han:
            break
    return ket_qua
