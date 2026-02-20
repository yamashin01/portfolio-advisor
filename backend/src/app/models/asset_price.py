from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.models.base import Base

if TYPE_CHECKING:
    from src.app.models.asset import Asset


class AssetPrice(Base):
    __tablename__ = "asset_prices"

    id: Mapped[int] = mapped_column(sa.BigInteger, primary_key=True, autoincrement=True)
    asset_id: Mapped[int] = mapped_column(sa.BigInteger, sa.ForeignKey("assets.id", ondelete="CASCADE"), nullable=False)
    date: Mapped[date] = mapped_column(sa.Date, nullable=False, index=True)
    open: Mapped[Decimal | None] = mapped_column(sa.Numeric(18, 6), nullable=True)
    high: Mapped[Decimal | None] = mapped_column(sa.Numeric(18, 6), nullable=True)
    low: Mapped[Decimal | None] = mapped_column(sa.Numeric(18, 6), nullable=True)
    close: Mapped[Decimal] = mapped_column(sa.Numeric(18, 6), nullable=False)
    adj_close: Mapped[Decimal | None] = mapped_column(sa.Numeric(18, 6), nullable=True)
    volume: Mapped[int | None] = mapped_column(sa.BigInteger, nullable=True)

    asset: Mapped["Asset"] = relationship("Asset", back_populates="prices")

    __table_args__ = (
        sa.UniqueConstraint("asset_id", "date", name="uq_asset_prices_asset_date"),
        sa.Index("ix_asset_prices_asset_id", "asset_id"),
    )
