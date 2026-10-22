"""Все настройки приложения. Импортируйте отсюда: from configs import db_settings."""
from configs.app import AppSettings
from configs.auth import AuthSettings
from configs.base import BASE_DIR, ENV_FILE, EnvSettings
from configs.celery import CelerySettings
from configs.database import DatabaseSettings
from configs.google_drive import GoogleDriveSettings
from configs.hh import HHSettings

app_settings = AppSettings()
auth_settings = AuthSettings()
db_settings = DatabaseSettings()
celery_settings = CelerySettings()
hh_settings = HHSettings()
gdrive_settings = GoogleDriveSettings()

__all__ = [
    "BASE_DIR",
    "ENV_FILE",
    "EnvSettings",
    "AppSettings",
    "AuthSettings",
    "DatabaseSettings",
    "CelerySettings",
    "HHSettings",
    "GoogleDriveSettings",
    "app_settings",
    "auth_settings",
    "db_settings",
    "celery_settings",
    "hh_settings",
    "gdrive_settings",
]
