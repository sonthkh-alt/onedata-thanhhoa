"""Kiểm thử phân hệ 8.8: kiểm kê báo cáo, phát hiện trùng lặp."""

from app.models import KiemKeBaoCao, NhatKy
from app.services.kiem_ke import do_giong_nhau, thong_ke_ganh_nang

MAT_KHAU = "Demo@2026"


def dang_nhap(client, ten_dang_nhap):
    resp = client.post(
        "/dang-nhap", data={"ten_dang_nhap": ten_dang_nhap, "mat_khau": MAT_KHAU}
    )
    assert resp.status_code == 303


def test_do_giong_nhau_bat_dung_cap_trung():
    """Tên khác 'tình hình'/'kết quả' nhưng cùng nội dung phải bắt được."""
    assert (
        do_giong_nhau(
            "Báo cáo tình hình giải ngân vốn đầu tư công",
            "Báo cáo kết quả giải ngân vốn đầu tư công",
        )
        >= 0.9
    )
    # Hai báo cáo khác hẳn nội dung thì không được coi là trùng
    assert (
        do_giong_nhau(
            "Báo cáo tình hình giải ngân vốn đầu tư công",
            "Báo cáo công tác tiếp công dân, giải quyết khiếu nại, tố cáo",
        )
        < 0.6
    )


def test_thong_ke_ganh_nang_va_cap_trung_cai_san(db):
    tk = thong_ke_ganh_nang(db)
    assert tk["so_loai"] >= 12
    assert tk["luot_mot_xa_nam"] > 50  # nhiều báo cáo tháng/quý cộng dồn
    assert tk["luot_toan_tinh_nam"] == tk["luot_mot_xa_nam"] * 166
    # 3 cặp nghi trùng đã cài sẵn trong seed
    assert len(tk["cap_trung"]) >= 3


def test_trang_kiem_ke_hien_thi(client):
    dang_nhap(client, "lanhdao")
    resp = client.get("/kiem-ke")
    assert resp.status_code == 200
    assert "nghi trùng lặp" in resp.text
    assert "166" in resp.text


def test_khai_bao_bao_cao_moi_va_log(client, db):
    dang_nhap(client, "lanhdao")
    truoc = db.query(KiemKeBaoCao).count()
    resp = client.post(
        "/kiem-ke",
        data={
            "ten_bao_cao": "Báo cáo thử nghiệm khai báo",
            "co_quan_yeu_cau": "Sở Demo",
            "tan_suat": "quy",
            "can_cu": "Kiểm thử tự động",
        },
    )
    assert resp.status_code == 303
    assert db.query(KiemKeBaoCao).count() == truoc + 1
    assert db.query(NhatKy).filter(NhatKy.hanh_dong == "khai_bao_kiem_ke").count() >= 1
    # Dọn lại để không ảnh hưởng thống kê của test khác
    ban_ghi = (
        db.query(KiemKeBaoCao)
        .filter_by(ten_bao_cao="Báo cáo thử nghiệm khai báo")
        .one()
    )
    db.delete(ban_ghi)
    db.commit()


def test_khai_bao_can_quyen_lanh_dao(client):
    dang_nhap(client, "daibieu")
    resp = client.post(
        "/kiem-ke",
        data={"ten_bao_cao": "X", "co_quan_yeu_cau": "Y", "tan_suat": "thang"},
    )
    assert resp.status_code == 403
    # Nhưng đại biểu vẫn XEM được bản kiểm kê
    assert client.get("/kiem-ke").status_code == 200


def test_hoi_dap_qua_lien_ket_get(client):
    """Hỏi đáp qua GET ?cau_hoi= (phục vụ chia sẻ liên kết)."""
    dang_nhap(client, "lanhdao")
    resp = client.get(
        "/hoi-dap",
        params={"cau_hoi": "Xếp hạng tỷ lệ giải ngân của các xã trong tháng 7"},
    )
    assert resp.status_code == 200
    assert "v_so_lieu" in resp.text
