# StarLift — Архитектура MVP

> Техническая спецификация платформы учёта и оценки корпоративных спикеров  
> Версия: 0.1.0 | Дата: 2026-03-03 | Горизонт MVP: 3 месяца

---

## 1. Общая архитектура

```
┌─────────────────────────────────────────────────────────────────────┐
│                          ИСТОЧНИКИ ДАННЫХ                          │
│                                                                     │
│  ┌──────────────┐  ┌──────────────────┐  ┌───────────────────────┐ │
│  │  Внутренние   │  │  Telegram-бот    │  │  Внешние площадки     │ │
│  │  отчёты (CSV/ │  │  (самотёк от     │  │  (Habr, YouTube,     │ │
│  │  Excel/API)   │  │  спикеров)       │  │  Timepad, конф-сайты)│ │
│  └──────┬───────┘  └────────┬─────────┘  └──────────┬────────────┘ │
│         │                   │                        │              │
└─────────┼───────────────────┼────────────────────────┼──────────────┘
          │                   │                        │
          ▼                   ▼                        ▼
┌─────────────────────────────────────────────────────────────────────┐
│                           BACKEND (API)                             │
│                                                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐  ┌──────────┐ │
│  │  Import      │  │  Bot Gateway│  │  Parser      │  │  Scoring │ │
│  │  Service     │  │  Service    │  │  Service     │  │  Engine  │ │
│  └──────┬──────┘  └──────┬──────┘  └──────┬───────┘  └────┬─────┘ │
│         │                │                 │               │        │
│         └────────────────┴─────────────────┘               │        │
│                          │                                 │        │
│                          ▼                                 │        │
│                 ┌────────────────┐                         │        │
│                 │  Unified       │◄────────────────────────┘        │
│                 │  Speaker       │                                  │
│                 │  Pipeline      │                                  │
│                 └───────┬────────┘                                  │
│                         │                                          │
│              ┌──────────┼──────────┐                               │
│              ▼          ▼          ▼                                │
│  ┌──────────────┐ ┌──────────┐ ┌───────────────┐  ┌────────────┐  │
│  │  REST API    │ │  Candi-  │ │  Notification  │  │  Auth      │  │
│  │  (Dashboard) │ │  date    │ │  Service       │  │  Service   │  │
│  │              │ │  Selector│ │  (email/TG)    │  │  (OIDC)    │  │
│  └──────┬───────┘ └──────────┘ └───────────────┘  └────────────┘  │
│         │                                                          │
└─────────┼──────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          FRONTEND                                   │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  SPA Dashboard (React / Next.js)                              │  │
│  │  ┌──────────┐ ┌──────────┐ ┌───────────┐ ┌────────────────┐  │  │
│  │  │ Speakers │ │ Events   │ │ Candidate │ │ Analytics      │  │  │
│  │  │ List     │ │ Feed     │ │ Board     │ │ & Reports      │  │  │
│  │  └──────────┘ └──────────┘ └───────────┘ └────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                          ХРАНЕНИЕ                                   │
│                                                                     │
│  ┌──────────────────┐  ┌─────────────┐  ┌────────────────────────┐ │
│  │  PostgreSQL       │  │  Redis       │  │  S3-compatible         │ │
│  │  (основная БД)    │  │  (кэш, очер.)│  │  (файлы отчётов)      │ │
│  └──────────────────┘  └─────────────┘  └────────────────────────┘ │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Выделенные сервисы

Для MVP используется **модульный монолит** — единое приложение с чётко разделёнными доменными модулями. Это оптимальный баланс между скоростью разработки и возможностью будущего выделения в микросервисы.

| # | Модуль / Сервис | Ответственность | Развёртывание |
|---|----------------|-----------------|---------------|
| 1 | **Import Service** | Парсинг CSV/Excel/JSON внутренних отчётов, нормализация, дедупликация | Модуль монолита |
| 2 | **Telegram Bot** | Приём заявок от спикеров, диалоговый интерфейс, валидация | **Отдельный процесс** (long-polling/webhook) |
| 3 | **Parser Service** | Периодический сбор данных с внешних площадок (Habr, YouTube, Timepad и др.) | **Отдельный процесс** (cron-worker) |
| 4 | **Scoring Engine** | Расчёт метрик: частота выступлений, охват, качество, рост, internal/external ratio | Модуль монолита |
| 5 | **Candidate Selector** | Формирование шорт-листа кандидатов на федеральные конференции по scoring-правилам | Модуль монолита |
| 6 | **REST API** | CRUD спикеров, событий, дашбордных данных; фильтрация, пагинация, экспорт | Модуль монолита |
| 7 | **Auth Service** | Аутентификация HR/DevRel через корпоративный SSO (OIDC) или пароль | Модуль монолита |
| 8 | **Notification Service** | Уведомления через email и Telegram об изменениях статуса, напоминания | Модуль монолита (очередь через Redis) |

### Обоснование выделения отдельных процессов

- **Telegram Bot** — требует persistent connection (long-polling) или webhook-эндпоинт; его жизненный цикл не должен зависеть от рестартов API.
- **Parser Service** — выполняет тяжёлые I/O-операции с внешними сайтами; может упасть из-за изменения вёрстки; запускается по расписанию; не должен влиять на отзывчивость API.

---

## 3. Компоненты, обязательные для MVP

### 3.1 Must Have (Месяц 1–2)

| Компонент | Функциональность |
|-----------|-----------------|
| **PostgreSQL-схема** | Таблицы: `speakers`, `events`, `talks`, `devrel_flags`, `scores`, `scoring_weights`, `candidate_lists`, `users` |
| **REST API** | CRUD спикеров, событий; загрузка отчётов; получение scores; эндпоинт candidate list |
| **Import Service** | Загрузка CSV/Excel → парсинг → нормализация → сохранение в `events` + `talks` |
| **Telegram Bot** | Регистрация выступления: тема, дата, ссылка, площадка, кол-во зрителей |
| **Scoring Engine** | Расчёт базовых метрик (кол-во выступлений, средний охват, recency, разнообразие площадок) |
| **Candidate Selector** | Фильтр по порогам scoring → список кандидатов |
| **Dashboard (frontend)** | Таблица спикеров с сортировкой/фильтрами, карточка спикера, candidate board |
| **Auth** | JWT + роли (admin, hr, devrel, viewer) |

### 3.2 Should Have (Месяц 2–3)

| Компонент | Функциональность |
|-----------|-----------------|
| **Parser Service** | Habr (статьи-доклады), YouTube (видео докладов по каналу компании), Timepad (ивенты) |
| **Notification Service** | Email-уведомления о попадании в шорт-лист; TG-напоминание спикеру о незаполненных данных |
| **Analytics-страница** | Графики: динамика выступлений по месяцам, top-спикеры, распределение по площадкам |
| **Экспорт** | CSV/PDF выгрузка candidate list и отчётов |

### 3.3 Nice to Have (Пост-MVP)

- Интеграция с Jira/Confluence для автоматического учёта внутренних tech talks
- ML-ранжирование кандидатов
- Gamification (бейджи, уровни спикеров)
- Публичный профиль спикера (витрина)

---

## 4. Потоки данных

### 4.1 Поток «Внутренние отчёты»

```
HR/DevRel ──► Dashboard (upload CSV) ──► REST API ──► Import Service
                                                          │
                                         парсинг + нормализация
                                                          │
                                                          ▼
                                                    PostgreSQL
                                              (events, talks)
                                                          │
                                                          ▼
                                                   Scoring Engine
                                                    (пересчёт)
