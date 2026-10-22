"""Статистика для дашборда."""
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import Date, cast, func, select
from sqlalchemy.orm import Session

from configs import app_settings
from database.models import CollectRun, DriveExport, GoogleCredential, Vacancy
from enums import VacancyStatus, WorkFormat
from schemas.app import DayCount, RunOut, StatsOut


def collect_stats(session: Session) -> StatsOut:
    tz = app_settings.timezone
    total = session.scalar(select(func.count(Vacancy.id))) or 0
    by_status = {s.value: 0 for s in VacancyStatus}
    for status, cnt in session.execute(select(Vacancy.status, func.count()).group_by(Vacancy.status)):
        by_status[status.value] = cnt

    today = datetime.now(ZoneInfo(tz)).date()
    start = today - timedelta(days=6)
    local_day = cast(func.timezone(tz, Vacancy.created_at), Date)
    rows = dict(
        session.execute(
            select(local_day, func.count()).where(local_day >= start).group_by(local_day)
        ).all()
    )
    days = [DayCount(day=start + timedelta(days=i), count=rows.get(start + timedelta(days=i), 0)) for i in range(7)]

    perm_total = session.scalar(select(func.count(Vacancy.id)).where(Vacancy.area == "Пермь")) or 0
    remote_total = session.scalar(
        select(func.count(Vacancy.id)).where(Vacancy.work_format == WorkFormat.REMOTE)
    ) or 0
    last_run = session.scalar(select(CollectRun).order_by(CollectRun.started_at.desc()).limit(1))
    last_export = session.scalar(select(DriveExport).order_by(DriveExport.created_at.desc()).limit(1))
    connected = session.scalar(select(func.count(GoogleCredential.id))) or 0

    return StatsOut(
        total=total,
        by_status=by_status,
        new_last_7_days=days,
        perm_total=perm_total,
        remote_total=remote_total,
        last_run=RunOut.model_validate(last_run) if last_run else None,
        drive_connected=connected > 0,
        last_export_at=last_export.created_at if last_export else None,
        last_export_status=last_export.status.value if last_export else None,
    )


def to_local(dt: datetime | None) -> str:
    if not dt:
        return "—"
    return dt.astimezone(ZoneInfo(app_settings.timezone)).strftime("%d.%m.%Y %H:%M")


def today_local() -> date:
    return datetime.now(ZoneInfo(app_settings.timezone)).date()
