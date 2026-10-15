import asyncio
import logging
import time

import aiohttp

from app.config import get_settings

logger = logging.getLogger(__name__)


class DeribitClient:
    """Async public API client for Deribit index prices."""

    def __init__(self, base_url: str | None = None, timeout_seconds: float | None = None) -> None:
        settings = get_settings()
        self._base_url = (base_url or settings.deribit_base_url).rstrip("/")
        self._timeout = timeout_seconds or settings.request_timeout_seconds

    async def get_index_price(self, ticker: str) -> tuple[float, int]:
        url = f"{self._base_url}/public/get_index_price"
        timeout = aiohttp.ClientTimeout(total=self._timeout)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, params={"index_name": ticker}) as response:
                response.raise_for_status()
                payload = await response.json()
        return float(payload["result"]["index_price"]), int(time.time())

    async def fetch_supported_prices(self) -> list[tuple[str, float, int]]:
        results = await asyncio.gather(
            self.get_index_price("btc_usd"),
            self.get_index_price("eth_usd"),
            return_exceptions=True,
        )
        prices: list[tuple[str, float, int]] = []
        for ticker, result in zip(("btc_usd", "eth_usd"), results, strict=True):
            if isinstance(result, Exception):
                logger.error("Failed to fetch %s index price: %s", ticker, result)
                continue
            price, timestamp = result
            prices.append((ticker, price, timestamp))
        return prices
