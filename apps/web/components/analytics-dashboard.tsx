/**
 * analytics-dashboard.tsx — Painel de impacto do Mentor Digital (Micro-Batch 8.3)
 *
 * Server Component puro: recebe AnalyticsSummary como prop e renderiza métricas
 * de impacto anonimizadas. Sem chamadas a APIs aqui — o fetch ocorre na page.tsx.
 */

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import type { AnalyticsSummary } from "@/lib/api";

// ── Labels em português ───────────────────────────────────────────────────────

const PLATFORM_LABELS: Record<string, string> = {
  telegram: "Telegram",
  whatsapp: "WhatsApp",
  web: "Web",
};

const CONTENT_TYPE_LABELS: Record<string, string> = {
  text: "Texto",
  link: "Link",
  image: "Imagem",
  video: "Vídeo",
  audio: "Áudio",
  document: "Documento",
};

const RISK_LABELS: Record<string, string> = {
  low: "Baixo",
  moderate: "Moderado",
  high: "Alto",
  critical: "Crítico",
};

const RISK_ORDER = ["critical", "high", "moderate", "low"];

const RISK_COLORS: Record<string, { bar: string; label: string; dot: string }> = {
  critical: {
    bar: "bg-red-500",
    label: "text-red-700",
    dot: "bg-red-500",
  },
  high: {
    bar: "bg-orange-500",
    label: "text-orange-700",
    dot: "bg-orange-500",
  },
  moderate: {
    bar: "bg-amber-500",
    label: "text-amber-700",
    dot: "bg-amber-500",
  },
  low: {
    bar: "bg-green-500",
    label: "text-green-700",
    dot: "bg-green-500",
  },
};

const FEELING_LABELS: Record<string, string> = {
  empowered: "Empoderado/a",
  grateful: "Grato/a",
  relieved: "Aliviado/a",
  confused: "Confuso/a",
  frustrated: "Frustrado/a",
};

const FEELING_ICONS: Record<string, string> = {
  empowered: "💪",
  grateful: "🙏",
  relieved: "😌",
  confused: "🤔",
  frustrated: "😤",
};

// ── Subcomponentes ────────────────────────────────────────────────────────────

function DistributionRow({
  label,
  count,
  total,
  colorClass = "bg-foreground",
  labelClass = "",
  dot,
}: {
  label: string;
  count: number;
  total: number;
  colorClass?: string;
  labelClass?: string;
  dot?: string;
}) {
  const pct = total > 0 ? Math.round((count / total) * 100) : 0;
  return (
    <div className="flex items-center gap-3 py-1">
      {dot && (
        <span className={`w-2 h-2 rounded-full shrink-0 ${dot}`} aria-hidden />
      )}
      <span className={`text-sm w-24 shrink-0 ${labelClass}`}>{label}</span>
      <div className="flex-1 relative h-2 bg-muted rounded-full overflow-hidden">
        <div
          className={`absolute inset-y-0 left-0 rounded-full ${colorClass}`}
          style={{ width: `${pct}%` }}
          role="progressbar"
          aria-valuenow={pct}
          aria-valuemin={0}
          aria-valuemax={100}
        />
      </div>
      <span className="text-sm tabular-nums text-muted-foreground w-16 text-right">
        {count} <span className="text-xs">({pct}%)</span>
      </span>
    </div>
  );
}

function SectionCard({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground uppercase tracking-wide">
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-1">{children}</CardContent>
    </Card>
  );
}

function CoverageCard({
  label,
  value,
}: {
  label: string;
  value: number;
}) {
  const pct = Math.round(value * 100);
  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex justify-between text-sm">
        <span>{label}</span>
        <span className="font-medium tabular-nums">{pct}%</span>
      </div>
      <Progress value={pct} className="h-2" />
    </div>
  );
}

// ── Componente principal ──────────────────────────────────────────────────────

interface Props {
  summary: AnalyticsSummary | null;
}

