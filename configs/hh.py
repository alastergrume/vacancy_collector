from pydantic import Field
from pydantic_settings import SettingsConfigDict

from configs.base import EnvSettings


class HHSettings(EnvSettings):
    """Доступ к API hh.ru и общие правила фильтрации."""

    model_config = SettingsConfigDict(env_prefix="HH_")

    api_url: str = "https://api.hh.ru"
    # hh требует заголовок HH-User-Agent вида "AppName/1.0 (email@example.com)"
    user_agent: str = "VacancyCollector/1.0 (you@example.com)"
    # Токен приложения (обязателен: поиск вакансий в API hh требует авторизации приложения).
    # Генерируется один раз, смотреть в https://dev.hh.ru/admin. Срока жизни и refresh нет.
    app_token: str = ""

    @property
    def has_token(self) -> bool:
        return bool(self.app_token.strip())
    # Бережный режим: пауза между запросами и лимиты
    request_delay_sec: float = 1.5
    per_page: int = 100
    max_pages: int = 5
    timeout_sec: float = 20.0
    retries: int = 2
    # За сколько дней назад брать вакансии (1 = за вчера и сегодня)
    period_days: int = 1
    # Слова в названии вакансии, при которых она отбрасывается (через запятую)
    exclude_words: str = Field(
        default="senior,lead,тимлид,team lead,architect,архитектор,java,golang,go-разработчик,c#,.net,php,1с,1c,стажёр продаж"
    )

    @property
    def exclude_list(self) -> list[str]:
        return [w.strip().lower() for w in self.exclude_words.split(",") if w.strip()]
