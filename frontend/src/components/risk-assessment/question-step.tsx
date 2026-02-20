"use client";

import { cn } from "@/lib/utils";
import type { Question } from "@/types/risk-assessment";

interface QuestionStepProps {
  question: Question;
  onAnswer: (value: string) => void;
  selectedValue?: string;
}

export function QuestionStep({
  question,
  onAnswer,
  selectedValue,
}: QuestionStepProps) {
  return (
    <div className="space-y-6">
      <h2 className="text-lg font-semibold leading-relaxed text-foreground">
        {question.question}
      </h2>

      <div
        role="radiogroup"
        aria-label={question.question}
        className="grid gap-3"
      >
        {question.options.map((option) => {
          const isSelected = selectedValue === option.value;

          return (
            <button
              key={option.value}
              type="button"
              role="radio"
              aria-checked={isSelected}
              onClick={() => onAnswer(option.value)}
              className={cn(
                "flex min-h-14 w-full items-center rounded-lg border px-4 py-3 text-left text-sm transition-all",
                "hover:bg-accent/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
                isSelected
                  ? "border-primary bg-primary/5 ring-2 ring-primary font-medium"
                  : "border-border bg-card"
              )}
            >
              <span
                className={cn(
                  "mr-3 flex h-5 w-5 shrink-0 items-center justify-center rounded-full border-2 transition-colors",
                  isSelected
                    ? "border-primary bg-primary"
                    : "border-muted-foreground/40"
                )}
              >
                {isSelected && (
                  <span className="h-2 w-2 rounded-full bg-primary-foreground" />
                )}
              </span>
              <span className="leading-relaxed">{option.label}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
