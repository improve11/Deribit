# Deribit Price API

Сервис раз в минуту получает index price `btc_usd` и `eth_usd` из публичного API Deribit, сохраняет цену и Unix timestamp в PostgreSQL и предоставляет read-only API на FastAPI. Клиент биржи использует `aiohttp`, расписание и выполнение сбора обеспечивает Celery Beat и Celery Worker.

## Возможности

- Сбор двух index price через `public/get_index_price`.
- Хранение тикера, цены и времени получения в PostgreSQL.
- Запрос всей истории, последней цены и истории начиная с выбранной даты.
- Документация API доступна в Swagger UI по адресу `/docs`.

## Быстрый запуск через Docker Compose

Нужны Docker и Docker Compose.

```bash
docker compose up --build
```

Compose запускает API, PostgreSQL, Redis, Celery Worker и Celery Beat. После старта API доступно на `http://localhost:8000`; таблица создаётся при старте приложения. Для остановки используйте `docker compose down`. Данные PostgreSQL хранятся в именованном volume `postgres_data`; `docker compose down -v` удаляет эти данные.

Для локальной разработки скопируйте `.env.example` в `.env`, установите зависимости `pip install -e '.[dev]'`, запустите PostgreSQL и Redis, затем в отдельных терминалах запустите API, worker и beat:

```bash
uvicorn app.main:app --reload
celery -A app.celery_app:celery_app worker --loglevel=INFO
celery -A app.celery_app:celery_app beat --loglevel=INFO
```

## API

У каждого метода обязателен query-параметр `ticker`.

| Метод | Описание |
| --- | --- |
| `GET /prices?ticker=btc_usd` | Все сохранённые цены тикера в порядке возрастания времени |
| `GET /prices/latest?ticker=btc_usd` | Последняя сохранённая цена; если данных нет, возвращается `404` |
| `GET /prices?ticker=btc_usd&from_date=2025-01-01T00:00:00Z` | Цены начиная с даты (включительно), формат ISO 8601 |

Ответ содержит `ticker`, `price` и `timestamp` (Unix time в секундах). В `from_date` следует передавать UTC дату со знаком `Z` или явным смещением. Если зона не указана, значение трактуется как UTC.

Примеры:

```bash
curl 'http://localhost:8000/prices?ticker=btc_usd'
curl 'http://localhost:8000/prices/latest?ticker=eth_usd'
curl 'http://localhost:8000/prices?ticker=btc_usd&from_date=2025-01-01T00:00:00Z'
```

## Конфигурация

| Переменная | Назначение | Значение по умолчанию |
| --- | --- | --- |
| `DATABASE_URL` | SQLAlchemy URL PostgreSQL | `postgresql+psycopg://prices:prices@localhost:5432/prices` |
| `CELERY_BROKER_URL` | Брокер Celery | `redis://localhost:6379/0` |
| `CELERY_RESULT_BACKEND` | Backend результатов Celery | `redis://localhost:6379/1` |
| `DERIBIT_BASE_URL` | Базовый адрес Deribit API | `https://www.deribit.com/api/v2` |
| `COLLECTION_INTERVAL_SECONDS` | Интервал Celery Beat | `60` |
| `REQUEST_TIMEOUT_SECONDS` | Таймаут HTTP-запроса | `10` |

## Проверка

```bash
pip install -e '.[dev]'
pytest
```

## Design decisions

- **Разделение ответственности.** `DeribitClient` отвечает за HTTP, `PriceCollector` за сценарий сбора, `PriceRepository` за запросы к БД, а FastAPI-маршруты — за HTTP-контракт. Это упрощает замену клиента и изолированное тестирование логики.
- **Index price, а не последняя сделка.** Используется официальный публичный метод `public/get_index_price`, поскольку задание требует индексную цену валюты.
- **Периодический сбор в Celery.** Beat публикует задачу с настраиваемым интервалом; worker выполняет её. Redis выбран как простой брокер для локального запуска. Один запуск получает оба тикера параллельно, но сбой одного запроса не мешает сохранить результат другого.
- **Время наблюдения.** В таблицу записывается Unix timestamp в секундах на момент получения ответа. Deribit index endpoint отдаёт цену индекса, но не timestamp самой цены; поэтому это время сбора сервиса.
- **Денежное значение.** PostgreSQL `NUMERIC(24, 8)` сохраняет цену с фиксированной точностью. В JSON FastAPI сериализует её как десятичное число.
- **Фильтр даты.** `from_date` задаёт включительную нижнюю границу в UTC. Это однозначный и индексируемый вариант фильтрации истории.
- **Индексация.** Составной индекс `(ticker, timestamp)` ускоряет выборки истории и последней цены по тикеру.
- **Схема БД.** Для компактности тестового задания таблица создаётся через SQLAlchemy `create_all` при старте API. Для production следует добавить Alembic миграции и отдельную команду миграции перед развёртыванием.
- **Повторные попытки.** Celery повторяет задачу при непредвиденной ошибке. Ошибки по отдельным тикерам логируются, чтобы частичный сбой не терял успешную цену другого инструмента.


