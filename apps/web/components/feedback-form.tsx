/**
 * feedback-form.tsx — Inline feedback collection on analysis pages
 *
 * Collects anonymized feedback: usefulness rating (1-5), feeling, recommendation.
 * Submits to /feedback endpoint. Shows only once per content_id (localStorage).
 */

"use client";

import { useState, useEffect } from "react";
import PanelCard from "@/components/panel-card";

const API_URL =
  process.env.NEXT_PUBLIC_BOT_API_URL ?? "http://127.0.0.1:8000";

const FEELINGS = [
  { id: "empowered", label: "Mais preparado(a)", icon: "💪" },
  { id: "grateful", label: "Grato(a)", icon: "🙏" },
  { id: "relieved", label: "Aliviado(a)", icon: "😌" },
  { id: "confused", label: "Confuso(a)", icon: "🤔" },
  { id: "frustrated", label: "Frustrado(a)", icon: "😤" },
];

interface Props {
  contentId: string;
}

export default function FeedbackForm({ contentId }: Props) {
  const [submitted, setSubmitted] = useState(false);
  const [dismissed, setDismissed] = useState(false);
  const [rating, setRating] = useState<number | null>(null);
  const [feeling, setFeeling] = useState<string | null>(null);
  const [recommend, setRecommend] = useState<boolean | null>(null);
  const [submitting, setSubmitting] = useState(false);

  // Check if already submitted for this content
  useEffect(() => {
    try {
      const key = `mentor-feedback-${contentId}`;
      if (localStorage.getItem(key)) {
        setSubmitted(true);
      }
    } catch {
      // localStorage unavailable
    }
  }, [contentId]);

  if (submitted || dismissed) return null;

  const handleSubmit = async () => {
    setSubmitting(true);
    try {
      await fetch(`${API_URL}/feedback`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          content_id: contentId,
          usefulness_rating: rating,
          feeling_after: feeling,
          would_recommend: recommend,
        }),
      });
      localStorage.setItem(`mentor-feedback-${contentId}`, "1");
      setSubmitted(true);
    } catch {
      // silently fail — feedback is nice-to-have
      setDismissed(true);
    } finally {
      setSubmitting(false);
    }
  };

  const canSubmit = rating !== null;

  return (
    <PanelCard>
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <p className="text-xs font-mono text-muted-foreground uppercase tracking-wider">
            Sua opinião
          </p>
          <button
            onClick={() => setDismissed(true)}
            className="text-xs text-muted-foreground hover:text-foreground"
            aria-label="Fechar feedback"
          >
            ✕
          </button>
        </div>

        {/* Rating */}
        <div className="space-y-1.5">
          <p className="text-sm">
            Esta análise foi útil para você?
          </p>
          <div className="flex gap-1">
            {[1, 2, 3, 4, 5].map((n) => (
              <button
                key={n}
                onClick={() => setRating(n)}
                className={`w-9 h-9 rounded-md border text-sm font-mono transition-colors ${
                  rating === n
                    ? "border-primary bg-primary/10 text-primary font-bold"
                    : "border-border hover:border-foreground/30"
                }`}
                aria-label={`Nota ${n} de 5`}
              >
                {n}
              </button>
            ))}
          </div>
          <p className="text-[10px] text-muted-foreground font-mono">
            1 = nada útil · 5 = muito útil
          </p>
        </div>

        {/* Feeling */}
        {rating !== null && (
          <div className="space-y-1.5">
            <p className="text-sm">Como você se sente agora?</p>
            <div className="flex flex-wrap gap-1.5">
              {FEELINGS.map((f) => (
                <button
                  key={f.id}
                  onClick={() => setFeeling(f.id)}
                  className={`text-xs px-2.5 py-1.5 rounded-md border transition-colors ${
                    feeling === f.id
                      ? "border-primary bg-primary/10"
                      : "border-border hover:border-foreground/30"
                  }`}
                >
                  {f.icon} {f.label}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Recommend */}
        {rating !== null && (
          <div className="space-y-1.5">
            <p className="text-sm">
              Recomendaria o Mentor Digital para alguém?
            </p>
            <div className="flex gap-2">
              <button
                onClick={() => setRecommend(true)}
                className={`text-xs px-3 py-1.5 rounded-md border transition-colors ${
                  recommend === true
                    ? "border-green-500 bg-green-500/10 text-green-700 dark:text-green-300"
                    : "border-border hover:border-foreground/30"
                }`}
              >
                Sim
              </button>
              <button
                onClick={() => setRecommend(false)}
                className={`text-xs px-3 py-1.5 rounded-md border transition-colors ${
                  recommend === false
                    ? "border-red-500 bg-red-500/10 text-red-700 dark:text-red-300"
                    : "border-border hover:border-foreground/30"
                }`}
              >
                Não
              </button>
            </div>
          </div>
        )}

        {/* Submit */}
        {canSubmit && (
          <button
            onClick={handleSubmit}
            disabled={submitting}
            className="w-full text-sm py-2 rounded-md border border-primary bg-primary/10 text-primary hover:bg-primary/20 transition-colors disabled:opacity-50"
          >
            {submitting ? "Enviando…" : "Enviar feedback"}
          </button>
        )}

        <p className="text-[10px] text-muted-foreground text-center">
          Feedback anonimizado · Nenhum dado pessoal é coletado
        </p>
      </div>
    </PanelCard>
  );
}
