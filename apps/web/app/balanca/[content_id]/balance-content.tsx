/**
 * balance-content.tsx — Client component for Balança da Evidência
 *
 * Fetches balance data from API and renders an interactive
 * supports-vs-contradicts visualization.
 */

"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import PanelCard from "@/components/panel-card";
import type { BalanceData, BalanceEvidenceItem } from "@/lib/api";

const API_URL =
  process.env.NEXT_PUBLIC_BOT_API_URL ?? "http://127.0.0.1:8000";

// ── Source card ───────────────────────────────────────────────────────────────

function SourceCard({
  item,
  variant,
}: {
  item: BalanceEvidenceItem;
  variant: "supports" | "contradicts" | "neutral";
}) {
  const borderColor =
    variant === "contradicts"
      ? "border-red-400/40"
      : variant === "supports"
        ? "border-green-400/40"
        : "border-border";

  const typeLabels: Record<string, string> = {
    fact_check: "Fact-check",
    gdelt: "Notícia",
    google_news: "Google News",
    wikipedia: "Wikipedia",
    brazilian_fc: "Verificador BR",
  };

  return (
    <div
      className={`border ${borderColor} rounded-lg p-3 space-y-1.5 bg-card/50`}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          {item.title && (
            <p className="text-sm font-medium leading-tight line-clamp-2">
              {item.title}
            </p>
          )}
          {item.excerpt && (
            <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
              {item.excerpt}
            </p>
          )}
        </div>
        {item.is_fact_checker && (
          <span className="shrink-0 text-[10px] font-mono uppercase tracking-wider bg-blue-500/10 text-blue-600 dark:text-blue-400 px-1.5 py-0.5 rounded">
            FC
          </span>
        )}
      </div>

      <div className="flex items-center justify-between text-[11px] text-muted-foreground">
        <span className="font-mono">
          {typeLabels[item.source_type] ?? item.source_type}
          {item.source_name ? ` · ${item.source_name}` : ""}
        </span>
        {item.fact_check_rating && (
          <span className="font-semibold text-foreground">
            {item.fact_check_rating}
          </span>
        )}
      </div>

      {item.source_url && (
        <a
          href={item.source_url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-[11px] text-primary hover:underline block truncate"
        >
          {item.source_domain || item.source_url}
        </a>
      )}
    </div>
  );
}

// ── Balance bar ───────────────────────────────────────────────────────────────

function BalanceBar({ score }: { score: number }) {
  // Map -1..+1 to 0..100
  const position = ((score + 1) / 2) * 100;

  const getLabel = (s: number) => {
    if (s < -0.6) return "A maioria das fontes contradiz";
    if (s < -0.2) return "Mais fontes contradizem do que confirmam";
    if (s < 0.2) return "Evidências divididas";
    if (s < 0.6) return "Mais fontes confirmam do que contradizem";
    return "A maioria das fontes confirma";
  };

  return (
    <div className="space-y-2">
      <div
        className="relative h-3 bg-gradient-to-r from-red-400/60 via-amber-300/40 to-green-400/60 rounded-full overflow-hidden"
        role="meter"
        aria-label={`Balança: ${getLabel(score)}`}
        aria-valuenow={Math.round(score * 100)}
        aria-valuemin={-100}
        aria-valuemax={100}
      >
        <div
          className="absolute top-0 w-4 h-3 bg-foreground rounded-full transform -translate-x-1/2 transition-all duration-700"
          style={{ left: `${position}%` }}
        />
      </div>
      <p className="text-center text-xs text-muted-foreground font-mono">
        {getLabel(score)}
      </p>
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

export default function BalanceContent({ contentId }: { contentId: string }) {
  const [data, setData] = useState<BalanceData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/balance/${contentId}`);
      if (!res.ok) {
        setError("Análise não encontrada ou expirada.");
        return;
      }
      const json = await res.json();
      setData(json);
    } catch {
      setError("Erro ao carregar evidências.");
    } finally {
      setLoading(false);
    }
  }, [contentId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  if (loading) {
    return (
      <main className="max-w-2xl mx-auto px-6 py-12">
        <div className="text-center space-y-3">
          <div className="h-6 w-6 border-2 border-foreground/30 border-t-foreground rounded-full animate-spin mx-auto" />
          <p className="text-sm text-muted-foreground font-mono">
            Carregando evidências…
          </p>
        </div>
      </main>
    );
  }

  if (error || !data) {
    return (
      <main className="max-w-2xl mx-auto px-6 py-12 text-center space-y-4">
        <p className="text-sm text-muted-foreground">{error}</p>
        <Link
          href="/"
          className="text-sm text-primary hover:underline"
        >
          ← Analisar outro conteúdo
        </Link>
      </main>
    );
  }

  return (
    <main className="max-w-2xl mx-auto px-6 py-8 space-y-6">
      {/* Header */}
      <div className="text-center space-y-2">
        <h1 className="font-display text-3xl sm:text-4xl tracking-wide">
          BALANÇA DA EVIDÊNCIA
        </h1>
        <p className="text-sm text-muted-foreground max-w-md mx-auto">
          Ao observar essas evidências, o que <strong>VOCÊ</strong> conclui?
        </p>
      </div>

      {/* Balance score bar */}
      <PanelCard>
        <BalanceBar score={data.balance_score} />

        <div className="flex justify-between text-[10px] font-mono text-muted-foreground mt-1">
          <span>CONTRADIZ</span>
          <span>CONFIRMA</span>
        </div>
      </PanelCard>

      {/* Fact-checker verdict */}
      {data.fact_checker_verdict && (
        <PanelCard>
          <div className="space-y-1">
            <p className="text-xs font-mono text-muted-foreground uppercase tracking-wider">
              Agências de verificação dizem
            </p>
            <p className="text-sm">{data.fact_checker_verdict}</p>
          </div>
        </PanelCard>
      )}

      {/* Two columns */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Contradicting */}
        <div className="space-y-3">
          <h3 className="flex items-center gap-2 text-sm font-semibold">
            <span className="w-2.5 h-2.5 bg-red-500 rounded-full" />
            Fontes que questionam ({data.contradicting.length})
          </h3>
          {data.contradicting.length === 0 ? (
            <p className="text-xs text-muted-foreground pl-5">
              Nenhuma fonte contradiz diretamente.
            </p>
          ) : (
            data.contradicting.map((item, i) => (
              <SourceCard key={i} item={item} variant="contradicts" />
            ))
          )}
        </div>

        {/* Supporting */}
        <div className="space-y-3">
          <h3 className="flex items-center gap-2 text-sm font-semibold">
            <span className="w-2.5 h-2.5 bg-green-500 rounded-full" />
            Fontes que confirmam ({data.supporting.length})
          </h3>
          {data.supporting.length === 0 ? (
            <p className="text-xs text-muted-foreground pl-5">
              Nenhuma fonte confirma diretamente.
            </p>
          ) : (
            data.supporting.map((item, i) => (
              <SourceCard key={i} item={item} variant="supports" />
            ))
          )}
        </div>
      </div>

      {/* Neutral sources */}
      {data.neutral.length > 0 && (
        <div className="space-y-3">
          <h3 className="flex items-center gap-2 text-sm font-semibold">
            <span className="w-2.5 h-2.5 bg-amber-400 rounded-full" />
            Fontes relacionadas — sem posição clara ({data.neutral.length})
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {data.neutral.slice(0, 6).map((item, i) => (
              <SourceCard key={i} item={item} variant="neutral" />
            ))}
          </div>
          {data.neutral.length > 6 && (
            <p className="text-xs text-muted-foreground text-center">
              +{data.neutral.length - 6} fontes adicionais
            </p>
          )}
        </div>
      )}

      {/* Empowerment CTA */}
      <PanelCard>
        <div className="text-center space-y-2">
          <p className="text-sm">
            Lembre-se: quanto mais fontes diferentes você consultar, mais segura
            será sua conclusão.
          </p>
          <div className="flex flex-wrap justify-center gap-3 mt-2">
            <Link
              href={`/analise/${contentId}`}
              className="text-xs text-primary hover:underline"
            >
              ← Ver análise completa
            </Link>
            <Link
              href="/aprender"
              className="text-xs text-primary hover:underline"
            >
              Aprenda a analisar fontes →
            </Link>
          </div>
        </div>
      </PanelCard>
    </main>
  );
}
