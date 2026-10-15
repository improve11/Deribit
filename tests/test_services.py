import pytest

from app.services import PriceCollector


class StubClient:
    async def fetch_supported_prices(self):
        return [("btc_usd", 65000.25, 1_700_000_000), ("eth_usd", 3200.5, 1_700_000_001)]


class StubRepository:
    def __init__(self):
        self.records = []

    def add(self, ticker, price, timestamp):
        self.records.append((ticker, price, timestamp))


@pytest.mark.asyncio
async def test_collector_persists_each_fetched_price():
    repository = StubRepository()
    collector = PriceCollector(StubClient(), repository)

    count = await collector.collect()

    assert count == 2
    assert repository.records == [
        ("btc_usd", 65000.25, 1_700_000_000),
        ("eth_usd", 3200.5, 1_700_000_001),
    ]
