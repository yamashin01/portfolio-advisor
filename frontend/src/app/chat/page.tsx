"use client";

import { ChatContainer } from "@/components/chat/chat-container";
import { ChatInput } from "@/components/chat/chat-input";
import { SuggestionChips } from "@/components/chat/suggestion-chips";
import { useStreamChat } from "@/hooks/use-stream-chat";
import { usePortfolioResultStore } from "@/stores/portfolio-result-store";
import type { PortfolioContext } from "@/types/api";

export default function ChatPage() {
  const portfolio = usePortfolioResultStore((s) => s.portfolio);

  const portfolioContext: PortfolioContext | undefined = portfolio
    ? {
        strategy: portfolio.strategy,
        risk_tolerance: portfolio.risk_profile.risk_tolerance,
        allocations: portfolio.allocations.map((a) => ({
          symbol: a.asset.symbol,
          name_ja: a.asset.name_ja || undefined,
          weight: a.weight,
        })),
        metrics:
          portfolio.metrics.expected_return !== null
            ? {
                expected_return: portfolio.metrics.expected_return!,
                volatility: portfolio.metrics.volatility!,
                sharpe_ratio: portfolio.metrics.sharpe_ratio!,
              }
            : undefined,
      }
    : undefined;

  const { messages, isLoading, error, sendMessage } =
    useStreamChat(portfolioContext);

  return (
    <div className="mx-auto flex h-[calc(100vh-8rem)] max-w-3xl flex-col px-4 py-4">
      <div className="mb-2">
        <h1 className="text-lg font-bold">AIアドバイザー</h1>
        <p className="text-xs text-muted-foreground">
          ※ 教育目的の情報提供です。投資助言ではありません。
        </p>
      </div>

      <div className="flex-1 overflow-hidden">
        <ChatContainer messages={messages} isLoading={isLoading} />
      </div>

      {error && (
        <p className="py-1 text-center text-sm text-destructive">{error}</p>
      )}

      {messages.length === 0 && (
        <SuggestionChips onSelect={sendMessage} disabled={isLoading} />
      )}

      <div className="pt-2">
        <ChatInput onSend={sendMessage} isLoading={isLoading} />
      </div>
    </div>
  );
}
