/**
 * AnalysisHeader — HUD header card for /analise/[content_id]
 * VT323 heading, meta row, compact RiskMeter badge, action buttons.
 */

import Link from "next/link";
import CopyLinkButton from "@/components/copy-link-button";
import RiskMeter from "@/components/risk-meter";
import PanelCard from "@/components/panel-card";
import type { RiskScore } from "@/lib/api";

interface Props {
  query: string;
  analyzedAt: string;
  wordCount: number;
  riskScore?: RiskScore;
}

export default function AnalysisHeader({
  query,
  analyzedAt,
  wordCount,
  riskScore,
}: Props) {
  const date = new Date(analyzedAt).toLocaleString("pt-BR", {
    dateStyle: "short",
    timeStyle: "short",
  });

  return (
    <PanelCard as="header" className="space-y-4">
      {/* Title row */}
      <div className="flex flex-wrap items-start gap-4">
        <div className="min-w-0 flex-1 space-y-1">
          <p className="text-[10px] font-mono tracking-[0.18em] text-hud-muted uppercase">
            MENTOR DIGITAL · ANÁLISE DE CONTEÚDO
          </p>
          <h1 className="font-display text-3xl sm:text-4xl leading-tight line-clamp-4 text-foreground">
            {query || "Conteúdo de mídia"}
          </h1>
        </div>

        {riskScore && (
          <div className="shrink-0 self-start pt-1">
            <RiskMeter
              level={riskScore.level}
              overall={riskScore.overall}
              compact
            />
          </div>
        )}
      </div>

      {/* Meta */}
      <p className="text-[11px] font-mono text-hud-muted">
        {date}
        {wordCount > 0 && <span> · {wordCount} palavras</span>}
      </p>

      {/* Actions */}
      <div className="flex flex-wrap gap-2 pt-1 border-t border-border">
        <CopyLinkButton />
        <Link
          href="/"
          className="inline-flex items-center gap-1 text-xs px-3 py-1.5 rounded-md border border-border text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors font-mono hud-focus"
        >
          + Nova análise
        </Link>
      </div>
    </PanelCard>
  );
}
