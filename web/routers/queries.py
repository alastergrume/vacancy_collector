from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_session
from database.models import SearchQuery
from schemas.app import SearchQueryIn
from services.default_queries import seed_default_queries
from web.security import require_user, verify_csrf
from web.templating import flash, render

router = APIRouter(prefix="/queries", dependencies=[Depends(require_user)])


def _form_to_schema(title, text, area, only_remote, experience, exclude_words, priority, is_active) -> SearchQueryIn:
    return SearchQueryIn(
        title=title, text=text, area=area, only_remote=bool(only_remote), experience=experience,
        exclude_words=exclude_words, priority=priority, is_active=bool(is_active),
    )


@router.get("")
def list_queries(request: Request, session: Session = Depends(get_session)):
    items = session.scalars(select(SearchQuery).order_by(SearchQuery.priority, SearchQuery.id)).all()
    return render(request, "queries.html", {"items": items})


@router.post("")
def save_query(
    request: Request,
    query_id: str = Form(""),
    title: str = Form(...),
    text: str = Form(...),
    area: int = Form(113),
    only_remote: str | None = Form(None),
    experience: str = Form("between1And3,between3And6"),
    exclude_words: str = Form(""),
    priority: int = Form(100),
    is_active: str | None = Form(None),
    csrf: str = Form(""),
    session: Session = Depends(get_session),
):
    verify_csrf(request, csrf)
    try:
        data = _form_to_schema(title, text, area, only_remote, experience, exclude_words, priority, is_active)
    except ValidationError as exc:
        flash(request, "Ошибка: " + "; ".join(e["msg"] for e in exc.errors()), "error")
        return RedirectResponse("/queries", status_code=303)
    if query_id.strip().isdigit():
        obj = session.get(SearchQuery, int(query_id))
        if obj is None:
            raise HTTPException(404)
    else:
        obj = SearchQuery()
        session.add(obj)
    for field, value in data.model_dump().items():
        setattr(obj, field, value)
    session.commit()
    flash(request, "Запрос сохранён", "success")
    return RedirectResponse("/queries", status_code=303)


@router.post("/{query_id}/delete")
def delete_query(request: Request, query_id: int, csrf: str = Form(""), session: Session = Depends(get_session)):
    verify_csrf(request, csrf)
    obj = session.get(SearchQuery, query_id)
    if obj:
        session.delete(obj)
        session.commit()
        flash(request, "Запрос удалён", "success")
    return RedirectResponse("/queries", status_code=303)


@router.post("/seed")
def seed(request: Request, csrf: str = Form(""), session: Session = Depends(get_session)):
    verify_csrf(request, csrf)
    added = seed_default_queries(session)
    flash(request, f"Добавлено стандартных запросов: {added}", "success")
    return RedirectResponse("/queries", status_code=303)
