"use client";

import { cn } from "@/lib/utils";

interface ScoreGaugeProps {
  score: number;
  tolerance: string;
}

const TOLERANCE_LABELS: Record<string, string> = {
  conservative: "安定型",
  moderate: "中立型",
  aggressive: "積極型",
};

function getGaugeColor(score: number): string {
  if (score <= 3) return "text-green-500";
  if (score <= 7) return "text-yellow-500";
  return "text-red-500";
}

function getStrokeColor(score: number): string {
  if (score <= 3) return "stroke-green-500";
  if (score <= 7) return "stroke-yellow-500";
  return "stroke-red-500";
}

export function ScoreGauge({ score, tolerance }: ScoreGaugeProps) {
  const clampedScore = Math.max(1, Math.min(10, score));
  const radius = 56;
  const strokeWidth = 8;
  const circumference = 2 * Math.PI * radius;
  const progress = clampedScore / 10;
  const dashOffset = circumference * (1 - progress);
  const toleranceLabel = TOLERANCE_LABELS[tolerance] ?? tolerance;

  return (
    <div className="flex flex-col items-center gap-3">
      <div className="relative inline-flex items-center justify-center">
        <svg
          width="144"
          height="144"
          viewBox="0 0 144 144"
          className="-rotate-90"
          role="img"
          aria-label={`リスクスコア: ${clampedScore} / 10`}
        >
          <title>{`リスクスコア: ${clampedScore} / 10`}</title>
          {/* Background track */}
          <circle
            cx="72"
            cy="72"
            r={radius}
            fill="none"
            className="stroke-muted"
            strokeWidth={strokeWidth}
          />
          {/* Progress arc */}
          <circle
            cx="72"
            cy="72"
            r={radius}
            fill="none"
            className={cn("transition-all duration-700", getStrokeColor(clampedScore))}
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={dashOffset}
          />
        </svg>

        {/* Center content */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span
            className={cn(
              "text-4xl font-bold tabular-nums",
              getGaugeColor(clampedScore)
            )}
          >
            {clampedScore}
          </span>
          <span className="text-xs text-muted-foreground">/ 10</span>
        </div>
      </div>

      <span className="text-sm font-medium text-muted-foreground">
        {toleranceLabel}
      </span>
    </div>
  );
}