```

**Кто пишет:** Import Service → `events`, `talks`  
**Кто читает:** Scoring Engine ← `events`, `talks`  
**Результат:** Scoring Engine → `scores`

### 4.2 Поток «Самотёк через Telegram-бота»

```
Спикер ──► Telegram Bot ──► REST API (internal) ──► PostgreSQL
                                                   (talks,
                                                    status = 'pending')
                                                          │
                                                          ▼
                                              HR верифицирует через Dashboard
                                              (status → 'approved' | 'rejected')
                                                          │
                                                          ▼
                                                   Scoring Engine
                                                    (пересчёт)
```

**Кто пишет:** Telegram Bot → `talks` (status=pending)  
**Кто читает:** Dashboard ← `talks` (pending); HR обновляет статус  
**Результат:** Scoring Engine → `scores`

### 4.3 Поток «Парсинг внешних площадок»

```
Cron (каждые 6ч) ──► Parser Service ──► Habr API / YouTube API / Timepad API
                                              │
                                         парсинг + матчинг со спикерами
                                              │
                                              ▼
                                        PostgreSQL
                                   (events, talks,
                                    source = 'external_parsed')
                                              │
                                              ▼
                                       Scoring Engine
                                        (пересчёт)
```

**Кто пишет:** Parser Service → `events`, `talks`  
**Кто читает:** Scoring Engine ← все talks; Candidate Selector ← scores  
**Результат:** Candidate Selector → `candidate_lists`

### 4.4 Поток «Формирование кандидатов»

```
Scoring Engine ──► scores (PostgreSQL) ──► Candidate Selector
                                                   │
                                     применение правил отбора:
                                     - score >= threshold
                                     - min N выступлений за 6 мес.
                                     - есть external площадка
                                                   │
                                                   ▼
                                            candidate_lists
                                                   │
                                    ┌──────────────┼───────────────┐
                                    ▼              ▼               ▼
                              Dashboard      Notification     CSV Export
                            (candidate        (email/TG)
                              board)
