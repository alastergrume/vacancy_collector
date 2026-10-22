"""Сбор вакансий: выполняет активные поисковые запросы и сохраняет результат в базу."""
import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from configs import app_settings, hh_settings
from database.models import CollectRun, SearchQuery, Vacancy
from enums import RunStatus, RunTrigger, VacancyStatus
from schemas.hh import HHVacancyItem
from services.filters import detect_work_format, passes
from services.hh_client import HHApiError, HHClient

logger = logging.getLogger(__name__)

# Статусы, которые сборщик не перезаписывает (их ставит человек)
PROTECTED_STATUSES = {
    VacancyStatus.SUITABLE,
    VacancyStatus.APPLIED,
    VacancyStatus.INTERVIEW,
    VacancyStatus.REJECTED,
    VacancyStatus.HIDDEN,
}


def period_start(days: int, tz: str = app_settings.timezone) -> datetime:
    """Начало дня N дней назад в часовом поясе пользователя (1 = со вчерашнего утра)."""
    zone = ZoneInfo(tz)
    today = datetime.now(zone).replace(hour=0, minute=0, second=0, microsecond=0)
    return today - timedelta(days=days)


def _apply_item(vacancy: Vacancy, item: HHVacancyItem) -> None:
    vacancy.name = item.name[:512]
    vacancy.employer = (item.employer.name if item.employer else None)
    vacancy.area = item.area.name if item.area else None
    if item.salary:
        vacancy.salary_from = item.salary.from_
        vacancy.salary_to = item.salary.to
        vacancy.salary_currency = item.salary.currency
        vacancy.salary_gross = item.salary.gross
    vacancy.experience = item.experience.name if item.experience else None
    vacancy.schedule = item.schedule.name if item.schedule else None
    vacancy.work_format = detect_work_format(item)
    vacancy.requirement = item.snippet.requirement if item.snippet else None
    vacancy.responsibility = item.snippet.responsibility if item.snippet else None
    vacancy.url = item.alternate_url
    vacancy.published_at = item.published_at
    vacancy.archived = item.archived
    if item.archived and vacancy.status not in PROTECTED_STATUSES:
        vacancy.status = VacancyStatus.ARCHIVED


def save_item(session: Session, item: HHVacancyItem, query: SearchQuery, run: CollectRun) -> bool:
    """Создаёт или обновляет вакансию. Возвращает True, если вакансия новая."""
    vacancy = session.scalar(select(Vacancy).where(Vacancy.hh_id == item.id))
    is_new = vacancy is None
    if is_new:
        vacancy = Vacancy(hh_id=item.id, status=VacancyStatus.NEW,
                          search_query_id=query.id, first_run_id=run.id)
        session.add(vacancy)
    _apply_item(vacancy, item)
    return is_new


def run_collect(session: Session, trigger: RunTrigger = RunTrigger.SCHEDULE,
                client: HHClient | None = None) -> CollectRun:
    run = CollectRun(trigger=trigger, status=RunStatus.RUNNING)
    session.add(run)
    session.commit()

    queries = session.scalars(
        select(SearchQuery).where(SearchQuery.is_active.is_(True)).order_by(SearchQuery.priority, SearchQuery.id)
    ).all()
    run.queries_total = len(queries)
    date_from = period_start(hh_settings.period_days)
    seen: set[str] = set()
    own_client = client is None
    client = client or HHClient()

    try:
        for query in queries:
            words = hh_settings.exclude_list + query.exclude_list
            for page in client.search_all(query.text, query.area, query.experience_list, date_from):
                for item in page.items:
                    if item.id in seen:
                        continue
                    seen.add(item.id)
                    run.found_total += 1
                    ok, reason = passes(item, words, query.only_remote)
                    if not ok:
                        run.filtered_out += 1
                        logger.debug("Отброшена %s (%s): %s", item.id, item.name, reason)
                        continue
                    if save_item(session, item, query, run):
                        run.new_count += 1
                    else:
                        run.updated_count += 1
                session.commit()
        run.status = RunStatus.SUCCESS
    except HHApiError as exc:
        session.rollback()
        run.status = RunStatus.FAILED
        run.error = str(exc)
        logger.warning("Сбор остановлен: %s", exc)
    except Exception as exc:  # noqa: BLE001 — фиксируем любую ошибку в статистике
        session.rollback()
        run.status = RunStatus.FAILED
        run.error = f"{type(exc).__name__}: {exc}"
        logger.exception("Ошибка сбора")
    finally:
        run.requests_made = client.requests_made
        run.finished_at = datetime.now(ZoneInfo("UTC"))
        session.add(run)
        session.commit()
        if own_client:
            client.close()
    return run
