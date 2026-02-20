"use client";

import { useCallback, useRef, useState } from "react";
import { apiClient } from "@/lib/api-client";
import type { ChatMessage, PortfolioContext } from "@/types/api";

interface UseStreamChatReturn {
  messages: ChatMessage[];
  isLoading: boolean;
  error: string | null;
  sendMessage: (content: string) => Promise<void>;
  clearMessages: () => void;
}

export function useStreamChat(
  portfolioContext?: PortfolioContext
): UseStreamChatReturn {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const sendMessage = useCallback(
    async (content: string) => {
      setError(null);
      const userMessage: ChatMessage = { role: "user", content };
      const updatedMessages = [...messages, userMessage];
      setMessages(updatedMessages);
      setIsLoading(true);

      // Add placeholder for assistant response
      const assistantMessage: ChatMessage = { role: "assistant", content: "" };
      setMessages([...updatedMessages, assistantMessage]);

      try {
        abortRef.current = new AbortController();
        const response = await apiClient.streamChat({
          messages: updatedMessages,
          portfolio_context: portfolioContext,
        });

        const reader = response.body?.getReader();
        if (!reader) throw new Error("No response body");

        const decoder = new TextDecoder();
        let buffer = "";
        let assistantText = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          for (const line of lines) {
            if (!line.startsWith("data: ")) continue;
            const jsonStr = line.slice(6).trim();
            if (!jsonStr) continue;

            try {
              const event = JSON.parse(jsonStr);
              if (event.type === "text-delta") {
                assistantText += event.text;
                setMessages((prev) => {
                  const newMsgs = [...prev];
                  newMsgs[newMsgs.length - 1] = {
                    role: "assistant",
                    content: assistantText,
                  };
                  return newMsgs;
                });
              } else if (event.type === "error") {
                setError(event.message);
              }
            } catch {
              // Skip malformed JSON
            }
          }
        }
      } catch (err) {
        const message =
          err instanceof Error ? err.message : "チャットでエラーが発生しました。";
        setError(message);
        // Remove empty assistant message on error
        setMessages((prev) =>
          prev.filter((m) => m.role !== "assistant" || m.content !== "")
        );
      } finally {
        setIsLoading(false);
        abortRef.current = null;
      }
    },
    [messages, portfolioContext]
  );

  const clearMessages = useCallback(() => {
    setMessages([]);
    setError(null);
  }, []);

  return { messages, isLoading, error, sendMessage, clearMessages };
}
