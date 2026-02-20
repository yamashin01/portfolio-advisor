import enum
from datetime import datetime
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.models.base import Base

if TYPE_CHECKING:
    from src.app.models.asset_price import AssetPrice


class AssetType(str, enum.Enum):
    STOCK = "stock"
    ETF = "etf"
    BOND = "bond"
    REIT = "reit"


class Market(str, enum.Enum):
    JP = "jp"
    US = "us"


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(sa.BigInteger, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(sa.String(20), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(sa.String(200), nullable=False)
    name_ja: Mapped[str | None] = mapped_column(sa.String(200), nullable=True)
    asset_type: Mapped[str] = mapped_column(sa.String(20), nullable=False, index=True)
    market: Mapped[str] = mapped_column(sa.String(10), nullable=False, index=True)
    currency: Mapped[str] = mapped_column(sa.String(3), nullable=False)
    sector: Mapped[str | None] = mapped_column(sa.String(50), nullable=True)
    description: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(sa.Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now())
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()
    )

    prices: Mapped[list["AssetPrice"]] = relationship(
        "AssetPrice", back_populates="asset", cascade="all, delete-orphan"
    )

    __table_args__ = (
        sa.CheckConstraint("asset_type IN ('stock', 'etf', 'bond', 'reit')", name="ck_assets_asset_type"),
        sa.CheckConstraint("market IN ('jp', 'us')", name="ck_assets_market"),
        sa.CheckConstraint("currency IN ('JPY', 'USD')", name="ck_assets_currency"),
    )
