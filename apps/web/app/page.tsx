export default function Home() {
  return (
    <main className="min-h-screen flex flex-col items-center justify-center p-8 text-center">
      <div className="max-w-md space-y-4">
        <h1 className="text-2xl font-semibold tracking-tight">
          Mentor Digital
        </h1>
        <p className="text-muted-foreground">
          Esta página exibe os resultados de análise de um conteúdo compartilhado
          via bot. Para acessar uma análise, use o link enviado pelo Mentor Digital
          no Telegram.
        </p>
        <p className="text-sm text-muted-foreground">
          Os resultados ficam disponíveis por 7 dias.
        </p>
      </div>
    </main>
  );
}
