"""Kiểm thử M5: hỏi đáp AI offline + validator SQL (chặn các ca tấn công)."""

import pytest

from app.models import NhatKy
from app.services import ai_query
from app.services.ai_query import LoiSQL, validate_sql

MAT_KHAU = "Demo@2026"


def dang_nhap(client, ten_dang_nhap):
    resp = client.post(
        "/dang-nhap", data={"ten_dang_nhap": ten_dang_nhap, "mat_khau": MAT_KHAU}
    )
    assert resp.status_code == 303


# ------------------------- Validator SQL -------------------------


@pytest.mark.parametrize(
    "sql_xau",
    [
        "UPDATE gia_tri_chi_tieu SET gia_tri = 0",
        "DELETE FROM nhat_ky",
        "DROP TABLE nguoi_dung",
        "INSERT INTO don_vi (ma, ten) VALUES ('X', 'Y')",
        "SELECT * FROM nguoi_dung",
        "SELECT * FROM gia_tri_chi_tieu",
        "SELECT mat_khau_hash FROM nguoi_dung",
        "SELECT * FROM v_so_lieu; DROP TABLE nguoi_dung",
        "PRAGMA table_info(nguoi_dung)",
        "ATTACH DATABASE 'x.db' AS x",
        "SELECT * FROM v_so_lieu JOIN nguoi_dung ON 1=1",
    ],
)
def test_validator_chan_sql_nguy_hiem(sql_xau):
    with pytest.raises(LoiSQL):
        validate_sql(sql_xau)


def test_validator_cho_qua_select_hop_le_va_them_limit():
    sql = validate_sql("SELECT ten_don_vi, gia_tri FROM v_so_lieu WHERE thang = 7")
    assert "LIMIT 200" in sql.upper()


def test_validator_giu_limit_co_san():
    sql = validate_sql("SELECT ten_don_vi FROM v_so_lieu LIMIT 5")
    assert "LIMIT 5" in sql.upper()
    assert "200" not in sql


# ------------------------- Bộ câu hỏi mẫu offline -------------------------


def test_toan_bo_cau_hoi_mau_chay_duoc(csdl_demo):
    """Cả ~20 câu hỏi mẫu: khớp đúng chính nó, SQL qua validator và thực thi
    được trên Kho dữ liệu; tối thiểu 18 câu có dữ liệu trả về."""
    ds_mau = ai_query.tai_cau_hoi_mau()
    assert len(ds_mau) >= 20

    so_cau_co_du_lieu = 0
    for mau in ds_mau:
        ket_qua = ai_query.hoi_offline(mau["cau_hoi"])
        assert ket_qua.sql is not None, f"Không khớp câu mẫu: {mau['cau_hoi']}"
        assert ket_qua.cau_hoi_mau == mau["cau_hoi"]
        if ket_qua.so_dong:
            so_cau_co_du_lieu += 1
    assert so_cau_co_du_lieu >= 18


def test_cau_hoi_diem_nong_giai_ngan(csdl_demo):
    """Câu hỏi trọng tâm kịch bản demo: xã giải ngân dưới 30% tháng 7."""
    ket_qua = ai_query.hoi_offline("Những xã nào giải ngân dưới 30% trong tháng 7?")
    ten_cac_xa = " ".join(str(d[0]) for d in ket_qua.dong)
    assert "Các Sơn" in ten_cac_xa
    assert "Demo 12" in ten_cac_xa
    assert all(d[1] < 30 for d in ket_qua.dong)


def test_cau_hoi_khong_khop_tra_loi_khong_co_du_lieu(csdl_demo):
    ket_qua = ai_query.hoi_offline("Thời tiết Thanh Hóa hôm nay thế nào?")
    assert "Không có dữ liệu phù hợp" in ket_qua.tra_loi
    assert ket_qua.sql is None


def test_chuan_hoa_khong_dau():
    assert ai_query.chuan_hoa("Giải  NGÂN dưới 30%") == "giai ngan duoi 30%"
    assert ai_query.chuan_hoa("Đúng hạn") == "dung han"


# ------------------------- Giao diện /hoi-dap -------------------------


def test_trang_hoi_dap_lanh_dao(client):
    dang_nhap(client, "lanhdao")
    resp = client.get("/hoi-dap")
    assert resp.status_code == 200
    assert "Câu hỏi gợi ý" in resp.text


def test_gui_cau_hoi_va_ghi_nhat_ky(client, db):
    dang_nhap(client, "lanhdao")
    truoc = db.query(NhatKy).filter(NhatKy.hanh_dong == "hoi_dap_ai").count()
    resp = client.post(
        "/hoi-dap",
        data={"cau_hoi": "Những xã nào giải ngân dưới 30% trong tháng 7?"},
    )
    assert resp.status_code == 200
    assert "Xã Các Sơn" in resp.text
    assert "SQL" in resp.text
    assert "v_so_lieu" in resp.text
    sau = db.query(NhatKy).filter(NhatKy.hanh_dong == "hoi_dap_ai").count()
    assert sau == truoc + 1


@pytest.mark.parametrize("tai_khoan", ["daibieu", "xa.hacthanh"])
def test_hoi_dap_phan_quyen(client, tai_khoan):
    dang_nhap(client, tai_khoan)
    assert client.get("/hoi-dap").status_code == 403
