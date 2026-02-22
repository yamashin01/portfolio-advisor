"""Tests for risk assessment service and endpoints."""

import pytest

from src.app.services.risk_profiler import QUESTIONS, RiskProfiler


# ============================================================
# RiskProfiler service tests
# ============================================================


class TestRiskProfiler:
    def setup_method(self):
        self.profiler = RiskProfiler()

    def test_get_questions_returns_8_questions(self):
        questions = self.profiler.get_questions()
        assert len(questions) == 8

    def test_get_questions_all_have_options(self):
        for q in self.profiler.get_questions():
            assert len(q["options"]) >= 2

    def test_calculate_score_max(self):
        """All maximum-weight answers → score should be 10."""
        answers = []
        for q in QUESTIONS:
            max_opt = max(q["options"], key=lambda o: o["score_weight"])
            answers.append({"question_id": q["id"], "value": max_opt["value"]})

        result = self.profiler.calculate_score(answers)
        assert result["risk_score"] == 10
        assert result["risk_tolerance"] == "aggressive"
        assert result["recommended_strategy"] == "max_sharpe"

    def test_calculate_score_min(self):
        """All minimum-weight answers → score should be 1."""
        answers = []
        for q in QUESTIONS:
            min_opt = min(q["options"], key=lambda o: o["score_weight"])
            answers.append({"question_id": q["id"], "value": min_opt["value"]})

        result = self.profiler.calculate_score(answers)
        assert result["risk_score"] == 1
        assert result["risk_tolerance"] == "conservative"
        assert result["recommended_strategy"] == "min_volatility"

    def test_calculate_score_moderate(self):
        """Mid-range answers → moderate tolerance."""
        # Pick middle-weight options to land in moderate range
        answers = [
            {"question_id": 1, "value": "40s"},   # weight=2
            {"question_id": 2, "value": "retirement"},  # weight=2
            {"question_id": 3, "value": "medium"},  # weight=2
            {"question_id": 4, "value": "intermediate"},  # weight=2
            {"question_id": 5, "value": "hold"},   # weight=2
            {"question_id": 6, "value": "30k_100k"},  # weight=2
            {"question_id": 7, "value": "balanced"},  # weight=2
            {"question_id": 8, "value": "partial"},  # weight=1
        ]
        result = self.profiler.calculate_score(answers)
        assert 4 <= result["risk_score"] <= 7
        assert result["risk_tolerance"] == "moderate"
        assert result["recommended_strategy"] == "hrp"

    def test_calculate_score_extracts_horizon_and_experience(self):
        answers = [
            {"question_id": 1, "value": "20s"},
            {"question_id": 2, "value": "wealth_growth"},
            {"question_id": 3, "value": "long"},
            {"question_id": 4, "value": "advanced"},
            {"question_id": 5, "value": "buy_more"},
            {"question_id": 6, "value": "over_100k"},
            {"question_id": 7, "value": "growth"},
            {"question_id": 8, "value": "yes"},
        ]
        result = self.profiler.calculate_score(answers)
        assert result["investment_horizon"] == "long"
        assert result["investment_experience"] == "advanced"

    def test_calculate_score_includes_description(self):
        answers = [
            {"question_id": q["id"], "value": q["options"][0]["value"]}
            for q in QUESTIONS
        ]
        result = self.profiler.calculate_score(answers)
        assert result["description"]
        assert isinstance(result["description"], str)

    def test_get_recommended_strategy(self):
        assert self.profiler.get_recommended_strategy("conservative") == "min_volatility"
        assert self.profiler.get_recommended_strategy("moderate") == "hrp"
        assert self.profiler.get_recommended_strategy("aggressive") == "max_sharpe"
        assert self.profiler.get_recommended_strategy("unknown") == "hrp"


# ============================================================
# Endpoint tests
# ============================================================


class TestRiskAssessmentEndpoints:
    @pytest.mark.asyncio
    async def test_get_questions(self, client):
        response = await client.get("/api/v1/risk-assessment/questions")
        assert response.status_code == 200
        data = response.json()
        assert "questions" in data
        assert len(data["questions"]) == 8
        assert "Cache-Control" in response.headers

    @pytest.mark.asyncio
    async def test_calculate_risk(self, client):
        answers = [
            {"question_id": q["id"], "value": q["options"][0]["value"]}
            for q in QUESTIONS
        ]
        response = await client.post(
            "/api/v1/risk-assessment/calculate",
            json={"answers": answers},
        )
        assert response.status_code == 200
        data = response.json()
        assert "risk_score" in data
        assert "risk_tolerance" in data
        assert 1 <= data["risk_score"] <= 10

    @pytest.mark.asyncio
    async def test_calculate_risk_invalid_answers(self, client):
        # Too few answers
        response = await client.post(
            "/api/v1/risk-assessment/calculate",
            json={"answers": [{"question_id": 1, "value": "20s"}]},
        )
        assert response.status_code == 422
