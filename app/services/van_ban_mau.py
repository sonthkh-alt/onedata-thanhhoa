"""Sinh nội dung văn bản mô phỏng (báo cáo tháng của xã) chứa số liệu trong
câu văn — đầu vào cho Lớp 1 và kênh 2 "máy trích xuất – người xác nhận".

Dùng chung cho scripts/seed.py (tạo bản ghi Lớp 1) và
scripts/make_sample_docs.py (xuất file .docx bằng nd30).
Định dạng số kiểu Việt Nam: 45.000 (nghìn), 27,0% (thập phân).
"""


def dinh_dang_so(gia_tri: float, thap_phan: int = 0) -> str:
    """45.000 hoặc 745,2 — dấu chấm ngăn nghìn, dấu phẩy thập phân."""
    chuoi = f"{gia_tri:,.{thap_phan}f}"
    return chuoi.replace(",", "_").replace(".", ",").replace("_", ".")


def dinh_dang_phan_tram(gia_tri: float) -> str:
    """27,0% — luôn một chữ số thập phân."""
    return f"{dinh_dang_so(gia_tri, 1)}%"


def trich_yeu_bao_cao(thang: int, nam: int) -> str:
    return (
        f"Tình hình kinh tế - xã hội tháng {thang} năm {nam} "
        "(đầu tư công, thủ tục hành chính, an sinh xã hội)"
    )


def noi_dung_bao_cao(ten_don_vi: str, thang: int, nam: int, so: dict) -> list[str]:
    """Các đoạn văn của báo cáo tháng, số liệu nằm NGUYÊN VĂN trong câu.

    `so` = map mã chỉ tiêu → giá trị (16 chỉ tiêu của kỳ đó).
    """
    doan_1 = (
        f"Thực hiện chế độ báo cáo định kỳ, UBND {ten_don_vi} báo cáo tình hình "
        f"kinh tế - xã hội tháng {thang} năm {nam} trên địa bàn như sau."
    )
    doan_2 = (
        f"Về giải ngân vốn đầu tư công: kế hoạch vốn giao năm {nam} là "
        f"{dinh_dang_so(so['DTC01'])} triệu đồng; giải ngân lũy kế đến hết "
        f"tháng {thang} đạt {dinh_dang_so(so['DTC02'])} triệu đồng; tỷ lệ giải "
        f"ngân đạt {dinh_dang_phan_tram(so['DTC03'])}. Toàn địa bàn có "
        f"{dinh_dang_so(so['DTC04'])} dự án đang triển khai, trong đó có "
        f"{dinh_dang_so(so['DTC05'])} dự án chậm tiến độ."
    )
    doan_3 = (
        f"Về giải quyết thủ tục hành chính: trong tháng đã tiếp nhận "
        f"{dinh_dang_so(so['TTHC01'])} hồ sơ; giải quyết đúng hạn "
        f"{dinh_dang_so(so['TTHC02'])} hồ sơ; quá hạn "
        f"{dinh_dang_so(so['TTHC03'])} hồ sơ; tỷ lệ đúng hạn đạt "
        f"{dinh_dang_phan_tram(so['TTHC04'])}. Số hồ sơ nộp trực tuyến là "
        f"{dinh_dang_so(so['TTHC05'])} hồ sơ; tỷ lệ hồ sơ trực tuyến đạt "
        f"{dinh_dang_phan_tram(so['TTHC06'])}."
    )
    doan_4 = (
        f"Về an sinh xã hội: toàn địa bàn còn {dinh_dang_so(so['AS01'])} hộ "
        f"nghèo và {dinh_dang_so(so['AS02'])} hộ cận nghèo; có "
        f"{dinh_dang_so(so['AS03'])} đối tượng bảo trợ xã hội đang hưởng trợ "
        f"cấp hằng tháng; kinh phí chi trả tháng là "
        f"{dinh_dang_so(so['AS04'], 1)} triệu đồng; tỷ lệ chi trả không dùng "
        f"tiền mặt đạt {dinh_dang_phan_tram(so['AS05'])}."
    )
    doan_5 = (
        f"UBND {ten_don_vi} tiếp tục chỉ đạo đẩy nhanh tiến độ giải ngân, "
        "nâng cao chất lượng giải quyết thủ tục hành chính và bảo đảm chi trả "
        "an sinh xã hội đầy đủ, kịp thời, đúng đối tượng./."
    )
    return [doan_1, doan_2, doan_3, doan_4, doan_5]
