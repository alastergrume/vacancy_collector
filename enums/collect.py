from enum import Enum


class RunStatus(str, Enum):
    """Состояние запуска сборщика."""

    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class RunTrigger(str, Enum):
    """Кто запустил сбор."""

    SCHEDULE = "schedule"
    MANUAL = "manual"
