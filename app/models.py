"""Mô hình dữ liệu SQLAlchemy — xem Mục 6 CLAUDE.md."""

from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

# Các giá trị hợp lệ (dùng chuỗi thay vì Enum để đơn giản, dễ seed/truy vấn)
LOAI_DON_VI = ("xa", "phuong", "so_nganh", "tinh")
VUNG = ("do_thi", "dong_bang", "mien_nui")
TAN_SUAT = ("thang", "quy", "nam")
NGUON = ("he_thong", "nhap_tay")
VAI_TRO = ("quan_tri", "lanh_dao", "chuyen_vien_xa", "dai_bieu_hdnd")
# 3 lớp chia sẻ theo QĐ 2053/QĐ-UBND ngày 07/7/2026
MUC_CHIA_SE = ("chuyen_nganh", "dung_chung", "mo")
TRANG_THAI = ("dang_hieu_luc", "het_hieu_luc")


class DonVi(Base):
    """Đơn vị hành chính: xã/phường, sở ngành, tỉnh (lớp dữ liệu chủ).

    Trường chuẩn theo QĐ 2176/QĐ-UBND ngày 20/7/2026: ma_dinh_danh (mã định
    danh điện tử cơ quan theo QCVN 102:2016/BTTTT), ma_dvhc (mã đơn vị hành
    chính theo danh mục quốc gia), loai_dvhc (phân loại I/II/III — DGHC19).
    """

    __tablename__ = "don_vi"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ma: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    ma_dinh_danh: Mapped[str | None] = mapped_column(String(20), nullable=True)
    ma_dvhc: Mapped[str | None] = mapped_column(String(10), nullable=True)
    ten: Mapped[str] = mapped_column(String(200), nullable=False)
    loai: Mapped[str] = mapped_column(String(20), nullable=False)
    loai_dvhc: Mapped[str | None] = mapped_column(String(5), nullable=True)
    vung: Mapped[str | None] = mapped_column(String(20), nullable=True)
    trang_thai: Mapped[str] = mapped_column(
        String(20), nullable=False, default="dang_hieu_luc"
    )
    ngay_cap_nhat: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now
    )

    gia_tri: Mapped[list["GiaTriChiTieu"]] = relationship(back_populates="don_vi")


class LinhVuc(Base):
    """Lĩnh vực dữ liệu: DTC, TTHC, ASXH (lớp dữ liệu tham chiếu)."""

    __tablename__ = "linh_vuc"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ma: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    ten: Mapped[str] = mapped_column(String(200), nullable=False)
    trang_thai: Mapped[str] = mapped_column(
        String(20), nullable=False, default="dang_hieu_luc"
    )
    ngay_cap_nhat: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now
    )

    chi_tieu: Mapped[list["ChiTieu"]] = relationship(back_populates="linh_vuc")


class ChiTieu(Base):
    """Chỉ tiêu thống kê thuộc một lĩnh vực (lớp dữ liệu chủ).

    Trường chuẩn theo 2 quyết định của tỉnh: nguon_du_lieu (tên CSDL nguồn
    theo Danh mục QĐ 2053), muc_chia_se (3 lớp chia sẻ), cong_thuc (mô phỏng
    Formula của HTTT báo cáo tỉnh — chỉ tiêu dẫn xuất hệ thống tự tính),
    rang_buoc (mô phỏng Content.Rule — quy tắc kiểm tra dữ liệu khi nhập).
    """

    __tablename__ = "chi_tieu"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ma: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    ten: Mapped[str] = mapped_column(String(300), nullable=False)
    linh_vuc_id: Mapped[int] = mapped_column(ForeignKey("linh_vuc.id"), nullable=False)
    don_vi_tinh: Mapped[str] = mapped_column(String(50), nullable=False)
    tan_suat: Mapped[str] = mapped_column(String(10), nullable=False, default="thang")
    co_quan_chu_chi_tieu: Mapped[str] = mapped_column(String(200), nullable=False)
    nguon_du_lieu: Mapped[str] = mapped_column(String(300), default="")
    muc_chia_se: Mapped[str] = mapped_column(
        String(20), nullable=False, default="dung_chung"
    )
    cong_thuc: Mapped[str | None] = mapped_column(String(100), nullable=True)
    rang_buoc: Mapped[str | None] = mapped_column(String(200), nullable=True)
    dinh_nghia: Mapped[str] = mapped_column(Text, default="")
    cong_khai: Mapped[bool] = mapped_column(Boolean, default=False)
    trang_thai: Mapped[str] = mapped_column(
        String(20), nullable=False, default="dang_hieu_luc"
    )
    ngay_cap_nhat: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now
    )

    linh_vuc: Mapped["LinhVuc"] = relationship(back_populates="chi_tieu")


