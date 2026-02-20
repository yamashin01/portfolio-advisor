"use client";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface StrategyRecommendationProps {
  strategy: string | null;
  description: string | null;
  tolerance: string;
}

const STRATEGY_LABELS: Record<string, string> = {
  min_volatility: "安定重視",
  hrp: "バランス型",
  max_sharpe: "積極型",
  risk_parity: "リスクパリティ",
  equal_weight: "均等配分",
};

const TOLERANCE_LABELS: Record<string, string> = {
  conservative: "安定型",
  moderate: "中立型",
  aggressive: "積極型",
};

const TOLERANCE_VARIANTS: Record<string, "default" | "secondary" | "destructive"> = {
  conservative: "secondary",
  moderate: "default",
  aggressive: "destructive",
};

export function StrategyRecommendation({
  strategy,
  description,
  tolerance,
}: StrategyRecommendationProps) {
  const strategyLabel = strategy
    ? (STRATEGY_LABELS[strategy] ?? strategy)
    : "未決定";
  const toleranceLabel = TOLERANCE_LABELS[tolerance] ?? tolerance;
  const badgeVariant = TOLERANCE_VARIANTS[tolerance] ?? "default";

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>推奨戦略</CardTitle>
          <Badge variant={badgeVariant}>{toleranceLabel}</Badge>
        </div>
        <CardDescription>
          あなたのリスク許容度に基づく推奨投資戦略
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="rounded-lg border bg-muted/50 p-4">
          <p className="text-xl font-bold text-foreground">{strategyLabel}</p>
        </div>
        {description && (
          <p className="text-sm leading-relaxed text-muted-foreground">
            {description}
          </p>
        )}
      </CardContent>
    </Card>
  );
}
