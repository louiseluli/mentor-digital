/**
 * FactCheckSection — LOG DE VERIFICAÇÕES (retro HUD Quest Log style)
 *
 * - Agrupa claims duplicados por texto normalizado com contador "+N ocorrências"
 * - Verdict como stamp: FALSO / ENGANOSO / VERDADEIRO / SEM VEREDITO
 * - "Por que apareceu aqui?" por grupo
 * - Sub-seção verificadores brasileiros (Aos Fatos / Agência Lupa)
 * - Empty state e aviso de cobertura limitada
 */

import type { BrazilianFCData, ClaimReview, FactCheckClaim } from "@/lib/api";
import PanelCard from "@/components/panel-card";

interface Props {
  pt: { results: FactCheckClaim[]; error: string };
  en: { results: FactCheckClaim[]; error: string };
  brazilianFc?: BrazilianFCData;
}

// ── Deduplication ─────────────────────────────────────────────────────────────

interface ClaimGroup {
  representative: FactCheckClaim;
  allReviews: ClaimReview[];
  count: number;
}

function normalizeClaim(text: string): string {
  return text.toLowerCase().replace(/\s+/g, " ").trim().slice(0, 100);
}

function deduplicateClaims(claims: FactCheckClaim[]): ClaimGroup[] {
  const groups = new Map<string, ClaimGroup>();
  for (const claim of claims) {
    const key = normalizeClaim(claim.text);
    if (groups.has(key)) {
      const g = groups.get(key)!;
      g.allReviews.push(...claim.reviews);
      g.count++;
    } else {
      groups.set(key, {
        representative: claim,
        allReviews: [...claim.reviews],
        count: 1,
      });
    }
  }
  return Array.from(groups.values());
}

// ── Verdict stamp ─────────────────────────────────────────────────────────────

function worstVerdict(reviews: ClaimReview[]): {
  label: string;
  cls: string;
} {
  let hasFalse = false;
  let hasMixed = false;
  let hasTrue = false;

  for (const r of reviews) {
    const v = r.rating_value;
    if (v >= 1 && v <= 2) hasFalse = true;
    else if (v >= 3 && v <= 4) hasMixed = true;
    else if (v >= 5) hasTrue = true;
  }

  if (hasFalse)
    return {
      label: "FALSO",
      cls: "text-hud-danger border-hud-danger bg-hud-danger/10",
    };
  if (hasMixed)
    return {
      label: "ENGANOSO",
      cls: "text-hud-warning border-hud-warning bg-hud-warning/10",
    };
  if (hasTrue)
    return {
      label: "VERDADEIRO",
      cls: "text-hud-success border-hud-success bg-hud-success/10",
    };
  return { label: "SEM VEREDITO", cls: "text-hud-muted border-border" };
}

// ── Quest Log Item ────────────────────────────────────────────────────────────

