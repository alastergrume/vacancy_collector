from pydantic_settings import SettingsConfigDict

from configs.base import EnvSettings


class CelerySettings(EnvSettings):
    """Celery и брокер Redis. Расписание сбора — в часовом поясе APP_TIMEZONE."""

    model_config = SettingsConfigDict(env_prefix="CELERY_")

    broker_url: str = "redis://localhost:6379/0"
    result_backend: str = "redis://localhost:6379/1"
    # Ежедневный сбор: часы и минуты (по умолчанию 10:00)
    collect_hour: int = 10
    collect_minute: int = 0
    # Экспорт на Google Диск после каждого сбора
    export_after_collect: bool = True
