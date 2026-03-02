/**
 * module-content.tsx — Interactive learning module renderer
 *
 * Client component that renders sections (explanation, example, quiz, tip)
 * with interactive quizzes and progress tracking.
 */

"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import PanelCard from "@/components/panel-card";
import type { LearningModuleFull, ModuleSection } from "@/lib/api";

const API_URL =
  process.env.NEXT_PUBLIC_BOT_API_URL ?? "http://127.0.0.1:8000";

// ── Section renderers ─────────────────────────────────────────────────────────

function ExplanationSection({ section }: { section: ModuleSection }) {
  return (
    <PanelCard>
      <div className="space-y-2">
        {section.title && (
          <h3 className="text-sm font-semibold">{section.title}</h3>
        )}
        <div className="text-sm leading-relaxed whitespace-pre-line">
          {section.content}
        </div>
      </div>
    </PanelCard>
  );
}

function ExampleSection({ section }: { section: ModuleSection }) {
  return (
    <PanelCard>
      <div className="space-y-3">
        {section.title && (
          <h3 className="text-sm font-semibold flex items-center gap-2">
            <span className="text-amber-500" aria-hidden="true">
              💡
            </span>
            {section.title}
          </h3>
        )}
        {section.scenario && (
          <div className="bg-secondary/50 rounded-lg p-3">
            <p className="text-sm leading-relaxed italic">{section.scenario}</p>
          </div>
        )}
        {section.question && (
          <p className="text-sm font-medium text-muted-foreground">
            {section.question}
          </p>
        )}
      </div>
    </PanelCard>
  );
}

function QuizSection({ section }: { section: ModuleSection }) {
  const [selected, setSelected] = useState<string | null>(null);
  const [showFeedback, setShowFeedback] = useState(false);

  const selectedOption = section.options?.find((o) => o.id === selected);

  const handleSelect = (optionId: string) => {
    if (showFeedback) return; // already answered
    setSelected(optionId);
    setShowFeedback(true);
  };

  return (
    <PanelCard>
      <div className="space-y-3">
        {section.title && (
          <p className="text-xs font-mono text-muted-foreground uppercase tracking-wider">
            {section.title}
          </p>
        )}
        <p className="text-sm font-semibold">{section.question}</p>

        <div className="space-y-2">
          {section.options?.map((opt) => {
            const isSelected = selected === opt.id;
            const showResult = showFeedback && isSelected;

            let borderClass = "border-border hover:border-foreground/30";
            if (showFeedback) {
              if (opt.correct) {
                borderClass = "border-green-500 bg-green-500/5";
              } else if (isSelected && !opt.correct) {
                borderClass = "border-red-500 bg-red-500/5";
              } else {
                borderClass = "border-border opacity-50";
              }
            }

            return (
              <button
                key={opt.id}
                onClick={() => handleSelect(opt.id)}
                disabled={showFeedback}
                className={`w-full text-left border ${borderClass} rounded-lg p-3 text-sm transition-colors ${
                  showFeedback ? "cursor-default" : "cursor-pointer"
                }`}
              >
                <span>{opt.text}</span>
                {showResult && (
                  <p className="mt-2 text-xs text-muted-foreground">
                    {opt.feedback}
                  </p>
                )}
                {showFeedback && opt.correct && !isSelected && (
                  <p className="mt-2 text-xs text-green-600 dark:text-green-400">
                    ← Resposta correta: {opt.feedback}
                  </p>
                )}
              </button>
            );
          })}
        </div>

        {showFeedback && selectedOption && (
          <div
            className={`rounded-lg p-3 text-sm ${
              selectedOption.correct
                ? "bg-green-500/10 text-green-700 dark:text-green-300"
                : "bg-red-500/10 text-red-700 dark:text-red-300"
            }`}
          >
            {selectedOption.correct ? "✅ Correto!" : "❌ Não é bem assim."}
          </div>
        )}
      </div>
    </PanelCard>
  );
}

