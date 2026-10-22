from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base, TimestampMixin


class SearchQuery(TimestampMixin, Base):
    """Поисковый запрос к hh: что, где и с каким опытом искать."""

    __tablename__ = "search_queries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(128))
    # Строка поиска hh (поддерживает язык запросов: OR, AND, NOT, кавычки)
    text: Mapped[str] = mapped_column(String(512))
    # ID региона hh: 72 — Пермь, 113 — Россия
    area: Mapped[int] = mapped_column(Integer, default=113)
    only_remote: Mapped[bool] = mapped_column(Boolean, default=False)
    # Через запятую: noExperience, between1And3, between3And6
    experience: Mapped[str] = mapped_column(String(128), default="between1And3,between3And6")
    # Доп. стоп-слова для названия вакансии, через запятую
    exclude_words: Mapped[str] = mapped_column(String(512), default="")
    # Чем меньше число, тем раньше выполняется (Пермь — первой)
    priority: Mapped[int] = mapped_column(Integer, default=100)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    vacancies = relationship("Vacancy", back_populates="search_query")

    @property
    def experience_list(self) -> list[str]:
        return [e.strip() for e in self.experience.split(",") if e.strip()]

    @property
    def exclude_list(self) -> list[str]:
        return [w.strip().lower() for w in self.exclude_words.split(",") if w.strip()]
