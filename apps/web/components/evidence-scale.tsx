/**
 * EvidenceScale — Balança da Evidência
 *
 * Componente visual pedagógico que exibe o nível de atenção recomendado
 * com base nos sinais NLP. NÃO é um veredito de verdadeiro/falso —
 * é um indicador de características linguísticas preocupantes.
 *
 * Score composto: urgência × 0.4 + manipulação × 0.6
 * (manipulação tem peso maior pois é o sinal mais diagnóstico)
 */

import type { NLPSignal } from "@/lib/api";

interface Props {
  urgency: NLPSignal;
  claim: NLPSignal;
  manipulation: NLPSignal;
}

function computeScore(urgency: NLPSignal, manipulation: NLPSignal): number {
  return Math.min(1, urgency.score * 0.4 + manipulation.score * 0.6);
}

type Level = "low" | "moderate" | "high" | "critical";

function getLevel(score: number): Level {
  if (score < 0.25) return "low";
  if (score < 0.5) return "moderate";
  if (score < 0.75) return "high";
  return "critical";
}

const LEVEL_CONFIG: Record<
  Level,
  { label: string; description: string; color: string; bar: string; border: string }
> = {
  low: {
    label: "Linguagem Moderada",
    description:
      "Poucos sinais de linguagem manipulativa ou urgência artificial.",
    color: "text-green-700",
    bar: "bg-green-500",
    border: "border-green-200 bg-green-50/40",
  },
  moderate: {
    label: "Atenção Recomendada",
    description:
      "Alguns sinais linguísticos que merecem verificação antes de compartilhar.",
    color: "text-amber-700",
    bar: "bg-amber-400",
    border: "border-amber-200 bg-amber-50/40",
  },
  high: {
    label: "Vários Sinais de Alerta",
    description:
      "Linguagem com múltiplos padrões associados a desinformação. Verifique a fonte.",
    color: "text-orange-700",
    bar: "bg-orange-500",
    border: "border-orange-200 bg-orange-50/40",
  },
  critical: {
    label: "Alto Nível de Alerta",
    description:
      "Linguagem fortemente associada a conteúdo manipulativo. Muita cautela antes de compartilhar.",
    color: "text-red-700",
    bar: "bg-red-500",
    border: "border-red-200 bg-red-50/40",
  },
};

export default function EvidenceScale({ urgency, claim, manipulation }: Props) {
  const score = computeScore(urgency, manipulation);
  const pct = Math.round(score * 100);
  const level = getLevel(score);
  const cfg = LEVEL_CONFIG[level];

  return (
    <section className={`rounded-xl border p-5 space-y-4 ${cfg.border}`}>
      <div className="space-y-1">
        <p className="text-xs text-muted-foreground uppercase tracking-wider font-medium">
          Balança da Evidência
        </p>
        <h2 className={`text-lg font-semibold ${cfg.color}`}>{cfg.label}</h2>
        <p className="text-sm text-muted-foreground">{cfg.description}</p>
      </div>

      {/* Barra de progresso */}
      <div className="space-y-1">
        <div className="h-3 rounded-full bg-secondary overflow-hidden">
          <div
            className={`h-full rounded-full ${cfg.bar} transition-all`}
            style={{ width: `${pct}%` }}
          />
        </div>
        <p className="text-xs text-muted-foreground text-right">
          {pct}% de nível de alerta
        </p>
      </div>

      {/* Três sinais individuais */}
      <div className="grid grid-cols-3 gap-3">
        <SignalPill label="Urgência" score={urgency.score} />
        <SignalPill label="Manipulação" score={manipulation.score} />
        <SignalPill label="Afirmações" score={claim.score} />
      </div>

      {/* Evidências (frases detectadas) */}
      <EvidenceList
        items={[
          ...urgency.evidence.map((e) => ({ tag: "Urgência", text: e })),
          ...manipulation.evidence.map((e) => ({ tag: "Manipulação", text: e })),
          ...claim.evidence.map((e) => ({ tag: "Afirmação", text: e })),
        ]}
      />

      <p className="text-xs text-muted-foreground border-t pt-3">
        Esta análise detecta padrões linguísticos — não determina se o conteúdo
        é verdadeiro ou falso. Verifique sempre a fonte original antes de
        compartilhar.
      </p>
    </section>
  );
}

function SignalPill({ label, score }: { label: string; score: number }) {
  const pct = Math.round(score * 100);
  return (
    <div className="rounded-lg bg-secondary/60 p-3 text-center space-y-0.5">
      <p className="text-lg font-semibold tabular-nums">{pct}%</p>
      <p className="text-xs text-muted-foreground">{label}</p>
    </div>
  );
}

function EvidenceList({
  items,
}: {
  items: { tag: string; text: string }[];
}) {
  if (items.length === 0) return null;
  return (
    <ul className="space-y-1">
      {items.map((item, i) => (
        <li key={i} className="flex items-start gap-2 text-xs text-muted-foreground">
          <span className="shrink-0 rounded bg-secondary px-1.5 py-0.5 font-medium">
            {item.tag}
          </span>
          <span className="leading-relaxed">"{item.text}"</span>
        </li>
      ))}
    </ul>
  );
}
