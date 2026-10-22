from pydantic_settings import SettingsConfigDict

from configs.base import EnvSettings


class AppSettings(EnvSettings):
    """Общие настройки веб-приложения."""

    model_config = SettingsConfigDict(env_prefix="APP_")

    name: str = "Vacancy Collector"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    # Внешний адрес приложения: нужен для OAuth-редиректа Google
    public_url: str = "http://localhost:8000"
    timezone: str = "Asia/Yekaterinburg"
