/**
 * /balanca/[content_id] — Balança da Evidência
 *
 * Visualizes evidence supporting vs contradicting a claim,
 * following the AGENT_BLUEPRINT Section 5.1 design.
 * Client-side fetching for reliability.
 */

import type { Metadata } from "next";
import BalanceContent from "./balance-content";

interface Props {
  params: Promise<{ content_id: string }>;
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { content_id } = await params;
  return {
    title: `Balança da Evidência — Mentor Digital`,
    description: "Veja as evidências a favor e contra para formar sua própria conclusão.",
  };
}

export default async function BalancaPage({ params }: Props) {
  const { content_id } = await params;
  return <BalanceContent contentId={content_id} />;
}
