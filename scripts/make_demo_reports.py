"""Sinh sẵn một số báo cáo mẫu ra outputs/ để mở nhanh khi trình diễn.

Chạy:  python scripts/make_demo_reports.py
(cần chạy `python scripts/seed.py` trước để có CSDL)
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db import SessionLocal
from app.models import DonVi
from app.services import report_builder

THANG_DEMO = 7
CAC_XA_MAU = ["CACSON", "NGASON", "HACTHANH"]  # điểm nóng, khá, thiếu số liệu


def main() -> None:
    db = SessionLocal()
    try:
        bat_dau = time.perf_counter()
        ds_file: list[Path] = []
        for ma_xa in CAC_XA_MAU:
            dv = db.query(DonVi).filter_by(ma=ma_xa).one()
            ds_file.append(report_builder.tao_bao_cao_giai_ngan(db, dv, THANG_DEMO))
            ds_file.append(report_builder.tao_bao_cao_tthc(db, dv, THANG_DEMO))
        thoi_gian = time.perf_counter() - bat_dau
    finally:
        db.close()

    print(f"Đã sinh {len(ds_file)} báo cáo mẫu trong {thoi_gian:.2f} giây:")
    for f in ds_file:
        print(f"  - {f}")
    print("Mở file bất kỳ bằng Word/LibreOffice để xem thể thức NĐ 30/2020/NĐ-CP.")


if __name__ == "__main__":
    main()
