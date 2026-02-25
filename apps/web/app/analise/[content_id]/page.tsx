/**
 * /analise/[content_id] — Página de análise de conteúdo
 *
 * Micro-Batch 5.3: Balança da Evidência + fact-checks + cobertura GDELT.
 */

import EvidenceScale from "@/components/evidence-scale";
import FactCheckSection from "@/components/factcheck-section";
import GDELTSection from "@/components/gdelt-section";
import { fetchAnalysis } from "@/lib/api";
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

      {/* Balança da Evidência */}
      {!data.nlp.error && (
        <EvidenceScale
          urgency={data.nlp.urgency}
          claim={data.nlp.claim}
          manipulation={data.nlp.manipulation}
        />
      )}

      {/* Verificações de fatos */}
      <FactCheckSection pt={data.fact_check.pt} en={data.fact_check.en} />

      {/* Cobertura midiática */}
      <GDELTSection por={data.gdelt.por} en={data.gdelt.en} />

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
