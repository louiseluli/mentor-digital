"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import ChatInterface, {
  type ChatMessage,
  type ChatOption,
} from "@/components/chat-interface";

const BASE_URL =
  process.env.NEXT_PUBLIC_BOT_API_URL ?? "http://localhost:8000";

interface SessionSnapshot {
  messages: Array<{ type: string; body: string; options?: ChatOption[] }>;
  state: string;
  content_id: string;
}

function parseInitialMessages(
  raw: SessionSnapshot["messages"]
): { chatMessages: ChatMessage[]; options: ChatOption[] } {
  const chatMessages: ChatMessage[] = [];
  let options: ChatOption[] = [];

  for (const msg of raw) {
    if (msg.body) {
      chatMessages.push({ role: "bot", body: msg.body });
    }
    if (msg.options && msg.options.length > 0) {
      options = msg.options;
    }
  }

  return { chatMessages, options };
}

export default function ConversaPage() {
  const { session_id } = useParams<{ session_id: string }>();
  const router = useRouter();

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [options, setOptions] = useState<ChatOption[]>([]);
  const [state, setState] = useState<string>("");
  const [contentId, setContentId] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [analysisReady, setAnalysisReady] = useState(false);
  const [expired, setExpired] = useState(false);

  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    const raw = sessionStorage.getItem(`chat_${session_id}`);
    if (!raw) {
      setExpired(true);
      return;
    }
    const snapshot: SessionSnapshot = JSON.parse(raw);
    const { chatMessages, options: opts } = parseInitialMessages(
      snapshot.messages
    );
    setMessages(chatMessages);
    setOptions(opts);
    setState(snapshot.state);
    setContentId(snapshot.content_id);
  }, [session_id]);

  const stopPolling = useCallback(() => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
  }, []);

  useEffect(() => {
    if (analysisReady || !session_id || expired) return;

    pollingRef.current = setInterval(async () => {
      try {
        const res = await fetch(`${BASE_URL}/chat/${session_id}/status`);
        if (!res.ok) return;
        const data = await res.json();
        if (data.ready) {
          setAnalysisReady(true);
          stopPolling();
        }
      } catch {
        // silencia erros de polling
      }
    }, 3000);

    return stopPolling;
  }, [session_id, analysisReady, expired, stopPolling]);

  async function handleOption(optionId: string, optionTitle: string) {
    setLoading(true);
    setOptions([]);
    setMessages((prev) => [...prev, { role: "user", body: optionTitle }]);

    try {
      const res = await fetch(`${BASE_URL}/chat/reply/${session_id}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ option_id: optionId }),
      });

      if (!res.ok) {
        if (res.status === 404) {
          setExpired(true);
          return;
        }
        return;
      }

      const data = await res.json();
      const { chatMessages: newMsgs, options: newOpts } = parseInitialMessages(
        data.messages
      );

      setMessages((prev) => [...prev, ...newMsgs]);
      setOptions(newOpts);
      setState(data.state);
      setContentId(data.content_id);

      if (data.analysis_ready) {
        setAnalysisReady(true);
        stopPolling();
      }

      if (data.state === "end") {
        const snap = sessionStorage.getItem(`chat_${session_id}`);
        if (snap) {
          const parsed = JSON.parse(snap);
          parsed.content_id = data.content_id;
          sessionStorage.setItem(`chat_${session_id}`, JSON.stringify(parsed));
        }
      }
    } finally {
      setLoading(false);
    }
  }

  // ── Sessão expirada ───────────────────────────────────────────────────────
  if (expired) {
    return (
      <main className="min-h-screen flex flex-col items-center justify-center px-4 py-12">
        <div className="hud-panel rounded-xl p-8 w-full max-w-md text-center space-y-5">
          <p className="font-display text-4xl text-foreground">
            SESSÃO ENCERRADA
          </p>
          <p className="text-sm font-mono text-hud-muted">
            Esta conversa expirou ou foi aberta em outra aba. Comece uma nova
            análise na página inicial.
          </p>
          <button
            onClick={() => router.push("/")}
            className="rounded-md bg-hud-accent px-5 py-2.5 text-sm font-mono
                       font-bold uppercase tracking-widest text-background
                       hover:opacity-90 transition-opacity"
          >
            Voltar ao início
          </button>
        </div>
      </main>
    );
  }

  return (
    <main className="max-w-2xl mx-auto px-4 py-6 pb-16 space-y-4">
      {/* Cabeçalho */}
      <header className="hud-panel rounded-xl p-4 space-y-2">
        <p className="text-[10px] font-mono text-hud-muted uppercase tracking-[0.18em]">
          MENTOR DIGITAL · ANÁLISE GUIADA
        </p>
        <p className="text-xs font-mono text-hud-muted">
          Respondendo às perguntas você desenvolve seu senso crítico sobre o
          conteúdo antes de decidir compartilhá-lo.
        </p>
        {!analysisReady && state !== "" && state !== "end" && (
          <p className="text-xs font-mono text-hud-muted animate-pulse">
            ▶ Analisando fontes em segundo plano…
          </p>
        )}
        {analysisReady && state !== "end" && (
          <p className="text-xs font-mono text-hud-success">
            ✓ Análise de fontes concluída — disponível ao final da conversa.
          </p>
        )}
      </header>

      {/* Interface de chat */}
      <ChatInterface
        messages={messages}
        options={options}
        loading={loading}
        onOption={handleOption}
        contentId={state === "end" ? contentId : undefined}
      />
    </main>
  );
}
