"""Cấu hình ứng dụng — đọc từ file .env (pydantic-settings)."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Thư mục gốc dự án (chứa CLAUDE.md, app/, data/ ...)
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Biến môi trường của ứng dụng, xem .env.example."""

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # 1 = offline (mặc định cho demo), 0 = dùng Claude API
    offline: int = 1
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6"
    database_url: str = "sqlite:///data/onedata.db"
    secret_key: str = "doi-chuoi-nay-khi-chay-that"
    # Đường dẫn mô hình embedding tải sẵn (models/...). Để trống → dùng FTS5.
    embedding_model_path: str = ""

    # Tên phiên cookie và thời hạn (giây) — 8 giờ, đủ cho buổi demo
    session_cookie: str = "onedata_session"
    session_max_age: int = 8 * 60 * 60


settings = Settings()
