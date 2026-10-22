"""Тесты работают с базой из configs/.env (нужна поднятая и мигрированная PostgreSQL)."""
import sys
from pathlib import Path

import pytest
from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database import SessionLocal, engine  # noqa: E402


@pytest.fixture()
def session():
    s = SessionLocal()
    yield s
    s.close()
    with engine.begin() as conn:
        conn.execute(text(
            "TRUNCATE vacancies, search_queries, collect_runs, drive_exports, google_credentials, "
            "login_attempts RESTART IDENTITY CASCADE"
        ))


def hh_item(id_: str, name: str, **extra) -> dict:
    item = {
        "id": id_,
        "name": name,
        "area": {"id": "72", "name": "Пермь"},
        "salary": {"from": 150000, "to": None, "currency": "RUR", "gross": False},
        "employer": {"id": "1", "name": "ООО Тест"},
        "published_at": "2026-10-21T09:00:00+0300",
        "alternate_url": f"https://hh.ru/vacancy/{id_}",
        "snippet": {"requirement": "Опыт с <highlighttext>Python</highlighttext>", "responsibility": "Писать код"},
        "schedule": {"id": "remote", "name": "Удаленная работа"},
        "experience": {"id": "between1And3", "name": "От 1 года до 3 лет"},
        "archived": False,
    }
    item.update(extra)
    return item