```

### 4.5 Сводная матрица «кто → куда»

| Писатель | Таблица/Хранилище | Читатель |
|----------|-------------------|----------|
| Import Service | `events`, `talks` | Scoring Engine, Dashboard |
| Telegram Bot | `talks` (pending) | Dashboard (HR-модерация) |
| Parser Service | `events`, `talks` | Scoring Engine, Dashboard |
| HR (Dashboard) | `talks.status` | Scoring Engine |
| Scoring Engine | `scores` | Candidate Selector, Dashboard |
| Candidate Selector | `candidate_lists` | Dashboard, Notification Service |
| Auth Service | `users`, `sessions` | REST API (middleware) |
| Dashboard | — (read-only) | REST API |

---

## 5. Технологический стек

### Обоснование: приоритет — скорость разработки, минимальный DevOps, зрелые библиотеки.

| Слой | Технология | Обоснование |
|------|-----------|-------------|
| **Backend** | **Python 3.12 + FastAPI** | Быстрый старт, async I/O, автогенерация OpenAPI, обширная экосистема парсинга |
| **ORM** | **SQLAlchemy 2.0 + Alembic** | Зрелый, типизированный, миграции из коробки |
| **БД** | **PostgreSQL 16** | Надёжная, JSON-поля для гибкой схемы, полнотекстовый поиск |
| **Кэш / Очередь** | **Redis 7** | Кэш дашборда, очередь задач (через простой pub/sub или список) |
| **Фоновые задачи** | **APScheduler** или **Celery (light)** | APScheduler для MVP (проще); Celery — если очередь задач вырастет |
| **Telegram Bot** | **aiogram 3** | Async, FSM для диалогов, middleware |
| **Парсинг** | **httpx + BeautifulSoup4** / **YouTube Data API v3** / **Timepad API** | httpx — async HTTP-клиент; BS4 — проверенный HTML-парсер |
| **Frontend** | **Next.js 14 (App Router) + TypeScript** | SSR/SSG, быстрый рендеринг таблиц, встроенный API-прокси |
| **UI-компоненты** | **shadcn/ui + Tailwind CSS** | Копипастимые компоненты, не зависят от npm-пакета, быстрая кастомизация |
| **Графики** | **Recharts** | Простая интеграция с React, достаточный набор чартов |
| **Аутентификация** | **FastAPI-Users** или ручной JWT | Быстрый старт; позже — подключение OIDC (Keycloak) |
| **Файловое хранилище** | **MinIO** (self-hosted S3) или локальная FS | Хранение загруженных отчётов |
| **CI/CD** | **GitHub Actions** | Линтинг, тесты, деплой |
| **Контейнеризация** | **Docker Compose** | Единый `docker-compose.yml` для всех сервисов |
| **Деплой (MVP)** | **VPS (2 vCPU, 4 GB RAM)** или **Railway / Fly.io** | Минимальные затраты на инфраструктуру |

### Структура репозитория (monorepo)

```
StarLift/
├── backend/
│   ├── app/
│   │   ├── api/              # FastAPI routers
│   │   ├── core/             # config, security, deps
│   │   ├── models/           # SQLAlchemy models
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── services/
│   │   │   ├── import_svc.py
│   │   │   ├── scoring.py
│   │   │   ├── candidate.py
│   │   │   └── notification.py
│   │   ├── parsers/
│   │   │   ├── habr.py
│   │   │   ├── youtube.py
│   │   │   └── timepad.py
│   │   └── main.py
│   ├── alembic/
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
├── bot/
│   ├── handlers/
│   ├── middlewares/
│   ├── states/
│   ├── main.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/              # Next.js App Router pages
│   │   ├── components/
│   │   ├── lib/              # API client, utils
│   │   └── types/
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
├── docs/
│   └── architecture.md
├── .env.example
└── README.md
```

---

## 6. Схема базы данных

### 6.1 ER-диаграмма

```
┌──────────────────────┐       ┌──────────────────────────────────────────┐
│       speakers       │       │                  events                  │
├──────────────────────┤       ├──────────────────────────────────────────┤
│ id           UUID PK │       │ id             UUID PK                  │
│ full_name    TEXT     │       │ title          TEXT                     │
│ department   TEXT     │       │ event_type     event_type_enum          │
│ city         TEXT     │       │ city           TEXT                     │
│ role         TEXT     │       │ event_date     DATE                     │
│ photo_url    TEXT     │       │ url            TEXT                     │
│ topics       TEXT[]   │       │ created_at     TIMESTAMPTZ              │
│ email        TEXT     │       │ updated_at     TIMESTAMPTZ              │
│ telegram_id  BIGINT   │       └──────────┬───────────────────────────────┘
│ created_at   TIMESTZ  │                  │
│ updated_at   TIMESTZ  │                  │ 1
└───────┬──────────────┘                  │
        │                                  │
        │ 1                                │
        │          ┌───────────────────────┘
        │          │
        ▼  N       ▼ N
┌──────────────────────────────────────────────────────┐
│                        talks                          │
├──────────────────────────────────────────────────────┤
│ id               UUID PK                              │
│ speaker_id       UUID FK → speakers.id                │
│ event_id         UUID FK → events.id                  │
│ topic            TEXT                                  │
│ talk_date        DATE                                  │
│ nps              SMALLINT (0..100)                     │
│ source           talk_source_enum                      │
│ recording_url    TEXT                                   │
│ photo_report     TEXT[]                                 │
│ status           talk_status_enum                      │
│ metadata         JSONB                                  │
│ created_at       TIMESTAMPTZ                            │
│ reviewed_by      UUID FK → users.id                    │
│ reviewed_at      TIMESTAMPTZ                            │
└──────────────────────────────────────────────────────┘
        │
        │ speaker_id
        ▼
┌──────────────────────────────────────────┐
│             devrel_flags                  │
├──────────────────────────────────────────┤
│ id             UUID PK                    │
│ speaker_id     UUID FK → speakers.id UQ   │
│ status         devrel_status_enum         │
│ comment        TEXT                        │
│ updated_by     UUID FK → users.id         │
│ updated_at     TIMESTAMPTZ                │
└──────────────────────────────────────────┘

┌──────────────────────────────┐    ┌────────────────────────────────────────┐
│        candidate_lists       │    │         candidate_list_items            │
├──────────────────────────────┤    ├────────────────────────────────────────┤
│ id            UUID PK        │◄───│ list_id      UUID FK                   │
│ title         TEXT           │    │ speaker_id   UUID FK → speakers.id     │
│ target_event  TEXT           │    │ composite_score FLOAT                  │
│ created_at    TIMESTAMPTZ    │    │ rank         INT                       │
│ created_by    UUID FK        │    │ status       candidate_status_enum     │
└──────────────────────────────┘    │ notes        TEXT                      │
                                    └────────────────────────────────────────┘

