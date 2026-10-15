from app.deribit_client import DeribitClient
from app.repositories import PriceRepository


class PriceCollector:
    def __init__(self, client: DeribitClient, repository: PriceRepository) -> None:
        self._client = client
        self._repository = repository

    async def collect(self) -> int:
        prices = await self._client.fetch_supported_prices()
        for ticker, price, timestamp in prices:
            self._repository.add(ticker, price, timestamp)
        return len(prices)
