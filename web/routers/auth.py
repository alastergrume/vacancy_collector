from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from database import get_session
from web.security import check_credentials, client_ip, current_user, is_locked, record_attempt, verify_csrf
from web.templating import render

router = APIRouter()


@router.get("/login")
def login_page(request: Request):
    if current_user(request):
        return RedirectResponse("/", status_code=303)
    return render(request, "login.html")


@router.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    csrf: str = Form(""),
    session: Session = Depends(get_session),
):
    verify_csrf(request, csrf)
    ip = client_ip(request)
    if is_locked(session, ip):
        return render(request, "login.html", {"error": "Слишком много попыток. Попробуйте позже."}, 429)
    if not check_credentials(username, password):
        record_attempt(session, ip, username, False)
        return render(request, "login.html", {"error": "Неверный логин или пароль", "username": username}, 401)
    record_attempt(session, ip, username, True)
    request.session.clear()
    request.session["user"] = username
    return RedirectResponse("/", status_code=303)


@router.post("/logout")
def logout(request: Request, csrf: str = Form("")):
    verify_csrf(request, csrf)
    request.session.clear()
    return RedirectResponse("/login", status_code=303)
