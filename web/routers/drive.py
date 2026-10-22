from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from configs import gdrive_settings
from database import get_session
from database.models import DriveExport
from services import google_drive as gd
from tasks.collect import export_vacancies_to_drive
from web.security import require_user, verify_csrf
from web.templating import flash, render

router = APIRouter(prefix="/drive", dependencies=[Depends(require_user)])


@router.get("")
def drive_page(request: Request, session: Session = Depends(get_session)):
    record = gd.get_record(session)
    exports = session.scalars(select(DriveExport).order_by(DriveExport.created_at.desc()).limit(20)).all()
    return render(request, "drive.html", {
        "record": record,
        "exports": exports,
        "configured": gdrive_settings.is_configured,
        "folder_id": gdrive_settings.folder_id,
        "redirect_uri": gd.redirect_uri(),
    })


@router.post("/connect")
def connect(request: Request, csrf: str = Form("")):
    verify_csrf(request, csrf)
    try:
        url, state, verifier = gd.authorization_url()
    except gd.DriveNotConnected as exc:
        flash(request, str(exc), "error")
        return RedirectResponse("/drive", status_code=303)
    request.session["gdrive_state"] = state
    request.session["gdrive_verifier"] = verifier
    return RedirectResponse(url, status_code=303)


@router.get("/callback")
def callback(request: Request, session: Session = Depends(get_session)):
    state = request.session.pop("gdrive_state", None)
    verifier = request.session.pop("gdrive_verifier", None)
    if not state or request.query_params.get("state") != state:
        flash(request, "Сессия авторизации Google устарела, попробуйте ещё раз", "error")
        return RedirectResponse("/drive", status_code=303)
    if request.query_params.get("error"):
        flash(request, f"Google отказал: {request.query_params['error']}", "error")
        return RedirectResponse("/drive", status_code=303)
    try:
        gd.finish_authorization(session, state, verifier, str(request.url))
        flash(request, "Google Диск подключён", "success")
    except Exception as exc:  # noqa: BLE001
        flash(request, f"Не удалось подключить Диск: {exc}", "error")
    return RedirectResponse("/drive", status_code=303)


@router.post("/export")
def export(request: Request, csrf: str = Form("")):
    verify_csrf(request, csrf)
    export_vacancies_to_drive.delay()
    flash(request, "Выгрузка запущена", "success")
    return RedirectResponse("/drive", status_code=303)


@router.post("/disconnect")
def disconnect(request: Request, csrf: str = Form(""), session: Session = Depends(get_session)):
    verify_csrf(request, csrf)
    gd.disconnect(session)
    flash(request, "Google Диск отключён", "success")
    return RedirectResponse("/drive", status_code=303)
