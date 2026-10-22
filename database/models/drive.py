from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base, TimestampMixin, pg_enum
from enums import ExportStatus


class GoogleCredential(TimestampMixin, Base):
    """OAuth-токен Google Диска (одна запись на приложение)."""

    __tablename__ = "google_credentials"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    account_email: Mapped[str | None] = mapped_column(String(256))
    # JSON авторизации google.oauth2.credentials.Credentials (с refresh_token)
    token_json: Mapped[str] = mapped_column(Text)
    # ID выгружаемого файла на Диске, чтобы обновлять его, а не плодить копии
    export_file_id: Mapped[str | None] = mapped_column(String(128))


class DriveExport(Base):
    """История выгрузок на Google Диск."""

    __tablename__ = "drive_exports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    status: Mapped[ExportStatus] = mapped_column(pg_enum(ExportStatus, "export_status"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    rows: Mapped[int] = mapped_column(Integer, default=0)
    file_url: Mapped[str | None] = mapped_column(String(512))
    error: Mapped[str | None] = mapped_column(Text)
