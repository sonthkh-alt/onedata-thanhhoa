"""Kiểm thử seed: đủ bản ghi, ràng buộc UNIQUE, view chỉ đọc."""

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.models import (
    ChiTieu,
    DonVi,
    GiaTriChiTieu,
    LinhVuc,
    NghiQuyetTheoDoi,
    NguoiDung,
)


def test_du_don_vi(db):
    """15 xã/phường + 5 sở ngành + 1 tỉnh."""
    assert db.query(DonVi).filter(DonVi.loai.in_(["xa", "phuong"])).count() == 15
    assert db.query(DonVi).filter(DonVi.loai == "so_nganh").count() == 5
    assert db.query(DonVi).filter(DonVi.loai == "tinh").count() == 1


def test_truong_chuan_tinh_cua_don_vi(db):
    """Mọi đơn vị có mã định danh QCVN 102:2016/BTTTT; xã có mã ĐVHC."""
    for dv in db.query(DonVi).all():
        assert dv.ma_dinh_danh and dv.ma_dinh_danh.endswith(".H56")
        assert dv.trang_thai == "dang_hieu_luc"
    for dv in db.query(DonVi).filter(DonVi.loai.in_(["xa", "phuong"])).all():
        assert dv.ma_dvhc and len(dv.ma_dvhc) == 5
        assert dv.loai_dvhc in {"I", "II", "III"}


def test_truong_chuan_tinh_cua_chi_tieu(db):
    """Chỉ tiêu có nguồn CSDL, mức chia sẻ; chỉ tiêu dẫn xuất có công thức."""
    for ct in db.query(ChiTieu).all():
        assert ct.nguon_du_lieu
        assert ct.muc_chia_se in {"chuyen_nganh", "dung_chung", "mo"}
        if ct.cong_khai:
            assert ct.muc_chia_se == "mo"
    dan_xuat = {
        ct.ma: ct.cong_thuc
        for ct in db.query(ChiTieu).filter(ChiTieu.cong_thuc.isnot(None))
    }
    assert dan_xuat == {
        "DTC03": "DTC02/DTC01*100",
        "TTHC04": "TTHC02/TTHC01*100",
        "TTHC06": "TTHC05/TTHC01*100",
    }


def test_co_quan_chu_chi_tieu_dung_danh_muc(db):
    """Cơ quan chủ chỉ tiêu bám Danh mục QĐ 2053/QĐ-UBND."""
    map_cq = {ct.ma: ct.co_quan_chu_chi_tieu for ct in db.query(ChiTieu).all()}
    assert map_cq["DTC01"] == "Sở Tài chính"
    assert map_cq["TTHC01"] == "Trung tâm Phục vụ hành chính công tỉnh"
    assert map_cq["AS01"] == "Sở Nông nghiệp và Môi trường"
    assert map_cq["AS03"] == "Sở Nội vụ"


def test_du_ba_vung(db):
    """Các xã được phân bổ đủ 3 vùng."""
    vung = {
        v
        for (v,) in db.query(DonVi.vung)
        .filter(DonVi.loai.in_(["xa", "phuong"]))
        .distinct()
    }
    assert vung == {"do_thi", "dong_bang", "mien_nui"}


def test_du_danh_muc(db):
    assert db.query(LinhVuc).count() == 3
    assert db.query(ChiTieu).count() == 16
    assert db.query(NguoiDung).count() == 4
    assert db.query(NghiQuyetTheoDoi).count() >= 3


def test_du_gia_tri_va_o_trong_demo(db):
    """Đủ giá trị 7 tháng, trừ các ô cố ý để trống phục vụ kịch bản demo."""
    tong = db.query(GiaTriChiTieu).count()
    assert tong == 15 * 16 * 7 - 6  # 6 ô để trống tháng 7

    # Phường Hạc Thành còn thiếu DTC02 tháng 7 (sẽ nhập trong demo)
    hac_thanh = db.query(DonVi).filter(DonVi.ma == "HACTHANH").one()
    dtc02 = db.query(ChiTieu).filter(ChiTieu.ma == "DTC02").one()
    thieu = (
        db.query(GiaTriChiTieu)
        .filter_by(don_vi_id=hac_thanh.id, chi_tieu_id=dtc02.id, nam=2026, thang=7)
        .first()
    )
    assert thieu is None


def test_diem_nong_giai_ngan_thang_7(db):
    """Có ít nhất 2 xã tỷ lệ giải ngân tháng 7 dưới 30% (điểm nóng demo)."""
    dtc03 = db.query(ChiTieu).filter(ChiTieu.ma == "DTC03").one()
    so_xa_thap = (
        db.query(GiaTriChiTieu)
        .filter_by(chi_tieu_id=dtc03.id, nam=2026, thang=7)
        .filter(GiaTriChiTieu.gia_tri < 30)
        .count()
    )
    assert so_xa_thap >= 2


def test_ty_le_trong_khoang_0_100(db):
    """Mọi chỉ tiêu đơn vị tính % phải nằm trong [0; 100]."""
    ket_qua = db.execute(text("""
            SELECT COUNT(*) FROM gia_tri_chi_tieu g
            JOIN chi_tieu c ON c.id = g.chi_tieu_id
            WHERE c.don_vi_tinh = '%' AND (g.gia_tri < 0 OR g.gia_tri > 100)
            """)).scalar()
    assert ket_qua == 0


def test_rang_buoc_unique_mot_so_lieu(db):
    """Không thể có 2 bản ghi cùng (chỉ tiêu, đơn vị, năm, tháng)."""
    mau = db.query(GiaTriChiTieu).first()
    trung = GiaTriChiTieu(
        chi_tieu_id=mau.chi_tieu_id,
        don_vi_id=mau.don_vi_id,
        nam=mau.nam,
        thang=mau.thang,
        gia_tri=999.0,
        nguon="nhap_tay",
    )
    db.add(trung)
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


def test_view_cho_ai(db):
    """3 view chỉ đọc cho AI truy vấn được và join đủ tên."""
    dong = db.execute(
        text("SELECT ten_don_vi, ten_chi_tieu, gia_tri FROM v_so_lieu LIMIT 5")
    ).fetchall()
    assert len(dong) == 5
    assert db.execute(text("SELECT COUNT(*) FROM v_don_vi")).scalar() == 21
    assert db.execute(text("SELECT COUNT(*) FROM v_chi_tieu")).scalar() == 16
    # View số liệu có cột kỳ chuẩn YYYYMM
    ky = db.execute(text("SELECT DISTINCT ky FROM v_so_lieu LIMIT 1")).scalar()
    assert 202601 <= ky <= 202607
