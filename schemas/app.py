"""Схемы для веб-интерфейса и API приложения."""
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from enums import RunStatus, RunTrigger, VacancyStatus

EXPERIENCE_IDS = {"noExperience", "between1And3", "between3And6", "moreThan6"}


class SearchQueryIn(BaseModel):
    title: str = Field(min_length=1, max_length=128)
    text: str = Field(min_length=1, max_length=512)
    area: int = Field(default=113, ge=1)
    only_remote: bool = False
    experience: str = "between1And3,between3And6"
    exclude_words: str = ""
    priority: int = Field(default=100, ge=0, le=10000)
    is_active: bool = True

    @field_validator("experience")
    @classmethod
    def check_experience(cls, v: str) -> str:
        items = [e.strip() for e in v.split(",") if e.strip()]
        bad = [e for e in items if e not in EXPERIENCE_IDS]
        if bad:
            raise ValueError(f"Неизвестный опыт: {', '.join(bad)}")
        return ",".join(items)


class VacancyStatusIn(BaseModel):
    status: VacancyStatus
    note: str | None = None


class RunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    trigger: RunTrigger
    status: RunStatus
    started_at: datetime
    finished_at: datetime | None
    duration_sec: int | None
    queries_total: int
    requests_made: int
    found_total: int
    filtered_out: int
    new_count: int
    updated_count: int
    error: str | None


class DayCount(BaseModel):
    day: date
    count: int


class StatsOut(BaseModel):
    total: int
    by_status: dict[str, int]
    new_last_7_days: list[DayCount]
    perm_total: int
    remote_total: int
    last_run: RunOut | None
    drive_connected: bool
    last_export_at: datetime | None
    last_export_status: str | None