export default function AnalyticsDashboard({ summary }: Props) {
  if (!summary || summary.total === 0) {
    return (
      <Card className="text-center py-12">
        <CardContent>
          <p className="text-muted-foreground text-sm">
            Ainda não há análises registradas.
          </p>
          <p className="text-muted-foreground text-sm mt-1">
            Envie seu primeiro conteúdo pelo Telegram ou WhatsApp para começar.
          </p>
        </CardContent>
      </Card>
    );
  }

  const riskTotal = Object.values(summary.by_risk_level).reduce(
    (a, b) => a + b,
    0
  );

  const fb = summary.feedback;
  const persistent = summary.persistent;

  return (
    <div className="space-y-6">
      {/* Total */}
      <Card className="text-center py-6">
        <CardContent className="pt-0">
          <p className="text-5xl font-bold tabular-nums">{summary.total}</p>
          <p className="text-muted-foreground text-sm mt-1">
            análises realizadas nos últimos {summary.period_days} dias
          </p>
          {persistent && persistent.total_evidence_items > 0 && (
            <p className="text-muted-foreground text-xs mt-2">
              {persistent.total_evidence_items} evidências coletadas de fontes externas
            </p>
          )}
        </CardContent>
      </Card>

      {/* Feedback do público */}
      {fb && fb.total > 0 && (
        <Card className="border-blue-200 dark:border-blue-800">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground uppercase tracking-wide">
              Feedback do público
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-3 gap-4 text-center mb-4">
              <div>
                <p className="text-3xl font-bold tabular-nums">
                  {fb.avg_rating > 0 ? `${fb.avg_rating.toFixed(1)}` : "—"}
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                  nota média (1-5)
                </p>
              </div>
              <div>
                <p className="text-3xl font-bold tabular-nums">{fb.total}</p>
                <p className="text-xs text-muted-foreground mt-1">respostas</p>
              </div>
              <div>
                <p className="text-3xl font-bold tabular-nums">
                  {fb.would_recommend_pct > 0 ? `${fb.would_recommend_pct}%` : "—"}
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                  recomendariam
                </p>
              </div>
            </div>

            {Object.keys(fb.feeling_distribution).length > 0 && (
              <>
                <Separator className="my-3" />
                <p className="text-xs text-muted-foreground mb-2">
                  Como as pessoas se sentiram após a análise:
                </p>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(fb.feeling_distribution)
                    .sort(([, a], [, b]) => b - a)
                    .map(([feeling, count]) => (
                      <span
                        key={feeling}
                        className="inline-flex items-center gap-1 text-xs bg-muted px-2 py-1 rounded-full"
                      >
                        <span>{FEELING_ICONS[feeling] ?? "❓"}</span>
                        <span>{FEELING_LABELS[feeling] ?? feeling}</span>
                        <span className="font-medium tabular-nums">({count})</span>
                      </span>
                    ))}
                </div>
              </>
            )}
          </CardContent>
        </Card>
      )}

      {/* Nível de risco */}
      <SectionCard title="Nível de risco detectado">
        {RISK_ORDER.filter((k) => summary.by_risk_level[k] !== undefined).map(
          (key) => (
            <DistributionRow
              key={key}
              label={RISK_LABELS[key] ?? key}
              count={summary.by_risk_level[key] ?? 0}
              total={riskTotal}
              colorClass={RISK_COLORS[key]?.bar ?? "bg-foreground"}
              labelClass={RISK_COLORS[key]?.label ?? ""}
              dot={RISK_COLORS[key]?.dot}
            />
          )
        )}
      </SectionCard>

      {/* Plataforma */}
      <SectionCard title="Por plataforma">
        {Object.entries(summary.by_platform).map(([key, count]) => (
          <DistributionRow
            key={key}
            label={PLATFORM_LABELS[key] ?? key}
            count={count}
            total={summary.total}
          />
        ))}
      </SectionCard>

      {/* Tipo de conteúdo */}
      <SectionCard title="Por tipo de conteúdo">
        {Object.entries(summary.by_content_type)
          .sort(([, a], [, b]) => b - a)
          .map(([key, count]) => (
            <DistributionRow
              key={key}
              label={CONTENT_TYPE_LABELS[key] ?? key}
              count={count}
              total={summary.total}
            />
          ))}
      </SectionCard>

      <Separator />

      {/* Cobertura de fontes externas */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground uppercase tracking-wide">
            Cobertura de fontes externas
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <CoverageCard
            label="Google Fact Check encontrou verificações"
            value={summary.fact_check_coverage}
          />
          <CoverageCard
            label="GDELT encontrou cobertura na mídia"
            value={summary.gdelt_coverage}
          />
          {persistent && persistent.avg_confidence > 0 && (
            <CoverageCard
              label="Confiança média nas análises"
              value={persistent.avg_confidence}
            />
          )}
        </CardContent>
      </Card>

      {/* Médias de sinais */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground uppercase tracking-wide">
            Sinais médios de linguagem
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <CoverageCard
            label="Urgência média"
            value={summary.avg_urgency}
          />
          <CoverageCard
            label="Manipulação média"
            value={summary.avg_manipulation}
          />
        </CardContent>
      </Card>

      {/* Rodapé */}
      <p className="text-xs text-muted-foreground text-center pb-4">
        Dados anonimizados — sem identificação pessoal (LGPD).
        Atualizado a cada 5 minutos.
      </p>
    </div>
  );
}
