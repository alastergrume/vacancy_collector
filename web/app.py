"""Веб-приложение FastAPI: статистика, вакансии, запросы, Google Диск."""
import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from configs import BASE_DIR, app_settings, auth_settings
from web.routers import api, auth, dashboard, drive, queries, vacancies
from web.security import LoginRequired

logging.basicConfig(level=logging.DEBUG if app_settings.debug else logging.INFO)

app = FastAPI(title=app_settings.name, docs_url=None, redoc_url=None, openapi_url=None)
app.add_middleware(
    SessionMiddleware,
    secret_key=auth_settings.secret_key,
    max_age=auth_settings.session_max_age_sec,
    same_site="lax",
    https_only=auth_settings.cookie_secure,
)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

for router in (auth.router, dashboard.router, vacancies.router, queries.router, drive.router, api.router):
    app.include_router(router)


@app.exception_handler(LoginRequired)
def _login_required(request: Request, exc: LoginRequired):
    if request.url.path.startswith("/api/"):
        return JSONResponse({"detail": "Требуется вход"}, status_code=401)
    return RedirectResponse("/login", status_code=303)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("Referrer-Policy", "same-origin")
    return response


@app.get("/health", include_in_schema=False)
def health():
    return {"status": "ok"}
