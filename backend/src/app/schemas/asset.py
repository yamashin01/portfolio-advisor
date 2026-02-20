"""Asset-related Pydantic schemas."""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class LatestPrice(BaseModel):
    close: float
    date: date
    change_pct: float | None = None


class AssetResponse(BaseModel):
    symbol: str
    name: str
    name_ja: str | None = None
    asset_type: str
    market: str
    currency: str
    sector: str | None = None
    latest_price: LatestPrice | None = None

    model_config = {"from_attributes": True}


class AssetPriceResponse(BaseModel):
    date: date
    open: float | None = None
    high: float | None = None
    low: float | None = None
    close: float
    adj_close: float | None = None
    volume: int | None = None

    model_config = {"from_attributes": True}


class AssetPricesResponse(BaseModel):
    symbol: str
    period: str
    interval: str
    prices: list[AssetPriceResponse]
    data_source_note: str = "データは教育・情報提供目的です。投資判断の根拠として使用しないでください。"


class PaginatedAssetResponse(BaseModel):
    items: list[AssetResponse]
    total: int
    page: int
    per_page: int
    pages: int
