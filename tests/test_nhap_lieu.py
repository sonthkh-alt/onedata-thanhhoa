"""Kiểm thử phân hệ nhập liệu tại nguồn (M2): phân quyền, ghi đè, tự tính."""

import pytest

from app.db import SessionLocal
from app.models import ChiTieu, DonVi, GiaTriChiTieu, NhatKy
from scripts.seed import reset_db, seed_all

MAT_KHAU = "Demo@2026"


@pytest.fixture(scope="module", autouse=True)
def reseed_sau_module():
    """Các test dưới đây làm thay đổi dữ liệu — seed lại sau khi chạy xong
    để không ảnh hưởng test_seed (chạy sau theo thứ tự bảng chữ cái)."""
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


def lay_gia_tri(db, ma_ct, ma_dv, thang):
    ct = db.query(ChiTieu).filter_by(ma=ma_ct).one()
    dv = db.query(DonVi).filter_by(ma=ma_dv).one()
    return (
        db.query(GiaTriChiTieu)
        .filter_by(chi_tieu_id=ct.id, don_vi_id=dv.id, nam=2026, thang=thang)
        .first()
    )


def test_chuyen_vien_xa_mo_duoc_trang(client):
    dang_nhap(client, "xa.hacthanh")
    resp = client.get("/nhap-lieu?thang=7")
    assert resp.status_code == 200
    assert "Phường Hạc Thành" in resp.text
    assert "MỘT LẦN" in resp.text
    assert "Đúng - Đủ - Sạch - Sống" in resp.text


@pytest.mark.parametrize("tai_khoan", ["lanhdao", "daibieu"])
def test_vai_tro_khac_khong_duoc_nhap(client, tai_khoan):
    dang_nhap(client, tai_khoan)
    assert client.get("/nhap-lieu").status_code == 403
    assert client.post("/nhap-lieu", data={"thang": "7"}).status_code == 403


def test_nhap_moi_va_tu_tinh_dan_xuat(client, db):
    """Nhập DTC02 tháng 7 (ô trống theo seed) → lưu + tự tính DTC03."""
    dang_nhap(client, "xa.hacthanh")
    ke_hoach = lay_gia_tri(db, "DTC01", "HACTHANH", 7).gia_tri
    gia_tri_moi = round(ke_hoach * 0.55, 0)

    resp = client.post("/nhap-lieu", data={"thang": "7", "gt_DTC02": str(gia_tri_moi)})
    assert resp.status_code == 200
    assert "Đã lưu 1 số liệu" in resp.text

    db.expire_all()
    dtc02 = lay_gia_tri(db, "DTC02", "HACTHANH", 7)
    assert dtc02 is not None and dtc02.gia_tri == gia_tri_moi
    assert dtc02.nguon == "nhap_tay"

    dtc03 = lay_gia_tri(db, "DTC03", "HACTHANH", 7)
    assert dtc03 is not None
    assert dtc03.gia_tri == round(gia_tri_moi / ke_hoach * 100, 1)
    assert dtc03.nguon == "he_thong"

    so_log = db.query(NhatKy).filter(NhatKy.hanh_dong == "nhap_so_lieu").count()
    assert so_log >= 1


def test_canh_bao_luy_ke_giam_van_luu(client, db):
    """DTC02 tháng 7 nhỏ hơn tháng 6 → cảnh báo nhưng vẫn lưu (gắn cờ)."""
    dang_nhap(client, "xa.hacthanh")
    thang6 = lay_gia_tri(db, "DTC02", "HACTHANH", 6).gia_tri
    gia_tri_giam = round(thang6 * 0.9, 0)

    resp = client.post("/nhap-lieu", data={"thang": "7", "gt_DTC02": str(gia_tri_giam)})
    assert resp.status_code == 200
    assert "GIẢM so với kỳ trước" in resp.text

    db.expire_all()
    assert lay_gia_tri(db, "DTC02", "HACTHANH", 7).gia_tri == gia_tri_giam
    assert db.query(NhatKy).filter(NhatKy.hanh_dong == "canh_bao_du_lieu").count() >= 1


def test_phan_tram_ngoai_khoang_bi_chan(client, db):
    """Tháng 4: AS05 là nhập tay (kênh 3) nên sửa được — nhưng 150% bị chặn."""
    dang_nhap(client, "xa.hacthanh")
    resp = client.post("/nhap-lieu", data={"thang": "4", "gt_AS05": "150"})
    assert resp.status_code == 200
    assert "phải nằm trong [0; 100]" in resp.text
    db.expire_all()
    as05 = lay_gia_tri(db, "AS05", "HACTHANH", 4)
    assert as05 is None or as05.gia_tri != 150


def test_kenh_3_khong_ghi_de_so_lieu_kenh_1_2(client, db):
    """v0.2: chỉ tiêu đã có từ kênh 1/2 (hệ thống, văn bản) KHÔNG nhập tay được.

    AS03 tháng 6 có nguồn 'van_ban' (báo cáo tháng 6 trong Kho) → gửi giá
    trị mới phải bị bỏ qua.
    """
    dang_nhap(client, "xa.hacthanh")
    truoc = lay_gia_tri(db, "AS03", "HACTHANH", 6)
    assert truoc.nguon == "van_ban"

    client.post("/nhap-lieu", data={"thang": "6", "gt_AS03": "77777"})
    db.expire_all()
    sau = lay_gia_tri(db, "AS03", "HACTHANH", 6)
    assert sau.gia_tri == truoc.gia_tri  # không bị ghi đè
    assert sau.nguon == "van_ban"


def test_sua_ghi_de_va_log(client, db):
    """Tháng 4 (nhập tay): sửa AS03 hai lần → ghi đè MỘT bản ghi + log."""
    dang_nhap(client, "xa.hacthanh")
    client.post("/nhap-lieu", data={"thang": "4", "gt_AS03": "500"})
    client.post("/nhap-lieu", data={"thang": "4", "gt_AS03": "512"})

    db.expire_all()
    as03 = lay_gia_tri(db, "AS03", "HACTHANH", 4)
    assert as03.gia_tri == 512
    # Vẫn chỉ MỘT bản ghi cho (chỉ tiêu, đơn vị, kỳ)
    ct = db.query(ChiTieu).filter_by(ma="AS03").one()
    dv = db.query(DonVi).filter_by(ma="HACTHANH").one()
    so_ban_ghi = (
        db.query(GiaTriChiTieu)
        .filter_by(chi_tieu_id=ct.id, don_vi_id=dv.id, nam=2026, thang=4)
        .count()
    )
    assert so_ban_ghi == 1
    assert db.query(NhatKy).filter(NhatKy.hanh_dong == "sua_so_lieu").count() >= 1


def test_chuyen_vien_xa_khong_sua_duoc_xa_khac(client, db):
    """Gửi don_vi=NGASON nhưng tài khoản Hạc Thành → dữ liệu Nga Sơn không đổi."""
    dang_nhap(client, "xa.hacthanh")
    truoc = lay_gia_tri(db, "AS03", "NGASON", 4).gia_tri

    client.post(
        "/nhap-lieu", data={"thang": "4", "don_vi": "NGASON", "gt_AS03": "99999"}
    )

    db.expire_all()
    assert lay_gia_tri(db, "AS03", "NGASON", 4).gia_tri == truoc
    assert lay_gia_tri(db, "AS03", "HACTHANH", 4).gia_tri == 99999
