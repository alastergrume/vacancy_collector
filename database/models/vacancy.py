from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base, TimestampMixin, pg_enum
from enums import VacancyStatus, WorkFormat


class Vacancy(TimestampMixin, Base):
    """Вакансия с hh.ru."""

    __tablename__ = "vacancies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    hh_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(512))
    employer: Mapped[str | None] = mapped_column(String(512))
    area: Mapped[str | None] = mapped_column(String(128), index=True)
    salary_from: Mapped[int | None] = mapped_column(Integer)
    salary_to: Mapped[int | None] = mapped_column(Integer)
    salary_currency: Mapped[str | None] = mapped_column(String(8))
    salary_gross: Mapped[bool | None] = mapped_column(Boolean)
    experience: Mapped[str | None] = mapped_column(String(64))
    work_format: Mapped[WorkFormat] = mapped_column(
        pg_enum(WorkFormat, "work_format"), default=WorkFormat.UNKNOWN
    )
    schedule: Mapped[str | None] = mapped_column(String(64))
    requirement: Mapped[str | None] = mapped_column(Text)
    responsibility: Mapped[str | None] = mapped_column(Text)
    url: Mapped[str] = mapped_column(String(512))
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    archived: Mapped[bool] = mapped_column(Boolean, default=False)

    status: Mapped[VacancyStatus] = mapped_column(
        pg_enum(VacancyStatus, "vacancy_status"), default=VacancyStatus.NEW, index=True
    )
    note: Mapped[str | None] = mapped_column(Text)
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    search_query_id: Mapped[int | None] = mapped_column(
        ForeignKey("search_queries.id", ondelete="SET NULL")
    )
    first_run_id: Mapped[int | None] = mapped_column(
        ForeignKey("collect_runs.id", ondelete="SET NULL")
    )

    search_query = relationship("SearchQuery", back_populates="vacancies")

    @property
    def salary_text(self) -> str:
        if not self.salary_from and not self.salary_to:
            return "не указана"
        cur = {"RUR": "₽", "USD": "$", "EUR": "€"}.get(self.salary_currency or "", self.salary_currency or "")
        if self.salary_from and self.salary_to:
            text = f"{self.salary_from:,}–{self.salary_to:,} {cur}"
        elif self.salary_from:
            text = f"от {self.salary_from:,} {cur}"
        else:
            text = f"до {self.salary_to:,} {cur}"
        text = text.replace(",", " ")
        if self.salary_gross is True:
            text += " до вычета"
        elif self.salary_gross is False:
            text += " на руки"
        return text