function QuestLogItem({ group }: { group: ClaimGroup }) {
  const { representative: claim, allReviews, count } = group;
  const stamp = worstVerdict(allReviews);

  // Deduplicate reviews by publisher+url
  const uniqueReviews = allReviews.filter(
    (r, i, arr) =>
      arr.findIndex(
        (x) => x.publisher_name === r.publisher_name && x.url === r.url
      ) === i
  );

  return (
    <div className="hud-panel-inset rounded-lg p-4 space-y-3">
      {/* Header: stamp + occurrence count */}
      <div className="flex flex-wrap items-start justify-between gap-2">
        <span
          className={`font-mono text-[11px] font-bold uppercase tracking-widest px-2 py-0.5 rounded border ${stamp.cls}`}
        >
          {stamp.label}
        </span>
        {count > 1 && (
          <span className="text-[10px] font-mono text-hud-muted bg-secondary px-2 py-0.5 rounded">
            +{count - 1} ocorrência{count - 1 > 1 ? "s" : ""}
          </span>
        )}
      </div>

      {/* Claim text */}
      <p className="text-sm leading-snug text-foreground">{claim.text}</p>

      {/* Claimant */}
      {claim.claimant && (
        <p className="text-[11px] font-mono text-hud-muted">
          Alegado por:{" "}
          <span className="font-bold text-foreground">{claim.claimant}</span>
        </p>
      )}

      {/* Reviews */}
      {uniqueReviews.length > 0 && (
        <ul className="space-y-1.5">
          {uniqueReviews.map((r, i) => (
            <li
              key={i}
              className="flex flex-wrap items-center gap-x-2 gap-y-0.5 text-xs"
            >
              <span className="font-mono font-medium text-foreground">
                {r.publisher_name}
              </span>
              {r.url && (
                <a
                  href={r.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-hud-info underline underline-offset-2 hover:opacity-80 transition-opacity"
                >
                  Ver verificação ↗
                </a>
              )}
            </li>
          ))}
        </ul>
      )}

      {/* "Por que apareceu aqui?" */}
      <p className="text-[10px] font-mono text-hud-muted border-t border-border pt-2">
        Por que apareceu aqui? Alegação similar ao texto analisado encontrada em
        bases de fact-checking.
      </p>
    </div>
  );
}

// ── Main export ───────────────────────────────────────────────────────────────

export default function FactCheckSection({ pt, en, brazilianFc }: Props) {
  const all = [...(pt.results ?? []), ...(en.results ?? [])];
  const hasApiError = Boolean(pt.error || en.error);
  const brResults = brazilianFc?.results ?? [];
  const hasAnything = all.length > 0 || brResults.length > 0;

  if (!hasAnything && !hasApiError) return null;

  const groups = deduplicateClaims(all);
  const isLimitedCoverage = groups.length > 0 && groups.length < 3;

  return (
    <PanelCard as="section" className="space-y-5">
      {/* Section title */}
      <h2 className="font-display text-2xl text-foreground">
        LOG DE VERIFICAÇÕES
      </h2>

      {/* Empty state */}
      {groups.length === 0 ? (
        <div className="rounded-lg border border-dashed border-border px-4 py-6 text-center space-y-1">
          <p className="font-mono text-[11px] text-hud-muted uppercase tracking-widest">
            {hasApiError ? "ERRO AO CONSULTAR API" : "NENHUM REGISTO ENCONTRADO"}
          </p>
          <p className="text-xs text-hud-muted">
            {hasApiError
              ? "Não foi possível consultar a base de fact-checking."
              : "Nenhum fact-check encontrado para este conteúdo. Isso não indica que é verdadeiro."}
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {groups.map((group, i) => (
            <QuestLogItem key={i} group={group} />
          ))}
        </div>
      )}

      {/* Limited coverage warning */}
      {isLimitedCoverage && (
        <p className="text-[10px] font-mono text-hud-muted border-t border-border pt-3">
          COBERTURA LIMITADA: poucas verificações encontradas. A ausência de
          fact-checks não confirma a veracidade do conteúdo.
        </p>
      )}

      {/* Brazilian FC sub-section */}
      {brResults.length > 0 && (
        <div className="space-y-3 border-t border-border pt-4">
          <p className="text-[10px] font-mono text-hud-muted uppercase tracking-widest">
            Verificadores brasileiros (Aos Fatos · Agência Lupa)
          </p>
          <div className="space-y-2">
            {brResults.map((r, i) => (
              <a
                key={i}
                href={r.url}
                target="_blank"
                rel="noopener noreferrer"
                className="block rounded-lg border border-border p-3 space-y-1 hover:bg-secondary/40 transition-colors"
              >
                <p className="text-sm font-medium leading-snug line-clamp-2">
                  {r.title}
                </p>
                <div className="flex items-center gap-2 text-[11px] font-mono text-hud-muted">
                  <span className="rounded bg-secondary px-1.5 py-0.5">
                    {r.source}
                  </span>
                  {r.date && <span>{r.date}</span>}
                </div>
                {r.snippet && (
                  <p className="text-xs text-hud-muted line-clamp-2">
                    {r.snippet}
                  </p>
                )}
              </a>
            ))}
          </div>
        </div>
      )}
    </PanelCard>
  );
}
