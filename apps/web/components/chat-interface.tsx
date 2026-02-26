"use client";

import { useEffect, useRef } from "react";
import Link from "next/link";

export interface ChatMessage {
  role: "bot" | "user";
  body: string;
}

export interface ChatOption {
  id: string;
  title: string;
}

interface Props {
  messages: ChatMessage[];
  options: ChatOption[];
  loading: boolean;
  onOption: (id: string, title: string) => void;
  contentId?: string; // definido quando state === "end"
}

export default function ChatInterface({
  messages,
  options,
  loading,
  onOption,
  contentId,
}: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  return (
    <div className="flex flex-col gap-4">
      {/* Histórico de mensagens */}
      <div className="flex flex-col gap-3">
        {messages.map((msg, i) => (
          <ChatBubble key={i} message={msg} />
        ))}

        {/* Indicador de carregamento */}
        {loading && (
          <div className="flex items-center gap-1.5 px-4 py-3 rounded-2xl rounded-tl-sm bg-secondary w-fit max-w-[85%]">
            <span className="w-2 h-2 rounded-full bg-muted-foreground animate-bounce [animation-delay:-0.3s]" />
            <span className="w-2 h-2 rounded-full bg-muted-foreground animate-bounce [animation-delay:-0.15s]" />
            <span className="w-2 h-2 rounded-full bg-muted-foreground animate-bounce" />
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Botões de opção */}
      {!loading && options.length > 0 && !contentId && (
        <div className="grid grid-cols-1 gap-2 pt-1">
          {options.map((opt) => (
            <button
              key={opt.id}
              onClick={() => onOption(opt.id, opt.title)}
              className="w-full rounded-xl border border-input bg-background px-4 py-3
                         text-sm text-left hover:bg-secondary transition-colors
                         focus:outline-none focus:ring-2 focus:ring-ring"
            >
              {opt.title}
            </button>
          ))}
        </div>
      )}

      {/* Card de conclusão */}
      {contentId && !loading && (
        <div className="rounded-xl border border-green-200 bg-green-50/40 p-5 space-y-3">
          <div className="space-y-1">
            <p className="text-sm font-medium text-green-800">
              Conversa concluída
            </p>
            <p className="text-xs text-green-700">
              Obrigado por pensar antes de compartilhar. A análise completa do
              conteúdo está pronta — com fact-checks, cobertura midiática e
              contexto da Wikipedia.
            </p>
          </div>
          <Link
            href={`/analise/${contentId}`}
            className="inline-flex items-center gap-1.5 rounded-lg bg-green-700 px-4 py-2
                       text-sm font-medium text-white hover:bg-green-800 transition-colors"
          >
            Ver análise completa →
          </Link>
        </div>
      )}
    </div>
  );
}

function ChatBubble({ message }: { message: ChatMessage }) {
  const isBot = message.role === "bot";
  return (
    <div className={`flex ${isBot ? "justify-start" : "justify-end"}`}>
      <div
        className={`
          max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap
          ${
            isBot
              ? "bg-secondary text-foreground rounded-tl-sm"
              : "bg-primary text-primary-foreground rounded-tr-sm"
          }
        `}
      >
        {message.body}
      </div>
    </div>
  );
}
