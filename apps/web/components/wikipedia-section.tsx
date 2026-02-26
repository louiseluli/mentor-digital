/**
 * WikipediaSection — Contexto da Wikipedia
 *
 * Exibe até 2 artigos da Wikipedia (PT + EN mesclados, deduplicados por URL)
 * como cards de contexto para embasar a análise de conteúdo.
 *
 * Dados fornecidos gratuitamente pela API pública da Wikipedia, sem API key.
 */

import type { WikipediaData } from "@/lib/api";

interface Props {
  pt: WikipediaData;
  en: WikipediaData;
}

export default function WikipediaSection({ pt, en }: Props) {
  // Mescla PT e EN, elimina duplicatas por URL e limita a 2 resultados
  const seen = new Set<string>();
  const combined = [...(pt.results ?? []), ...(en.results ?? [])].filter(
    (r) => {
      if (!r.url || seen.has(r.url)) return false;
      seen.add(r.url);
      return true;
    }
  ).slice(0, 2);

  if (combined.length === 0) return null;

  return (
    <section className="space-y-3">
      <div className="flex items-center gap-2">
        <span className="text-base">📚</span>
        <h2 className="text-sm font-semibold tracking-wide uppercase text-muted-foreground">
          Contexto da Wikipedia
        </h2>
      </div>

      <div className="space-y-3">
        {combined.map((result, i) => (
          <a
            key={i}
            href={result.url}
            target="_blank"
            rel="noopener noreferrer"
            className="block rounded-xl border border-border bg-card p-4 space-y-1.5
                       hover:bg-secondary/50 transition-colors group"
          >
            <div className="flex items-start justify-between gap-2">
              <p className="text-sm font-medium group-hover:underline underline-offset-2 leading-snug">
                {result.title}
              </p>
              <span className="shrink-0 rounded bg-secondary px-1.5 py-0.5 text-xs text-muted-foreground uppercase">
                {result.lang === "pt" ? "PT" : "EN"}
              </span>
            </div>
            {result.extract && (
              <p className="text-xs text-muted-foreground leading-relaxed line-clamp-3">
                {result.extract}
              </p>
            )}
            <p className="text-xs text-muted-foreground/60">
              wikipedia.org →
            </p>
          </a>
        ))}
      </div>

      <p className="text-xs text-muted-foreground">
        Conteúdo fornecido pela{" "}
        <a
          href="https://www.wikipedia.org"
          target="_blank"
          rel="noopener noreferrer"
          className="underline underline-offset-2 hover:text-foreground"
        >
          Wikipedia
        </a>{" "}
        sob licença{" "}
        <a
          href="https://creativecommons.org/licenses/by-sa/4.0/"
          target="_blank"
          rel="noopener noreferrer"
          className="underline underline-offset-2 hover:text-foreground"
        >
          CC BY-SA 4.0
        </a>
        .
      </p>
    </section>
  );
}
