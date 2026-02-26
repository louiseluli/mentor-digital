/**
 * EvidenceScale — Painel de Análise (retro HUD Stats Panel)
 *
 * Com riskScore: exibe veredito multi-dimensional (linguística + fact-checks + cobertura)
 *               com barras segmentadas arcade e verdict stamp.
 * Sem riskScore: modo legado (NLP only) com estilo retro simplificado.
 */

import type { NLPSignal, RiskScore } from "@/lib/api";
import PanelCard from "@/components/panel-card";
import RiskMeter from "@/components/risk-meter";

interface Props {
  urgency: NLPSignal;
  claim: NLPSignal;
  manipulation: NLPSignal;
  riskScore?: RiskScore;
}

// ── Verdict stamp config ───────────────────────────────────────────────────────

const VERDICT_STAMP: Record<string, { text: string; cls: string }> = {
  verified_false: {
    text: "FALSO VERIFICADO",
    cls: "text-hud-danger border-hud-danger bg-hud-danger/10",
  },
  mixed: {
    text: "CONTESTADO",
    cls: "text-hud-warning border-hud-warning bg-hud-warning/10",
  },
  verified_true: {
    text: "VERIFICADO",
    cls: "text-hud-success border-hud-success bg-hud-success/10",
  },
  no_clear_verdict: {
    text: "INCONCLUSIVO",
    cls: "text-hud-muted border-border bg-secondary/50",
  },
  no_data: {
    text: "SEM DADOS FC",
    cls: "text-hud-muted border-border bg-secondary/50",
  },
};

// ── Segmented retro bar (10 blocks) ───────────────────────────────────────────

function RetroBar({
  value,
  noData = false,
  label,
}: {
  value: number | null;
  noData?: boolean;
  label: string;
}) {
  const TOTAL = 10;
  const filled =
    noData || value === null ? 0 : Math.round(value * TOTAL);
  const blockColor =
    noData || value === null
      ? ""
      : value < 0.3
        ? "bg-hud-success"
        : value < 0.6
          ? "bg-hud-warning"
          : "bg-hud-danger";

  return (
    <div
      className="flex gap-0.5"
      role="meter"
      aria-label={label}
      aria-valuenow={noData || value === null ? 0 : Math.round(value * 100)}
      aria-valuemin={0}
      aria-valuemax={100}
    >
      {Array.from({ length: TOTAL }, (_, i) => (
        <div
          key={i}
          aria-hidden="true"
          className={`h-2.5 w-4 rounded-sm ${
            i < filled && !noData ? blockColor : "bg-border"
          }`}
        />
      ))}
    </div>
  );
}

// ── Dimension row ─────────────────────────────────────────────────────────────

