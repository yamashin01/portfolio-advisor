"""Portfolio-related Pydantic schemas."""

from pydantic import BaseModel, Field


# --- Request schemas ---

class PortfolioConstraints(BaseModel):
    max_single_asset_weight: float = 0.3
    include_markets: list[str] = ["jp", "us"]
    include_asset_types: list[str] = ["etf", "bond", "reit"]


class PortfolioGenerateRequest(BaseModel):
    risk_score: int = Field(..., ge=1, le=10)
    risk_tolerance: str = Field(..., pattern="^(conservative|moderate|aggressive)$")
    investment_horizon: str = Field(..., pattern="^(short|medium|long)$")
    strategy: str = "auto"
    investment_amount: int | None = None
    currency: str = "JPY"
    constraints: PortfolioConstraints | None = None


class AllocationInput(BaseModel):
    symbol: str
    weight: float = Field(..., ge=0, le=1)


class ExplainAllocationInput(BaseModel):
    symbol: str
    name_ja: str | None = None
    weight: float


class ExplainRequest(BaseModel):
    strategy: str
    risk_tolerance: str
    allocations: list[ExplainAllocationInput]
    metrics: dict | None = None


# --- Response schemas ---

class AssetSummary(BaseModel):
    symbol: str
    name_ja: str | None = None
    asset_type: str
    market: str


class AllocationResponse(BaseModel):
    asset: AssetSummary
    weight: float
    amount: float | None = None


class PortfolioMetrics(BaseModel):
    expected_return: float | None = None
    volatility: float | None = None
    sharpe_ratio: float | None = None


class RiskProfileSummary(BaseModel):
    risk_score: int
    risk_tolerance: str


class PortfolioResponse(BaseModel):
    name: str | None = None
    strategy: str
    risk_profile: RiskProfileSummary
    metrics: PortfolioMetrics
    allocations: list[AllocationResponse]
    currency: str


class ExplainResponse(BaseModel):
    explanation: str
