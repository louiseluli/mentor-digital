import AnalysisForm from "@/components/analysis-form";
import PanelCard from "@/components/panel-card";

export default function Home() {
  return (
    <main className="min-h-screen flex flex-col items-center justify-center px-4 py-12">
      <div className="w-full max-w-lg space-y-6">
        {/* Hero */}
        <div className="text-center space-y-3">
          <h1 className="font-display text-6xl text-foreground tracking-wide">
            MENTOR DIGITAL
          </h1>
          <p className="text-[10px] font-mono text-hud-muted uppercase tracking-[0.25em]">
            Análise de conteúdo · Apoio ao pensamento crítico
          </p>
          <p className="text-sm text-muted-foreground max-w-sm mx-auto leading-relaxed">
            Cole um texto ou notícia que recebeu. Vamos analisar juntos —
            identificar linguagem de urgência, apelos emocionais e verificar
            fatos antes de compartilhar.
          </p>
        </div>

        {/* Form inside HUD panel */}
        <PanelCard>
          <AnalysisForm />
        </PanelCard>

        <p className="text-center text-[11px] font-mono text-hud-muted">
          Resultados disponíveis por 7 dias · Nenhum dado pessoal é armazenado
        </p>
      </div>
    </main>
  );
}
