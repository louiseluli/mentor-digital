/**
 * /analise/[content_id] — Página de análise
 *
 * Pure client-side fetch — avoids Next.js server-side fetch issues
 * (IPv6, caching, Turbopack). The browser can always reach the backend
 * reliably (same path as the chat flow).
 */

import type { Metadata } from "next";
import AnalysisContent from "./analysis-content";

interface Props {
  params: Promise<{ content_id: string }>;
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { content_id } = await params;
  return {
    title: `Análise ${content_id.slice(0, 8)}… — Mentor Digital`,
  };
}

export default async function AnalisePage({ params }: Props) {
  const { content_id } = await params;
  return <AnalysisContent contentId={content_id} />;
}
