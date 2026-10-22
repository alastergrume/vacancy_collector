"""Фильтры вакансий без участия модели: стоп-слова, удалёнка, формат работы."""
import re

from enums import WorkFormat
from schemas.hh import HHVacancyItem


def detect_work_format(item: HHVacancyItem) -> WorkFormat:
    ids = {(w.id or "").upper() for w in item.work_format}
    if "REMOTE" in ids:
        return WorkFormat.REMOTE
    if "HYBRID" in ids:
        return WorkFormat.HYBRID
    if "ON_SITE" in ids:
        return WorkFormat.OFFICE
    schedule = (item.schedule.id if item.schedule else "") or ""
    if schedule == "remote":
        return WorkFormat.REMOTE
    if schedule in {"fullDay", "shift", "flexible"}:
        return WorkFormat.OFFICE
    return WorkFormat.UNKNOWN


def _word_hit(title: str, word: str) -> bool:
    # Слово целиком, чтобы «go» не отсекало «Google», а «lead» — «leading-edge» не важно
    pattern = r"(?<![\w])" + re.escape(word) + r"(?![\w])"
    return re.search(pattern, title, flags=re.IGNORECASE) is not None


def excluded_by_words(title: str, words: list[str]) -> str | None:
    """Возвращает стоп-слово, из-за которого вакансия отброшена, или None."""
    for w in words:
        if w and _word_hit(title, w):
            return w
    return None


def passes(item: HHVacancyItem, exclude_words: list[str], only_remote: bool) -> tuple[bool, str | None]:
    if item.archived:
        return False, "архив"
    hit = excluded_by_words(item.name, exclude_words)
    if hit:
        return False, f"стоп-слово «{hit}»"
    if only_remote and detect_work_format(item) != WorkFormat.REMOTE:
        return False, "не удалёнка"
    return True, None
