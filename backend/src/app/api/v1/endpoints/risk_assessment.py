"""Risk assessment endpoints."""

from fastapi import APIRouter

from src.app.schemas.risk_assessment import (
    QuestionsResponse,
    RiskAssessmentCalculateRequest,
    RiskAssessmentResponse,
)
from src.app.services.risk_profiler import RiskProfiler

router = APIRouter(prefix="/risk-assessment", tags=["risk-assessment"])
profiler = RiskProfiler()


@router.get("/questions", response_model=QuestionsResponse)
async def get_questions():
    """Get risk assessment questions."""
    return QuestionsResponse(questions=profiler.get_questions())


@router.post("/calculate", response_model=RiskAssessmentResponse)
async def calculate_risk(request: RiskAssessmentCalculateRequest):
    """Calculate risk score from answers. Stateless - no DB storage."""
    answers = [{"question_id": a.question_id, "value": a.value} for a in request.answers]
    result = profiler.calculate_score(answers)
    return RiskAssessmentResponse(**result)
