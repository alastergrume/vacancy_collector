from enum import Enum


class ExportStatus(str, Enum):
    """Результат выгрузки на Google Диск."""

    SUCCESS = "success"
    FAILED = "failed"
