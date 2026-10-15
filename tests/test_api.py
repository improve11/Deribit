from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.main import get_latest_price, get_prices
from app.models import PriceRecord


def make_record(ticker="btc_usd", price=65000, timestamp=1_700_000_000):
    return PriceRecord(ticker=ticker, price=price, timestamp=timestamp)


def test_latest_price_returns_404_when_ticker_has_no_records():
    session = MagicMock()
    session.scalar.return_value = None

    with pytest.raises(HTTPException) as error:
        get_latest_price("btc_usd", session)

    assert error.value.status_code == 404


def test_latest_price_returns_saved_record():
    session = MagicMock()
    session.scalar.return_value = make_record()

    response = get_latest_price("btc_usd", session)

    assert response.ticker == "btc_usd"
    assert response.price == 65000
    assert response.timestamp == 1_700_000_000


def test_get_prices_returns_records_for_ticker():
    session = MagicMock()
    session.scalars.return_value = [make_record()]

    response = get_prices("btc_usd", session)

    assert len(response) == 1
    assert response[0].ticker == "btc_usd"
