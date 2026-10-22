"""Приложение Celery: брокер Redis, ежедневный сбор по расписанию (beat)."""
from celery import Celery
from celery.schedules import crontab

from configs import app_settings, celery_settings

celery_app = Celery(
    "vacancy_collector",
    broker=celery_settings.broker_url,
    backend=celery_settings.result_backend,
    include=["tasks.collect"],
)

celery_app.conf.update(
    timezone=app_settings.timezone,
    enable_utc=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_time_limit=60 * 30,
    result_expires=60 * 60 * 24,
    beat_schedule={
        "daily-collect": {
            "task": "tasks.collect.collect_vacancies",
            "schedule": crontab(hour=celery_settings.collect_hour, minute=celery_settings.collect_minute),
            "kwargs": {"trigger": "schedule"},
        },
    },
)
