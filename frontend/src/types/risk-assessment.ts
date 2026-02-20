export interface QuestionOption {
  value: string;
  label: string;
  score_weight: number;
}

export interface Question {
  id: number;
  question: string;
  type: string;
  options: QuestionOption[];
}

export interface QuestionsResponse {
  questions: Question[];
}

export interface RiskAssessmentAnswer {
  question_id: number;
  value: string;
}

export interface RiskAssessmentCalculateRequest {
  answers: RiskAssessmentAnswer[];
}

export interface RiskAssessmentResult {
  risk_score: number;
  risk_tolerance: string;
  investment_horizon: string;
  investment_experience: string;
  recommended_strategy: string | null;
  description: string | null;
}
