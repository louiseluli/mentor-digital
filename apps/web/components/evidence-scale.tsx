/**
 * EvidenceScale — Balança da Evidência
 *
 * Com riskScore: exibe veredito multi-dimensional (linguística + fact-checks + cobertura).
 * Sem riskScore: comportamento legado (NLP only).
 */

import type { NLPSignal, RiskScore } from "@/lib/api";

interface Props {
  urgency: NLPSignal;
  claim: NLPSignal;
  manipulation: NLPSignal;
  riskScore?: RiskScore;
}

// ── Configurações visuais por nível ───────────────────────────────────────────

type Level = "low" | "moderate" | "high" | "critical";

const LEVEL_CONFIG: Record<
  Level,
  { label: string; description: string; color: string; bar: string; border: string; badge: string }
> = {
  low: {
    label: "Baixo risco",
    description: "Poucos sinais de linguagem manipulativa ou urgência artificial.",
    color: "text-green-700",
    bar: "bg-green-500",
    border: "border-green-200 bg-green-50/40",
    badge: "bg-green-100 text-green-800 border-green-300",
  },
  moderate: {
    label: "Risco moderado",
    description: "Alguns sinais que merecem verificação antes de compartilhar.",
    color: "text-amber-700",
    bar: "bg-amber-400",
    border: "border-amber-200 bg-amber-50/40",
    badge: "bg-amber-100 text-amber-800 border-amber-300",
  },
  high: {
    label: "Alto risco",
    description: "Múltiplos padrões associados a desinformação. Verifique a fonte.",
    color: "text-orange-700",
    bar: "bg-orange-500",
    border: "border-orange-200 bg-orange-50/40",
    badge: "bg-orange-100 text-orange-800 border-orange-300",
  },
  critical: {
    label: "Risco crítico",
    description: "Linguagem fortemente associada a conteúdo manipulativo. Muita cautela.",
    color: "text-red-700",
    bar: "bg-red-500",
    border: "border-red-200 bg-red-50/40",
    badge: "bg-red-100 text-red-800 border-red-300",
  },
};

const VERDICT_ICON: Record<string, string> = {
  verified_false: "🔴",
  mixed: "🟡",
  verified_true: "🟢",
  no_clear_verdict: "⚪",
  no_data: "⚪",
};

// ── Legado (NLP only) ─────────────────────────────────────────────────────────

function computeNlpScore(urgency: NLPSignal, manipulation: NLPSignal): number {
  return Math.min(1, urgency.score * 0.4 + manipulation.score * 0.6);
}

function getLevel(score: number): Level {
  if (score < 0.25) return "low";
  if (score < 0.5) return "moderate";
  if (score < 0.75) return "high";
  return "critical";
}

// ── Componente principal ──────────────────────────────────────────────────────

export default function EvidenceScale({ urgency, claim, manipulation, riskScore }: Props) {
  const evidenceItems = [
    ...urgency.evidence.map((e) => ({ tag: "Urgência", text: e })),
    ...manipulation.evidence.map((e) => ({ tag: "Manipulação", text: e })),
    ...claim.evidence.map((e) => ({ tag: "Afirmação", text: e })),
  ];

  if (riskScore) {
    return (
      <MultiDimensionalScale
        riskScore={riskScore}
        evidenceItems={evidenceItems}
      />
    );
  }

  // Legado
  const score = computeNlpScore(urgency, manipulation);
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

      <div className="space-y-1">
        <div className="h-3 rounded-full bg-secondary overflow-hidden">
          <div className={`h-full rounded-full ${cfg.bar} transition-all`} style={{ width: `${pct}%` }} />
        </div>
        <p className="text-xs text-muted-foreground text-right">{pct}% de nível de alerta</p>
      </div>

      <div className="grid grid-cols-3 gap-3">
        <SignalPill label="Urgência" score={urgency.score} />
        <SignalPill label="Manipulação" score={manipulation.score} />
        <SignalPill label="Afirmações" score={claim.score} />
      </div>

      <EvidenceList items={evidenceItems} />

      <p className="text-xs text-muted-foreground border-t pt-3">
        Esta análise detecta padrões linguísticos — não determina se o conteúdo é verdadeiro
        ou falso. Verifique sempre a fonte original antes de compartilhar.
      </p>
    </section>
  );
}

// ── Visão multi-dimensional (com riskScore) ───────────────────────────────────

