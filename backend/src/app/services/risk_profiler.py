"""Risk profiling service - 8-question risk assessment with scoring."""


QUESTIONS = [
    {
        "id": 1,
        "question": "あなたの年齢を教えてください",
        "type": "single_choice",
        "options": [
            {"value": "20s", "label": "20代", "score_weight": 3},
            {"value": "30s", "label": "30代", "score_weight": 3},
            {"value": "40s", "label": "40代", "score_weight": 2},
            {"value": "50s", "label": "50代", "score_weight": 1},
            {"value": "60plus", "label": "60代以上", "score_weight": 0},
        ],
    },
    {
        "id": 2,
        "question": "投資の目的は何ですか？",
        "type": "single_choice",
        "options": [
            {"value": "retirement", "label": "老後の資金準備", "score_weight": 2},
            {"value": "education", "label": "教育資金", "score_weight": 1},
            {"value": "wealth_growth", "label": "資産を増やしたい", "score_weight": 3},
            {"value": "preservation", "label": "資産を守りたい", "score_weight": 0},
        ],
    },
    {
        "id": 3,
        "question": "投資期間はどれくらいを予定していますか？",
        "type": "single_choice",
        "options": [
            {"value": "short", "label": "1〜3年", "score_weight": 0},
            {"value": "medium", "label": "3〜10年", "score_weight": 2},
            {"value": "long", "label": "10年以上", "score_weight": 3},
        ],
    },
    {
        "id": 4,
        "question": "投資経験はありますか？",
        "type": "single_choice",
        "options": [
            {"value": "none", "label": "まったくない", "score_weight": 0},
            {"value": "beginner", "label": "1年未満", "score_weight": 1},
            {"value": "intermediate", "label": "1〜5年", "score_weight": 2},
            {"value": "advanced", "label": "5年以上", "score_weight": 3},
        ],
    },
    {
        "id": 5,
        "question": "投資した資産が1ヶ月で20%下落した場合、どうしますか？",
        "type": "single_choice",
        "options": [
            {"value": "sell_all", "label": "すべて売却する", "score_weight": 0},
            {"value": "sell_part", "label": "一部を売却する", "score_weight": 1},
            {"value": "hold", "label": "そのまま保持する", "score_weight": 2},
            {"value": "buy_more", "label": "買い増しする", "score_weight": 3},
        ],
    },
    {
        "id": 6,
        "question": "毎月の投資可能額はどれくらいですか？",
        "type": "single_choice",
        "options": [
            {"value": "under_10k", "label": "1万円未満", "score_weight": 0},
            {"value": "10k_30k", "label": "1〜3万円", "score_weight": 1},
            {"value": "30k_100k", "label": "3〜10万円", "score_weight": 2},
            {"value": "over_100k", "label": "10万円以上", "score_weight": 3},
        ],
    },
    {
        "id": 7,
        "question": "以下のうち、最も共感する投資方針はどれですか？",
        "type": "single_choice",
        "options": [
            {"value": "safety_first", "label": "元本割れはなるべく避けたい", "score_weight": 0},
            {"value": "balanced", "label": "多少のリスクは許容し、バランスよく運用したい", "score_weight": 2},
            {"value": "growth", "label": "リスクを取ってでも高いリターンを狙いたい", "score_weight": 3},
        ],
    },
    {
        "id": 8,
        "question": "緊急時に使える預貯金（生活費の3〜6ヶ月分）はありますか？",
        "type": "single_choice",
        "options": [
            {"value": "no", "label": "ない", "score_weight": 0},
            {"value": "partial", "label": "一部ある（3ヶ月未満）", "score_weight": 1},
            {"value": "yes", "label": "十分にある（6ヶ月以上）", "score_weight": 2},
        ],
    },
]

# Build lookup: question_id -> {value -> score_weight}
_SCORE_MAP: dict[int, dict[str, int]] = {}
_MAX_SCORES: dict[int, int] = {}
for q in QUESTIONS:
    _SCORE_MAP[q["id"]] = {opt["value"]: opt["score_weight"] for opt in q["options"]}
    _MAX_SCORES[q["id"]] = max(opt["score_weight"] for opt in q["options"])

MAX_POSSIBLE_SCORE = sum(_MAX_SCORES.values())

# Tolerance category descriptions
TOLERANCE_DESCRIPTIONS = {
    "conservative": "あなたのリスク許容度は「安定重視型」です。元本の安全性を重視し、債券を中心とした安定的なポートフォリオをおすすめします。",
    "moderate": "あなたのリスク許容度は「バランス型」です。長期投資を前提に、株式と債券をバランスよく組み合わせたポートフォリオをおすすめします。",
    "aggressive": "あなたのリスク許容度は「積極型」です。高いリターンを目指し、株式を中心としたポートフォリオをおすすめします。リスクも相応に高くなります。",
}

STRATEGY_MAP = {
    "conservative": "min_volatility",
    "moderate": "hrp",
    "aggressive": "max_sharpe",
}


class RiskProfiler:
    """Stateless risk tolerance scoring service.

    Score calculation:
    1. Sum each question's score_weight
    2. Normalize to 0-1 range
    3. Scale to 1-10: round(normalized * 9) + 1
    4. Categorize: 1-3=conservative, 4-7=moderate, 8-10=aggressive
    """

    def get_questions(self) -> list[dict]:
        return QUESTIONS

    def calculate_score(self, answers: list[dict]) -> dict:
        """Calculate risk score from answers.

        Args:
            answers: List of {"question_id": int, "value": str}

        Returns:
            dict with risk_score, risk_tolerance, investment_horizon,
            investment_experience, recommended_strategy, description
        """
        raw_score = 0
        investment_horizon = "medium"
        investment_experience = "none"

        for answer in answers:
            qid = answer["question_id"]
            value = answer["value"]

            score_map = _SCORE_MAP.get(qid)
            if score_map is None:
                continue

            weight = score_map.get(value, 0)
            raw_score += weight

            # Extract specific fields
            if qid == 3:
                investment_horizon = value
            elif qid == 4:
                investment_experience = value

        # Normalize and scale to 1-10
        normalized = raw_score / MAX_POSSIBLE_SCORE if MAX_POSSIBLE_SCORE > 0 else 0
        risk_score = round(normalized * 9) + 1
        risk_score = max(1, min(10, risk_score))

        # Categorize
        if risk_score <= 3:
            risk_tolerance = "conservative"
        elif risk_score <= 7:
            risk_tolerance = "moderate"
        else:
            risk_tolerance = "aggressive"

        return {
            "risk_score": risk_score,
            "risk_tolerance": risk_tolerance,
            "investment_horizon": investment_horizon,
            "investment_experience": investment_experience,
            "recommended_strategy": STRATEGY_MAP[risk_tolerance],
            "description": TOLERANCE_DESCRIPTIONS[risk_tolerance],
        }

    def get_recommended_strategy(self, risk_tolerance: str) -> str:
        return STRATEGY_MAP.get(risk_tolerance, "hrp")
