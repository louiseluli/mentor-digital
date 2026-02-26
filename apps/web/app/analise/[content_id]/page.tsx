/**
 * /analise/[content_id] — Página de análise de conteúdo
 */

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

/** Computa contagens simples dos vereditos FC para exibir aviso independente do risk_score. */
function fcVerdictCounts(
  allClaims: FactCheckClaim[]
): { falseCount: number; mixedCount: number; total: number } {
  let falseCount = 0;
  let mixedCount = 0;
  for (const claim of allClaims) {
    const rv = claim.reviews?.[0]?.rating_value ?? 0;
    if (rv >= 1 && rv <= 2) falseCount++;
    else if (rv >= 3 && rv <= 4) mixedCount++;
  }
  return { falseCount, mixedCount, total: allClaims.length };
}

export default async function AnalisePage({ params }: Props) {
  const { content_id } = await params;
  const data = await fetchAnalysis(content_id);

  if (!data) {
    return (
      <main className="min-h-screen flex flex-col items-center justify-center p-8 text-center">
        <div className="max-w-md space-y-3">
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
  const hasMixed = mixedCount > 0 && falseCount === 0;

  return (
    <main className="max-w-2xl mx-auto px-6 py-8 space-y-8">
      {/* Cabeçalho */}
      <header className="space-y-1">
        <p className="text-xs text-muted-foreground uppercase tracking-wider">
          Mentor Digital · Análise de Conteúdo
        </p>
        <h1 className="text-xl font-semibold leading-snug line-clamp-3">
          {data.query || "Conteúdo de mídia"}
        </h1>
        <p className="text-xs text-muted-foreground">
          Analisado em{" "}
          {new Date(data.analyzed_at).toLocaleString("pt-BR", {
            dateStyle: "short",
            timeStyle: "short",
          })}
          {data.nlp.word_count > 0 && <> · {data.nlp.word_count} palavras</>}
        </p>
      </header>

      {/* ── Aviso proeminente baseado nos fact-checks ────────────────────────── */}
      {hasVerifiedFalse && (
        <div
          role="alert"
          className="rounded-xl border-2 border-red-400 bg-red-50 px-5 py-4 space-y-1"
        >
          <p className="font-bold text-red-800 text-base">
            ⚠️ Cuidado: alegações similares foram verificadas como falsas
          </p>
          <p className="text-sm text-red-700">
            {falseCount} fact-check{falseCount > 1 ? "s" : ""} de agências
            verificadoras{mixedCount > 0 ? ` e ${mixedCount} com avaliação mista` : ""}{" "}
            foram encontrados para este conteúdo. Verifique a fonte antes de
            compartilhar.
          </p>
        </div>
      )}
      {hasMixed && !hasVerifiedFalse && (
        <div
          role="alert"
          className="rounded-xl border-2 border-amber-400 bg-amber-50 px-5 py-4 space-y-1"
        >
          <p className="font-bold text-amber-800 text-base">
            ⚠️ Atenção: informações contestadas ou parcialmente incorretas
          </p>
          <p className="text-sm text-amber-700">
            {mixedCount} fact-check{mixedCount > 1 ? "s" : ""} classificaram
            alegações similares como enganosas ou com contexto incompleto.
          </p>
        </div>
      )}

      {/* Balança da Evidência */}
      {!data.nlp.error && (
        <EvidenceScale
          urgency={data.nlp.urgency}
          claim={data.nlp.claim}
          manipulation={data.nlp.manipulation}
          riskScore={data.risk_score}
        />
      )}

      {/* Verificações de fatos */}
      <FactCheckSection
        pt={data.fact_check.pt}
        en={data.fact_check.en}
        brazilianFc={data.brazilian_fc}
      />

      {/* Cobertura midiática */}
      <GDELTSection por={data.gdelt.por} en={data.gdelt.en} />

      {/* Contexto da Wikipedia */}
      {data.wikipedia && (
        <WikipediaSection pt={data.wikipedia.pt} en={data.wikipedia.en} />
      )}

      {/* Rodapé pedagógico */}
      <footer className="border-t pt-6 text-xs text-muted-foreground space-y-1">
        <p>
          O Mentor Digital apoia o pensamento crítico — não substitui a
          verificação humana. Consulte veículos de fact-checking como{" "}
          <a
            href="https://www.aosfatos.org"
            target="_blank"
            rel="noopener noreferrer"
            className="underline underline-offset-2 hover:text-foreground"
          >
            Aos Fatos
          </a>
          {" e "}
          <a
            href="https://www.agenciapublica.org.br"
            target="_blank"
            rel="noopener noreferrer"
            className="underline underline-offset-2 hover:text-foreground"
          >
            Agência Pública
          </a>
          .
        </p>
        <p>Resultados disponíveis por 7 dias.</p>
      </footer>
    </main>
  );
}
