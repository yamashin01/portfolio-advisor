"""Chat-related Pydantic schemas."""

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str


class PortfolioContextAllocation(BaseModel):
    symbol: str
    name_ja: str | None = None
    weight: float


class PortfolioContext(BaseModel):
    strategy: str | None = None
    risk_tolerance: str | None = None
    allocations: list[PortfolioContextAllocation] = []
    metrics: dict | None = None


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(..., min_length=1)
    portfolio_context: PortfolioContext | None = None
