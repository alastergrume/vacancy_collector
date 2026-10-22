from enum import Enum


class VacancyStatus(str, Enum):
    """Статус вакансии в воронке откликов."""

    NEW = "new"            # только что собрана
    SUITABLE = "suitable"  # отмечена как подходящая
    APPLIED = "applied"    # отклик отправлен
    INTERVIEW = "interview"
    REJECTED = "rejected"  # отказ
    HIDDEN = "hidden"      # не интересна
    ARCHIVED = "archived"  # снята с публикации на hh

    @property
    def label(self) -> str:
        return {
            "new": "новая",
            "suitable": "подходит",
            "applied": "отклик",
            "interview": "собеседование",
            "rejected": "отказ",
            "hidden": "скрыта",
            "archived": "архив",
        }[self.value]


class WorkFormat(str, Enum):
    """Формат работы, упрощённо по данным hh."""

    REMOTE = "remote"
    HYBRID = "hybrid"
    OFFICE = "office"
    UNKNOWN = "unknown"
