import re

import pytest
from fastapi.testclient import TestClient

from configs import auth_settings
from web.security import hash_password, verify_password

PASSWORD = "very-secret-pass"


@pytest.fixture()
def client(session, monkeypatch):
    monkeypatch.setattr(auth_settings, "admin_password_hash", hash_password(PASSWORD))
    from web.app import app
    with TestClient(app) as c:
        yield c


def csrf_from(html: str) -> str:
    return re.search(r'name="csrf" value="([^"]+)"', html).group(1)


def login(client, password=PASSWORD):
    page = client.get("/login")
    return client.post("/login", data={"username": "admin", "password": password, "csrf": csrf_from(page.text)},
                       follow_redirects=False)


def test_password_hash_roundtrip():
    h = hash_password("abc123456789")
    assert verify_password("abc123456789", h)
    assert not verify_password("wrong", h)


def test_requires_login(client):
    r = client.get("/", follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == "/login"
    assert client.get("/api/stats").status_code == 401


def test_login_and_pages(client):
    assert login(client).status_code == 303
    for path in ["/", "/vacancies", "/queries", "/runs", "/drive", "/api/stats", "/vacancies/export.xlsx"]:
        r = client.get(path)
        assert r.status_code == 200, path


def test_csrf_required(client):
    login(client)
    r = client.post("/queries/seed", data={"csrf": "bad"})
    assert r.status_code == 403


def test_seed_and_edit_queries(client):
    login(client)
    token = csrf_from(client.get("/queries").text)
    client.post("/queries/seed", data={"csrf": token})
    html = client.get("/queries").text
    assert "Пермь: Python" in html
    r = client.post("/queries", data={"csrf": token, "query_id": "", "title": "Новый", "text": "fastapi",
                                      "area": "72", "experience": "noExperience", "priority": "5", "is_active": "1"},
                    follow_redirects=False)
    assert r.status_code == 303
    assert "Новый" in client.get("/queries").text


def test_lockout_after_failed_logins(client):
    for _ in range(auth_settings.max_failed_logins):
        assert login(client, "wrong").status_code == 401
    assert login(client).status_code == 429
