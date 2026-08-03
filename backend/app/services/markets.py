from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.domain import Market
from app.schemas.market import MarketCreate


def list_markets(db: Session) -> list[Market]:
    return list(db.scalars(select(Market).order_by(Market.code)))


def create_market(db: Session, payload: MarketCreate) -> Market:
    market = Market(**payload.model_dump())
    db.add(market)
    db.commit()
    db.refresh(market)
    return market
