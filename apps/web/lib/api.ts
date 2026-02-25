/**
 * api.ts — cliente para o backend FastAPI do Mentor Digital
 *
 * Usa NEXT_PUBLIC_BOT_API_URL configurado no .env.local.
 * Fallback para localhost:8000 em desenvolvimento.
 */

const BASE_URL =
  process.env.NEXT_PUBLIC_BOT_API_URL ?? "http://localhost:8000";

// ── NLP ──────────────────────────────────────────────────────────────────────

export interface NLPSignal {
  score: number;
  evidence: string[];
}

// ── Fact-check ────────────────────────────────────────────────────────────────

export interface ClaimReview {
  publisher_name: string;
  publisher_site: string;
  url: string;
  title: string;
  review_date: string;
  text_rating: string;
  rating_value: number; // 1–7 Google scale (1=false, 7=true), 0=unknown
  language_code: string;
}

export interface FactCheckClaim {
  text: string;
  claimant: string;
  claim_date: string;
  reviews: ClaimReview[];
}

export interface FactCheckData {
  query: string;
  error: string;
  next_page_token: string;
  results: FactCheckClaim[];
}

// ── GDELT ─────────────────────────────────────────────────────────────────────

export interface GDELTArticle {
  url: string;
  title: string;
  domain: string;
  language: string;
  source_country: string;
  seen_date: string; // ISO 8601
  social_image: string;
}

export interface GDELTData {
  query: string;
  error: string;
  articles: GDELTArticle[];
}

// ── Análise completa ──────────────────────────────────────────────────────────

export interface AnalysisResult {
  analyzed_at: string;
  query: string;
  fact_check: {
    pt: FactCheckData;
    en: FactCheckData;
  };
  gdelt: {
    por: GDELTData;
    en: GDELTData;
  };
  nlp: {
    language: string;
    word_count: number;
    caps_ratio: number;
    error: string;
    urgency: NLPSignal;
    claim: NLPSignal;
    manipulation: NLPSignal;
  };
  domain?: {
    domain: string;
    error: string;
  };
}

// ── Analytics ─────────────────────────────────────────────────────────────────

export interface AnalyticsSummary {
  total: number;
  period_days: number;
  by_platform: Record<string, number>;
  by_content_type: Record<string, number>;
  by_risk_level: Record<string, number>;
  by_language: Record<string, number>;
  fact_check_coverage: number;
  gdelt_coverage: number;
  avg_urgency: number;
  avg_manipulation: number;
  error?: string;
}

// ── Fetch ─────────────────────────────────────────────────────────────────────

export async function fetchAnalysis(
  contentId: string
): Promise<AnalysisResult | null> {
  try {
    const res = await fetch(`${BASE_URL}/analysis/${contentId}`, {
      next: { revalidate: 60 }, // cache por 60s no Next.js
    });
    if (!res.ok) return null;
    return res.json() as Promise<AnalysisResult>;
  } catch {
    return null;
  }
}

export async function fetchAnalyticsSummary(
  days = 30
): Promise<AnalyticsSummary | null> {
  try {
    const res = await fetch(`${BASE_URL}/analytics/summary?days=${days}`, {
      next: { revalidate: 300 }, // cache por 5 min — analytics não muda a cada segundo
    });
    if (!res.ok) return null;
    return res.json() as Promise<AnalyticsSummary>;
  } catch {
    return null;
  }
}
