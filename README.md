# StarLift

> Платформа учёта и оценки корпоративных спикеров.

## Быстрый старт

### Предварительные требования

- Docker + Docker Compose
- (опционально) Python 3.12, Node.js 20

### Запуск через Docker

```bash
# Скопировать переменные окружения
cp .env.example .env

# Поднять все сервисы
docker compose up --build
```

Сервисы:

| Сервис   | URL                        |
|----------|----------------------------|
| API      | http://localhost:8000       |
| API Docs | http://localhost:8000/docs  |
| DB       | localhost:5432              |
| Redis    | localhost:6379              |

### Миграции БД

```bash
cd backend
alembic upgrade head
```

### Создание первого пользователя

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@company.com", "password": "admin123", "full_name": "Admin", "role": "admin"}'
```

### Загрузка CSV

Формат файла:

```
speaker_name,topic,talk_date,event_title,event_type,city,nps,recording_url,event_url
Иванов Иван,Микросервисы на Go,2026-01-15,GoConf 2026,external,Москва,85,,https://goconf.ru
```

## Архитектура

Подробная документация: [docs/architecture.md](docs/architecture.md)

## Структура проекта

```
StarLift/
├── backend/          # FastAPI + SQLAlchemy
│   ├── app/
│   │   ├── api/      # HTTP роутеры
│   │   ├── core/     # конфиг, auth, deps
│   │   ├── models/   # ORM модели
│   │   ├── schemas/  # Pydantic-схемы
│   │   ├── services/ # бизнес-логика
│   │   └── parsers/  # парсеры внешних площадок
│   └── alembic/      # миграции БД
├── bot/              # Telegram-бот (aiogram 3)
├── docs/             # архитектурная документация
└── docker-compose.yml
```

## API Endpoints

```
POST   /api/v1/auth/register
POST   /api/v1/auth/login
POST   /api/v1/auth/refresh
GET    /api/v1/auth/me

GET    /api/v1/speakers
POST   /api/v1/speakers
GET    /api/v1/speakers/{id}
PATCH  /api/v1/speakers/{id}

GET    /api/v1/events
POST   /api/v1/events
PATCH  /api/v1/events/{id}

GET    /api/v1/talks
POST   /api/v1/talks
PATCH  /api/v1/talks/{id}
PATCH  /api/v1/talks/{id}/review

POST   /api/v1/import/upload

GET    /api/v1/scores
GET    /api/v1/scores/{speaker_id}
POST   /api/v1/scores/recalculate

GET    /api/v1/candidates/lists
POST   /api/v1/candidates/lists
GET    /api/v1/candidates/lists/{id}
POST   /api/v1/candidates/generate

GET    /api/v1/analytics/overview

POST   /api/v1/bot/talks          # internal — from TG bot
```
