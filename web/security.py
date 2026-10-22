"""Пароли (PBKDF2), сессия пользователя, CSRF и блокировка перебора."""
import base64
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from configs import auth_settings
from database.models import LoginAttempt

ALGO = "pbkdf2_sha256"
ITERATIONS = 390_000


def hash_password(password: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), ITERATIONS)
    return f"{ALGO}${ITERATIONS}${salt}${base64.b64encode(digest).decode()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, iterations, salt, expected = stored.split("$", 3)
    except ValueError:
        return False
    if algo != ALGO:
        return False
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), int(iterations))
    return hmac.compare_digest(base64.b64encode(digest).decode(), expected)


def check_credentials(username: str, password: str) -> bool:
    if not auth_settings.admin_password_hash:
        return False
    user_ok = hmac.compare_digest(username, auth_settings.admin_username)
    pass_ok = verify_password(password, auth_settings.admin_password_hash)
    return user_ok and pass_ok


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def is_locked(session: Session, ip: str) -> bool:
    since = datetime.now(timezone.utc) - timedelta(minutes=auth_settings.lockout_minutes)
    failed = session.scalar(
        select(func.count(LoginAttempt.id)).where(
            LoginAttempt.ip == ip, LoginAttempt.success.is_(False), LoginAttempt.created_at >= since
        )
    ) or 0
    return failed >= auth_settings.max_failed_logins


def record_attempt(session: Session, ip: str, username: str, success: bool) -> None:
    session.add(LoginAttempt(ip=ip, username=username[:128], success=success))
    session.commit()


def current_user(request: Request) -> str | None:
    return request.session.get("user")


def csrf_token(request: Request) -> str:
    token = request.session.get("csrf")
    if not token:
        token = secrets.token_urlsafe(32)
        request.session["csrf"] = token
    return token


def verify_csrf(request: Request, token: str | None) -> None:
    expected = request.session.get("csrf")
    if not expected or not token or not hmac.compare_digest(expected, token):
        raise HTTPException(status_code=403, detail="Неверный CSRF-токен, обновите страницу")


class LoginRequired(Exception):
    """Перехватывается в app.py и превращается в редирект на /login."""


def require_user(request: Request) -> str:
    user = current_user(request)
    if not user:
        raise LoginRequired()
    return user
