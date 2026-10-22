"""Все модели — импорт здесь нужен Alembic для автогенерации."""
from database.models.collect_run import CollectRun
from database.models.drive import DriveExport, GoogleCredential
from database.models.login_attempt import LoginAttempt
from database.models.search_query import SearchQuery
from database.models.vacancy import Vacancy

__all__ = ["CollectRun", "DriveExport", "GoogleCredential", "LoginAttempt", "SearchQuery", "Vacancy"]
