from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import PriceRecord


class PriceRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, ticker: str, price: float, timestamp: int) -> PriceRecord:
        record = PriceRecord(ticker=ticker, price=price, timestamp=timestamp)
        self._session.add(record)
        self._session.commit()
        self._session.refresh(record)
        return record

    def list_for_ticker(self, ticker: str, from_timestamp: int | None = None) -> list[PriceRecord]:
        statement = select(PriceRecord).where(PriceRecord.ticker == ticker)
        if from_timestamp is not None:
            statement = statement.where(PriceRecord.timestamp >= from_timestamp)
        return list(self._session.scalars(statement.order_by(PriceRecord.timestamp.asc())))

    def latest(self, ticker: str) -> PriceRecord | None:
        statement = (
            select(PriceRecord)
            .where(PriceRecord.ticker == ticker)
            .order_by(PriceRecord.timestamp.desc(), PriceRecord.id.desc())
            .limit(1)
        )
        return self._session.scalar(statement)
