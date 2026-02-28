# Shop

Интернет‑магазин продуктов на Django.

## Возможности

- Просмотр списка товаров и карточки товара.
- Регистрация и аутентификация пользователей.
- Просмотр профиля пользователя, изменение его данных.
- Корзина: добавление, изменение количества и удаление товаров.
- Внутренние административные страницы:
  - клиенты,
  - заказы (включая изменение статуса),
  - товары (добавление/редактирование),
  - статистика.

## Cтек

- **Python 3.12**
- **Django 5.2**
- **PostgreSQL 16**
- **Docker / Docker Compose**
- Дополнительно:
  - `python-decouple` для конфигурации через переменные окружения,
  - `psycopg2-binary` для подключения к PostgreSQL,
  - `Pillow` для работы с изображениями,
  - `django-phonenumber-field` для полей телефонных номеров.

## Запуск через Docker Compose

### 1. Подготовка

Создайте файл `.env` в корне проекта:

```env
SECRET_KEY=secret
DEBUG=True

DB_NAME=shop
DB_USER=postgres
DB_PASSWORD=my_pass
DB_HOST=db
DB_PORT=5432
```

> `DB_HOST=db` — имя сервиса базы данных из `docker-compose.yml`.

### 2. Сборка и запуск

```bash
docker compose up --build
```

После запуска приложение будет доступно на:

- http://localhost:8000

Если хотите создать суперпользователя:

```bash
docker compose exec web python manage.py createsuperuser
```
