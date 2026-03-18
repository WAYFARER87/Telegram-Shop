# Telegram Shop

Заготовка интернет-магазина в формате Telegram-бота с backend на FastAPI и bot-слоем на aiogram 3. Проект разделён на `api`, `bot`, `services`, `repositories`, `db`, `schemas`, использует async SQLAlchemy 2, PostgreSQL, Redis, Alembic и Docker Compose.

## Возможности

- Регистрация пользователя через `/start` и API.
- Каталог категорий и товаров.
- Активная корзина на пользователя.
- Оформление заказа через FSM checkout.
- Mock online payment и идемпотентный webhook.
- Public API и Admin API.
- Docker-окружение с `app`, `postgres`, `redis`.
- Базовые интеграционные тесты.

## Структура

```text
app/
  api/
  bot/
  core/
  db/
  integrations/
  repositories/
  schemas/
  services/
  main.py
alembic/
tests/
Dockerfile
docker-compose.yml
```

## Запуск локально

1. Создать окружение и установить зависимости:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Подготовить `.env`:

```bash
cp .env.example .env
```

3. Запустить инфраструктуру и приложение:

```bash
docker compose up --build
```

Приложение будет доступно на `http://localhost:8000`.

## Миграции

Применить миграции вручную:

```bash
alembic upgrade head
```

Откат:

```bash
alembic downgrade -1
```

## Webhook Telegram

Приложение принимает webhook на:

```text
POST /telegram/webhook
```

Пример настройки webhook:

```bash
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
  -d "url=https://your-domain.example.com/telegram/webhook"
```

## Основные ENV-переменные

- `APP_HOST`
- `APP_PORT`
- `DEBUG`
- `DATABASE_URL`
- `REDIS_URL`
- `BOT_TOKEN`
- `BASE_URL`
- `PAYMENT_PROVIDER`

См. пример в [.env.example](/Users/anton/Projects/Research/fastapi+aiogram/.env.example).

## Тесты

```bash
pytest
```

Тесты используют SQLite + fake Redis для изолированной проверки бизнес-логики API.
