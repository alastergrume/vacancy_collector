"""Клиент API hh.ru с бережным режимом: пауза между запросами, повторы, остановка на 403."""
import logging
import time
from datetime import datetime

import httpx

from configs import HHSettings, hh_settings
from schemas.hh import HHSearchResponse

logger = logging.getLogger(__name__)


class HHApiError(Exception):
    """Ошибка API hh, после которой продолжать сбор нельзя (403, неверный запрос)."""


class HHClient:
    def __init__(self, settings: HHSettings = hh_settings, transport: httpx.BaseTransport | None = None):
        self.settings = settings
        headers = {
            "HH-User-Agent": settings.user_agent,
            "User-Agent": settings.user_agent,
            "Accept": "application/json",
        }
        if settings.has_token:
            headers["Authorization"] = f"Bearer {settings.app_token.strip()}"
        self._client = httpx.Client(
            base_url=settings.api_url,
            headers=headers,
            timeout=settings.timeout_sec,
            transport=transport,
        )
        self._last_request_at = 0.0
        self.requests_made = 0

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "HHClient":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def _pause(self) -> None:
        wait = self.settings.request_delay_sec - (time.monotonic() - self._last_request_at)
        if wait > 0:
            time.sleep(wait)

    def _get(self, path: str, params: list[tuple[str, str | int]]) -> dict:
        if not self.settings.has_token:
            raise HHApiError(
                "Не задан HH_APP_TOKEN: поиск вакансий в API hh требует токен приложения. "
                "Получите его один раз в https://dev.hh.ru/admin и укажите в configs/.env"
            )
        attempt = 0
        while True:
            self._pause()
            self._last_request_at = time.monotonic()
            self.requests_made += 1
            try:
                resp = self._client.get(path, params=params)
            except httpx.HTTPError as exc:
                if attempt >= self.settings.retries:
                    raise HHApiError(f"Сеть недоступна: {exc}") from exc
                attempt += 1
                time.sleep(2 ** attempt)
                continue

            if resp.status_code == 200:
                return resp.json()
            if resp.status_code == 429 or resp.status_code >= 500:
                if attempt >= self.settings.retries:
                    raise HHApiError(f"hh ответил {resp.status_code} после {attempt + 1} попыток")
                attempt += 1
                retry_after = resp.headers.get("Retry-After")
                time.sleep(float(retry_after) if retry_after and retry_after.isdigit() else 5 * attempt)
                continue
            # 400/401/403/404: повтор не поможет — останавливаемся, чтобы не получить бан
            hint = ""
            if resp.status_code in (401, 403):
                hint = (" — токен приложения недействителен или отозван (например, выпущен новый). "
                        "Возьмите актуальный в https://dev.hh.ru/admin и обновите HH_APP_TOKEN")
            raise HHApiError(f"hh ответил {resp.status_code}{hint}: {resp.text[:300]}")

    def search(
        self,
        text: str,
        area: int,
        experience: list[str],
        date_from: datetime,
        page: int = 0,
    ) -> HHSearchResponse:
        params: list[tuple[str, str | int]] = [
            ("text", text),
            ("area", area),
            ("per_page", self.settings.per_page),
            ("page", page),
            ("order_by", "publication_time"),
            ("date_from", date_from.isoformat(timespec="seconds")),
        ]
        params += [("experience", e) for e in experience]
        data = self._get("/vacancies", params)
        return HHSearchResponse.model_validate(data)

    def search_all(self, text: str, area: int, experience: list[str], date_from: datetime):
        """Все страницы выдачи, но не больше max_pages."""
        page = 0
        while page < self.settings.max_pages:
            result = self.search(text, area, experience, date_from, page)
            yield result
            page += 1
            if page >= result.pages:
                break
