"""Базовый класс настроек: все конфиги читают configs/.env."""
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

CONFIGS_DIR = Path(__file__).resolve().parent
BASE_DIR = CONFIGS_DIR.parent
ENV_FILE = CONFIGS_DIR / ".env"


class EnvSettings(BaseSettings):
    """Общий родитель: файл .env, кодировка, лишние переменные игнорируются."""

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )
