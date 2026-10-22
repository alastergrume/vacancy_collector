"""Jinja2-шаблоны и общие переменные для всех страниц."""
from fastapi import Request
from fastapi.templating import Jinja2Templates

from configs import BASE_DIR, app_settings
from enums import VacancyStatus
from services.stats import to_local
from web.security import csrf_token, current_user

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
templates.env.filters["local"] = to_local
templates.env.globals["app_name"] = app_settings.name
templates.env.globals["statuses"] = list(VacancyStatus)


def render(request: Request, name: str, context: dict | None = None, status_code: int = 200):
    ctx = {"user": current_user(request), "csrf": csrf_token(request)}
    ctx.update(context or {})
    flash = request.session.pop("flash", None)
    if flash:
        ctx["flash"] = flash
    return templates.TemplateResponse(request, name, ctx, status_code=status_code)


def flash(request: Request, message: str, kind: str = "info") -> None:
    request.session["flash"] = {"message": message, "kind": kind}