┌────────────────────────────────────────┐
│               users                     │
├────────────────────────────────────────┤
│ id             UUID PK                  │
│ email          TEXT UQ                  │
│ password_hash  TEXT                      │
│ full_name      TEXT                      │
│ role           user_role_enum           │
│ created_at     TIMESTAMPTZ              │
└────────────────────────────────────────┘

┌────────────────────────────────────────┐
│          scoring_weights               │
├────────────────────────────────────────┤
│ id             UUID PK                  │
│ metric_name    TEXT UQ                  │
│ weight         FLOAT                    │
│ description    TEXT                      │
│ updated_at     TIMESTAMPTZ              │
└────────────────────────────────────────┘
```

### 6.2 Enum-типы

```sql
-- Тип мероприятия
CREATE TYPE event_type_enum AS ENUM (
    'internal',          -- внутреннее (tech talk, demo day)
    'external'           -- внешнее (конференция, митап, подкаст)
);

-- Источник данных о выступлении
CREATE TYPE talk_source_enum AS ENUM (
    'internal',          -- загружено HR/DevRel из внутренних отчётов
    'self',              -- спикер сообщил сам (Telegram-бот, форма)
    'parser'             -- собрано автоматическим парсером
);

-- Статус модерации выступления
CREATE TYPE talk_status_enum AS ENUM (
    'pending',           -- на модерации
    'approved',          -- подтверждено
    'rejected'           -- отклонено
);

-- DevRel-статус спикера
CREATE TYPE devrel_status_enum AS ENUM (
    'recommended',       -- рекомендован для внешних конференций
    'development',       -- в развитии, требуется менторинг
    'not_recommended'    -- не рекомендован (причина в comment)
);

-- Роль пользователя платформы
CREATE TYPE user_role_enum AS ENUM (
    'admin',
    'hr',
    'devrel',
    'viewer'
);
```

> **Расширяемость:** добавление нового источника (`talk_source_enum`) — одна миграция `ALTER TYPE ... ADD VALUE`, без изменения кода. То же для `event_type_enum`.

### 6.3 Таблицы — DDL

```sql
-- ============================================================
-- 1. USERS (создаётся первой — на неё ссылаются другие таблицы)
-- ============================================================
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           TEXT UNIQUE NOT NULL,
    password_hash   TEXT NOT NULL,
    full_name       TEXT,
    role            user_role_enum NOT NULL DEFAULT 'viewer',
    created_at      TIMESTAMPTZ    NOT NULL DEFAULT now()
);

