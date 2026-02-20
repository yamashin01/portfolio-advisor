"use client";

import { useRouter } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { ScoreGauge } from "@/components/risk-assessment/score-gauge";
import { StrategyRecommendation } from "@/components/risk-assessment/strategy-recommendation";
import { useRiskAssessmentStore } from "@/stores/risk-assessment-store";

export default function RiskResultPage() {
  const router = useRouter();
  const result = useRiskAssessmentStore((s) => s.result);
  const reset = useRiskAssessmentStore((s) => s.reset);

  if (!result) {
    return (
      <div className="flex min-h-[50vh] flex-col items-center justify-center gap-4">
        <p className="text-muted-foreground">
          診断結果がありません。先にリスク診断を行ってください。
        </p>
        <Button asChild>
          <Link href="/risk-assessment">リスク診断を始める</Link>
        </Button>
      </div>
    );
  }

  const toleranceLabel: Record<string, string> = {
    conservative: "安定型（Conservative）",
    moderate: "バランス型（Moderate）",
    aggressive: "積極型（Aggressive）",
  };

  return (
    <div className="mx-auto max-w-xl px-4 py-8">
      <h1 className="mb-8 text-center text-2xl font-bold">
        あなたのリスク診断結果
      </h1>

      <div className="flex justify-center">
        <ScoreGauge score={result.risk_score} tolerance={result.risk_tolerance} />
      </div>

      <div className="mt-6 text-center">
        <p className="text-lg font-medium">
          リスク許容度:{" "}
          {toleranceLabel[result.risk_tolerance] || result.risk_tolerance}
        </p>
      </div>

      {result.description && (
        <div className="mt-6 rounded-lg border bg-muted/50 p-4">
          <h3 className="mb-2 font-semibold">あなたの特徴</h3>
          <p className="text-sm text-muted-foreground">{result.description}</p>
        </div>
      )}

      <div className="mt-6">
        <StrategyRecommendation
          strategy={result.recommended_strategy}
          description={null}
          tolerance={result.risk_tolerance}
        />
      </div>

      <div className="mt-8 flex flex-col items-center gap-3">
        <Button asChild size="lg" className="w-full max-w-xs">
          <Link
            href={`/portfolio?risk_score=${result.risk_score}&risk_tolerance=${result.risk_tolerance}&investment_horizon=${result.investment_horizon}&strategy=${result.recommended_strategy || "auto"}`}
          >
            ポートフォリオを生成する →
          </Link>
        </Button>
        <button
          onClick={() => {
            reset();
            router.push("/risk-assessment");
          }}
          className="text-sm text-muted-foreground hover:underline"
        >
          もう一度診断する
        </button>
      </div>
    </div>
  );
}
