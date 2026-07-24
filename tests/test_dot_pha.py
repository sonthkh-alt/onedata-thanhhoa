"""Kiểm thử các tính năng đột phá: hash chain, điều tra nguyên nhân,
phòng lab what-if, phân tích tức thì sau nhập liệu."""

import pytest
from sqlalchemy import text

from app.db import SessionLocal
from app.models import DonVi
from app.services import audit
from scripts.seed import reset_db, seed_all

MAT_KHAU = "Demo@2026"


@pytest.fixture(scope="module", autouse=True)
def reseed_sau_module():
    """Test giả mạo dữ liệu làm hỏng chuỗi — seed lại sau khi chạy xong."""
    yield
    reset_db()
    db = SessionLocal()
    try:
        seed_all(db)
    finally:
        db.close()


def dang_nhap(client, ten_dang_nhap):
    resp = client.post(
        "/dang-nhap", data={"ten_dang_nhap": ten_dang_nhap, "mat_khau": MAT_KHAU}
    )
    assert resp.status_code == 303


# ------------------------- Hash chain -------------------------


def test_chuoi_nhat_ky_toan_ven_sau_thao_tac(client, db):
    """Ghi vài thao tác rồi kiểm chứng: chuỗi phải toàn vẹn."""
    dang_nhap(client, "lanhdao")  # sinh thêm bản ghi đăng nhập
    kq = audit.kiem_chung_chuoi(db)
    assert kq.toan_ven
    assert kq.so_ban_ghi >= 2


def test_sua_len_bi_phat_hien(client, db):
    """Sửa lén nội dung một bản ghi thẳng trong CSDL → kiểm chứng phải bắt được."""
    dang_nhap(client, "lanhdao")
    db.execute(
        text(
            "UPDATE nhat_ky SET chi_tiet = 'DA BI SUA LEN' "
            "WHERE id = (SELECT MIN(id) FROM nhat_ky)"
        )
    )
    db.commit()
    kq = audit.kiem_chung_chuoi(db)
    assert not kq.toan_ven
    assert kq.vi_tri_loi is not None
    assert "SỬA" in (kq.mo_ta_loi or "")


def test_trang_kiem_chung(client):
    dang_nhap(client, "lanhdao")
    resp = client.get("/kiem-chung")
    assert resp.status_code == 200
    assert "Kiểm chứng toàn vẹn" in resp.text


# ------------------------- AI điều tra nguyên nhân -------------------------


def test_dieu_tra_giai_ngan_xa_diem_nong(client):
    dang_nhap(client, "lanhdao")
    resp = client.get("/dieu-tra?don_vi=CACSON&van_de=giai_ngan")
    assert resp.status_code == 200
    assert "Vì sao Xã Các Sơn giải ngân thấp?" in resp.text
    assert "Chuỗi điều tra" in resp.text
    assert "Kết luận" in resp.text
    assert "Khuyến nghị" in resp.text


def test_dieu_tra_tthc(client):
    dang_nhap(client, "lanhdao")
    resp = client.get("/dieu-tra?don_vi=NONGCONG&van_de=tthc")
    assert resp.status_code == 200
    assert "đúng hạn thấp" in resp.text
    assert "hồ sơ quá hạn" in resp.text


def test_dieu_tra_phan_quyen_va_404(client):
    dang_nhap(client, "xa.hacthanh")
    assert client.get("/dieu-tra?don_vi=CACSON").status_code == 403
    dang_nhap(client, "lanhdao")
    assert client.get("/dieu-tra?don_vi=KHONGCO").status_code == 404


# ------------------------- Phòng lab what-if -------------------------


def test_phong_lab(client, db):
    dang_nhap(client, "lanhdao")
    resp = client.get("/lab")
    assert resp.status_code == 200
    assert "Phòng lab chính sách" in resp.text
    assert "tangToc" in resp.text  # thanh trượt kịch bản
    # Dữ liệu mô phỏng nhúng đủ 15 xã
    so_xa = db.query(DonVi).filter(DonVi.loai.in_(["xa", "phuong"])).count()
    assert resp.text.count('"ma":') == so_xa


# ------------------------- Phân tích tức thì sau nhập liệu -------------------------


def test_nhap_lieu_co_phan_tich_tuc_thi(client):
    dang_nhap(client, "xa.hacthanh")
    resp = client.post("/nhap-lieu", data={"thang": "7", "gt_DTC02": "25000"})
    assert resp.status_code == 200
    assert "Phân tích tức thì" in resp.text
    assert "xếp thứ" in resp.text
    assert "Dự báo cả năm cập nhật lại ngay" in resp.text
