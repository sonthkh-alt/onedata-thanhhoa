"""Nhật ký chống sửa lén — chuỗi hash kiểu sổ cái (tamper-evident ledger).

Mỗi bản ghi nhật ký mang SHA-256 của (hash bản ghi trước + nội dung chính
mình). Ai sửa/xóa lén một dòng — kể cả sửa thẳng trong file SQLite — thì
toàn bộ chuỗi phía sau không khớp và bị phát hiện khi kiểm chứng.
Đạt tính "không thể chối bỏ" của blockchain mà không cần blockchain.
"""

import hashlib
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from app.models import NhatKy

HASH_GOC = "0" * 64  # mỏ neo của chuỗi (bản ghi đầu tiên)


def _tinh_hash(
    hash_truoc: str,
    nguoi_dung_id: int | None,
    hanh_dong: str,
    chi_tiet: str,
    thoi_diem: datetime,
) -> str:
    noi_dung = (
        f"{hash_truoc}|{nguoi_dung_id}|{hanh_dong}|{chi_tiet}|"
        f"{thoi_diem.isoformat()}"
    )
    return hashlib.sha256(noi_dung.encode("utf-8")).hexdigest()


def ghi_nhat_ky(
    db: Session, nguoi_dung_id: int | None, hanh_dong: str, chi_tiet: str = ""
) -> NhatKy:
    """Ghi một dòng nhật ký, khóa hash với dòng liền trước, rồi commit."""
    truoc = db.query(NhatKy).order_by(NhatKy.id.desc()).first()
    hash_truoc = truoc.hash_ban_ghi if truoc and truoc.hash_ban_ghi else HASH_GOC
    thoi_diem = datetime.now()
    ban_ghi = NhatKy(
        nguoi_dung_id=nguoi_dung_id,
        hanh_dong=hanh_dong,
        chi_tiet=chi_tiet,
        thoi_diem=thoi_diem,
        hash_truoc=hash_truoc,
        hash_ban_ghi=_tinh_hash(
            hash_truoc, nguoi_dung_id, hanh_dong, chi_tiet, thoi_diem
        ),
    )
    db.add(ban_ghi)
    db.commit()
    return ban_ghi


@dataclass
class KetQuaKiemChung:
    """Kết quả kiểm chứng toàn vẹn chuỗi nhật ký."""

    toan_ven: bool
    so_ban_ghi: int
    vi_tri_loi: int | None = None  # id bản ghi đầu tiên bị phá vỡ chuỗi
    mo_ta_loi: str | None = None


def kiem_chung_chuoi(db: Session) -> KetQuaKiemChung:
    """Duyệt toàn bộ nhật ký, tính lại từng hash và đối chiếu chuỗi."""
    ds = db.query(NhatKy).order_by(NhatKy.id).all()
    hash_truoc = HASH_GOC
    for ban_ghi in ds:
        if ban_ghi.hash_truoc != hash_truoc:
            return KetQuaKiemChung(
                toan_ven=False,
                so_ban_ghi=len(ds),
                vi_tri_loi=ban_ghi.id,
                mo_ta_loi="Liên kết chuỗi bị đứt — có bản ghi bị xóa hoặc "
                "chèn lén trước vị trí này.",
            )
        hash_tinh_lai = _tinh_hash(
            ban_ghi.hash_truoc,
            ban_ghi.nguoi_dung_id,
            ban_ghi.hanh_dong,
            ban_ghi.chi_tiet,
            ban_ghi.thoi_diem,
        )
        if ban_ghi.hash_ban_ghi != hash_tinh_lai:
            return KetQuaKiemChung(
                toan_ven=False,
                so_ban_ghi=len(ds),
                vi_tri_loi=ban_ghi.id,
                mo_ta_loi="Nội dung bản ghi đã bị SỬA sau khi ghi "
                "(hash tính lại không khớp).",
            )
        hash_truoc = ban_ghi.hash_ban_ghi
    return KetQuaKiemChung(toan_ven=True, so_ban_ghi=len(ds))
