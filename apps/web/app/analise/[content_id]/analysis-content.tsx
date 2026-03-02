"use client";

/**
 * AnalysisContent — renders analysis data or fetches client-side as fallback.
 *
 * Server component passes initialData when server-side fetch succeeds.
 * When initialData is null (server couldn't reach backend), this component
 * retries from the browser — which reliably reaches localhost:8000.
 */

import { useEffect, useState } from "react";
import AnalysisHeader from "@/components/analysis-header";
import EvidenceScale from "@/components/evidence-scale";
import FactCheckSection from "@/components/factcheck-section";
import GDELTSection from "@/components/gdelt-section";
import WikipediaSection from "@/components/wikipedia-section";
import FeedbackForm from "@/components/feedback-form";
import type { AnalysisResult, FactCheckClaim } from "@/lib/api";
import Link from "next/link";

const CLIENT_BASE_URL =
  process.env.NEXT_PUBLIC_BOT_API_URL ?? "http://localhost:8000";

interface Props {
  contentId: string;
  initialData?: AnalysisResult | null;
}

function fcVerdictCounts(allClaims: FactCheckClaim[]) {
  let falseCount = 0;
  let mixedCount = 0;
  for (const claim of allClaims) {
    const rv = claim.reviews?.[0]?.rating_value ?? 0;
    if (rv >= 1 && rv <= 2) falseCount++;
    else if (rv >= 3 && rv <= 4) mixedCount++;
  }
  return { falseCount, mixedCount };
}

