"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

const BASE_URL =
  process.env.NEXT_PUBLIC_BOT_API_URL ?? "http://localhost:8000";

export default function AnalysisForm() {
  const router = useRouter();
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (text.trim().length < 10) {
      setError("Cole um texto com pelo menos 10 caracteres.");
      return;
    }
    setError("");
    setLoading(true);
    try {
      const res = await fetch(`${BASE_URL}/chat/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: text.trim() }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        setError(data.detail ?? "Erro ao iniciar análise. Tente novamente.");
        return;
      }
      const { session_id, messages, state, content_id } = await res.json();
      sessionStorage.setItem(
        `chat_${session_id}`,
        JSON.stringify({ messages, state, content_id })
      );
      router.push(`/conversa/${session_id}`);
    } catch {
      setError("Não foi possível conectar ao servidor. Tente novamente.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="w-full space-y-4">
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Cole aqui o texto, notícia ou mensagem que quer verificar..."
        rows={6}
        disabled={loading}
        className="w-full rounded-md border border-border bg-hud-surface px-3 py-2.5
                   text-sm font-mono text-foreground placeholder:text-hud-muted
                   focus:outline-none hud-focus resize-none disabled:opacity-50"
      />
      {error && (
        <p className="text-xs font-mono text-hud-danger">{error}</p>
      )}
      <button
        type="submit"
        disabled={loading || text.trim().length < 10}
        className="w-full rounded-md bg-hud-accent px-4 py-2.5 text-sm font-mono
                   font-bold uppercase tracking-widest text-background
                   hover:opacity-90 disabled:opacity-40 transition-opacity"
      >
        {loading ? "Iniciando conversa…" : "Conversar com o Mentor"}
      </button>
    </form>
  );
}
