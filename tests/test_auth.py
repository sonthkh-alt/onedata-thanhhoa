"""Kiểm thử đăng nhập/đăng xuất và bảo vệ trang chủ."""

import pytest

from app.models import NhatKy

TAI_KHOAN_DEMO = ["admin", "lanhdao", "xa.hacthanh", "daibieu"]
MAT_KHAU = "Demo@2026"


def test_trang_chu_chuyen_ve_dang_nhap_khi_chua_dang_nhap(client):
    resp = client.get("/")
    assert resp.status_code == 303
    assert resp.headers["location"] == "/dang-nhap"


def test_trang_dang_nhap_hien_thi(client):
    resp = client.get("/dang-nhap")
    assert resp.status_code == 200
    assert "Đăng nhập hệ thống" in resp.text


@pytest.mark.parametrize("ten_dang_nhap", TAI_KHOAN_DEMO)
def test_dang_nhap_thanh_cong_4_tai_khoan(client, ten_dang_nhap):
    resp = client.post(
        "/dang-nhap", data={"ten_dang_nhap": ten_dang_nhap, "mat_khau": MAT_KHAU}
    )
    assert resp.status_code == 303
    assert resp.headers["location"] == "/"
    # Cookie phiên được ghi và truy cập được trang chủ
    trang_chu = client.get("/")
    assert trang_chu.status_code == 200
    assert "Xin chào" in trang_chu.text


def test_dang_nhap_sai_mat_khau(client):
    resp = client.post(
        "/dang-nhap", data={"ten_dang_nhap": "lanhdao", "mat_khau": "sai-mat-khau"}
    )
    assert resp.status_code == 401
    assert "không đúng" in resp.text


def test_dang_xuat_xoa_phien(client):
    client.post("/dang-nhap", data={"ten_dang_nhap": "lanhdao", "mat_khau": MAT_KHAU})
    resp = client.get("/dang-xuat")
    assert resp.status_code == 303
    sau_dang_xuat = client.get("/")
    assert sau_dang_xuat.status_code == 303
    assert sau_dang_xuat.headers["location"] == "/dang-nhap"


def test_nhat_ky_ghi_dang_nhap(client, db):
    truoc = db.query(NhatKy).filter(NhatKy.hanh_dong == "dang_nhap").count()
    client.post("/dang-nhap", data={"ten_dang_nhap": "admin", "mat_khau": MAT_KHAU})
    sau = db.query(NhatKy).filter(NhatKy.hanh_dong == "dang_nhap").count()
    assert sau == truoc + 1
