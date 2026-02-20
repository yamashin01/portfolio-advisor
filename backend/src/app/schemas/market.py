"""Market-related Pydantic schemas."""

from datetime import date, datetime

from pydantic import BaseModel


class IndexData(BaseModel):
    name: str
    symbol: str
    value: float | None = None
    change_pct: float | None = None
    as_of: date | None = None


class BondData(BaseModel):
    name: str
    indicator_type: str
    value: float | None = None
    as_of: date | None = None


class ForexData(BaseModel):
    pair: str
    rate: float | None = None
    change_pct: float | None = None
    as_of: date | None = None


class MarketSummaryResponse(BaseModel):
    updated_at: datetime | None = None
    indices: list[IndexData] = []
    bonds: list[BondData] = []
    forex: list[ForexData] = []
    disclaimer: str = "※ データは情報提供目的であり、リアルタイムではありません。"


class EconomicIndicatorResponse(BaseModel):
    indicator_type: str
    indicator_name: str
    value: float
    currency: str | None = None
    as_of: date | None = None
    source: str

    model_config = {"from_attributes": True}
