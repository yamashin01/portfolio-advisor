"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { ProgressIndicator } from "@/components/risk-assessment/progress-indicator";
import { QuestionStep } from "@/components/risk-assessment/question-step";
import { useRiskAssessmentStore } from "@/stores/risk-assessment-store";
import { apiClient } from "@/lib/api-client";
import type { Question } from "@/types/risk-assessment";

export default function RiskAssessmentPage() {
  const router = useRouter();
  const [questions, setQuestions] = useState<Question[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const {
    currentStep,
    answers,
    isSubmitting,
    setAnswer,
    nextStep,
    prevStep,
    setIsSubmitting,
    setResult,
    reset,
  } = useRiskAssessmentStore();

  useEffect(() => {
    reset();
    apiClient
      .getQuestions()
      .then((res) => setQuestions(res.questions))
      .catch(() => setError("質問の読み込みに失敗しました。"))
      .finally(() => setLoading(false));
  }, [reset]);

  const currentQuestion = questions[currentStep];
  const isLastStep = currentStep === questions.length - 1;
  const hasAnswer = currentQuestion && answers[currentQuestion.id] !== undefined;

  const handleNext = async () => {
    if (isLastStep) {
      setIsSubmitting(true);
      setError(null);
      try {
        const answerList = Object.entries(answers).map(([qId, value]) => ({
          question_id: Number(qId),
          value,
        }));
        const result = await apiClient.calculateRisk({ answers: answerList });
        setResult(result);
        router.push("/risk-assessment/result");
      } catch {
        setError("診断結果の計算に失敗しました。もう一度お試しください。");
      } finally {
        setIsSubmitting(false);
      }
    } else {
      nextStep();
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <p className="text-muted-foreground">読み込み中...</p>
      </div>
    );
  }

  if (error && questions.length === 0) {
    return (
      <div className="flex min-h-[50vh] flex-col items-center justify-center gap-4">
        <p className="text-destructive">{error}</p>
        <Button onClick={() => window.location.reload()}>再読み込み</Button>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-xl px-4 py-8">
      <ProgressIndicator
        currentStep={currentStep + 1}
        totalSteps={questions.length}
      />

      {currentQuestion && (
        <div className="mt-8">
          <QuestionStep
            question={currentQuestion}
            onAnswer={(value) => setAnswer(currentQuestion.id, value)}
            selectedValue={answers[currentQuestion.id]}
          />
        </div>
      )}

      {error && (
        <p className="mt-4 text-center text-sm text-destructive">{error}</p>
      )}

      <div className="mt-8 flex justify-between">
        <Button
          variant="outline"
          onClick={prevStep}
          disabled={currentStep === 0}
        >
          ← 戻る
        </Button>
        <Button
          onClick={handleNext}
          disabled={!hasAnswer || isSubmitting}
        >
          {isSubmitting
            ? "計算中..."
            : isLastStep
              ? "診断結果を見る"
              : "次へ →"}
        </Button>
      </div>
    </div>
  );
}
