from pydantic_settings import SettingsConfigDict

from configs.base import EnvSettings


class AuthSettings(EnvSettings):
    """Вход в веб-интерфейс. Пароль храним только хешем (scripts/hash_password.py)."""

    model_config = SettingsConfigDict(env_prefix="AUTH_")

    secret_key: str = "change-me"
    admin_username: str = "admin"
    admin_password_hash: str = ""
    session_max_age_sec: int = 60 * 60 * 24 * 7
    # https_only=True, когда приложение работает за HTTPS
    cookie_secure: bool = False
    # Защита от перебора: столько неудачных входов с одного IP за окно
    max_failed_logins: int = 5
    lockout_minutes: int = 15