function MultiDimensionalScale({
  riskScore,
  evidenceItems,
}: {
  riskScore: RiskScore;
  evidenceItems: { tag: string; text: string }[];
}) {
  const level = riskScore.level as Level;
  const cfg = LEVEL_CONFIG[level] ?? LEVEL_CONFIG.moderate;
  const overallPct = Math.round(riskScore.overall * 100);
  const confidencePct = Math.round(riskScore.confidence * 100);
  const icon = VERDICT_ICON[riskScore.verdict] ?? "⚪";
  const { fc_verdict_breakdown: fc } = riskScore;

  return (
    <section className={`rounded-xl border p-5 space-y-5 ${cfg.border}`}>
      {/* Cabeçalho + veredito */}
      <div className="space-y-2">
        <p className="text-xs text-muted-foreground uppercase tracking-wider font-medium">
          Balança da Evidência
        </p>
        <div className="flex flex-wrap items-center gap-2">
          <h2 className={`text-lg font-semibold ${cfg.color}`}>{cfg.label}</h2>
          <span className={`text-xs font-semibold px-2.5 py-0.5 rounded-full border ${cfg.badge}`}>
            {icon} {riskScore.verdict_pt}
          </span>
        </div>
        <p className="text-sm text-muted-foreground">{cfg.description}</p>
      </div>

      {/* Barra geral */}
      <div className="space-y-1">
        <div className="flex justify-between text-xs text-muted-foreground">
          <span>Nível de risco geral</span>
          <span className="font-medium">{overallPct}%</span>
        </div>
        <div className="h-3 rounded-full bg-secondary overflow-hidden">
          <div className={`h-full rounded-full ${cfg.bar} transition-all`} style={{ width: `${overallPct}%` }} />
        </div>
      </div>

      {/* 3 dimensões */}
      <div className="space-y-2">
        <p className="text-xs text-muted-foreground font-medium">Dimensões da análise</p>
        <DimensionBar
          label="Linguística"
          value={riskScore.dimensions.linguistic}
          tooltip="Urgência artificial, manipulação emocional e uso excessivo de maiúsculas"
        />
        <DimensionBar
          label="Fact-checks"
          value={riskScore.dimensions.factcheck}
          tooltip={
            riskScore.dimensions.factcheck === null
              ? "Nenhum fact-check encontrado para este conteúdo"
              : "Baseado nos vereditos de agências verificadoras indexadas"
          }
          noData={riskScore.dimensions.factcheck === null}
        />
        <DimensionBar
          label="Cobertura"
          value={riskScore.dimensions.coverage === null ? null : 1 - riskScore.dimensions.coverage}
          tooltip="Ausência de cobertura em veículos confiáveis aumenta o risco"
          noData={riskScore.dimensions.coverage === null}
        />
      </div>

      {/* Confiança + breakdown FC */}
      <div className="rounded-lg bg-secondary/50 p-3 space-y-2">
        <div className="flex items-center justify-between text-xs">
          <span className="text-muted-foreground">Confiança da análise</span>
          <span className="font-semibold">{confidencePct}%</span>
        </div>
        {fc.total > 0 && (
          <div className="flex items-center gap-3 text-xs text-muted-foreground pt-1 border-t">
            <span>{fc.total} fact-check{fc.total > 1 ? "s" : ""} encontrado{fc.total > 1 ? "s" : ""}:</span>
            {fc.false > 0 && <span className="text-red-600 font-medium">{fc.false} falso{fc.false > 1 ? "s" : ""}</span>}
            {fc.mixed > 0 && <span className="text-amber-600 font-medium">{fc.mixed} misto{fc.mixed > 1 ? "s" : ""}</span>}
            {fc.true > 0 && <span className="text-green-600 font-medium">{fc.true} verdadeiro{fc.true > 1 ? "s" : ""}</span>}
          </div>
        )}
      </div>

      {/* Sinais NLP específicos */}
      <EvidenceList items={evidenceItems} />

      <p className="text-xs text-muted-foreground border-t pt-3">
        Análise combina sinais linguísticos, vereditos de agências verificadoras e cobertura em
        fontes confiáveis. Não substitui a verificação humana.
      </p>
    </section>
  );
}

// ── Sub-componentes ───────────────────────────────────────────────────────────

function DimensionBar({
  label,
  value,
  tooltip,
  noData = false,
}: {
  label: string;
  value: number | null;
  tooltip: string;
  noData?: boolean;
}) {
  const pct = value !== null ? Math.round(value * 100) : 0;
  const barColor =
    noData ? "bg-muted-foreground/30"
    : pct < 30 ? "bg-green-400"
    : pct < 60 ? "bg-amber-400"
    : "bg-red-500";

  return (
    <div className="space-y-0.5" title={tooltip}>
      <div className="flex justify-between text-xs">
        <span className="text-muted-foreground">{label}</span>
        <span className="font-medium text-muted-foreground">
          {noData ? "sem dados" : `${pct}%`}
        </span>
      </div>
      <div className="h-2 rounded-full bg-secondary overflow-hidden">
        {!noData && (
          <div className={`h-full rounded-full ${barColor} transition-all`} style={{ width: `${pct}%` }} />
        )}
      </div>
    </div>
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

function EvidenceList({ items }: { items: { tag: string; text: string }[] }) {
  if (items.length === 0) return null;
  return (
    <ul className="space-y-1">
      {items.map((item, i) => (
        <li key={i} className="flex items-start gap-2 text-xs text-muted-foreground">
          <span className="shrink-0 rounded bg-secondary px-1.5 py-0.5 font-medium">{item.tag}</span>
          <span className="leading-relaxed">"{item.text}"</span>
        </li>
      ))}
    </ul>
  );
}
