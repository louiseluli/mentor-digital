/**
 * GDELTSection — cobertura midiática global (GDELT DOC API v2)
 *
 * Exibe artigos de mídia em PT e EN, desduplicados por URL.
 * Limita a 5 artigos para não sobrecarregar a página.
 * Oculta a seção se não houver artigos.
 */

import type { GDELTArticle } from "@/lib/api";

interface Props {
  por: { articles: GDELTArticle[]; error: string };
  en: { articles: GDELTArticle[]; error: string };
}

export default function GDELTSection({ por, en }: Props) {
  // Mescla PT + EN, desduplicando por URL, limita a 5
  const seen = new Set<string>();
  const all: GDELTArticle[] = [];
  for (const article of [...(por.articles ?? []), ...(en.articles ?? [])]) {
    if (article.url && !seen.has(article.url)) {
      seen.add(article.url);
      all.push(article);
    }
  }

  const hasError = Boolean(por.error || en.error);

  return (
    <section className="space-y-3">
      <h2 className="text-sm font-medium text-muted-foreground">
        Cobertura na mídia{" "}
        <span className="font-normal text-xs">(fontes de notícias brasileiras e globais)</span>
      </h2>

      {all.length === 0 ? (
        <div className="rounded-lg border border-dashed border-border px-4 py-5 text-center space-y-1">
          <p className="font-mono text-[11px] text-muted-foreground uppercase tracking-widest">
            {hasError ? "Erro ao buscar fontes" : "Nenhuma fonte encontrada"}
          </p>
          <p className="text-xs text-muted-foreground">
            {hasError
              ? "Não foi possível consultar as fontes de notícias no momento."
              : "Não encontramos artigos de mídia sobre este conteúdo. Isso não confirma nem nega a informação."}
          </p>
        </div>
      ) : (
        <>
          <div className="space-y-2">
            {all.slice(0, 5).map((article) => (
              <ArticleRow key={article.url} article={article} />
            ))}
          </div>

          {all.length > 5 && (
            <p className="text-xs text-muted-foreground">
              +{all.length - 5} artigos adicionais encontrados.
            </p>
          )}
        </>
      )}
    </section>
  );
}

function ArticleRow({ article }: { article: GDELTArticle }) {
  const date = article.seen_date
    ? new Date(article.seen_date).toLocaleDateString("pt-BR", {
        dateStyle: "short",
      })
    : "";

  const label = [article.domain, date, article.source_country]
    .filter(Boolean)
    .join(" · ");

  return (
    <a
      href={article.url}
      target="_blank"
      rel="noopener noreferrer"
      className="flex items-start gap-3 rounded-lg border p-3 hover:bg-secondary/50 transition-colors group"
    >
      <div className="flex-1 min-w-0 space-y-0.5">
        <p className="text-sm font-medium leading-snug line-clamp-2 group-hover:underline">
          {article.title || article.domain}
        </p>
        {label && (
          <p className="text-xs text-muted-foreground">{label}</p>
        )}
      </div>
      <span
        aria-hidden="true"
        className="shrink-0 text-muted-foreground text-xs mt-0.5"
      >
        ↗
      </span>
    </a>
  );
}
