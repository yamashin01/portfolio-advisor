"use client";

import { Button } from "@/components/ui/button";

interface SuggestionChipsProps {
  onSelect: (suggestion: string) => void;
  disabled?: boolean;
}

const suggestions = [
  "リスクを下げたい",
  "もっと詳しく教えて",
  "他の戦略は？",
  "初心者向けに説明して",
] as const;

export function SuggestionChips({
  onSelect,
  disabled = false,
}: SuggestionChipsProps) {
  return (
    <div
      className="flex gap-2 overflow-x-auto pb-1 scrollbar-none"
      role="group"
      aria-label="おすすめの質問"
    >
      {suggestions.map((suggestion) => (
        <Button
          key={suggestion}
          variant="outline"
          size="sm"
          onClick={() => onSelect(suggestion)}
          disabled={disabled}
          className="shrink-0 rounded-full text-xs"
        >
          {suggestion}
        </Button>
      ))}
    </div>
  );
}
