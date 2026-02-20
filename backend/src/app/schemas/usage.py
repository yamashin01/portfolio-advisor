"""Usage-related Pydantic schemas."""

from pydantic import BaseModel


class DailyUsage(BaseModel):
    date: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    estimated_cost_usd: float
    budget_tokens: int
    remaining_tokens: int


class MonthlyUsage(BaseModel):
    month: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    estimated_cost_usd: float
    budget_tokens: int
    remaining_tokens: int


class UsageSummaryResponse(BaseModel):
    daily: DailyUsage
    monthly: MonthlyUsage