export default function AnalysisContent({ contentId, initialData }: Props) {
  const [data, setData] = useState<AnalysisResult | null>(initialData ?? null);
  const [status, setStatus] = useState<string>(initialData ? "ready" : "loading");

  useEffect(() => {
    if (initialData) return;

    let cancelled = false;

    async function poll() {
      const url = `${CLIENT_BASE_URL}/analysis/${contentId}`;
      const maxRetries = 30;   // 30 × 2s = 60s max
      for (let i = 0; i < maxRetries; i++) {
        if (cancelled) return;
        setStatus(`Tentativa ${i + 1}/${maxRetries}…`);
        try {
          const res = await fetch(url);
          if (res.ok) {
            const json = await res.json();
            if (!cancelled) {
              setData(json);
              setStatus("ready");
            }
            return;
          }
          if (res.status === 202) {
            // Analysis still processing — keep polling
            setStatus(`Análise em andamento… (${i + 1}/${maxRetries})`);
          } else {
            setStatus(`Tentativa ${i + 1}: HTTP ${res.status}, aguardando…`);
          }
        } catch (err) {
          setStatus(`Tentativa ${i + 1}: erro de rede, aguardando…`);
        }
        await new Promise((r) => setTimeout(r, 2000));
      }
      if (!cancelled) setStatus("failed");
    }

    poll();
    return () => { cancelled = true; };
  }, [contentId, initialData]);

  if (status !== "ready" && status !== "failed") {
    return (
      <main className="min-h-screen flex flex-col items-center justify-center p-8 text-center">
        <div className="max-w-md space-y-3">
          <p className="font-mono text-sm text-muted-foreground animate-pulse">
            Carregando análise…
          </p>
          <p className="font-mono text-xs text-muted-foreground">{status}</p>
          <p className="font-mono text-[10px] text-muted-foreground/60">
            {CLIENT_BASE_URL}/analysis/{contentId.slice(0, 8)}…
          </p>
        </div>
      </main>
    );
  }

  if (!data || status === "failed") {
    return (
      <main className="min-h-screen flex flex-col items-center justify-center p-8 text-center">
        <div className="max-w-md space-y-3">
          <p className="font-display text-4xl text-foreground">404</p>
          <h1 className="text-xl font-semibold">Análise não encontrada</h1>
          <p className="text-muted-foreground text-sm">
            Esta análise pode ter expirado (disponível por 7 dias) ou o link
            pode estar incorreto.
          </p>
          <button
            onClick={() => window.location.reload()}
            className="mt-2 rounded-md bg-hud-accent px-4 py-2 text-sm font-mono
                       font-bold uppercase tracking-widest text-background
                       hover:opacity-90 transition-opacity"
          >
            Tentar novamente
          </button>
        </div>
      </main>
    );
  }

  const allFcClaims = [
    ...(data.fact_check.pt.results ?? []),
    ...(data.fact_check.en.results ?? []),
  ];
  const { falseCount, mixedCount } = fcVerdictCounts(allFcClaims);
  const hasVerifiedFalse = falseCount > 0;
  const hasMixed = mixedCount > 0 && !hasVerifiedFalse;

  return (
    <main className="max-w-5xl mx-auto px-4 sm:px-6 py-8 space-y-6">
      <AnalysisHeader
        query={data.query}
        analyzedAt={data.analyzed_at}
        wordCount={data.nlp.word_count}
        riskScore={data.risk_score}
      />

      {hasVerifiedFalse && (
        <div
          role="alert"
          className="rounded-xl border-2 border-hud-danger bg-hud-danger/10 px-5 py-4 space-y-1"
        >
          <p className="font-mono font-bold text-hud-danger text-sm uppercase tracking-wide">
            ⚠ Cuidado: alegações similares foram verificadas como falsas
          </p>
          <p className="text-sm text-hud-danger/80">
            {falseCount} fact-check{falseCount > 1 ? "s" : ""} de agências
            verificadoras
            {mixedCount > 0
              ? ` e ${mixedCount} com avaliação mista`
              : ""}{" "}
            foram encontrados. Verifique a fonte antes de compartilhar.
          </p>
        </div>
      )}
      {hasMixed && (
        <div
          role="alert"
          className="rounded-xl border-2 border-hud-warning bg-hud-warning/10 px-5 py-4 space-y-1"
        >
          <p className="font-mono font-bold text-hud-warning text-sm uppercase tracking-wide">
            ⚠ Atenção: informações contestadas ou parcialmente incorretas
          </p>
          <p className="text-sm text-hud-warning/80">
            {mixedCount} fact-check{mixedCount > 1 ? "s" : ""} classificaram
            alegações similares como enganosas ou com contexto incompleto.
          </p>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-[1fr_1.1fr] gap-6 items-start">
        <div className="space-y-6">
          {!data.nlp.error && (
            <EvidenceScale
              urgency={data.nlp.urgency}
              claim={data.nlp.claim}
              manipulation={data.nlp.manipulation}
              riskScore={data.risk_score}
            />
          )}

          <GDELTSection por={data.gdelt.por} en={data.gdelt.en} />

          {data.wikipedia && (
            <WikipediaSection pt={data.wikipedia.pt} en={data.wikipedia.en} />
          )}

          <footer className="text-[11px] font-mono text-hud-muted space-y-1 border-t border-border pt-4">
            <p>
              O Mentor Digital apoia o pensamento crítico — não substitui a
              verificação humana. Consulte{" "}
              <a
                href="https://www.aosfatos.org"
                target="_blank"
                rel="noopener noreferrer"
                className="underline underline-offset-2 hover:text-foreground transition-colors"
              >
                Aos Fatos
              </a>
              {" e "}
              <a
                href="https://www.agenciapublica.org.br"
                target="_blank"
                rel="noopener noreferrer"
                className="underline underline-offset-2 hover:text-foreground transition-colors"
              >
                Agência Pública
              </a>
              .
            </p>
            <p>Resultados disponíveis por 7 dias.</p>
            <div className="flex flex-wrap gap-3 pt-2">
              <Link
                href={`/balanca/${contentId}`}
                className="text-primary hover:underline font-medium"
              >
                Ver Balança da Evidência →
              </Link>
              <Link
                href="/aprender"
                className="text-primary hover:underline"
              >
                Módulos de aprendizagem →
              </Link>
              <Link
                href="/guia-acao"
                className="text-primary hover:underline"
              >
                Guia de ação →
              </Link>
            </div>
          </footer>

          <FeedbackForm contentId={contentId} />
        </div>

        <div className="lg:sticky lg:top-20">
          <FactCheckSection
            pt={data.fact_check.pt}
            en={data.fact_check.en}
            brazilianFc={data.brazilian_fc}
          />
        </div>
      </div>
    </main>
  );
}
