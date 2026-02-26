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
  contentId?: string;
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
          <div className="flex items-center gap-1.5 px-4 py-3 rounded-xl rounded-tl-sm bg-hud-surface-2 w-fit max-w-[85%]">
            <span className="w-2 h-2 rounded-sm bg-hud-accent animate-bounce [animation-delay:-0.3s]" />
            <span className="w-2 h-2 rounded-sm bg-hud-accent animate-bounce [animation-delay:-0.15s]" />
            <span className="w-2 h-2 rounded-sm bg-hud-accent animate-bounce" />
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
              className="w-full rounded-lg border border-border bg-hud-surface px-4 py-3
                         text-sm font-mono text-left text-foreground
                         hover:bg-hud-surface-2 hover:border-hud-accent/40
                         transition-colors hud-focus"
            >
              ▸ {opt.title}
            </button>
          ))}
        </div>
      )}

      {/* Card de conclusão */}
      {contentId && !loading && (
        <div className="hud-panel rounded-xl p-5 space-y-3 border-hud-success/40">
          <div className="space-y-1">
            <p className="font-display text-2xl text-hud-success">
              ANÁLISE CONCLUÍDA
            </p>
            <p className="text-xs font-mono text-hud-muted">
              Obrigado por pensar antes de compartilhar. A análise completa do
              conteúdo está pronta — com fact-checks, cobertura midiática e
              contexto da Wikipedia.
            </p>
          </div>
          <Link
            href={`/analise/${contentId}`}
            className="inline-flex items-center gap-1.5 rounded-md bg-hud-accent
                       px-4 py-2 text-sm font-mono font-bold uppercase tracking-widest
                       text-background hover:opacity-90 transition-opacity"
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
        className={[
          "max-w-[85%] rounded-xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap",
          isBot
            ? "bg-hud-surface-2 text-foreground rounded-tl-sm"
            : "bg-hud-accent text-background rounded-tr-sm font-mono",
        ].join(" ")}
      >
        {message.body}
      </div>
    </div>
  );
}
