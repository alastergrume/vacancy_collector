from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request
from fastapi.responses import RedirectResponse, Response
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from database import get_session
from database.models import Vacancy
from enums import VacancyStatus, WorkFormat
from services.export_xlsx import build_xlsx
from web.security import require_user, verify_csrf
from web.templating import render

router = APIRouter(prefix="/vacancies", dependencies=[Depends(require_user)])
PAGE_SIZE = 50


@router.get("")
def list_vacancies(
    request: Request,
    status: str = Query(""),
    fmt: str = Query(""),
    q: str = Query(""),
    perm: bool = Query(False),
    page: int = Query(1, ge=1),
    session: Session = Depends(get_session),
):
    stmt = select(Vacancy)
    if status:
        stmt = stmt.where(Vacancy.status == VacancyStatus(status))
    else:
        stmt = stmt.where(Vacancy.status.notin_([VacancyStatus.HIDDEN, VacancyStatus.ARCHIVED]))
    if fmt:
        stmt = stmt.where(Vacancy.work_format == WorkFormat(fmt))
    if perm:
        stmt = stmt.where(Vacancy.area == "Пермь")
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(Vacancy.name.ilike(like), Vacancy.employer.ilike(like)))
    total = session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    items = session.scalars(
        stmt.order_by(Vacancy.published_at.desc()).offset((page - 1) * PAGE_SIZE).limit(PAGE_SIZE)
    ).all()
    pages = max((total + PAGE_SIZE - 1) // PAGE_SIZE, 1)
    filters = {"status": status, "fmt": fmt, "q": q, "perm": perm}
    return render(request, "vacancies.html", {
        "items": items, "total": total, "page": page, "pages": pages,
        "filters": filters, "formats": list(WorkFormat),
    })


@router.post("/{vacancy_id}/status")
def set_status(
    request: Request,
    vacancy_id: int,
    status: str = Form(...),
    csrf: str = Form(""),
    session: Session = Depends(get_session),
):
    verify_csrf(request, csrf)
    vacancy = session.get(Vacancy, vacancy_id)
    if vacancy is None:
        raise HTTPException(404, "Вакансия не найдена")
    vacancy.status = VacancyStatus(status)
    if vacancy.status == VacancyStatus.APPLIED and vacancy.applied_at is None:
        vacancy.applied_at = datetime.now(timezone.utc)
    session.commit()
    if request.headers.get("x-requested-with") == "fetch":
        return {"ok": True, "status": vacancy.status.value, "label": vacancy.status.label}
    return RedirectResponse(request.headers.get("referer") or "/vacancies", status_code=303)


@router.get("/export.xlsx")
def download_xlsx(session: Session = Depends(get_session)):
    content, _ = build_xlsx(session)
    return Response(
        content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=vacancies.xlsx"},
    )
