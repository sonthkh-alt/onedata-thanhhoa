"""Kết nối CSDL: engine, phiên làm việc và lớp Base cho models."""

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import BASE_DIR, settings


def _resolve_sqlite_url(url: str) -> str:
    """Đổi đường dẫn SQLite tương đối thành tuyệt đối theo thư mục gốc dự án.

    Nhờ đó chạy `uvicorn`/`pytest` từ bất kỳ thư mục nào cũng trỏ đúng file DB.
    """
    prefix = "sqlite:///"
    if url.startswith(prefix):
        raw_path = url[len(prefix) :]
        path = Path(raw_path)
        if not path.is_absolute():
            path = BASE_DIR / path
        path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{path.as_posix()}"
    return url


engine = create_engine(
    _resolve_sqlite_url(settings.database_url),
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    """Lớp cơ sở cho mọi model SQLAlchemy."""


def get_db():
    """Dependency FastAPI: cấp một phiên CSDL, tự đóng khi xong."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