-- ============================================================
-- 2. SPEAKERS — спикеры
-- ============================================================
CREATE TABLE speakers (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name       TEXT        NOT NULL,          -- ФИО
    department      TEXT,                           -- подразделение
    city            TEXT,                           -- город
    role            TEXT,                           -- роль / должность
    photo_url       TEXT,                           -- ссылка на фото (S3 / CDN)
    topics          TEXT[]      DEFAULT '{}',       -- список тем (массив PostgreSQL)
    email           TEXT        UNIQUE,
    telegram_id     BIGINT      UNIQUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON COLUMN speakers.topics IS
    'Массив тегов/тем, по которым спикер выступает. Пример: {"Go","Микросервисы","DevOps"}';

-- ============================================================
-- 3. EVENTS — мероприятия
-- ============================================================
CREATE TABLE events (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title           TEXT            NOT NULL,       -- название мероприятия
    event_type      event_type_enum NOT NULL,       -- internal / external
    city            TEXT,                            -- город или 'online'
    event_date      DATE,                            -- дата проведения
    url             TEXT,                            -- ссылка на страницу мероприятия
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT now()
);

-- ============================================================
-- 4. TALKS — выступления (центральная фактовая таблица)
-- ============================================================
CREATE TABLE talks (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    speaker_id      UUID            NOT NULL REFERENCES speakers(id) ON DELETE CASCADE,
    event_id        UUID                     REFERENCES events(id)   ON DELETE SET NULL,
    topic           TEXT            NOT NULL,              -- тема доклада
    talk_date       DATE            NOT NULL,              -- дата выступления
    nps             SMALLINT        CHECK (nps BETWEEN 0 AND 100),  -- NPS оценка
    source          talk_source_enum NOT NULL,             -- internal / self / parser
    recording_url   TEXT,                                   -- ссылка на запись (видео / слайды)
    photo_report    TEXT[]          DEFAULT '{}',           -- массив URL фотоотчёта
    status          talk_status_enum NOT NULL DEFAULT 'pending',
    metadata        JSONB           DEFAULT '{}',           -- произвольные данные от парсера
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT now(),
    reviewed_by     UUID            REFERENCES users(id),
    reviewed_at     TIMESTAMPTZ
);

COMMENT ON COLUMN talks.nps IS
    'Net Promoter Score выступления (0–100). NULL означает, что NPS ещё не собран.';
COMMENT ON COLUMN talks.source IS
    'Откуда получены данные. "internal" — импорт HR, "self" — спикер через бота, "parser" — автоматический сбор.';
COMMENT ON COLUMN talks.photo_report IS
    'Массив URL на фотографии с выступления. Хранятся в S3/MinIO.';

-- ============================================================
-- 5. DEVREL_FLAGS — DevRel-статус спикера
-- ============================================================
CREATE TABLE devrel_flags (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    speaker_id      UUID                NOT NULL UNIQUE REFERENCES speakers(id) ON DELETE CASCADE,
    status          devrel_status_enum  NOT NULL DEFAULT 'development',
    comment         TEXT,                           -- комментарий DevRel-менеджера
    updated_by      UUID                REFERENCES users(id),
    updated_at      TIMESTAMPTZ         NOT NULL DEFAULT now()
);

COMMENT ON TABLE devrel_flags IS
    'Один спикер — одна запись. DevRel-команда устанавливает рекомендательный статус.';

-- ============================================================
-- 6. SCORES — агрегированные метрики спикера (материализованный кэш)
-- ============================================================
CREATE TABLE scores (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    speaker_id        UUID        NOT NULL UNIQUE REFERENCES speakers(id) ON DELETE CASCADE,
    total_talks       INT         NOT NULL DEFAULT 0,
    external_talks    INT         NOT NULL DEFAULT 0,
    talks_last_6m     INT         NOT NULL DEFAULT 0,   -- выступлений за последние 6 мес.
    avg_nps           FLOAT,                              -- средний NPS
    avg_audience      FLOAT       DEFAULT 0,
    recency_score     FLOAT       DEFAULT 0,
    diversity_score   FLOAT       DEFAULT 0,
    composite_score   FLOAT       DEFAULT 0,
    calculated_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE scores IS
    'Материализованный кэш метрик. Пересчитывается Scoring Engine при изменении talks.';
COMMENT ON COLUMN scores.talks_last_6m IS
    'Кол-во approved-выступлений за последние 6 месяцев. Пересчёт — при каждом recalculate.';

-- ============================================================
-- 7. CANDIDATE_LISTS и CANDIDATE_LIST_ITEMS — шорт-листы
-- ============================================================
CREATE TABLE candidate_lists (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title           TEXT        NOT NULL,
    target_event    TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by      UUID        REFERENCES users(id)
);

CREATE TABLE candidate_list_items (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    list_id           UUID  NOT NULL REFERENCES candidate_lists(id) ON DELETE CASCADE,
    speaker_id        UUID  NOT NULL REFERENCES speakers(id) ON DELETE CASCADE,
    composite_score   FLOAT,
    rank              INT,
    status            TEXT  NOT NULL DEFAULT 'proposed'
                      CHECK (status IN ('proposed','approved','contacted','confirmed','declined')),
    notes             TEXT,
    UNIQUE (list_id, speaker_id)
);

-- ============================================================
-- 8. SCORING_WEIGHTS — конфигурация весов формулы
-- ============================================================
CREATE TABLE scoring_weights (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_name     TEXT        UNIQUE NOT NULL,   -- 'total_talks', 'external_ratio', ...
    weight          FLOAT       NOT NULL DEFAULT 0.2,
    description     TEXT,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Начальные веса
INSERT INTO scoring_weights (metric_name, weight, description) VALUES
    ('total_talks',     0.15, 'Кол-во одобренных выступлений за 12 мес.'),
    ('external_ratio',  0.20, 'Доля внешних выступлений'),
    ('avg_nps',         0.20, 'Средний NPS по всем выступлениям'),
    ('recency_score',   0.25, 'Свежесть: экспоненциальное затухание'),
    ('diversity_score', 0.20, 'Разнообразие площадок и типов');
```

### 6.4 Связи между таблицами

| Связь | Тип | FK-колонка | ON DELETE | Описание |
|-------|-----|-----------|-----------|----------|
| `talks` → `speakers` | N : 1 | `talks.speaker_id` | CASCADE | Каждое выступление принадлежит одному спикеру |
| `talks` → `events` | N : 1 | `talks.event_id` | SET NULL | Выступление привязано к мероприятию (может быть без привязки) |
| `talks` → `users` | N : 1 | `talks.reviewed_by` | — | Кто провёл модерацию |
| `devrel_flags` → `speakers` | 1 : 1 | `devrel_flags.speaker_id` (UQ) | CASCADE | Один статус на спикера |
| `devrel_flags` → `users` | N : 1 | `devrel_flags.updated_by` | — | Кто установил статус |
| `scores` → `speakers` | 1 : 1 | `scores.speaker_id` (UQ) | CASCADE | Одна строка метрик на спикера |
| `candidate_list_items` → `candidate_lists` | N : 1 | `list_id` | CASCADE | Элемент принадлежит списку |
| `candidate_list_items` → `speakers` | N : 1 | `speaker_id` | CASCADE | Кандидат — спикер |

### 6.5 Индексы

```sql
-- ======================= SPEAKERS ===========================
CREATE INDEX idx_speakers_city        ON speakers (city);
CREATE INDEX idx_speakers_department  ON speakers (department);
CREATE INDEX idx_speakers_topics      ON speakers USING GIN (topics);
                -- GIN-индекс для поиска по массиву тем:
                -- WHERE topics @> ARRAY['DevOps']

-- ======================= EVENTS =============================
CREATE INDEX idx_events_type          ON events (event_type);
CREATE INDEX idx_events_date          ON events (event_date);
CREATE INDEX idx_events_city          ON events (city);
CREATE INDEX idx_events_type_date     ON events (event_type, event_date);
                -- составной: быстрая выборка «внешние за период»

-- ======================= TALKS (основная нагрузка) ==========
CREATE INDEX idx_talks_speaker        ON talks (speaker_id);
CREATE INDEX idx_talks_event          ON talks (event_id);
CREATE INDEX idx_talks_date           ON talks (talk_date);
CREATE INDEX idx_talks_source         ON talks (source);
CREATE INDEX idx_talks_status         ON talks (status);

-- Составные индексы для частых аналитических запросов:
CREATE INDEX idx_talks_speaker_date   ON talks (speaker_id, talk_date);
                -- «все выступления спикера X за период»

CREATE INDEX idx_talks_speaker_status_date
    ON talks (speaker_id, status, talk_date)
    WHERE status = 'approved';
                -- Partial index: только подтверждённые выступления.
                -- Покрывает: подсчёт выступлений за 6 мес., средний NPS.

CREATE INDEX idx_talks_nps
    ON talks (nps)
    WHERE nps IS NOT NULL;
                -- Быстрый расчёт среднего NPS

-- ======================= DEVREL_FLAGS =======================
-- speaker_id уже UNIQUE → автоматический btree-индекс

-- ======================= SCORES =============================
CREATE INDEX idx_scores_composite     ON scores (composite_score DESC);
                -- ranking / top-спикеры

-- ======================= CANDIDATE_LIST_ITEMS ===============
CREATE INDEX idx_cli_list             ON candidate_list_items (list_id);
CREATE INDEX idx_cli_speaker          ON candidate_list_items (speaker_id);
```

### 6.6 Вычисляемые поля и агрегации

Агрегированные метрики спикера **не хранятся в таблице `speakers`** — они рассчитываются Scoring Engine и кэшируются в таблице `scores`. Это разделение обеспечивает нормализацию и предсказуемость пересчёта.

#### Вычисляемые метрики (SQL-логика внутри Scoring Engine)

```sql
-- 1. Общее количество выступлений
SELECT COUNT(*) AS total_talks
  FROM talks
 WHERE speaker_id = :sid
   AND status = 'approved';

-- 2. Количество выступлений за последние 6 месяцев
SELECT COUNT(*) AS talks_last_6m
  FROM talks
 WHERE speaker_id = :sid
   AND status = 'approved'
   AND talk_date >= CURRENT_DATE - INTERVAL '6 months';

-- 3. Количество внешних выступлений
SELECT COUNT(*) AS external_talks
  FROM talks t
  JOIN events e ON e.id = t.event_id
 WHERE t.speaker_id = :sid
   AND t.status = 'approved'
   AND e.event_type = 'external';

-- 4. Средний NPS спикера
SELECT ROUND(AVG(nps)::numeric, 1) AS avg_nps
  FROM talks
 WHERE speaker_id = :sid
   AND status = 'approved'
   AND nps IS NOT NULL;

-- 5. Средний NPS за произвольный период (фильтр по дате)
SELECT ROUND(AVG(nps)::numeric, 1) AS avg_nps_period
  FROM talks
 WHERE speaker_id = :sid
   AND status = 'approved'
   AND nps IS NOT NULL
   AND talk_date BETWEEN :date_from AND :date_to;

-- 6. Diversity score (уникальные площадки)
SELECT COUNT(DISTINCT e.id)::float /
       GREATEST(COUNT(*)::float, 1) AS diversity_score
  FROM talks t
  JOIN events e ON e.id = t.event_id
 WHERE t.speaker_id = :sid
   AND t.status = 'approved'
   AND t.talk_date >= CURRENT_DATE - INTERVAL '12 months';

-- 7. Recency score (экспоненциальное затухание)
SELECT SUM(
         EXP(-0.05 * EXTRACT(DAY FROM CURRENT_DATE - talk_date))
       ) AS recency_score
  FROM talks
 WHERE speaker_id = :sid
   AND status = 'approved';

-- 8. Пакетный пересчёт всех спикеров (batch recalculate)
INSERT INTO scores (speaker_id, total_talks, external_talks, talks_last_6m,
                    avg_nps, recency_score, diversity_score, composite_score, calculated_at)
SELECT
    s.id,
    COALESCE(agg.total_talks, 0),
    COALESCE(agg.external_talks, 0),
    COALESCE(agg.talks_last_6m, 0),
    agg.avg_nps,
    COALESCE(agg.recency_score, 0),
    COALESCE(agg.diversity_score, 0),
    0,  -- composite_score вычисляется в Python с учётом scoring_weights
    now()
FROM speakers s
LEFT JOIN LATERAL (
    SELECT
        COUNT(*) FILTER (WHERE t.status = 'approved')                        AS total_talks,
        COUNT(*) FILTER (WHERE t.status = 'approved'
                           AND e.event_type = 'external')                    AS external_talks,
        COUNT(*) FILTER (WHERE t.status = 'approved'
                           AND t.talk_date >= CURRENT_DATE - INTERVAL '6 months') AS talks_last_6m,
        ROUND(AVG(t.nps) FILTER (WHERE t.nps IS NOT NULL
                                   AND t.status = 'approved')::numeric, 1)  AS avg_nps,
        SUM(EXP(-0.05 * EXTRACT(DAY FROM CURRENT_DATE - t.talk_date))
            ) FILTER (WHERE t.status = 'approved')                           AS recency_score,
        COUNT(DISTINCT e.id) FILTER (WHERE t.status = 'approved')::float /
            GREATEST(COUNT(*) FILTER (WHERE t.status = 'approved')::float, 1) AS diversity_score
    FROM talks t
    LEFT JOIN events e ON e.id = t.event_id
    WHERE t.speaker_id = s.id
) agg ON TRUE
ON CONFLICT (speaker_id)
DO UPDATE SET
    total_talks     = EXCLUDED.total_talks,
    external_talks  = EXCLUDED.external_talks,
    talks_last_6m   = EXCLUDED.talks_last_6m,
    avg_nps         = EXCLUDED.avg_nps,
    recency_score   = EXCLUDED.recency_score,
    diversity_score  = EXCLUDED.diversity_score,
    composite_score  = EXCLUDED.composite_score,
    calculated_at    = EXCLUDED.calculated_at;
```

#### Итоговая формула `composite_score` (Python)

```python
# Scoring Engine: после SQL-пересчёта базовых метрик
# веса загружаются из таблицы scoring_weights

composite = (
    weights['total_talks']    * normalize(total_talks) +
    weights['external_ratio'] * normalize(external_talks / max(total_talks, 1)) +
    weights['avg_nps']        * normalize(avg_nps or 0) +
    weights['recency_score']  * normalize(recency_score) +
    weights['diversity_score'] * normalize(diversity_score)
)
```

#### Какие поля вычисляемые, какие хранимые

| Поле | Таблица | Тип | Комментарий |
|------|---------|-----|-------------|
| `total_talks` | `scores` | **Materialised** | Пересчитывается Scoring Engine по расписанию или по событию |
| `external_talks` | `scores` | **Materialised** | Аналогично |
| `talks_last_6m` | `scores` | **Materialised** | Скользящее окно — обязательно пересчитывать периодически |
| `avg_nps` | `scores` | **Materialised** | Среднее арифметическое по `approved` talks с NPS |
| `recency_score` | `scores` | **Materialised** | Экспоненциальное затухание |
| `diversity_score` | `scores` | **Materialised** | Уникальные площадки / всего |
| `composite_score` | `scores` | **Materialised** | Итоговый рейтинг; вычисляется в Python (нуждается в `scoring_weights`) |
| Среднее NPS за период | — | **On-the-fly** | Вычисляется SQL-запросом при запросе через API (фильтр `date_from`, `date_to`) |
| Кол-во выступлений за период | — | **On-the-fly** | Аналогично — `COUNT(*) ... WHERE talk_date BETWEEN ...` |
| Регионы спикера | — | **On-the-fly** | `SELECT DISTINCT e.city FROM talks t JOIN events e ...` |

### 6.7 Поддержка фильтрации по периоду

Все аналитические API-эндпоинты принимают параметры `date_from` и `date_to`. Ключевые запросы:

```sql
-- Все выступления спикера за период
SELECT * FROM talks
 WHERE speaker_id = :sid
   AND talk_date BETWEEN :date_from AND :date_to
   AND status = 'approved'
 ORDER BY talk_date DESC;
-- Использует: idx_talks_speaker_status_date (partial)

-- Top-спикеры по NPS за период
SELECT t.speaker_id, s.full_name,
       ROUND(AVG(t.nps)::numeric, 1) AS avg_nps,
       COUNT(*) AS talk_count
  FROM talks t
  JOIN speakers s ON s.id = t.speaker_id
 WHERE t.status = 'approved'
   AND t.nps IS NOT NULL
   AND t.talk_date BETWEEN :date_from AND :date_to
 GROUP BY t.speaker_id, s.full_name
 ORDER BY avg_nps DESC;

-- Выступления по регионам за период
SELECT e.city, COUNT(*) AS talk_count
  FROM talks t
  JOIN events e ON e.id = t.event_id
 WHERE t.status = 'approved'
   AND t.talk_date BETWEEN :date_from AND :date_to
 GROUP BY e.city
 ORDER BY talk_count DESC;
```

### 6.8 Дополнительные ограничения и триггеры

```sql
-- Автоматическое обновление updated_at
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_speakers_updated
    BEFORE UPDATE ON speakers
    FOR EACH ROW EXECUTE FUNCTION update_modified_column();

CREATE TRIGGER trg_events_updated
    BEFORE UPDATE ON events
    FOR EACH ROW EXECUTE FUNCTION update_modified_column();

CREATE TRIGGER trg_devrel_flags_updated
    BEFORE UPDATE ON devrel_flags
    FOR EACH ROW EXECUTE FUNCTION update_modified_column();
```

---

## 7. Риски архитектуры и митигация

### 7.1 Технические риски

| # | Риск | Вероятность | Влияние | Митигация |
|---|------|-------------|---------|-----------|
| R1 | **Парсеры ломаются при изменении вёрстки/API** внешних площадок | Высокая | Среднее | Изолировать парсеры в отдельный процесс; мониторинг через health-check эндпоинт; fallback — ручной импорт; версионирование парсеров |
| R2 | **Некорректный матчинг спикера** при парсинге (один человек — разные имена/ники) | Средняя | Высокое | Fuzzy-matching по имени + email/telegram_id; ручная верификация через Dashboard; таблица алиасов |
| R3 | **Scoring формула не отражает реальную ценность** спикера | Средняя | Высокое | Сделать веса метрик конфигурируемыми (YAML/DB); итеративная калибровка с DevRel-командой; A/B-тестирование формул |
| R4 | **Единая точка отказа** — монолит падает → всё недоступно | Низкая (MVP) | Высокое | Health-check + auto-restart через Docker; позже — выделение критических путей в отдельные сервисы |
| R5 | **Масштабирование** при росте числа спикеров/событий (>10K записей) | Низкая (MVP) | Среднее | Индексы на `speaker_id`, `event_date`, `source`; пагинация в API; кэширование через Redis; позже — read replicas |

### 7.2 Организационные риски

| # | Риск | Митигация |
|---|------|-----------|
| R6 | **HR не будут модерировать заявки** из Telegram-бота → данные протухают | Auto-approve через N дней без реакции; push-уведомления модератору |
| R7 | **Спикеры не мотивированы** заполнять данные через бота | Минимальный UX (3–4 шага); авто-подтягивание данных парсером; геймификация в пост-MVP |
| R8 | **Scope creep** — попытка добавить ML/gamification в MVP | Жёсткий feature freeze после фазы планирования; доска «ice box» для идей |

### 7.3 Риски безопасности

| # | Риск | Митигация |
|---|------|-----------|
| R9 | **Утечка персональных данных спикеров** | HTTPS everywhere; JWT с коротким TTL; RBAC; шифрование PII в БД (пост-MVP); аудит-лог |
| R10 | **Injection через парсер** (SSRF, XSS через сохранённые данные) | Санитизация всех входных данных; CSP-заголовки; парсер работает в ограниченном сетевом контексте |

---

## 8. План реализации по спринтам

```
Месяц 1 (Спринты 1–2)
├── Неделя 1–2: Инфраструктура
│   ├── Docker Compose (PostgreSQL, Redis, backend, frontend)
│   ├── CI/CD pipeline
│   ├── Схема БД + миграции (Alembic)
│   └── Auth (JWT + роли)
├── Неделя 3–4: Ядро
│   ├── REST API: CRUD спикеров, событий, talks
│   ├── Import Service (CSV/Excel)
│   ├── Dashboard: таблица спикеров, загрузка файлов
│   └── Базовый Scoring Engine

Месяц 2 (Спринты 3–4)
├── Неделя 5–6: Telegram Bot + Scoring
│   ├── Telegram Bot (aiogram): регистрация доклада
│   ├── Модерация talks в Dashboard
│   ├── Scoring Engine: полная формула
│   └── Candidate Selector: автоматический шорт-лист
├── Неделя 7–8: Dashboard
│   ├── Candidate Board (Kanban-стиль)
│   ├── Карточка спикера (история, score, график)
│   └── Фильтры и поиск

Месяц 3 (Спринты 5–6)
├── Неделя 9–10: Парсеры + Уведомления
│   ├── Parser: Habr, YouTube, Timepad
│   ├── Notification Service (email + TG)
│   └── Аналитическая страница (графики)
├── Неделя 11–12: Полировка + Деплой
│   ├── CSV/PDF-экспорт
│   ├── E2E-тесты
│   ├── Нагрузочное тестирование (light)
│   ├── Production deploy
│   └── Документация пользователя
```

---

## 9. API-контракт (ключевые эндпоинты)

```
GET    /api/v1/speakers                    # список спикеров (фильтры, пагинация)
GET    /api/v1/speakers/{id}               # карточка спикера
POST   /api/v1/speakers                    # создать спикера
PATCH  /api/v1/speakers/{id}               # обновить

GET    /api/v1/events                      # список мероприятий
POST   /api/v1/events                      # создать

GET    /api/v1/talks                      # выступления (фильтр по status, source, период)
POST   /api/v1/talks                      # создать выступление (бот / ручной)
PATCH  /api/v1/talks/{id}/review          # модерация (approve/reject)

POST   /api/v1/import/upload               # загрузка CSV/Excel
GET    /api/v1/import/history              # история импортов

GET    /api/v1/scores                      # все scores (с сортировкой)
GET    /api/v1/scores/{speaker_id}         # score конкретного спикера
POST   /api/v1/scores/recalculate         # пересчёт (admin)

GET    /api/v1/candidates/lists            # списки кандидатов
POST   /api/v1/candidates/lists            # создать список
GET    /api/v1/candidates/lists/{id}       # конкретный список
POST   /api/v1/candidates/generate         # автогенерация по правилам

GET    /api/v1/analytics/overview          # агрегированные метрики для дашборда

POST   /api/v1/auth/login                  # JWT
POST   /api/v1/auth/refresh                # refresh token
GET    /api/v1/auth/me                     # текущий пользователь
```

---

## 10. Формула Scoring (v1)

```python
composite_score = (
    w1 * normalized(total_talks) +
    w2 * normalized(external_talks / total_talks) +
    w3 * normalized(avg_audience) +
    w4 * recency_score +
    w5 * diversity_score
)
```

| Метрика | Описание | Вес по умолчанию |
|---------|----------|-----------------|
| `total_talks` | Кол-во одобренных выступлений за 12 месяцев | 0.15 |
| `external_ratio` | Доля внешних выступлений от общего числа | 0.20 |
| `avg_audience` | Средний размер аудитории | 0.20 |
| `recency_score` | Экспоненциальное затухание: свежие выступления весят больше | 0.25 |
| `diversity_score` | Кол-во уникальных площадок / типов мероприятий | 0.20 |

Веса хранятся в конфигурации (`scoring_config.yaml` или таблица `scoring_weights`) и могут быть изменены DevRel без деплоя.

---

## Резюме

StarLift MVP строится как **модульный монолит на Python (FastAPI) + Next.js**, с двумя выделенными процессами (Telegram-бот и парсер). Такая архитектура обеспечивает:

- **Быстрый старт** — минимум инфраструктуры, один Docker Compose
- **Чёткое разделение доменов** — каждый модуль отвечает за свою зону
- **Эволюционность** — модули легко выделяются в микросервисы при росте нагрузки
- **Прозрачные потоки данных** — три входа (импорт, бот, парсер) → единый пайплайн → scoring → кандидаты → дашборд
