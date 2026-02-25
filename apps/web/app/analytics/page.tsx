/**
 * /analytics — Painel de impacto do Mentor Digital (Micro-Batch 8.3)
 *
 * Server Component: busca sumário de analytics do bot FastAPI e renderiza
 * o dashboard com métricas anonimizadas. Cache de 5 min via ISR.
 */

import type { Metadata } from "next";
import AnalyticsDashboard from "@/components/analytics-dashboard";
import { fetchAnalyticsSummary } from "@/lib/api";

export const metadata: Metadata = {
  title: "Impacto — Mentor Digital",
  description:
    "Métricas anonimizadas de uso do Mentor Digital: análises realizadas, distribuição de risco, cobertura de fact-check e GDELT.",
};

export default async function AnalyticsPage() {
  const summary = await fetchAnalyticsSummary(30);

  return (
    <main className="max-w-2xl mx-auto px-6 py-8 space-y-4">
      <div>
        <h1 className="text-xl font-semibold">Impacto</h1>
        <p className="text-sm text-muted-foreground mt-0.5">
          Métricas anonimizadas dos últimos 30 dias
        </p>
      </div>
      <AnalyticsDashboard summary={summary} />
    </main>
  );
}
