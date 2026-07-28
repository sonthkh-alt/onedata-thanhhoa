"""Hỏi – đáp dữ liệu AI có kiểm soát (CLAUDE.md 8.5).

Nguyên tắc "AI không được bịa số liệu": câu trả lời CHỈ được dựng từ kết
quả truy vấn CSDL (qua các view chỉ đọc v_*), kèm SQL đã chạy và thời điểm
cập nhật. Không truy vấn được → trả lời "Không có dữ liệu phù hợp trong Kho".

- Chế độ offline (OFFLINE=1, mặc định): so khớp ~20 câu hỏi mẫu đã ánh xạ
  sẵn sang SQL (data/seed/cau_hoi_mau.json), chuẩn hóa không dấu + từ khóa.
- Chế độ online (OFFLINE=0 + ANTHROPIC_API_KEY): model sinh SELECT, validate
  bằng sqlglot (allowlist view, chỉ SELECT, tự thêm LIMIT), thực thi chỉ đọc,
  rồi model viết 2–4 câu trả lời CHỈ từ bảng kết quả.
"""

import json
import re
import time
import unicodedata
from dataclasses import dataclass, field

import sqlglot
from sqlalchemy import text
from sqlglot import exp

from app.config import BASE_DIR, settings
from app.db import engine

DUONG_DAN_CAU_HOI_MAU = BASE_DIR / "data" / "seed" / "cau_hoi_mau.json"

VIEW_ALLOWLIST = {"v_so_lieu", "v_don_vi", "v_chi_tieu"}
GIOI_HAN_DONG = 200
THOI_GIAN_TOI_DA_GIAY = 5

TRA_LOI_KHONG_CO_DU_LIEU = "Không có dữ liệu phù hợp trong Kho dữ liệu dùng chung."

SCHEMA_CHO_MODEL = """Các view CHỈ ĐỌC được phép truy vấn (SQLite):
- v_so_lieu(ma_chi_tieu, ten_chi_tieu, don_vi_tinh, ma_linh_vuc, ten_linh_vuc,
  ma_don_vi, ten_don_vi, loai_don_vi, vung, nam, thang, ky, gia_tri, nguon,
  thoi_diem_cap_nhat)
  -- mỗi dòng = giá trị một chỉ tiêu của một xã trong một tháng (nam=2026,
  -- thang=1..7, ky=YYYYMM); vung ∈ (do_thi, dong_bang, mien_nui)
- v_don_vi(id, ma, ma_dinh_danh, ma_dvhc, ten, loai, loai_dvhc, vung, trang_thai)
- v_chi_tieu(id, ma, ten, don_vi_tinh, tan_suat, co_quan_chu_chi_tieu,
  nguon_du_lieu, muc_chia_se, cong_thuc, cong_khai, ma_linh_vuc, ten_linh_vuc)
Mã chỉ tiêu: DTC01 kế hoạch vốn, DTC02 giải ngân lũy kế, DTC03 tỷ lệ giải
ngân %, DTC04 dự án đang triển khai, DTC05 dự án chậm; TTHC01 hồ sơ tiếp
nhận, TTHC02 đúng hạn, TTHC03 quá hạn, TTHC04 tỷ lệ đúng hạn %, TTHC05 hồ
sơ trực tuyến, TTHC06 tỷ lệ trực tuyến %; AS01 hộ nghèo, AS02 cận nghèo,
AS03 đối tượng BTXH, AS04 kinh phí chi trả, AS05 tỷ lệ không tiền mặt %."""


@dataclass
class KetQuaHoiDap:
    """Kết quả một lượt hỏi đáp, đủ dữ kiện để hiển thị và ghi nhật ký."""

    cau_hoi: str
    tra_loi: str
    loai: str = "so_lieu"  # so_lieu | van_ban | lai (định tuyến 2 lớp v0.2)
    sql: str | None = None
    cot: list[str] = field(default_factory=list)
    dong: list[list] = field(default_factory=list)
    doan_van_ban: list[dict] = field(default_factory=list)  # đoạn Lớp 1 dẫn nguồn
    che_do: str = "offline"
    cau_hoi_mau: str | None = None
    loi: str | None = None

    @property
    def so_dong(self) -> int:
        return len(self.dong)


