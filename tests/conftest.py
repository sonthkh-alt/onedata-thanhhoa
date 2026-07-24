"""Cấu hình pytest: CSDL tạm + TestClient dùng chung cho cả phiên kiểm thử."""

import os
import sys
import tempfile
from pathlib import Path

import pytest

# Trỏ DATABASE_URL sang file tạm TRƯỚC KHI import app (config đọc env lúc import)
_TMP_DIR = tempfile.mkdtemp(prefix="onedata_test_")
os.environ["DATABASE_URL"] = f"sqlite:///{Path(_TMP_DIR).as_posix()}/test_onedata.db"

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient  # noqa: E402

from app.db import SessionLocal  # noqa: E402
from app.main import app  # noqa: E402
from scripts.seed import reset_db, seed_all  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def csdl_demo():
    """Tạo CSDL mô phỏng một lần cho toàn bộ phiên kiểm thử."""
    reset_db()
    db = SessionLocal()
    try:
        thong_ke = seed_all(db)
    finally:
        db.close()
    return thong_ke


@pytest.fixture()
def db():
    """Phiên CSDL cho từng test."""
    phien = SessionLocal()
    try:
        yield phien
    finally:
        phien.close()


@pytest.fixture()
def client():
    """TestClient FastAPI (không tự theo redirect để kiểm tra mã trạng thái)."""
    with TestClient(app, follow_redirects=False) as c:
        yield c
