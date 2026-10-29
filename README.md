# Веб-сайт для аренды одежды

Дипломный проект: полноценный веб-сайт для публикации объявлений и аренды одежды.

## Возможности

- **Управление объявлениями** — создание, редактирование, удаление, одобрение
- **Фильтрация** — по цене (от/до) и городу
- **Поиск** — по названию объявления
- **Аренда** — оформление аренды с выбором дат
- **Оплата** — интеграция с ЮKassa
- **Комментарии** — оставление комментариев к объявлениям
- **Уведомления** — Telegram-бот для уведомлений об аренде
- **Пагинация** — по 10 объявлений на страницу

## Стек технологий

- **Backend:** Python 3.12, Django 5.x, Django REST Framework
- **Базы данных:** SQLite (dev) / PostgreSQL (prod)
- **Очереди сообщений:** RabbitMQ (aio_pika)
- **Telegram-бот:** aiogram 3.x
- **Оплата:** ЮKassa
- **API:** Swagger/OpenAPI документация
- **Контейнеризация:** Docker, Docker Compose
- **Тестирование:** pytest, Django TestCase

## Структура проекта

```
├── advertisements/   # Модуль объявлений, фильтров, оплат
├── api/              # REST API (сериаляйзеры, представления)
├── diplom/           # Настройки проекта, URL, конфиги
├── templates/        # HTML-шаблоны
├── tg_bot/           # Telegram-бот (consumer, handlers)
├── users/            # Модуль пользователей, профили
├── static/           # Статические файлы
├── docker-compose.yaml
└── Makefile
```

## Запуск проекта

### 1. Через Docker Compose (рекомендуется)

```bash
docker-compose up -d
```

Запускает RabbitMQ. Далее:

```bash
# Применение миграций
docker compose exec web python manage.py migrate

# Создание суперпользователя
docker compose exec web python manage.py createsuperuser

# Запуск сервера
docker compose up web worker bot
```

### 2. Локальный запуск

```bash
# Установка зависимостей
pip install uv
uv pip install -r pyproject.toml

# Применение миграций
python manage.py migrate

# Запуск сервера
make run
```

### 3. Запуск всех сервисов

```bash
# RabbitMQ
docker-compose up -d

# Django сервер
python manage.py runserver

# Celery worker / consumer
python manage.py shell < tg_bot/consumer.py

# Telegram-бот
python -m tg_bot
```

## URL-адреса

| Описание | URL |
|----------|-----|
| Главная | `/` |
| Список объявлений | `/advertisements` |
| Добавить объявление | `/advertisement/add/` |
| Поиск | `/search/` |
| Админ-панель | `/admin/` |
| API Swagger | `/api/docs/` |
| Вход | `/account/login/` |
| Регистрация | `/account/register/` |

## Переменные окружения

Создайте `.env` файл:

```env
TOKEN=<telegram_bot_token>
YOOKASSA_SHOP_ID=<yookassa_shop_id>
YOOKASSA_SECRET_KEY=<yookassa_secret_key>
```

## Тесты

```bash
python manage.py test
```

## Авторы

Родионов Георгий  
[george2066](https://t.me/george2066)  
george2066@yandex.ru
