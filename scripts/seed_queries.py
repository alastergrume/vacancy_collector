"""Добавляет стандартные поисковые запросы: python scripts/seed_queries.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database import session_scope  # noqa: E402
from services.default_queries import seed_default_queries  # noqa: E402

if __name__ == "__main__":
    with session_scope() as session:
        print(f"Добавлено запросов: {seed_default_queries(session)}")
