import httpx
from sqlalchemy import select

from configs import HHSettings
from database.models import SearchQuery, Vacancy
from enums import RunStatus, VacancyStatus, WorkFormat
from schemas.hh import HHVacancyItem
from services.collector import run_collect
from services.filters import detect_work_format, excluded_by_words, passes
from services.hh_client import HHClient
from tests.conftest import hh_item


def make_client(handler) -> HHClient:
    settings = HHSettings(request_delay_sec=0, retries=0, max_pages=3, app_token="test-token")
    return HHClient(settings, transport=httpx.MockTransport(handler))


def test_stop_words_whole_word():
    assert excluded_by_words("Senior Python Developer", ["senior"]) == "senior"
    assert excluded_by_words("Python разработчик в Google", ["go"]) is None
    assert excluded_by_words("Go-разработчик", ["go"]) == "go"


def test_work_format_and_passes():
    item = HHVacancyItem.model_validate(hh_item("1", "Python dev"))
    assert detect_work_format(item) == WorkFormat.REMOTE
    office = HHVacancyItem.model_validate(hh_item("2", "Python dev", schedule={"id": "fullDay", "name": "Полный день"}))
    assert passes(office, [], only_remote=True) == (False, "не удалёнка")
    archived = HHVacancyItem.model_validate(hh_item("3", "Python dev", archived=True))
    assert passes(archived, [], only_remote=False)[0] is False


def test_client_sends_user_agent_and_paginates():
    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        page = int(request.url.params["page"])
        return httpx.Response(200, json={"items": [hh_item(str(page), "Python")], "found": 2, "pages": 2,
                                         "page": page, "per_page": 100})

    client = make_client(handler)
    from datetime import datetime, timezone
    pages = list(client.search_all("python", 72, ["between1And3"], datetime.now(timezone.utc)))
    assert len(pages) == 2
    assert seen[0].headers["HH-User-Agent"]
    assert seen[0].headers["Authorization"] == "Bearer test-token"
    assert seen[0].url.params.get_list("experience") == ["between1And3"]


def test_run_collect_saves_filters_and_keeps_status(session):
    session.add(SearchQuery(title="Пермь", text="python", area=72, priority=1))
    session.commit()

    items = [hh_item("100", "Python разработчик"), hh_item("101", "Senior Python"),
             hh_item("102", "Backend Python", schedule={"id": "fullDay", "name": "Полный день"})]

    def handler(request):
        return httpx.Response(200, json={"items": items, "found": 3, "pages": 1, "page": 0, "per_page": 100})

    run = run_collect(session, client=make_client(handler))
    assert run.status == RunStatus.SUCCESS
    assert (run.found_total, run.filtered_out, run.new_count) == (3, 1, 2)
    v = session.scalar(select(Vacancy).where(Vacancy.hh_id == "100"))
    assert v.salary_text == "от 150 000 ₽ на руки"

    # Пользователь отметил отклик — повторный сбор не сбрасывает статус
    v.status = VacancyStatus.APPLIED
    session.commit()
    items[0]["archived"] = True
    run2 = run_collect(session, client=make_client(handler))
    assert run2.new_count == 0
    session.refresh(v)
    assert v.status == VacancyStatus.APPLIED


def test_run_collect_stops_on_403(session):
    session.add(SearchQuery(title="x", text="python", area=113))
    session.commit()
    run = run_collect(session, client=make_client(lambda r: httpx.Response(403, text="forbidden")))
    assert run.status == RunStatus.FAILED
    assert "403" in run.error
    assert run.requests_made == 1


def test_missing_token_stops_without_requests(session):
    session.add(SearchQuery(title="x", text="python", area=113))
    session.commit()
    calls = []
    client = HHClient(HHSettings(request_delay_sec=0, app_token=""),
                      transport=httpx.MockTransport(lambda r: calls.append(r) or httpx.Response(200, json={})))
    run = run_collect(session, client=client)
    assert run.status == RunStatus.FAILED
    assert "HH_APP_TOKEN" in run.error
    assert calls == [] and run.requests_made == 0


def test_revoked_token_hint(session):
    session.add(SearchQuery(title="x", text="python", area=113))
    session.commit()
    run = run_collect(session, client=make_client(lambda r: httpx.Response(401, json={"errors": [{"type": "oauth"}]})))
    assert "dev.hh.ru/admin" in run.error
