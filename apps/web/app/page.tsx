import AnalysisForm from "@/components/analysis-form";

export default function Home() {
  return (
    <main className="min-h-screen flex flex-col items-center justify-center p-8">
      <div className="w-full max-w-lg space-y-6">
        <div className="text-center space-y-2">
          <h1 className="text-2xl font-semibold tracking-tight">
            Mentor Digital
          </h1>
          <p className="text-sm text-muted-foreground">
            Cole um texto ou notícia que recebeu. Vamos analisar juntos —
            identificar linguagem de urgência, apelos emocionais e verificar
            fatos antes de compartilhar.
          </p>
        </div>

        <AnalysisForm />

        <p className="text-center text-xs text-muted-foreground">
          Os resultados ficam disponíveis por 7 dias. Nenhum dado pessoal é
          armazenado.
        </p>
      </div>
    </main>
  );
}
