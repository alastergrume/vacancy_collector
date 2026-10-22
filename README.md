# Vacancy Collector

Сборщик вакансий с hh.ru через официальный API: ежедневный сбор по расписанию (Celery), PostgreSQL, веб-интерфейс со статистикой, выгрузка таблицы на Google Диск.

## Структура

```
configs/        настройки на pydantic-settings (base.py → EnvSettings), .env и .env.example
database/       engine.py (движок и сессии), base.py, models/ — модели по файлам
enums/          Enum-типы
schemas/        pydantic-схемы (ответы hh API, формы и статистика)
services/       клиент hh API, фильтры, сборщик, xlsx, Google Диск, статистика
tasks/          Celery: приложение и задачи (сбор, выгрузка на Диск)
web/            FastAPI: роутеры, авторизация, шаблонизатор
templates/      base.html и наследуемые шаблоны
static/         css/style.css, js/scripts.js
migrations/     Alembic
docker/         Dockerfile и docker-compose.yml
scripts/        хеш пароля, стандартные запросы, разовый сбор
tests/          pytest
```

## Быстрый старт (Docker)

```bash
cp configs/.env.example configs/.env
python scripts/hash_password.py        # хеш → AUTH_ADMIN_PASSWORD_HASH
# заполните AUTH_SECRET_KEY, POSTGRES_PASSWORD, HH_USER_AGENT, APP_PUBLIC_URL
docker compose -f docker/docker-compose.yml up -d --build
docker compose -f docker/docker-compose.yml exec web python scripts/seed_queries.py
```

Контейнеры: `postgres`, `redis` (брокер), `migrate` (alembic upgrade head), `web`, `worker`, `beat`.
Веб слушает `127.0.0.1:8000` — наружу публикуйте через nginx или Caddy с HTTPS и ставьте `AUTH_COOKIE_SECURE=true`.

## Миграции (Alembic)

```bash
alembic revision --autogenerate -m "описание"   # генерация
alembic upgrade head                             # применить
alembic downgrade -1                             # откатить
alembic check                                    # модели и база совпадают?
```

Если в миграции создаются Enum-типы PostgreSQL, автогенерация не удаляет их в `downgrade`. Допишите удаление по именам, иначе повторный `upgrade` упадёт:

```python
sa.Enum(name="vacancy_status").drop(op.get_bind(), checkfirst=True)
```

Пример — `migrations/versions/*_initial.py`. Имена типов задаются в моделях через `pg_enum(EnumClass, "имя")`.

## hh.ru API

- Поиск вакансий требует **авторизации приложения** (см. [документацию hh](https://github.com/hhru/api/blob/master/docs/authorization_for_application.md)):
  1. зарегистрируйте приложение на https://dev.hh.ru;
  2. один раз получите токен приложения и скопируйте его в https://dev.hh.ru/admin;
  3. укажите его в `HH_APP_TOKEN` — приложение передаёт его в заголовке `Authorization: Bearer`.

  Токен приложения постоянный: обновлять через refresh не нужно. Если выпустить новый, старый отзывается — тогда обновите `HH_APP_TOKEN`. Без токена сбор не стартует, при 401/403 останавливается с подсказкой.
- Авторизация пользователя (access + refresh, протухают) нужна только для действий от имени соискателя — резюме и отклики. Сборщику она не нужна.
- Обязателен `HH_USER_AGENT` вида `AppName/1.0 (почта)`.
- Бережный режим: пауза `HH_REQUEST_DELAY_SEC` между запросами, не больше `HH_MAX_PAGES` страниц на запрос. На 403/400 сбор сразу останавливается, на 429/5xx — повторы с паузой.
- Поисковые запросы редактируются на странице «Запросы». Регион: 72 — Пермь, 113 — Россия. Пермские запросы идут первыми (меньший приоритет).
- Удалёнка определяется по `work_format`/`schedule` в ответе hh и фильтруется на стороне приложения.

## Google Диск

1. Google Cloud Console → APIs & Services: включите Google Drive API.
2. OAuth consent screen: тип External, добавьте свою почту в Test users.
3. Credentials → OAuth client ID → «Web application». Authorized redirect URI: `{APP_PUBLIC_URL}/drive/callback`.
4. `GDRIVE_CLIENT_ID`, `GDRIVE_CLIENT_SECRET` → `configs/.env`, перезапустите контейнеры.
5. В интерфейсе: «Google Диск» → «Подключить». Таблица обновляется в одном файле после каждого сбора.

Со scope `drive.file` приложение видит только свои файлы: файл создаётся в корне Диска. Чтобы класть его в существующую папку, укажите `GDRIVE_FOLDER_ID` и `GDRIVE_SCOPES=https://www.googleapis.com/auth/drive`.

## Разработка без Docker

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# в configs/.env: POSTGRES_HOST=localhost, CELERY_BROKER_URL=redis://localhost:6379/0
alembic upgrade head
uvicorn web.app:app --reload
celery -A tasks.celery_app:celery_app worker -l INFO
celery -A tasks.celery_app:celery_app beat -l INFO
python scripts/collect_now.py           # разовый сбор без Celery
pytest -q                               # тесты (нужна мигрированная база)
```
