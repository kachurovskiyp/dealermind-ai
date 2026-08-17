from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.domain import Market, Marketplace
from app.schemas.market import MarketCreate, MarketplaceCreate


def list_markets(db: Session) -> list[Market]:
    return list(db.scalars(select(Market).order_by(Market.code)))


def create_market(db: Session, payload: MarketCreate) -> Market:
    market = Market(**payload.model_dump())
    db.add(market)
    db.commit()
    db.refresh(market)
    return market


def list_marketplaces(db: Session) -> list[Marketplace]:
    return list(db.scalars(select(Marketplace).order_by(Marketplace.name)))


def create_marketplace(db: Session, payload: MarketplaceCreate) -> Marketplace:
    marketplace = Marketplace(**payload.model_dump())
    db.add(marketplace)
    db.commit()
    db.refresh(marketplace)
    return marketplace
