"""Схемы ответа API hh.ru (GET /vacancies). Лишние поля игнорируются."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class HHBase(BaseModel):
    model_config = ConfigDict(extra="ignore")


class HHIdName(HHBase):
    id: str | None = None
    name: str | None = None


class HHSalary(HHBase):
    from_: int | None = Field(default=None, alias="from")
    to: int | None = None
    currency: str | None = None
    gross: bool | None = None


class HHEmployer(HHBase):
    id: str | None = None
    name: str | None = None


class HHSnippet(HHBase):
    requirement: str | None = None
    responsibility: str | None = None


class HHVacancyItem(HHBase):
    id: str
    name: str
    area: HHIdName | None = None
    salary: HHSalary | None = None
    employer: HHEmployer | None = None
    published_at: datetime
    alternate_url: str
    snippet: HHSnippet | None = None
    schedule: HHIdName | None = None
    experience: HHIdName | None = None
    archived: bool = False
    # Новые поля hh (2025): формат работы списком
    work_format: list[HHIdName] = Field(default_factory=list)


class HHSearchResponse(HHBase):
    items: list[HHVacancyItem] = Field(default_factory=list)
    found: int = 0
    pages: int = 0
    page: int = 0
    per_page: int = 0