function TipSection({ section }: { section: ModuleSection }) {
  return (
    <PanelCard>
      <div className="space-y-2">
        <p className="text-xs font-mono text-muted-foreground uppercase tracking-wider flex items-center gap-1">
          <span aria-hidden="true">🎯</span>
          {section.title ?? "Dica prática"}
        </p>
        <p className="text-sm leading-relaxed">{section.tip}</p>
      </div>
    </PanelCard>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

export default function ModuleContent({ slug }: { slug: string }) {
  const [module, setModule] = useState<LearningModuleFull | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchModule = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/learning/modules/${slug}`);
      if (!res.ok) {
        setError("Módulo não encontrado.");
        return;
      }
      const json = await res.json();
      setModule(json);
    } catch {
      setError("Erro ao carregar módulo.");
    } finally {
      setLoading(false);
    }
  }, [slug]);

  useEffect(() => {
    fetchModule();
  }, [fetchModule]);

  if (loading) {
    return (
      <main className="max-w-2xl mx-auto px-6 py-12">
        <div className="text-center space-y-3">
          <div className="h-6 w-6 border-2 border-foreground/30 border-t-foreground rounded-full animate-spin mx-auto" />
          <p className="text-sm text-muted-foreground font-mono">
            Carregando módulo…
          </p>
        </div>
      </main>
    );
  }

  if (error || !module) {
    return (
      <main className="max-w-2xl mx-auto px-6 py-12 text-center space-y-4">
        <p className="text-sm text-muted-foreground">{error}</p>
        <Link href="/aprender" className="text-sm text-primary hover:underline">
          ← Voltar aos módulos
        </Link>
      </main>
    );
  }

  const DIFFICULTY_LABELS: Record<string, string> = {
    beginner: "Iniciante",
    intermediate: "Intermediário",
    advanced: "Avançado",
  };

  return (
    <main className="max-w-2xl mx-auto px-6 py-8 space-y-4">
      {/* Header */}
      <div className="space-y-2">
        <Link
          href="/aprender"
          className="text-xs text-muted-foreground hover:text-foreground transition-colors"
        >
          ← Módulos
        </Link>
        <h1 className="font-display text-2xl sm:text-3xl tracking-wide">
          {module.title.toUpperCase()}
        </h1>
        <div className="flex items-center gap-3 text-xs text-muted-foreground font-mono">
          <span>
            {DIFFICULTY_LABELS[module.difficulty] ?? module.difficulty}
          </span>
          <span>·</span>
          <span>{module.estimated_minutes} min</span>
        </div>
        {module.description && (
          <p className="text-sm text-muted-foreground">{module.description}</p>
        )}
      </div>

      {/* Sections */}
      {module.content.map((section, idx) => {
        switch (section.type) {
          case "explanation":
            return <ExplanationSection key={idx} section={section} />;
          case "example":
            return <ExampleSection key={idx} section={section} />;
          case "quiz":
            return <QuizSection key={idx} section={section} />;
          case "practical_tip":
            return <TipSection key={idx} section={section} />;
          default:
            return null;
        }
      })}

      {/* Completion footer */}
      <PanelCard>
        <div className="text-center space-y-2">
          <p className="text-sm font-medium">
            Parabéns por completar este módulo! 💛
          </p>
          <p className="text-xs text-muted-foreground">
            Cada módulo que você completa fortalece sua capacidade de questionar
            e se proteger de desinformação.
          </p>
          <div className="flex flex-wrap justify-center gap-4 pt-2">
            <Link
              href="/aprender"
              className="text-xs text-primary hover:underline"
            >
              ← Ver todos os módulos
            </Link>
            <Link href="/" className="text-xs text-primary hover:underline">
              Analisar conteúdo →
            </Link>
          </div>
        </div>
      </PanelCard>
    </main>
  );
}
