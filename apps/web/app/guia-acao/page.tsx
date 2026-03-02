/**
 * /guia-acao — Guia de Ação: Conteúdo Criminoso
 *
 * Criminal Content Action Guide per AGENT_BLUEPRINT.
 * Provides clear, actionable steps for reporting hate speech,
 * threats, exploitation, and other criminal content online.
 *
 * Static page — no API calls needed.
 */

import type { Metadata } from "next";
import PanelCard from "@/components/panel-card";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Guia de Ação — Mentor Digital",
  description:
    "Saiba como denunciar conteúdo criminoso online: discurso de ódio, ameaças, exploração. Canais oficiais e passo a passo.",
};

// ── Action cards data ─────────────────────────────────────────────────────────

interface ActionCard {
  icon: string;
  title: string;
  description: string;
  steps: string[];
  channels?: { name: string; url: string; description: string }[];
}

const ACTIONS: ActionCard[] = [
  {
    icon: "🛑",
    title: "Discurso de Ódio e Racismo",
    description:
      "Ofensas, xingamentos ou incitação à violência contra grupos por raça, etnia, religião, orientação sexual ou gênero. É crime no Brasil (Lei 7.716/89, Lei 14.532/2023).",
    steps: [
      "Faça screenshot/print com data, hora e perfil visíveis",
      "Denuncie dentro da plataforma (botão denunciar)",
      "Registre ocorrência online ou presencialmente",
      "Se possível, salve o link original do conteúdo",
    ],
    channels: [
      {
        name: "SaferNet Brasil",
        url: "https://denuncie.org.br",
        description: "Canal oficial para crimes cibernéticos",
      },
      {
        name: "Disque 100",
        url: "tel:100",
        description: "Direitos humanos — funciona 24h",
      },
    ],
  },
  {
    icon: "⚠️",
    title: "Ameaças e Intimidação",
    description:
      "Ameaças diretas ou indiretas de violência, perseguição (stalking) ou intimidação online. Crime previsto no Código Penal (Art. 147).",
    steps: [
      "Não responda à ameaça — isso pode escalá-la",
      "Faça screenshots de TUDO (mensagens, perfis, datas)",
      "Bloqueie o agressor na plataforma",
      "Registre Boletim de Ocorrência imediatamente",
      "Se sentir perigo imediato, ligue 190 (Polícia Militar)",
    ],
    channels: [
      {
        name: "Delegacia Online",
        url: "https://www.gov.br/pf/pt-br",
        description: "Varia por estado — busque 'delegacia eletrônica' + seu estado",
      },
      {
        name: "190 — Polícia Militar",
        url: "tel:190",
        description: "Emergências e ameaças iminentes",
      },
    ],
  },
  {
    icon: "🚨",
    title: "Violência contra Mulheres",
    description:
      "Revenge porn, assédio online, divulgação não consensual de imagens íntimas, perseguição digital. Lei Maria da Penha estende proteção ao ambiente digital.",
    steps: [
      "Salve todas as evidências (prints, links, vídeos)",
      "NÃO apague as mensagens — são provas",
      "Denuncie na plataforma onde ocorreu",
      "Ligue para 180 (Central de Atendimento à Mulher)",
      "Registre B.O. na Delegacia da Mulher mais próxima",
    ],
    channels: [
      {
        name: "Ligue 180",
        url: "tel:180",
        description: "Central de Atendimento à Mulher — 24h, gratuito",
      },
      {
        name: "SaferNet — Helpline",
        url: "https://helpline.org.br",
        description: "Orientação para vítimas de violência digital",
      },
    ],
  },
  {
    icon: "🔒",
    title: "Exploração de Crianças e Adolescentes",
    description:
      "Qualquer conteúdo que explore, exponha ou sexualize menores de 18 anos. Crime gravíssimo (ECA, Art. 241).",
    steps: [
      "NÃO compartilhe o conteúdo, mesmo para denunciar",
      "NÃO tente investigar por conta própria",
      "Denuncie imediatamente nos canais oficiais",
      "Se conhecer a vítima, acione o Conselho Tutelar",
    ],
    channels: [
      {
        name: "Disque 100",
        url: "tel:100",
        description: "Denúncia de violação de direitos de crianças — 24h",
      },
      {
        name: "SaferNet — Denúncia",
        url: "https://denuncie.org.br",
        description: "Denúncia online de exploração infantil",
      },
    ],
  },
  {
    icon: "📢",
    title: "Desinformação Perigosa",
    description:
      "Informações falsas que colocam vidas em risco: tratamentos médicos falsos, golpes financeiros, fraudes eleitorais.",
    steps: [
      "Verifique antes de compartilhar — use ferramentas como o Mentor Digital",
      "Denuncie na plataforma como 'informação falsa'",
      "Se envolver saúde pública, notifique a Ouvidoria do SUS",
      "Se envolver golpe financeiro, registre no Procon e B.O.",
      "Se envolver eleições, denuncie ao TSE",
    ],
    channels: [
      {
        name: "Mentor Digital",
        url: "/",
        description: "Analise conteúdo antes de compartilhar",
      },
      {
        name: "TSE — Denúncia de Fake News",
        url: "https://www.tse.jus.br",
        description: "Desinformação eleitoral",
      },
    ],
  },
];

