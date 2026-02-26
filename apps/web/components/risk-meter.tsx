/**
 * RiskMeter — arcade-style segmented health bar.
 * 10 blocks, filled count driven by risk level.
 * compact=true → small badge for the analysis header.
 */

import type { RiskLevel } from "@/lib/api";

const TOTAL = 10;

const FILLED_BLOCKS: Record<RiskLevel, number> = {
  low: 3,
  moderate: 5,
  high: 7,
  critical: 10,
};

const BLOCK_COLOR: Record<RiskLevel, string> = {
  low: "bg-hud-success",
  moderate: "bg-hud-warning",
  high: "bg-hud-danger",
  critical: "bg-hud-danger",
};

const TEXT_COLOR: Record<RiskLevel, string> = {
  low: "text-hud-success",
  moderate: "text-hud-warning",
  high: "text-hud-danger",
  critical: "text-hud-danger",
};

const LEVEL_LABEL: Record<RiskLevel, string> = {
  low: "BAIXO",
  moderate: "MODERADO",
  high: "ALTO",
  critical: "CRÍTICO",
};

interface Props {
  level: RiskLevel;
  overall: number; // 0–1
  /** Compact badge mode for the analysis header. */
  compact?: boolean;
}

export default function RiskMeter({ level, overall, compact = false }: Props) {
  const filled = FILLED_BLOCKS[level];
  const blockColor = BLOCK_COLOR[level];
  const textColor = TEXT_COLOR[level];
  const label = LEVEL_LABEL[level];
  const pct = Math.round(overall * 100);

  const bars = Array.from({ length: TOTAL }, (_, i) => (
    <div
      key={i}
      aria-hidden="true"
      className={[
        "rounded-sm transition-colors",
        compact ? "h-3 w-1.5" : "h-5 flex-1",
        i < filled ? blockColor : "bg-border",
      ].join(" ")}
    />
  ));

  if (compact) {
    return (
      <div
        className="flex flex-col items-end gap-0.5"
        role="meter"
        aria-valuenow={pct}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={`Nível de risco: ${label}`}
      >
        <div className="flex gap-0.5">{bars}</div>
        <span className={`text-[10px] font-mono font-bold tracking-widest ${textColor}`}>
          {label} · {pct}%
        </span>
      </div>
    );
  }

  return (
    <div
      className="space-y-1"
      role="meter"
      aria-valuenow={pct}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-label={`Nível de risco: ${label}`}
    >
      <div className="flex gap-1">{bars}</div>
      <div className="flex justify-between text-xs font-mono">
        <span className="text-hud-muted">RISCO</span>
        <span className={`font-bold tracking-widest ${textColor}`}>
          {label} · {pct}%
        </span>
      </div>
    </div>
  );
}
