from celery import Celery

from app.config import get_settings

settings = get_settings()
celery_app = Celery(
    "deribit_prices",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.tasks"],
)
celery_app.conf.update(
    beat_schedule={
        "collect-deribit-prices-every-minute": {
            "task": "app.tasks.collect_prices",
            "schedule": settings.collection_interval_seconds,
        }
    },
    timezone="UTC",
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
)
