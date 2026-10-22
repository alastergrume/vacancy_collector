from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from configs import hh_settings
from database import get_session
from database.models import CollectRun, DriveExport
from services.stats import collect_stats
from tasks.collect import collect_vacancies
from web.security import require_user, verify_csrf
from web.templating import flash, render

router = APIRouter(dependencies=[Depends(require_user)])


@router.get("/")
def dashboard(request: Request, session: Session = Depends(get_session)):
    stats = collect_stats(session)
    runs = session.scalars(select(CollectRun).order_by(CollectRun.started_at.desc()).limit(10)).all()
    exports = session.scalars(select(DriveExport).order_by(DriveExport.created_at.desc()).limit(5)).all()
    days = [{"day": d.day.strftime("%d.%m"), "count": d.count} for d in stats.new_last_7_days]
    return render(request, "dashboard.html", {"stats": stats, "runs": runs, "exports": exports, "days": days,
                                              "hh_token_missing": not hh_settings.has_token})


@router.get("/runs")
def runs_page(request: Request, session: Session = Depends(get_session)):
    runs = session.scalars(select(CollectRun).order_by(CollectRun.started_at.desc()).limit(100)).all()
    return render(request, "runs.html", {"runs": runs})


@router.post("/collect")
def start_collect(request: Request, csrf: str = Form("")):
    verify_csrf(request, csrf)
    collect_vacancies.delay(trigger="manual")
    flash(request, "Сбор запущен. Обновите страницу через минуту.", "success")
    return RedirectResponse("/", status_code=303)
