from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import engine, get_session
from app.models import Base
from app.repositories import PriceRepository
from app.schemas import PriceResponse


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Deribit Price API", version="1.0.0", lifespan=lifespan)
Ticker = Annotated[str, Query(min_length=1, max_length=16, pattern=r"^[a-z0-9_]+$")]


@app.get("/prices", response_model=list[PriceResponse])
def get_prices(
    ticker: Ticker,
    session: Session = Depends(get_session),
    from_date: Annotated[datetime | None, Query(description="ISO 8601 date/time; returns prices at or after it")] = None,
) -> list[PriceResponse]:
    if from_date is None:
        from_timestamp = None
    elif from_date.tzinfo is None:
        from_timestamp = int(from_date.replace(tzinfo=timezone.utc).timestamp())
    else:
        from_timestamp = int(from_date.astimezone(timezone.utc).timestamp())
    records = PriceRepository(session).list_for_ticker(ticker, from_timestamp)
    return [PriceResponse.model_validate(record) for record in records]


@app.get("/prices/latest", response_model=PriceResponse)
def get_latest_price(ticker: Ticker, session: Session = Depends(get_session)) -> PriceResponse:
    record = PriceRepository(session).latest(ticker)
    if record is None:
        raise HTTPException(status_code=404, detail=f"No prices found for ticker '{ticker}'")
    return PriceResponse.model_validate(record)
