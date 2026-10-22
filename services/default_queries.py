"""Стандартный набор поисковых запросов: сначала Пермь, потом удалёнка по России."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models import SearchQuery

PERM = 72
RUSSIA = 113
JUNIOR_MIDDLE = "noExperience,between1And3,between3And6"
JUNIOR = "noExperience,between1And3"

DEFAULT_QUERIES = [
    # Пермь — в первую очередь (priority меньше)
    dict(title="Пермь: Python", text="python", area=PERM, experience=JUNIOR_MIDDLE, priority=10),
    dict(title="Пермь: DevOps / Linux", text='devops OR ansible OR "системный администратор" OR linux',
         area=PERM, experience=JUNIOR_MIDDLE, priority=11),
    dict(title="Пермь: микроконтроллеры (junior)",
         text='stm32 OR микроконтроллер OR embedded OR "встраиваемого ПО" OR ПЛК OR codesys',
         area=PERM, experience=JUNIOR, priority=12),
    # Удалёнка по России
    dict(title="Удалёнка: Python backend", text="python AND (fastapi OR django OR flask OR backend)",
         area=RUSSIA, only_remote=True, experience=JUNIOR_MIDDLE, priority=50),
    dict(title="Удалёнка: Python-автоматизация",
         text="python AND (автоматизация OR интеграции OR боты OR парсинг OR bitrix24 OR n8n)",
         area=RUSSIA, only_remote=True, experience=JUNIOR_MIDDLE, priority=51),
    dict(title="Удалёнка: DevOps", text='devops OR "gitlab ci" OR ansible',
         area=RUSSIA, only_remote=True, experience=JUNIOR_MIDDLE, priority=52),
    dict(title="Удалёнка: сисадмин Linux", text='"системный администратор" AND linux',
         area=RUSSIA, only_remote=True, experience=JUNIOR_MIDDLE, priority=53),
    dict(title="Удалёнка: AI / VibeCoder",
         text='LLM OR "AI-агент" OR вайбкодер OR "vibe coding" OR "claude code" OR langchain',
         area=RUSSIA, only_remote=True, experience=JUNIOR_MIDDLE, priority=54),
    dict(title="Удалёнка: микроконтроллеры (junior)", text="stm32 OR микроконтроллер OR embedded",
         area=RUSSIA, only_remote=True, experience=JUNIOR, priority=55),
]


def seed_default_queries(session: Session) -> int:
    """Добавляет стандартные запросы, которых ещё нет (по названию)."""
    existing = set(session.scalars(select(SearchQuery.title)).all())
    added = 0
    for data in DEFAULT_QUERIES:
        if data["title"] in existing:
            continue
        session.add(SearchQuery(**data))
        added += 1
    session.commit()
    return added
