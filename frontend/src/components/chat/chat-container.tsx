"use client";

import { useEffect, useRef } from "react";
import type { ChatMessage } from "@/types/api";
import { MessageBubble } from "./message-bubble";

interface ChatContainerProps {
  messages: ChatMessage[];
  isLoading: boolean;
}

function LoadingIndicator() {
  return (
    <div className="flex justify-start" role="status" aria-label="応答を生成中">
      <div className="flex items-center gap-1.5 rounded-2xl rounded-bl-md bg-muted px-4 py-3">
        <span className="size-1.5 animate-bounce rounded-full bg-muted-foreground/60 [animation-delay:-0.3s]" />
        <span className="size-1.5 animate-bounce rounded-full bg-muted-foreground/60 [animation-delay:-0.15s]" />
        <span className="size-1.5 animate-bounce rounded-full bg-muted-foreground/60" />
      </div>
    </div>
  );
}

export function ChatContainer({ messages, isLoading }: ChatContainerProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  return (
    <div
      className="flex-1 overflow-y-auto px-4 py-4"
      role="list"
      aria-label="チャット履歴"
    >
      {messages.length === 0 && !isLoading && (
        <div className="flex h-full items-center justify-center">
          <p className="text-sm text-muted-foreground">
            AIアドバイザーにポートフォリオについて質問できます。
          </p>
        </div>
      )}

      <div className="mx-auto flex max-w-3xl flex-col gap-3">
        {messages.map((message, index) => (
          <MessageBubble key={index} message={message} />
        ))}
        {isLoading && <LoadingIndicator />}
        <div ref={bottomRef} aria-hidden="true" />
      </div>
    </div>
  );
}
