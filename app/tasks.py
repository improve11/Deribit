import asyncio
import logging

from app.celery_app import celery_app
from app.database import SessionFactory
from app.deribit_client import DeribitClient
from app.repositories import PriceRepository
from app.services import PriceCollector

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.collect_prices", autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def collect_prices() -> int:
    with SessionFactory() as session:
        collector = PriceCollector(DeribitClient(), PriceRepository(session))
        return asyncio.run(collector.collect())
