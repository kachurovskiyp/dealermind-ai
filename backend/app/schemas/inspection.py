from pydantic import BaseModel, Field


class ConfigurationReviewRead(BaseModel):
    make: str
    model: str
    configuration: str | None = None
    catalog_tier: str | None = None
    catalog_label: str | None = None
    knowledge_notes: list[str] = Field(default_factory=list)
    liquidity: list[dict[str, object]] = Field(default_factory=list)
    market_valuation: dict[str, object] | None = None
    registrations_30_days: int | None = None
    registrations_period: str | None = None
