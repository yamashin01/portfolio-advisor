"use client";

import { useMemo } from "react";
import type { ChatMessage } from "@/types/api";
import { cn } from "@/lib/utils";

interface MessageBubbleProps {
  message: ChatMessage;
}

function formatContent(content: string): React.ReactNode[] {
  const paragraphs = content.split(/\n{2,}/);

  return paragraphs.map((paragraph, pIdx) => {
    const segments = paragraph.split(/(\*\*[^*]+\*\*)/g);
    const children = segments.map((segment, sIdx) => {
      const boldMatch = segment.match(/^\*\*(.+)\*\*$/);
      if (boldMatch) {
        return (
          <strong key={sIdx} className="font-semibold">
            {boldMatch[1]}
          </strong>
        );
      }
      return <span key={sIdx}>{segment}</span>;
    });

    return (
      <p key={pIdx} className={pIdx > 0 ? "mt-2" : undefined}>
        {children}
      </p>
    );
  });
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";
  const formattedContent = useMemo(
    () => formatContent(message.content),
    [message.content]
  );

  return (
    <div
      className={cn("flex w-full", isUser ? "justify-end" : "justify-start")}
      role="listitem"
    >
      <div
        className={cn(
          "max-w-[80%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed",
          isUser
            ? "bg-primary text-primary-foreground rounded-br-md"
            : "bg-muted text-foreground rounded-bl-md"
        )}
      >
        <div className="whitespace-pre-line break-words">
          {formattedContent}
        </div>
      </div>
    </div>
  );
}
