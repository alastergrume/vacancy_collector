"""Задачи Celery: сбор вакансий и выгрузка на Google Диск."""
import logging

from configs import celery_settings
from database import session_scope
from database.models import GoogleCredential
from enums import RunTrigger
from services.collector import run_collect
from services.google_drive import export_to_drive
from tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="tasks.collect.collect_vacancies")
def collect_vacancies(trigger: str = "schedule") -> dict:
    with session_scope() as session:
        run = run_collect(session, RunTrigger(trigger))
        result = {
            "run_id": run.id,
            "status": run.status.value,
            "new": run.new_count,
            "updated": run.updated_count,
            "error": run.error,
        }
        drive_connected = session.query(GoogleCredential.id).first() is not None
    if celery_settings.export_after_collect and drive_connected:
        export_vacancies_to_drive.delay()
    logger.info("Сбор завершён: %s", result)
    return result


@celery_app.task(name="tasks.collect.export_to_drive")
def export_vacancies_to_drive() -> dict:
    with session_scope() as session:
        export = export_to_drive(session)
        return {"status": export.status.value, "rows": export.rows, "error": export.error}
