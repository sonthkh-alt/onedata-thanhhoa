"""Kiểm thử M3: dashboard, cảnh báo điểm nóng, trang công khai, giám sát."""

import pytest

from app.models import NhatKy
from app.services.canh_bao import tim_diem_nong

MAT_KHAU = "Demo@2026"


def dang_nhap(client, ten_dang_nhap):
    resp = client.post(
        "/dang-nhap", data={"ten_dang_nhap": ten_dang_nhap, "mat_khau": MAT_KHAU}
    )
    assert resp.status_code == 303


# ------------------------- Cảnh báo điểm nóng -------------------------


def test_canh_bao_dung_diem_nong_cai_san(db):
    """4 luật cảnh báo bắt đúng các điểm nóng đã cài trong seed."""
    diem_nong = tim_diem_nong(db, thang=7)
    theo_luat = {}
    for dn in diem_nong:
        theo_luat.setdefault(dn.luat.split(" kỳ ")[0], set()).add(dn.ma_don_vi)

    # Luật 1: 2 xã giải ngân dưới 30%
    xa_giai_ngan = {dn.ma_don_vi for dn in diem_nong if "Tỷ lệ giải ngân" in dn.luat}
    assert {"CACSON", "MUONGLAT"} <= xa_giai_ngan

    # Luật 2: 2 xã TTHC đúng hạn dưới 90%
    xa_tthc = {dn.ma_don_vi for dn in diem_nong if "đúng hạn TTHC" in dn.luat}
    assert {"TANTHANH", "NONGCONG"} <= xa_tthc

    # Luật 3: Hạc Thành và Bá Thước chưa nhập đủ kỳ tháng 7
    xa_thieu = {dn.ma_don_vi for dn in diem_nong if "Chưa nhập đủ" in dn.luat}
    assert {"HACTHANH", "BATHUOC"} <= xa_thieu

    # Luật 4: Hậu Lộc lũy kế tháng 6 giảm so tháng 5
    xa_giam = {dn.ma_don_vi for dn in diem_nong if "nghi sai số liệu" in dn.luat}
    assert "HAULOC" in xa_giam


# ------------------------- Dashboard -------------------------


def test_dashboard_phai_dang_nhap(client):
    assert client.get("/dashboard").status_code == 303


def test_dashboard_lanh_dao_xem_duoc(client):
    dang_nhap(client, "lanhdao")
    resp = client.get("/dashboard?thang=7")
    assert resp.status_code == 200
    assert "Dashboard điều hành" in resp.text
    assert "điểm nóng" in resp.text.lower()
    assert "Xã Các Sơn" in resp.text  # điểm nóng giải ngân
    assert "kỳ 202607" in resp.text  # mã kỳ chuẩn YYYYMM


def test_dashboard_chuyen_vien_xa_khong_duoc_xem(client):
    dang_nhap(client, "xa.hacthanh")
    assert client.get("/dashboard").status_code == 403


def test_chi_tiet_don_vi(client):
    dang_nhap(client, "lanhdao")
    resp = client.get("/don-vi/CACSON")
    assert resp.status_code == 200
    assert "Xã Các Sơn" in resp.text
    assert client.get("/don-vi/KHONG-TON-TAI").status_code == 404


# ------------------------- Trang công khai -------------------------


def test_cong_khai_khong_can_dang_nhap(client):
    resp = client.get("/cong-khai")
    assert resp.status_code == 200
    assert "DÂN BIẾT" in resp.text
    assert "Dữ liệu mô phỏng" in resp.text
    # Đủ 4 chỉ tiêu thuộc Danh mục dữ liệu mở
    for ma in ["DTC03", "TTHC04", "TTHC06", "AS05"]:
        assert ma in resp.text
    # Metadata theo cột Phụ lục 3 QĐ 2053
    assert "Cơ quan chủ trì cung cấp" in resp.text
    assert "Kỳ nhập liệu" in resp.text


def test_cong_khai_tai_json(client):
    resp = client.get("/cong-khai/tai-xuong?dinh_dang=json")
    assert resp.status_code == 200
    du_lieu = resp.json()
    assert du_lieu["ky"] == "202607"
    assert len(du_lieu["tap_du_lieu"]) == 4
    assert du_lieu["tap_du_lieu"][0]["so_lieu"]


def test_cong_khai_tai_excel(client):
    resp = client.get("/cong-khai/tai-xuong?dinh_dang=xlsx")
    assert resp.status_code == 200
    assert "spreadsheetml" in resp.headers["content-type"]
    assert resp.content[:2] == b"PK"  # file .xlsx (zip)


def test_gop_y_du_lieu_mo(client, db):
    truoc = db.query(NhatKy).filter(NhatKy.hanh_dong == "gop_y_du_lieu_mo").count()
    resp = client.post(
        "/cong-khai/gop-y",
        data={"noi_dung": "Đề nghị công khai tiến độ dự án đường liên xã."},
    )
    assert resp.status_code == 303
    sau = db.query(NhatKy).filter(NhatKy.hanh_dong == "gop_y_du_lieu_mo").count()
    assert sau == truoc + 1


# ------------------------- Giám sát HĐND -------------------------


@pytest.mark.parametrize("tai_khoan", ["daibieu", "lanhdao"])
def test_giam_sat_xem_duoc(client, tai_khoan):
    dang_nhap(client, tai_khoan)
    resp = client.get("/giam-sat")
    assert resp.status_code == 200
    assert "12/NQ-HĐND" in resp.text
    assert "Mục tiêu" in resp.text


def test_giam_sat_chuyen_vien_xa_khong_duoc_xem(client):
    dang_nhap(client, "xa.hacthanh")
    assert client.get("/giam-sat").status_code == 403
