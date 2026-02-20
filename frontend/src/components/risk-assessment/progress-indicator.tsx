"use client";

import { Progress } from "@/components/ui/progress";

interface ProgressIndicatorProps {
  currentStep: number;
  totalSteps: number;
}

export function ProgressIndicator({
  currentStep,
  totalSteps,
}: ProgressIndicatorProps) {
  const percentage = Math.round((currentStep / totalSteps) * 100);

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-sm">
        <span className="font-medium text-foreground">
          リスク診断 {currentStep}/{totalSteps}
        </span>
        <span className="text-muted-foreground">{percentage}%</span>
      </div>
      <Progress
        value={percentage}
        aria-label={`リスク診断の進捗: ${currentStep}問中${totalSteps}問完了`}
      />
    </div>
  );
}
