"""Risk assessment Pydantic schemas."""

from pydantic import BaseModel, Field


class RiskAssessmentAnswer(BaseModel):
    question_id: int
    value: str


class RiskAssessmentCalculateRequest(BaseModel):
    answers: list[RiskAssessmentAnswer] = Field(..., min_length=8, max_length=8)


class QuestionOption(BaseModel):
    value: str
    label: str
    score_weight: int


class Question(BaseModel):
    id: int
    question: str
    type: str
    options: list[QuestionOption]


class QuestionsResponse(BaseModel):
    questions: list[Question]


class RiskAssessmentResponse(BaseModel):
    risk_score: int
    risk_tolerance: str
    investment_horizon: str
    investment_experience: str
    recommended_strategy: str | None = None
    description: str | None = None
