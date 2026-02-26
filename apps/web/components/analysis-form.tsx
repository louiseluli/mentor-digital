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

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (text.trim().length < 10) {
      setError("Cole um texto com pelo menos 10 caracteres.");
      return;
    }
    setError("");
    setLoading(true);
    try {
      const res = await fetch(`${BASE_URL}/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: text.trim() }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        setError(data.detail ?? "Erro ao analisar. Tente novamente.");
        return;
      }
      const { content_id } = await res.json();
      router.push(`/analise/${content_id}`);
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
        className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm
                   placeholder:text-muted-foreground focus:outline-none focus:ring-2
                   focus:ring-ring resize-none disabled:opacity-50"
      />
      {error && (
        <p className="text-sm text-destructive">{error}</p>
      )}
      <button
        type="submit"
        disabled={loading || text.trim().length < 10}
        className="w-full rounded-md bg-primary px-4 py-2 text-sm font-medium
                   text-primary-foreground hover:bg-primary/90 disabled:opacity-50
                   transition-colors"
      >
        {loading ? "Analisando…" : "Analisar conteúdo"}
      </button>
    </form>
  );
}
