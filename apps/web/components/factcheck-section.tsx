/**
 * FactCheckSection — resultados da Google Fact Check Tools API
 * + sub-seção de verificadores brasileiros (Aos Fatos / Agência Lupa via RSS)
 */

import type { BrazilianFCData, FactCheckClaim } from "@/lib/api";

interface Props {
  pt: { results: FactCheckClaim[]; error: string };
  en: { results: FactCheckClaim[]; error: string };
  brazilianFc?: BrazilianFCData;
}

export default function FactCheckSection({ pt, en, brazilianFc }: Props) {
  const all = [...(pt.results ?? []), ...(en.results ?? [])];
  const hasError = Boolean(pt.error || en.error);
  const brResults = brazilianFc?.results ?? [];
  const hasAnything = all.length > 0 || brResults.length > 0;

  // Sem resultados e sem erro → não exibir seção
  if (!hasAnything && !hasError) return null;

  return (
    <section className="space-y-3">
      <h2 className="text-sm font-medium text-muted-foreground">
        Verificações de fatos
      </h2>

      {/* Google Fact Check (PT + EN) */}
      {all.length === 0 ? (
        <p className="text-sm text-muted-foreground italic rounded-lg border p-4">
          Nenhum fact-check encontrado para este conteúdo.
          {hasError && " (Não foi possível consultar a API de verificação.)"}
        </p>
      ) : (
        <div className="space-y-3">
          {all.map((claim, i) => (
            <ClaimCard key={i} claim={claim} />
          ))}
        </div>
      )}

      {/* Verificadores brasileiros via RSS */}
      {brResults.length > 0 && (
        <div className="space-y-2 pt-2">
          <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
            Mencionado por verificadores brasileiros
          </p>
          <div className="space-y-2">
            {brResults.map((r, i) => (
              <a
                key={i}
                href={r.url}
                target="_blank"
                rel="noopener noreferrer"
                className="block rounded-lg border p-3 space-y-1 hover:bg-secondary/40 transition-colors"
              >
                <p className="text-sm font-medium leading-snug line-clamp-2">
                  {r.title}
                </p>
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <span className="rounded bg-secondary px-1.5 py-0.5 font-medium">
                    {r.source}
                  </span>
                  {r.date && <span>{r.date}</span>}
                </div>
                {r.snippet && (
                  <p className="text-xs text-muted-foreground line-clamp-2">{r.snippet}</p>
                )}
              </a>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}

function ClaimCard({ claim }: { claim: FactCheckClaim }) {
  const review = claim.reviews?.[0];

  return (
    <div className="rounded-lg border p-4 space-y-2">
      <p className="text-sm leading-snug">{claim.text}</p>

      {claim.claimant && (
        <p className="text-xs text-muted-foreground">
          Alegado por:{" "}
          <span className="font-medium text-foreground">{claim.claimant}</span>
        </p>
      )}

      {review && (
        <div className="flex flex-wrap items-center gap-2 pt-1">
          <RatingBadge rating={review.text_rating} value={review.rating_value} />
          <span className="text-xs text-muted-foreground">
            {review.publisher_name}
            {review.url && (
              <>
                {" · "}
                <a
                  href={review.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="underline underline-offset-2 hover:text-foreground transition-colors"
                >
                  Ver verificação ↗
                </a>
              </>
            )}
          </span>
        </div>
      )}
    </div>
  );
}

function RatingBadge({ rating, value }: { rating: string; value: number }) {
  // value: 0=unknown, 1-2=false, 3-4=mixed, 5-7=true
  let cls = "border-secondary text-muted-foreground";
  if (value >= 1 && value <= 2) cls = "border-red-300 text-red-700 bg-red-50";
  else if (value >= 3 && value <= 4) cls = "border-amber-300 text-amber-700 bg-amber-50";
  else if (value >= 5) cls = "border-green-300 text-green-700 bg-green-50";

  return (
    <span className={`text-xs font-semibold px-2 py-0.5 rounded-full border ${cls}`}>
      {rating || "Sem classificação"}
    </span>
  );
}
