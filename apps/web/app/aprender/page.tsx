/**
 * /aprender — Módulos de Aprendizagem hub
 *
 * Lists all available learning modules with progress tracking.
 * Server Component — fetches module list from API.
 */

import type { Metadata } from "next";
import Link from "next/link";
import PanelCard from "@/components/panel-card";
import { fetchModules } from "@/lib/api";

export const metadata: Metadata = {
  title: "Aprender — Mentor Digital",
  description:
    "Módulos educativos sobre pensamento crítico, viés de confirmação, deepfakes, avaliação de fontes e direitos digitais.",
};

const TOPIC_ICONS: Record<string, string> = {
  bias: "🧠",
  sources: "🔍",
  deepfakes: "🎭",
  algorithms: "📱",
  rights: "⚖️",
};

const TOPIC_LABELS: Record<string, string> = {
  bias: "Viés Cognitivo",
  sources: "Fontes",
  deepfakes: "Deepfakes",
  algorithms: "Algoritmos",
  rights: "Direitos",
};

const DIFFICULTY_LABELS: Record<string, string> = {
  beginner: "Iniciante",
  intermediate: "Intermediário",
  advanced: "Avançado",
};

const DIFFICULTY_COLORS: Record<string, string> = {
  beginner: "text-green-600 dark:text-green-400 bg-green-500/10",
  intermediate: "text-amber-600 dark:text-amber-400 bg-amber-500/10",
  advanced: "text-red-600 dark:text-red-400 bg-red-500/10",
};

export default async function AprenderPage() {
  const modules = await fetchModules();

  return (
    <main className="max-w-2xl mx-auto px-6 py-8 space-y-6">
      {/* Header */}
      <div className="space-y-2">
        <h1 className="font-display text-3xl sm:text-4xl tracking-wide">
          APRENDER
        </h1>
        <p className="text-sm text-muted-foreground">
          Módulos curtos e práticos para fortalecer seu pensamento crítico.
          Cada um leva poucos minutos e inclui exemplos reais.
        </p>
      </div>

      {/* Module list */}
      {modules.length === 0 ? (
        <PanelCard>
          <p className="text-sm text-muted-foreground text-center py-4">
            Os módulos de aprendizagem estão sendo preparados. Volte em breve!
          </p>
        </PanelCard>
      ) : (
        <div className="space-y-3">
          {modules.map((mod, idx) => (
            <Link
              key={mod.slug}
              href={`/aprender/${mod.slug}`}
              className="block group"
            >
              <PanelCard>
                <div className="flex items-start gap-3">
                  <span
                    className="text-2xl mt-0.5"
                    aria-hidden="true"
                  >
                    {TOPIC_ICONS[mod.topic] ?? "📖"}
                  </span>
                  <div className="flex-1 min-w-0 space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-muted-foreground font-mono">
                        {String(idx + 1).padStart(2, "0")}
                      </span>
                      <h2 className="text-sm font-semibold group-hover:text-primary transition-colors truncate">
                        {mod.title}
                      </h2>
                    </div>
                    {mod.description && (
                      <p className="text-xs text-muted-foreground line-clamp-2">
                        {mod.description}
                      </p>
                    )}
                    <div className="flex items-center gap-2 pt-0.5">
                      <span
                        className={`text-[10px] font-mono uppercase px-1.5 py-0.5 rounded ${
                          DIFFICULTY_COLORS[mod.difficulty] ?? ""
                        }`}
                      >
                        {DIFFICULTY_LABELS[mod.difficulty] ?? mod.difficulty}
                      </span>
                      <span className="text-[10px] text-muted-foreground font-mono">
                        {mod.estimated_minutes} min
                      </span>
                      <span className="text-[10px] text-muted-foreground font-mono">
                        {TOPIC_LABELS[mod.topic] ?? mod.topic}
                      </span>
                    </div>
                  </div>
                  <span
                    className="text-muted-foreground group-hover:text-foreground transition-colors"
                    aria-hidden="true"
                  >
                    →
                  </span>
                </div>
              </PanelCard>
            </Link>
          ))}
        </div>
      )}

      {/* Footer */}
      <div className="text-center space-y-3 py-2">
        <p className="text-xs text-muted-foreground font-mono">
          Novos módulos são adicionados regularmente
        </p>
        <div className="flex flex-wrap justify-center gap-4">
          <Link href="/" className="text-xs text-primary hover:underline">
            ← Analisar conteúdo
          </Link>
          <Link
            href="/guia-acao"
            className="text-xs text-primary hover:underline"
          >
            Guia de ação →
          </Link>
        </div>
      </div>
    </main>
  );
}
