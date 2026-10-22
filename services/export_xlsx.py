"""Сборка таблицы вакансий в xlsx (для Google Диска и скачивания)."""
from io import BytesIO
from zoneinfo import ZoneInfo

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from sqlalchemy import select
from sqlalchemy.orm import Session

from configs import app_settings
from database.models import Vacancy
from enums import VacancyStatus

HEADERS = [
    ("Работодатель", 28), ("Должность", 40), ("З/п", 24), ("Формат", 12), ("Город", 16),
    ("Опыт", 16), ("Опубликовано", 14), ("Статус", 14), ("Ссылка на вакансию", 12), ("Требования", 60),
]
FORMAT_LABEL = {"remote": "удалённо", "hybrid": "гибрид", "office": "офис", "unknown": "—"}


def build_xlsx(session: Session) -> tuple[bytes, int]:
    vacancies = session.scalars(
        select(Vacancy)
        .where(Vacancy.status != VacancyStatus.HIDDEN)
        .order_by(Vacancy.published_at.desc())
    ).all()
    tz = ZoneInfo(app_settings.timezone)

    wb = Workbook()
    ws = wb.active
    ws.title = "Вакансии"
    head_font = Font(name="Arial", bold=True, color="FFFFFF")
    head_fill = PatternFill("solid", fgColor="2F5496")
    for col, (title, width) in enumerate(HEADERS, 1):
        cell = ws.cell(1, col, title)
        cell.font, cell.fill = head_font, head_fill
        cell.alignment = Alignment(vertical="center", wrap_text=True)
        ws.column_dimensions[get_column_letter(col)].width = width

    body_font = Font(name="Arial", size=10)
    link_font = Font(name="Arial", size=10, color="0563C1", underline="single")
    for row, v in enumerate(vacancies, 2):
        values = [
            v.employer, v.name, v.salary_text, FORMAT_LABEL.get(v.work_format.value, "—"), v.area,
            v.experience, v.published_at.astimezone(tz).replace(tzinfo=None) if v.published_at else None,
            v.status.label, "ссылка", (v.requirement or "").replace("<highlighttext>", "").replace("</highlighttext>", ""),
        ]
        for col, value in enumerate(values, 1):
            cell = ws.cell(row, col, value)
            cell.font = body_font
            cell.alignment = Alignment(vertical="top", wrap_text=True)
        ws.cell(row, 7).number_format = "dd.mm.yyyy"
        link = ws.cell(row, 9)
        link.hyperlink = v.url
        link.font = link_font

    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(HEADERS))}{max(len(vacancies) + 1, 1)}"
    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue(), len(vacancies)