class GiaTriChiTieu(Base):
    """Giá trị một chỉ tiêu của một đơn vị trong một kỳ (năm/tháng).

    Ràng buộc UNIQUE thể hiện nguyên tắc "một số liệu chỉ có một bản ghi".
    """

    __tablename__ = "gia_tri_chi_tieu"
    __table_args__ = (
        UniqueConstraint(
            "chi_tieu_id", "don_vi_id", "nam", "thang", name="uq_mot_so_lieu"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chi_tieu_id: Mapped[int] = mapped_column(ForeignKey("chi_tieu.id"), nullable=False)
    don_vi_id: Mapped[int] = mapped_column(ForeignKey("don_vi.id"), nullable=False)
    nam: Mapped[int] = mapped_column(Integer, nullable=False)
    thang: Mapped[int] = mapped_column(Integer, nullable=False)
    gia_tri: Mapped[float] = mapped_column(Float, nullable=False)
    nguon: Mapped[str] = mapped_column(String(20), nullable=False, default="nhap_tay")
    nguoi_cap_nhat_id: Mapped[int | None] = mapped_column(
        ForeignKey("nguoi_dung.id"), nullable=True
    )
    thoi_diem_cap_nhat: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now
    )

    chi_tieu: Mapped["ChiTieu"] = relationship()
    don_vi: Mapped["DonVi"] = relationship(back_populates="gia_tri")


class MauBaoCao(Base):
    """Mẫu báo cáo (cấu trúc chi tiết đặt trong report_builder.py)."""

    __tablename__ = "mau_bao_cao"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ma: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    ten: Mapped[str] = mapped_column(String(300), nullable=False)
    linh_vuc_id: Mapped[int] = mapped_column(ForeignKey("linh_vuc.id"), nullable=False)
    mo_ta: Mapped[str] = mapped_column(Text, default="")


class NguoiDung(Base):
    """Người dùng hệ thống với 4 vai trò."""

    __tablename__ = "nguoi_dung"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ten_dang_nhap: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    mat_khau_hash: Mapped[str] = mapped_column(String(200), nullable=False)
    ho_ten: Mapped[str] = mapped_column(String(200), nullable=False)
    # Email công vụ dạng ten@thanhhoa.gov.vn (mô phỏng — nguồn chuẩn thực tế
    # là CSDL cán bộ, công chức, viên chức tỉnh Thanh Hóa)
    email: Mapped[str | None] = mapped_column(String(100), nullable=True)
    vai_tro: Mapped[str] = mapped_column(String(20), nullable=False)
    don_vi_id: Mapped[int | None] = mapped_column(
        ForeignKey("don_vi.id"), nullable=True
    )

    don_vi: Mapped["DonVi | None"] = relationship()


class NhatKy(Base):
    """Nhật ký hệ thống: đăng nhập, nhập/sửa số liệu, sinh báo cáo, hỏi AI.

    Chống sửa lén (tamper-evident): mỗi bản ghi mang hash SHA-256 khóa với
    hash của bản ghi liền trước — sửa/xóa lén bất kỳ dòng nào là toàn bộ
    chuỗi phía sau không khớp, nút "Kiểm chứng toàn vẹn" phát hiện ngay.
    """

    __tablename__ = "nhat_ky"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nguoi_dung_id: Mapped[int | None] = mapped_column(
        ForeignKey("nguoi_dung.id"), nullable=True
    )
    hanh_dong: Mapped[str] = mapped_column(String(50), nullable=False)
    chi_tiet: Mapped[str] = mapped_column(Text, default="")
    thoi_diem: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now
    )
    hash_truoc: Mapped[str | None] = mapped_column(String(64), nullable=True)
    hash_ban_ghi: Mapped[str | None] = mapped_column(String(64), nullable=True)


class KiemKeBaoCao(Base):
    """Kiểm kê chế độ báo cáo cấp xã đang phải thực hiện (phân hệ 8.8).

    Mỗi bản ghi = một loại báo cáo mà cơ quan cấp trên yêu cầu xã lập định
    kỳ — dùng để thống kê "gánh nặng báo cáo" và tìm báo cáo nghi trùng lặp.
    """

    __tablename__ = "kiem_ke_bao_cao"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ten_bao_cao: Mapped[str] = mapped_column(String(300), nullable=False)
    co_quan_yeu_cau: Mapped[str] = mapped_column(String(200), nullable=False)
    # Số kỳ phải nộp trong một năm quy ước theo tần suất: thang=12, quy=4,
    # 6_thang=2, nam=1, dot_xuat=6 (ước tính demo)
    tan_suat: Mapped[str] = mapped_column(String(20), nullable=False, default="thang")
    can_cu: Mapped[str] = mapped_column(String(300), default="")
    nguoi_khai_id: Mapped[int | None] = mapped_column(
        ForeignKey("nguoi_dung.id"), nullable=True
    )
    thoi_diem_khai: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now
    )


class NghiQuyetTheoDoi(Base):
    """Nghị quyết HĐND được theo dõi trên trang giám sát."""

    __tablename__ = "nghi_quyet_theo_doi"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    so_ky_hieu: Mapped[str] = mapped_column(String(100), nullable=False)
    trich_yeu: Mapped[str] = mapped_column(Text, nullable=False)
    chi_tieu_id: Mapped[int] = mapped_column(ForeignKey("chi_tieu.id"), nullable=False)
    gia_tri_muc_tieu: Mapped[float] = mapped_column(Float, nullable=False)
    han_hoan_thanh: Mapped[date] = mapped_column(Date, nullable=False)

    chi_tieu: Mapped["ChiTieu"] = relationship()
