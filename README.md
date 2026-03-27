# Проект Starlift (project-version1)

Это веб-приложение на базе Django.

## Структура проекта
- starlift/ - основная папка с кодом Django приложения (настройки, маршруты, представления).
- docs/ - документация к проекту, включая архитектуру.
- requirements.txt - зависимости проекта.

## Требования
- Python 3.10+ (или совместимая версия)
- Виртуальное окружение (рекомендуется)
- PostgreSQL (требуется psycopg2-binary)

## Установка и запуск

1. **Клонируйте репозиторий и перейдите в папку проекта:**
   `
   git clone <url-вашего-репозитория>
   cd project-version1
   `

2. **Создайте и активируйте виртуальное окружение:**
   `
   python -m venv .venv
   
   # Для Windows:
   .venv\Scripts\activate
   # Для macOS/Linux:
   source .venv/bin/activate
   `

3. **Установите зависимости:**
   `
   pip install -r requirements.txt
   `

4. **Выполните миграции базы данных:**
   По умолчанию используется база данных из PostgreSQL. Выполните:
   `ash
   cd starlift
   python manage.py migrate
   `

5. **Запустите локальный сервер разработки:**
   `
   python manage.py runserver
   `
   Сервер будет доступен по адресу http://127.0.0.1:8000/.
