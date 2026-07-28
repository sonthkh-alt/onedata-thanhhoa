"""Kênh 2 — MÁY TRÍCH XUẤT: dò số liệu chỉ tiêu trong văn bản (CLAUDE.md 9.3).

Ngay khi một văn bản vào Lớp 1: với mỗi chỉ tiêu, dò `tu_khoa_trich_xuat`
trong từng câu; bắt số kèm đơn vị tính bằng biểu thức chính quy (xử lý được
"45.000 triệu đồng", "27,0%", "1.250 hồ sơ"); suy ra kỳ báo cáo từ trích
yếu/toàn văn; tạo bản ghi hàng chờ `trich_xuat_cho` kèm độ tin cậy và câu
trích dẫn. TUYỆT ĐỐI không ghi thẳng vào Lớp 2 — phải qua người xác nhận.

- Chế độ offline (mặc định): chỉ dùng biểu thức chính quy.
- Chế độ online: gửi văn bản + danh mục chỉ tiêu cho Claude, yêu cầu JSON;
  giá trị KHÔNG xuất hiện nguyên văn trong `doan_trich` thì loại bỏ.
"""

import json
import re
from datetime import datetime

from sqlalchemy.orm import Session

from app.config import settings
from app.models import ChiTieu, TrichXuatCho, VanBan

# Số kiểu Việt Nam: 45.000 | 1.250 | 27,0 | 12
MAU_SO = re.compile(r"(?<![\d.,])(\d{1,3}(?:\.\d{3})+|\d+)(?:,(\d+))?(?![\d.])")

# Đơn vị tính đi kèm số — dùng để chấm độ tin cậy
MAU_DON_VI = {
    "triệu đồng": re.compile(r"^\s*triệu\s+đồng"),
    "%": re.compile(r"^\s*%"),
    "hồ sơ": re.compile(r"^\s*hồ\s+sơ"),
    "dự án": re.compile(r"^\s*dự\s+án"),
    "hộ": re.compile(r"^\s*hộ\b"),
    "người": re.compile(r"^\s*(người|đối\s+tượng)"),
}

BAN_KINH_TIM_SO = 80  # ký tự quanh từ khóa để tìm con số gần nhất


def _doi_so(phan_nguyen: str, phan_le: str | None) -> float:
    """'45.000' + '5' → 45000.5 (bỏ dấu chấm nghìn, phẩy = thập phân)."""
    gia_tri = float(phan_nguyen.replace(".", ""))
    if phan_le:
        gia_tri += float(f"0.{phan_le}")
    return gia_tri


def _khop_don_vi(van_ban_sau_so: str, don_vi_tinh: str) -> bool:
    mau = MAU_DON_VI.get(don_vi_tinh)
    return bool(mau and mau.search(van_ban_sau_so))


def _tach_cau(toan_van: str) -> list[str]:
    """Tách câu thô: theo dấu chấm câu + xuống dòng."""
    tho = re.split(r"(?<=[.;])\s+|\n+", toan_van)
    return [c.strip() for c in tho if len(c.strip()) >= 15]


def suy_ra_ky(van_ban: VanBan) -> tuple[int, int] | None:
    """Suy kỳ (năm, tháng) từ trích yếu; không có thì dò toàn văn."""
    for nguon in (van_ban.trich_yeu or "", van_ban.toan_van[:500]):
        khop = re.search(r"tháng\s+(\d{1,2})\s*(?:/|năm\s+)(\d{4})", nguon)
        if khop:
            thang, nam = int(khop.group(1)), int(khop.group(2))
            if 1 <= thang <= 12:
                return nam, thang
    if van_ban.ngay_ban_hanh:
        return van_ban.ngay_ban_hanh.year, van_ban.ngay_ban_hanh.month
    return None


def _trich_tu_cau(cau: str, tu_khoa: str, don_vi_tinh: str) -> tuple[float, str] | None:
    """Tìm con số gần từ khóa nhất trong một câu; trả (giá trị, mức khớp).

    Mức khớp: "cao" nếu số đứng cạnh từ khóa VÀ đúng đơn vị tính;
    "trung_binh" nếu chỉ được một trong hai điều kiện.
    """
    vi_tri = cau.lower().find(tu_khoa.lower())
    if vi_tri < 0:
        return None
    dau = max(0, vi_tri - BAN_KINH_TIM_SO)
    cuoi = min(len(cau), vi_tri + len(tu_khoa) + BAN_KINH_TIM_SO)
    vung = cau[dau:cuoi]

    ung_vien: list[tuple[int, float, bool]] = []  # (khoảng cách, giá trị, đúng đvt)
    for khop in MAU_SO.finditer(vung):
        gia_tri = _doi_so(khop.group(1), khop.group(2))
        dung_dvt = _khop_don_vi(vung[khop.end() :], don_vi_tinh)
        tam_so = dau + (khop.start() + khop.end()) // 2
        tam_tu_khoa = vi_tri + len(tu_khoa) // 2
        khoang_cach = abs(tam_so - tam_tu_khoa)
        ung_vien.append((khoang_cach, gia_tri, dung_dvt))
    if not ung_vien:
        return None
    # Ưu tiên số ĐÚNG ĐƠN VỊ TÍNH, sau đó mới đến gần từ khóa nhất
    ung_vien.sort(key=lambda u: (not u[2], u[0]))
    khoang_cach, gia_tri, dung_dvt = ung_vien[0]
    muc = "cao" if dung_dvt and khoang_cach <= BAN_KINH_TIM_SO else "trung_binh"
    return gia_tri, muc