# Từ khóa định tuyến offline (chuẩn hóa không dấu)
TU_KHOA_LOP_VAN_BAN = (
    "van ban",
    "bao cao nao",
    "noi gi",
    "giai trinh",
    "nguyen nhan",
    "ke hoach",
    "thong bao",
    "ket luan",
    "chi dao",
)
TU_KHOA_LOP_SO_LIEU = (
    "bao nhieu",
    "ty le",
    "xa nao",
    "tong",
    "xep hang",
    "cao nhat",
    "thap nhat",
    "duoi",
    "tren",
    "so lieu",
    "danh sach",
)


def phan_loai_cau_hoi(cau_hoi: str) -> str:
    """Định tuyến câu hỏi: `so_lieu` | `van_ban` | `lai` (chế độ offline
    dùng từ khóa; chế độ online có thể hỏi mô hình)."""
    hoi = chuan_hoa(cau_hoi)
    co_van_ban = any(tk in hoi for tk in TU_KHOA_LOP_VAN_BAN)
    co_so_lieu = any(tk in hoi for tk in TU_KHOA_LOP_SO_LIEU)
    if co_van_ban and co_so_lieu:
        return "lai"
    if co_van_ban:
        return "van_ban"
    return "so_lieu"


def chuan_hoa(van_ban: str) -> str:
    """Chuẩn hóa tiếng Việt: bỏ dấu, thường hóa, gọn khoảng trắng."""
    van_ban = van_ban.lower().replace("đ", "d")
    van_ban = unicodedata.normalize("NFD", van_ban)
    van_ban = "".join(c for c in van_ban if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", van_ban).strip()


def tai_cau_hoi_mau() -> list[dict]:
    with open(DUONG_DAN_CAU_HOI_MAU, encoding="utf-8") as f:
        return json.load(f)


def tim_cau_hoi_mau(cau_hoi: str) -> dict | None:
    """So khớp gần đúng: điểm = số cụm từ khóa xuất hiện trong câu hỏi
    (đã chuẩn hóa); yêu cầu khớp đủ TẤT CẢ từ khóa của một mẫu."""
    hoi = chuan_hoa(cau_hoi)
    tot_nhat, diem_max = None, 0
    for mau in tai_cau_hoi_mau():
        if chuan_hoa(mau["cau_hoi"]) == hoi:
            return mau  # khớp nguyên câu → chọn ngay, không so từ khóa
        tu_khoa = mau["tu_khoa"]
        diem = sum(1 for tk in tu_khoa if chuan_hoa(tk) in hoi)
        if diem == len(tu_khoa) and diem > diem_max:
            tot_nhat, diem_max = mau, diem
    return tot_nhat


class LoiSQL(Exception):
    """SQL không vượt qua bước kiểm soát."""


def validate_sql(sql: str) -> str:
    """Kiểm soát SQL do AI sinh/ánh xạ: một câu SELECT duy nhất, chỉ đụng
    các view trong allowlist, cấm từ khóa nguy hiểm, tự thêm LIMIT."""
    sql = sql.strip().rstrip(";").strip()
    if ";" in sql:
        raise LoiSQL("Chỉ được phép MỘT câu lệnh SQL.")

    tu_cam = ("attach", "pragma", "vacuum", "reindex")
    chu_thuong = sql.lower()
    for tu in tu_cam:
        if re.search(rf"\b{tu}\b", chu_thuong):
            raise LoiSQL(f"Từ khóa bị cấm: {tu.upper()}.")

    try:
        cac_cau = sqlglot.parse(sql, read="sqlite")
    except sqlglot.errors.ParseError as e:
        raise LoiSQL(f"SQL không hợp lệ: {e}") from e
    if len(cac_cau) != 1 or cac_cau[0] is None:
        raise LoiSQL("Chỉ được phép MỘT câu lệnh SQL.")

    cau = cac_cau[0]
    if not isinstance(cau, exp.Select):
        raise LoiSQL("Chỉ được phép câu SELECT.")

    for bang in cau.find_all(exp.Table):
        if bang.name.lower() not in VIEW_ALLOWLIST:
            raise LoiSQL(
                f"Bảng/view '{bang.name}' không nằm trong danh mục được phép "
                f"({', '.join(sorted(VIEW_ALLOWLIST))})."
            )

    if cau.args.get("limit") is None:
        cau = cau.limit(GIOI_HAN_DONG)
    return cau.sql(dialect="sqlite")


def thuc_thi_sql(sql: str) -> tuple[list[str], list[list]]:
    """Thực thi SELECT trên kết nối CHỈ ĐỌC (PRAGMA query_only) với giới hạn
    thời gian chạy."""
    with engine.connect() as ket_noi:
        raw = ket_noi.connection.dbapi_connection
        han_chot = time.monotonic() + THOI_GIAN_TOI_DA_GIAY
        raw.set_progress_handler(
            lambda: 1 if time.monotonic() > han_chot else 0, 10_000
        )
        ket_noi.exec_driver_sql("PRAGMA query_only = ON")
        try:
            ket_qua = ket_noi.execute(text(sql))
            cot = list(ket_qua.keys())
            dong = [list(d) for d in ket_qua.fetchall()]
        finally:
            # Trả kết nối về trạng thái bình thường trước khi vào lại pool,
            # nếu không mọi thao tác GHI sau đó trên kết nối này sẽ hỏng.
            raw.set_progress_handler(None, 0)
            ket_noi.exec_driver_sql("PRAGMA query_only = OFF")
    return cot, dong


def _dinh_dang_dong(cot: list[str], dong: list[list]) -> list[list]:
    """Làm gọn giá trị hiển thị (float → tối đa 1 số lẻ nếu cần)."""
    ket_qua = []
    for d in dong:
        hang = []
        for gia_tri in d:
            if isinstance(gia_tri, float) and gia_tri == int(gia_tri):
                hang.append(int(gia_tri))
            else:
                hang.append(gia_tri)
        ket_qua.append(hang)
    return ket_qua


def _tra_loi_so_lieu(mau: dict, cau_hoi: str) -> KetQuaHoiDap:
    """Nhánh Lớp 2: chạy SQL đã ánh xạ sẵn (qua bộ kiểm soát)."""
    try:
        sql = validate_sql(mau["sql"])
        cot, dong = thuc_thi_sql(sql)
    except LoiSQL as e:
        return KetQuaHoiDap(
            cau_hoi=cau_hoi,
            tra_loi=TRA_LOI_KHONG_CO_DU_LIEU,
            che_do="offline",
            loi=str(e),
        )
    if not dong:
        return KetQuaHoiDap(
            cau_hoi=cau_hoi,
            tra_loi=TRA_LOI_KHONG_CO_DU_LIEU,
            sql=sql,
            che_do="offline",
            cau_hoi_mau=mau["cau_hoi"],
        )
    tra_loi = (
        f"{mau['tra_loi']} Kho dữ liệu trả về {len(dong)} dòng số liệu "
        "(bảng chi tiết bên dưới, kèm câu SQL đã chạy)."
    )
    return KetQuaHoiDap(
        cau_hoi=cau_hoi,
        tra_loi=tra_loi,
        sql=sql,
        cot=cot,
        dong=_dinh_dang_dong(cot, dong),
        che_do="offline",
        cau_hoi_mau=mau["cau_hoi"],
    )


def _tim_doan_van_ban(cau_hoi_fts: str, db=None, nguoi_dung=None) -> list[dict]:
    """Nhánh Lớp 1: lấy 5–8 đoạn liên quan (đã lọc quyền, loại mật)."""
    from app.db import SessionLocal
    from app.services import search

    phien = db or SessionLocal()
    try:
        return search.tim_kiem(phien, cau_hoi_fts, nguoi_dung)
    finally:
        if db is None:
            phien.close()


def hoi_offline(cau_hoi: str, db=None, nguoi_dung=None) -> KetQuaHoiDap:
    """Chế độ offline: so khớp câu mẫu → định tuyến so_lieu | van_ban | lai.

    Không khớp câu mẫu: câu thiên về văn bản vẫn tìm được qua FTS5;
    câu số liệu không khớp → trả lời rõ "Không có dữ liệu phù hợp".
    """
    mau = tim_cau_hoi_mau(cau_hoi)
    loai = mau.get("loai", "so_lieu") if mau else phan_loai_cau_hoi(cau_hoi)

    if mau is not None and loai == "so_lieu":
        kq = _tra_loi_so_lieu(mau, cau_hoi)
        kq.loai = "so_lieu"
        return kq

    if loai in ("van_ban", "lai"):
        truy_van_fts = (mau or {}).get("truy_van_fts") or cau_hoi
        cac_doan = _tim_doan_van_ban(truy_van_fts, db, nguoi_dung)
        kq_so_lieu: KetQuaHoiDap | None = None
        if loai == "lai" and mau is not None and mau.get("sql"):
            kq_so_lieu = _tra_loi_so_lieu(mau, cau_hoi)

        if not cac_doan and kq_so_lieu is None:
            return KetQuaHoiDap(
                cau_hoi=cau_hoi,
                tra_loi="Không tìm thấy trong Kho dữ liệu dùng chung "
                "(cả lớp số liệu lẫn lớp văn bản).",
                loai=loai,
                che_do="offline",
            )

        phan_van_ban = (
            f"Tìm thấy {len(cac_doan)} đoạn liên quan trong Kho văn bản — "
            "trích dẫn kèm số/ký hiệu, ngày ban hành ở dưới."
            if cac_doan
            else "Không tìm thấy văn bản liên quan trong Kho."
        )
        if kq_so_lieu is not None and kq_so_lieu.dong:
            tra_loi = f"{kq_so_lieu.tra_loi} {phan_van_ban}"
        else:
            tra_loi = phan_van_ban
        return KetQuaHoiDap(
            cau_hoi=cau_hoi,
            tra_loi=tra_loi,
            loai=loai,
            sql=kq_so_lieu.sql if kq_so_lieu else None,
            cot=kq_so_lieu.cot if kq_so_lieu else [],
            dong=kq_so_lieu.dong if kq_so_lieu else [],
            doan_van_ban=cac_doan,
            che_do="offline",
            cau_hoi_mau=mau["cau_hoi"] if mau else None,
        )

    return KetQuaHoiDap(
        cau_hoi=cau_hoi,
        tra_loi=TRA_LOI_KHONG_CO_DU_LIEU
        + " Anh/chị có thể chọn một câu hỏi gợi ý bên dưới.",
        loai="so_lieu",
        che_do="offline",
    )


def hoi_online(cau_hoi: str) -> KetQuaHoiDap:
    """Chế độ online (Claude API): sinh SELECT → validate → thực thi →
    model viết câu trả lời CHỈ dựa trên bảng kết quả. Mọi lỗi API đều được
    bắt để không làm sập trang."""
    try:
        import anthropic

        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

        phan_hoi_sql = client.messages.create(
            model=settings.anthropic_model,
            max_tokens=500,
            system=(
                "Bạn là trợ lý sinh SQL cho SQLite. Chỉ trả về DUY NHẤT một "
                "câu SELECT (không giải thích, không markdown), chỉ dùng các "
                "view sau:\n" + SCHEMA_CHO_MODEL
            ),
            messages=[{"role": "user", "content": cau_hoi}],
        )
        sql_tho = phan_hoi_sql.content[0].text.strip()
        sql_tho = re.sub(r"^```\w*|```$", "", sql_tho, flags=re.M).strip()

        sql = validate_sql(sql_tho)
        cot, dong = thuc_thi_sql(sql)
        if not dong:
            return KetQuaHoiDap(
                cau_hoi=cau_hoi,
                tra_loi=TRA_LOI_KHONG_CO_DU_LIEU,
                sql=sql,
                che_do="online",
            )

        bang_json = json.dumps(
            {"cot": cot, "dong": dong[:50]}, ensure_ascii=False, default=str
        )
        phan_hoi_tra_loi = client.messages.create(
            model=settings.anthropic_model,
            max_tokens=500,
            system=(
                "Viết 2–4 câu tiếng Việt trả lời câu hỏi, CHỈ dựa trên bảng "
                "kết quả JSON được cung cấp. Tuyệt đối không thêm số liệu "
                "ngoài bảng. Nêu rõ đây là dữ liệu mô phỏng nếu được hỏi về "
                "độ tin cậy."
            ),
            messages=[
                {
                    "role": "user",
                    "content": f"Câu hỏi: {cau_hoi}\nBảng kết quả: {bang_json}",
                }
            ],
        )
        tra_loi = phan_hoi_tra_loi.content[0].text.strip()
        return KetQuaHoiDap(
            cau_hoi=cau_hoi,
            tra_loi=tra_loi,
            sql=sql,
            cot=cot,
            dong=_dinh_dang_dong(cot, dong),
            che_do="online",
        )
    except LoiSQL as e:
        return KetQuaHoiDap(
            cau_hoi=cau_hoi,
            tra_loi=TRA_LOI_KHONG_CO_DU_LIEU,
            che_do="online",
            loi=f"SQL bị chặn bởi bộ kiểm soát: {e}",
        )
    except Exception as e:
        return KetQuaHoiDap(
            cau_hoi=cau_hoi,
            tra_loi="Không gọi được dịch vụ AI (chế độ online). "
            "Anh/chị có thể chuyển OFFLINE=1 để dùng bộ câu hỏi mẫu.",
            che_do="online",
            loi=str(e)[:200],
        )


def hoi(cau_hoi: str, db=None, nguoi_dung=None) -> KetQuaHoiDap:
    """Cửa vào duy nhất: chọn chế độ theo cấu hình OFFLINE.

    `db` + `nguoi_dung` phục vụ nhánh văn bản (lọc quyền, loại mật).
    """
    cau_hoi = cau_hoi.strip()
    if settings.offline or not settings.anthropic_api_key:
        return hoi_offline(cau_hoi, db, nguoi_dung)
    loai = phan_loai_cau_hoi(cau_hoi)
    if loai == "so_lieu":
        return hoi_online(cau_hoi)
    # Nhánh văn bản/lai online: lấy đoạn (đã lọc quyền/mật) rồi nhờ mô hình
    # tổng hợp CHỈ từ các đoạn đó; lỗi API → hiển thị đoạn thô như offline.
    kq = hoi_offline(cau_hoi, db, nguoi_dung)
    kq.che_do = "online"
    if not kq.doan_van_ban:
        return kq
    try:
        import anthropic

        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        boi_canh = json.dumps(kq.doan_van_ban, ensure_ascii=False)
        phan_hoi = client.messages.create(
            model=settings.anthropic_model,
            max_tokens=600,
            system=(
                "Trả lời 2–4 câu tiếng Việt CHỈ dựa trên các đoạn văn bản "
                "được cung cấp; BẮT BUỘC dẫn số/ký hiệu và ngày ban hành của "
                "văn bản. Không có thông tin thì nói rõ 'Không tìm thấy "
                "trong Kho'."
            ),
            messages=[
                {
                    "role": "user",
                    "content": f"Câu hỏi: {cau_hoi}\nCác đoạn văn bản: {boi_canh}",
                }
            ],
        )
        tra_loi_vb = phan_hoi.content[0].text.strip()
        kq.tra_loi = (
            f"{kq.tra_loi.split(' Tìm thấy')[0]} {tra_loi_vb}"
            if kq.loai == "lai" and kq.dong
            else tra_loi_vb
        )
    except Exception as e:
        kq.loi = f"Không gọi được AI online, hiển thị đoạn thô: {str(e)[:150]}"
    return kq
