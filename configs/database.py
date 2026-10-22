from pydantic_settings import SettingsConfigDict

from configs.base import EnvSettings


class DatabaseSettings(EnvSettings):
    """Подключение к PostgreSQL."""

    model_config = SettingsConfigDict(env_prefix="POSTGRES_")

    host: str = "localhost"
    port: int = 5432
    user: str = "collector"
    password: str = "collector"
    db: str = "vacancy_collector"
    echo: bool = False

    @property
    def url(self) -> str:
        return (
            f"postgresql+psycopg://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.db}"
        )