def trich_xuat_offline(db: Session, van_ban: VanBan) -> list[TrichXuatCho]:
    """Chạy máy trích xuất bằng biểu thức chính quy, tạo hàng chờ xác nhận."""
    if van_ban.mat:
        return []  # văn bản mật bị chặn khỏi trích xuất
    ky = suy_ra_ky(van_ban)
    if ky is None or van_ban.co_quan_id is None:
        return []
    nam, thang = ky

    cac_cau = _tach_cau(van_ban.toan_van)
    ket_qua: list[TrichXuatCho] = []
    for ct in db.query(ChiTieu).order_by(ChiTieu.ma).all():
        if ct.cong_thuc:
            continue  # chỉ tiêu dẫn xuất: hệ thống tự tính, không trích
        try:
            ds_tu_khoa = json.loads(ct.tu_khoa_trich_xuat or "[]")
        except json.JSONDecodeError:
            ds_tu_khoa = []
        tim_thay: tuple[float, str, str] | None = None
        for cau in cac_cau:
            for tu_khoa in ds_tu_khoa:
                khop = _trich_tu_cau(cau, tu_khoa, ct.don_vi_tinh)
                if khop is not None:
                    tim_thay = (khop[0], khop[1], cau)
                    break
            if tim_thay:
                break
        if tim_thay is None:
            continue
        gia_tri, muc, cau = tim_thay
        if ct.don_vi_tinh == "%" and not 0 <= gia_tri <= 100:
            muc = "thap"
        ban_ghi = TrichXuatCho(
            van_ban_id=van_ban.id,
            chi_tieu_id=ct.id,
            don_vi_id=van_ban.co_quan_id,
            nam=nam,
            thang=thang,
            gia_tri_may_doc=gia_tri,
            doan_trich=cau[:500],
            do_tin_cay=muc,
            trang_thai="cho_xac_nhan",
            thoi_diem=datetime.now(),
        )
        db.add(ban_ghi)
        ket_qua.append(ban_ghi)
    db.commit()
    return ket_qua


def _gia_tri_nam_trong_doan(gia_tri: float, doan: str) -> bool:
    """Giá trị AI trả về phải xuất hiện NGUYÊN VĂN trong đoạn trích."""
    for khop in MAU_SO.finditer(doan):
        if abs(_doi_so(khop.group(1), khop.group(2)) - gia_tri) < 1e-6:
            return True
    return False


def trich_xuat_online(db: Session, van_ban: VanBan) -> list[TrichXuatCho]:
    """Chế độ online: Claude đọc văn bản, trả JSON; bản ghi có giá trị không
    nằm nguyên văn trong đoạn trích thì LOẠI. Lỗi API → lùi về offline."""
    if van_ban.mat:
        return []
    try:
        import anthropic

        ky = suy_ra_ky(van_ban)
        if ky is None or van_ban.co_quan_id is None:
            return []
        nam, thang = ky
        danh_muc = [
            {
                "ma": ct.ma,
                "ten": ct.ten,
                "don_vi_tinh": ct.don_vi_tinh,
                "tu_khoa": json.loads(ct.tu_khoa_trich_xuat or "[]"),
            }
            for ct in db.query(ChiTieu).all()
            if not ct.cong_thuc
        ]
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        phan_hoi = client.messages.create(
            model=settings.anthropic_model,
            max_tokens=2000,
            system=(
                "Trích số liệu chỉ tiêu từ văn bản hành chính tiếng Việt. "
                "Chỉ trả về JSON array: [{ma_chi_tieu, gia_tri, doan_trich, "
                "do_tin_cay}] với do_tin_cay ∈ cao|trung_binh|thap; "
                "doan_trich là CÂU NGUYÊN VĂN chứa con số."
            ),
            messages=[
                {
                    "role": "user",
                    "content": f"Danh mục chỉ tiêu: {json.dumps(danh_muc, ensure_ascii=False)}\n\n"
                    f"Văn bản: {van_ban.toan_van[:8000]}",
                }
            ],
        )
        tho = re.sub(r"^```\w*|```$", "", phan_hoi.content[0].text.strip(), flags=re.M)
        du_lieu = json.loads(tho)
        map_ct = {ct.ma: ct for ct in db.query(ChiTieu).all()}
        ket_qua: list[TrichXuatCho] = []
        for muc in du_lieu:
            ct = map_ct.get(str(muc.get("ma_chi_tieu", "")))
            gia_tri = float(muc.get("gia_tri", 0))
            doan = str(muc.get("doan_trich", ""))[:500]
            if ct is None or not doan:
                continue
            if not _gia_tri_nam_trong_doan(gia_tri, doan):
                continue  # AI không được bịa: số phải nằm nguyên văn trong câu
            ban_ghi = TrichXuatCho(
                van_ban_id=van_ban.id,
                chi_tieu_id=ct.id,
                don_vi_id=van_ban.co_quan_id,
                nam=nam,
                thang=thang,
                gia_tri_may_doc=gia_tri,
                doan_trich=doan,
                do_tin_cay=str(muc.get("do_tin_cay", "trung_binh")),
                trang_thai="cho_xac_nhan",
                thoi_diem=datetime.now(),
            )
            db.add(ban_ghi)
            ket_qua.append(ban_ghi)
        db.commit()
        return ket_qua
    except Exception:
        return trich_xuat_offline(db, van_ban)


def trich_xuat(db: Session, van_ban: VanBan) -> list[TrichXuatCho]:
    """Cửa vào duy nhất của máy trích xuất — chọn chế độ theo OFFLINE."""
    if settings.offline or not settings.anthropic_api_key:
        return trich_xuat_offline(db, van_ban)
    return trich_xuat_online(db, van_ban)
