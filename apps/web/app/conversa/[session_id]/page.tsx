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

  // ── Inicialização a partir do sessionStorage ──────────────────────────────
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

  // ── Polling de status da análise ──────────────────────────────────────────
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

  // ── Processamento de opção escolhida ─────────────────────────────────────
  async function handleOption(optionId: string, optionTitle: string) {
    setLoading(true);
    setOptions([]);

    // Adiciona a resposta do usuário no histórico imediatamente
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

      // Ao finalizar, guarda content_id no sessionStorage para navegação de volta
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
      <main className="min-h-screen flex flex-col items-center justify-center p-8 text-center">
        <div className="max-w-md space-y-4">
          <p className="text-xl font-semibold">Sessão encerrada</p>
          <p className="text-sm text-muted-foreground">
            Esta conversa expirou ou foi aberta em outra aba. Comece uma nova
            análise na página inicial.
          </p>
          <button
            onClick={() => router.push("/")}
            className="rounded-md bg-primary px-4 py-2 text-sm font-medium
                       text-primary-foreground hover:bg-primary/90 transition-colors"
          >
            Voltar ao início
          </button>
        </div>
      </main>
    );
  }

  return (
    <main className="max-w-2xl mx-auto px-4 py-6 pb-16">
      {/* Cabeçalho */}
      <header className="mb-6 space-y-1">
        <p className="text-xs text-muted-foreground uppercase tracking-wider">
          Mentor Digital · Análise guiada
        </p>
        <p className="text-xs text-muted-foreground">
          Respondendo às perguntas você desenvolve seu senso crítico sobre o
          conteúdo antes de decidir compartilhá-lo.
        </p>
        {!analysisReady && state !== "" && state !== "end" && (
          <p className="text-xs text-muted-foreground animate-pulse">
            ⏳ Analisando fontes em segundo plano…
          </p>
        )}
        {analysisReady && state !== "end" && (
          <p className="text-xs text-green-700">
            ✅ Análise de fontes concluída — disponível ao final da conversa.
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