// ── Page component ────────────────────────────────────────────────────────────

export default function GuiaAcaoPage() {
  return (
    <main className="max-w-2xl mx-auto px-6 py-8 space-y-6">
      {/* Header */}
      <div className="space-y-2">
        <h1 className="font-display text-3xl sm:text-4xl tracking-wide">
          GUIA DE AÇÃO
        </h1>
        <p className="text-sm text-muted-foreground">
          Encontrou conteúdo criminoso ou perigoso online? Saiba como se
          proteger e denunciar de forma efetiva.
        </p>
      </div>

      {/* Important note */}
      <PanelCard>
        <div className="space-y-2">
          <p className="text-xs font-mono text-muted-foreground uppercase tracking-wider">
            Importante
          </p>
          <p className="text-sm">
            Sua segurança vem primeiro. Nunca confronte o agressor diretamente
            online. Salve evidências, denuncie nos canais oficiais e busque apoio.
            Você não precisa enfrentar isso sozinha.
          </p>
        </div>
      </PanelCard>

      {/* Action cards */}
      {ACTIONS.map((action, idx) => (
        <PanelCard key={idx}>
          <div className="space-y-3">
            <div className="flex items-start gap-3">
              <span className="text-2xl" aria-hidden="true">
                {action.icon}
              </span>
              <div>
                <h2 className="text-base font-semibold">{action.title}</h2>
                <p className="text-sm text-muted-foreground mt-0.5">
                  {action.description}
                </p>
              </div>
            </div>

            <div className="space-y-1.5 pl-2">
              <p className="text-xs font-mono text-muted-foreground uppercase tracking-wider">
                Passo a passo
              </p>
              <ol className="list-decimal list-inside space-y-1 text-sm">
                {action.steps.map((step, i) => (
                  <li key={i} className="leading-relaxed">
                    {step}
                  </li>
                ))}
              </ol>
            </div>

            {action.channels && action.channels.length > 0 && (
              <div className="space-y-1.5 pl-2">
                <p className="text-xs font-mono text-muted-foreground uppercase tracking-wider">
                  Onde denunciar
                </p>
                <div className="space-y-2">
                  {action.channels.map((ch, i) => (
                    <a
                      key={i}
                      href={ch.url}
                      target={ch.url.startsWith("http") ? "_blank" : undefined}
                      rel={
                        ch.url.startsWith("http")
                          ? "noopener noreferrer"
                          : undefined
                      }
                      className="flex items-center gap-2 text-sm text-primary hover:underline"
                    >
                      <span className="font-medium">{ch.name}</span>
                      <span className="text-xs text-muted-foreground">
                        — {ch.description}
                      </span>
                    </a>
                  ))}
                </div>
              </div>
            )}
          </div>
        </PanelCard>
      ))}

      {/* Footer CTA */}
      <div className="text-center space-y-3 py-4">
        <p className="text-sm text-muted-foreground">
          Lembre-se: denunciar protege você e toda a comunidade.
        </p>
        <div className="flex flex-wrap justify-center gap-4">
          <Link
            href="/"
            className="text-xs text-primary hover:underline"
          >
            ← Analisar conteúdo
          </Link>
          <Link
            href="/aprender"
            className="text-xs text-primary hover:underline"
          >
            Aprender mais →
          </Link>
        </div>
      </div>
    </main>
  );
}
