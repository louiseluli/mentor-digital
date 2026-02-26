/**
 * /analise/[content_id] — Página de análise (retro HUD layout)
 *
 * Desktop: 2 colunas
 *   Esquerda: Header HUD + aviso + Stats Panel + GDELT + Wikipedia + rodapé
 *   Direita:  Quest Log (verificações FC)
 */

import AnalysisHeader from "@/components/analysis-header";
import EvidenceScale from "@/components/evidence-scale";
import FactCheckSection from "@/components/factcheck-section";
import GDELTSection from "@/components/gdelt-section";
import WikipediaSection from "@/components/wikipedia-section";
import { fetchAnalysis } from "@/lib/api";
import type { FactCheckClaim } from "@/lib/api";
import type { Metadata } from "next";

interface Props {
  params: Promise<{ content_id: string }>;
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { content_id } = await params;
  return {
    title: `Análise ${content_id.slice(0, 8)}… — Mentor Digital`,
  };
}

/** Computa contagens simples dos vereditos FC para o aviso independente do risk_score. */
function fcVerdictCounts(
  allClaims: FactCheckClaim[]
): { falseCount: number; mixedCount: number } {
  let falseCount = 0;
  let mixedCount = 0;
  for (const claim of allClaims) {
    const rv = claim.reviews?.[0]?.rating_value ?? 0;
    if (rv >= 1 && rv <= 2) falseCount++;
    else if (rv >= 3 && rv <= 4) mixedCount++;
  }
  return { falseCount, mixedCount };
}

export default async function AnalisePage({ params }: Props) {
  const { content_id } = await params;
  const data = await fetchAnalysis(content_id);

  if (!data) {
    return (
      <main className="min-h-screen flex flex-col items-center justify-center p-8 text-center">
        <div className="max-w-md space-y-3">
          <p className="font-display text-4xl text-foreground">404</p>
          <h1 className="text-xl font-semibold">Análise não encontrada</h1>
          <p className="text-muted-foreground text-sm">
            Esta análise pode ter expirado (disponível por 7 dias) ou o link
            pode estar incorreto.
          </p>
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
      {/* ── Full-width header ──────────────────────────────────────────────── */}
      <AnalysisHeader
        query={data.query}
        analyzedAt={data.analyzed_at}
        wordCount={data.nlp.word_count}
        riskScore={data.risk_score}
      />

      {/* ── Warning banner (works without risk_score — raw FC counts) ─────── */}
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

      {/* ── 2-column grid ─────────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-[1fr_1.1fr] gap-6 items-start">
        {/* LEFT — Summary HUD */}
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

          {/* Rodapé pedagógico */}
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
          </footer>
        </div>

        {/* RIGHT — Quest Log */}
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