function DimensionRow({
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
  const pct = noData || value === null ? null : Math.round(value * 100);

  return (
    <div className="space-y-1" title={tooltip}>
      <div className="flex items-center justify-between text-xs font-mono">
        <span className="text-hud-muted uppercase tracking-wider">{label}</span>
        <span className="text-foreground font-bold">
          {noData ? "—" : `${pct}%`}
        </span>
      </div>
      <RetroBar
        value={value}
        noData={noData}
        label={`${label}: ${noData ? "sem dados" : `${pct}%`}`}
      />
    </div>
  );
}

// ── Evidence chips ────────────────────────────────────────────────────────────

function EvidenceChips({ items }: { items: { tag: string; text: string }[] }) {
  if (items.length === 0) return null;
  return (
    <ul className="space-y-1.5">
      {items.map((item, i) => (
        <li key={i} className="flex items-start gap-2 text-xs text-hud-muted">
          <span className="shrink-0 rounded bg-secondary px-1.5 py-0.5 font-mono font-medium text-[10px] uppercase tracking-wide">
            {item.tag}
          </span>
          <span className="leading-relaxed">"{item.text}"</span>
        </li>
      ))}
    </ul>
  );
}

// ── Legacy (NLP only) ─────────────────────────────────────────────────────────

function computeNlpScore(urgency: NLPSignal, manipulation: NLPSignal): number {
  return Math.min(1, urgency.score * 0.4 + manipulation.score * 0.6);
}

type SimpleLevel = "low" | "moderate" | "high" | "critical";

function getLevel(score: number): SimpleLevel {
  if (score < 0.25) return "low";
  if (score < 0.5) return "moderate";
  if (score < 0.75) return "high";
  return "critical";
}

function LegacyStats({
  urgency,
  claim,
  manipulation,
  evidenceItems,
}: {
  urgency: NLPSignal;
  claim: NLPSignal;
  manipulation: NLPSignal;
  evidenceItems: { tag: string; text: string }[];
}) {
  const score = computeNlpScore(urgency, manipulation);
  const level = getLevel(score);

  return (
    <PanelCard as="section" className="space-y-5">
      <div className="flex items-center justify-between gap-4">
        <h2 className="font-display text-2xl text-foreground">
          PAINEL DE ANÁLISE
        </h2>
        <span className="text-[10px] font-mono text-hud-muted uppercase tracking-wider">
          Linguística
        </span>
      </div>

      <RiskMeter level={level} overall={score} />

      <div className="space-y-3">
        <DimensionRow
          label="Urgência"
          value={urgency.score}
          tooltip="Linguagem com urgência artificial: imperativos, exclamações, ameaças."
        />
        <DimensionRow
          label="Manipulação"
          value={manipulation.score}
          tooltip="Apelos emocionais, superlativos, framing polarizador."
        />
        <DimensionRow
          label="Afirmações"
          value={claim.score}
          tooltip="Número e tipo de afirmações factuais detectadas."
        />
      </div>

      <EvidenceChips items={evidenceItems} />

      <p className="text-[11px] font-mono text-hud-muted border-t border-border pt-3">
        Análise de padrões linguísticos — não determina veracidade.
        Verifique a fonte antes de compartilhar.
      </p>
    </PanelCard>
  );
}

// ── Multi-dimensional view ─────────────────────────────────────────────────────

function MultiDimensionalStats({
  riskScore,
  evidenceItems,
}: {
  riskScore: RiskScore;
  evidenceItems: { tag: string; text: string }[];
}) {
  const stamp = VERDICT_STAMP[riskScore.verdict] ?? VERDICT_STAMP.no_data;
  const { fc_verdict_breakdown: fc } = riskScore;
  const confidencePct = Math.round(riskScore.confidence * 100);
  const isVerifiedFalse = riskScore.verdict === "verified_false";

  return (
    <PanelCard
      as="section"
      className={`space-y-5 ${isVerifiedFalse ? "border-2 !border-hud-danger" : ""}`}
    >
      {/* Title + verdict stamp */}
      <div className="flex flex-wrap items-start justify-between gap-3">
        <h2 className="font-display text-2xl text-foreground">
          PAINEL DE ANÁLISE
        </h2>
        <span
          className={`font-mono text-[11px] font-bold uppercase tracking-widest px-2.5 py-1 rounded border ${stamp.cls}`}
          aria-label={`Veredito: ${stamp.text}`}
        >
          {stamp.text}
        </span>
      </div>

      {/* Overall risk meter */}
      <RiskMeter level={riskScore.level} overall={riskScore.overall} />

      {/* Dimension bars */}
      <div className="space-y-3">
        <DimensionRow
          label="Linguística"
          value={riskScore.dimensions.linguistic}
          tooltip="Urgência artificial, manipulação emocional e uso excessivo de maiúsculas."
        />
        <DimensionRow
          label="Fact-checks"
          value={riskScore.dimensions.factcheck}
          noData={riskScore.dimensions.factcheck === null}
          tooltip={
            riskScore.dimensions.factcheck === null
              ? "Nenhum fact-check encontrado para este conteúdo."
              : "Vereditos de agências verificadoras indexadas."
          }
        />
        <DimensionRow
          label="Cobertura"
          value={
            riskScore.dimensions.coverage === null
              ? null
              : 1 - riskScore.dimensions.coverage
          }
          noData={riskScore.dimensions.coverage === null}
          tooltip="Ausência de cobertura em veículos confiáveis eleva o risco."
        />
      </div>

      {/* Confidence + FC breakdown */}
      <div className="rounded-lg bg-secondary/50 px-3 py-2.5 space-y-2 font-mono text-xs">
        <div className="flex items-center justify-between">
          <span className="text-hud-muted uppercase tracking-wider text-[10px]">
            Confiança
          </span>
          <span className="font-bold text-foreground">{confidencePct}%</span>
        </div>
        {fc.total > 0 && (
          <div className="flex flex-wrap gap-x-3 gap-y-0.5 text-[11px] pt-1 border-t border-border">
            <span className="text-hud-muted">
              {fc.total} FC encontrado{fc.total > 1 ? "s" : ""}:
            </span>
            {fc.false > 0 && (
              <span className="text-hud-danger font-bold">
                {fc.false} falso{fc.false > 1 ? "s" : ""}
              </span>
            )}
            {fc.mixed > 0 && (
              <span className="text-hud-warning font-bold">
                {fc.mixed} misto{fc.mixed > 1 ? "s" : ""}
              </span>
            )}
            {fc.true > 0 && (
              <span className="text-hud-success font-bold">
                {fc.true} verdadeiro{fc.true > 1 ? "s" : ""}
              </span>
            )}
          </div>
        )}
      </div>

      {/* Evidence signals */}
      {evidenceItems.length > 0 && (
        <div className="space-y-2">
          <p className="text-[10px] font-mono text-hud-muted uppercase tracking-widest">
            Sinais detectados
          </p>
          <EvidenceChips items={evidenceItems} />
        </div>
      )}

      <p className="text-[11px] font-mono text-hud-muted border-t border-border pt-3">
        Combina sinais linguísticos, vereditos FC e cobertura em fontes confiáveis.
        Não substitui a verificação humana.
      </p>
    </PanelCard>
  );
}

// ── Main export ───────────────────────────────────────────────────────────────

export default function EvidenceScale({
  urgency,
  claim,
  manipulation,
  riskScore,
}: Props) {
  const evidenceItems = [
    ...urgency.evidence.map((e) => ({ tag: "Urgência", text: e })),
    ...manipulation.evidence.map((e) => ({ tag: "Manipulação", text: e })),
    ...claim.evidence.map((e) => ({ tag: "Afirmação", text: e })),
  ];

  if (riskScore) {
    return (
      <MultiDimensionalStats
        riskScore={riskScore}
        evidenceItems={evidenceItems}
      />
    );
  }

  return (
    <LegacyStats
      urgency={urgency}
      claim={claim}
      manipulation={manipulation}
      evidenceItems={evidenceItems}
    />
  );
}
