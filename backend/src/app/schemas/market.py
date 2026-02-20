"""Market-related Pydantic schemas."""

from datetime import date, datetime

from pydantic import BaseModel


class IndexData(BaseModel):
    value: float
    change_pct: float | None = None
    as_of: date | None = None


class BondData(BaseModel):
    value: float
    unit: str = "%"
    as_of: date | None = None


class ForexData(BaseModel):
    value: float
    change_pct: float | None = None
    as_of: date | None = None


class MarketSummaryResponse(BaseModel):
    updated_at: datetime | None = None
    indices: dict[str, IndexData] = {}
    bonds: dict[str, BondData] = {}
    forex: dict[str, ForexData] = {}
    disclaimer: str = "※ データは情報提供目的であり、リアルタイムではありません。"


class EconomicIndicatorResponse(BaseModel):
    indicator_type: str
    indicator_name: str
    value: float
    currency: str | None = None
    date: date
    source: str

    model_config = {"from_attributes": True}
