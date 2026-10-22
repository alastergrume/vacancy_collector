"""Google Диск: OAuth-подключение и выгрузка таблицы вакансий."""
import json
import logging
import os
from io import BytesIO

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseUpload
from sqlalchemy import select
from sqlalchemy.orm import Session

from configs import app_settings, gdrive_settings
from database.models import DriveExport, GoogleCredential
from enums import ExportStatus
from services.export_xlsx import build_xlsx

logger = logging.getLogger(__name__)

XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
REDIRECT_PATH = "/drive/callback"


class DriveNotConnected(Exception):
    pass


def redirect_uri() -> str:
    return app_settings.public_url.rstrip("/") + REDIRECT_PATH


def make_flow(state: str | None = None) -> Flow:
    # oauthlib требует HTTPS; для локальной отладки на http://localhost разрешаем http
    if app_settings.public_url.startswith(("http://localhost", "http://127.0.0.1")):
        os.environ.setdefault("OAUTHLIB_INSECURE_TRANSPORT", "1")
    if not gdrive_settings.is_configured:
        raise DriveNotConnected("Не заданы GDRIVE_CLIENT_ID и GDRIVE_CLIENT_SECRET в configs/.env")
    client_config = {
        "web": {
            "client_id": gdrive_settings.client_id,
            "client_secret": gdrive_settings.client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [redirect_uri()],
        }
    }
    flow = Flow.from_client_config(client_config, scopes=gdrive_settings.scope_list, state=state)
    flow.redirect_uri = redirect_uri()
    return flow


def authorization_url() -> tuple[str, str, str | None]:
    """URL для входа в Google, state и PKCE code_verifier (их храним в сессии)."""
    flow = make_flow()
    url, state = flow.authorization_url(access_type="offline", prompt="consent", include_granted_scopes="true")
    return url, state, getattr(flow, "code_verifier", None)


def finish_authorization(session: Session, state: str, code_verifier: str | None, full_callback_url: str) -> None:
    flow = make_flow(state=state)
    if code_verifier:
        flow.code_verifier = code_verifier
    flow.fetch_token(authorization_response=full_callback_url)
    creds = flow.credentials
    email = None
    try:
        about = build("drive", "v3", credentials=creds, cache_discovery=False).about().get(fields="user").execute()
        email = about.get("user", {}).get("emailAddress")
    except HttpError:
        logger.warning("Не удалось получить e-mail аккаунта Google")
    record = session.scalar(select(GoogleCredential).limit(1))
    if record is None:
        record = GoogleCredential(token_json=creds.to_json())
        session.add(record)
    else:
        record.token_json = creds.to_json()
        record.export_file_id = None
    record.account_email = email
    session.commit()


def get_record(session: Session) -> GoogleCredential | None:
    return session.scalar(select(GoogleCredential).limit(1))


def disconnect(session: Session) -> None:
    record = get_record(session)
    if record:
        session.delete(record)
        session.commit()


def _credentials(session: Session, record: GoogleCredential) -> Credentials:
    creds = Credentials.from_authorized_user_info(json.loads(record.token_json), gdrive_settings.scope_list)
    if not creds.valid and creds.refresh_token:
        creds.refresh(Request())
        record.token_json = creds.to_json()
        session.commit()
    return creds


def export_to_drive(session: Session) -> DriveExport:
    """Выгружает таблицу вакансий на Диск: обновляет тот же файл или создаёт новый."""
    export = DriveExport(status=ExportStatus.FAILED)
    try:
        record = get_record(session)
        if record is None:
            raise DriveNotConnected("Google Диск не подключён")
        service = build("drive", "v3", credentials=_credentials(session, record), cache_discovery=False)
        content, rows = build_xlsx(session)
        media = MediaIoBaseUpload(BytesIO(content), mimetype=XLSX_MIME, resumable=False)

        file = None
        if record.export_file_id:
            try:
                file = service.files().update(
                    fileId=record.export_file_id, media_body=media, fields="id,webViewLink"
                ).execute()
            except HttpError as exc:
                if getattr(exc, "status_code", None) != 404 and "404" not in str(exc):
                    raise
                media = MediaIoBaseUpload(BytesIO(content), mimetype=XLSX_MIME, resumable=False)
        if file is None:
            meta = {"name": gdrive_settings.export_file_name}
            if gdrive_settings.folder_id:
                meta["parents"] = [gdrive_settings.folder_id]
            file = service.files().create(body=meta, media_body=media, fields="id,webViewLink").execute()
            record.export_file_id = file["id"]

        export.status = ExportStatus.SUCCESS
        export.rows = rows
        export.file_url = file.get("webViewLink")
    except Exception as exc:  # noqa: BLE001
        export.error = f"{type(exc).__name__}: {exc}"[:2000]
        logger.warning("Выгрузка на Диск не удалась: %s", exc)
    session.add(export)
    session.commit()
    return export
