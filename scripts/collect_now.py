"""Разовый сбор без Celery (для отладки): python scripts/collect_now.py"""
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database import session_scope  # noqa: E402
from enums import RunTrigger  # noqa: E402
from services.collector import run_collect  # noqa: E402

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    with session_scope() as session:
        run = run_collect(session, RunTrigger.MANUAL)
        print(f"Статус: {run.status.value}, запросов к hh: {run.requests_made}, найдено: {run.found_total}, "
              f"отсеяно: {run.filtered_out}, новых: {run.new_count}, обновлено: {run.updated_count}")
        if run.error:
            print("Ошибка:", run.error)
