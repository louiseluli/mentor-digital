/**
 * api.ts — cliente para o backend FastAPI do Mentor Digital
 *
 * Server components (fetchAnalysis) use BOT_API_URL at runtime.
 * Client components use NEXT_PUBLIC_BOT_API_URL (inlined at build time).
 * Fallback para localhost:8000 em desenvolvimento.
 */

// Use 127.0.0.1 (not localhost) to avoid IPv6 resolution issues in Node.js
// server components — uvicorn binds to 127.0.0.1 by default.
const BASE_URL =
  process.env.BOT_API_URL ??
  process.env.NEXT_PUBLIC_BOT_API_URL ??
  "http://127.0.0.1:8000";

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

// ── Wikipedia ─────────────────────────────────────────────────────────────────

export interface WikipediaResult {
  title: string;
  extract: string;
  url: string;
  thumbnail: string;
  lang: string;
}

export interface WikipediaData {
  query: string;
  results: WikipediaResult[];
  error: string;
}

// ── Brazilian FC ─────────────────────────────────────────────────────────────

export interface BrazilianFCResult {
  title: string;
  url: string;
  date: string;
  source: string;
  snippet: string;
}

export interface BrazilianFCData {
  query: string;
  results: BrazilianFCResult[];
  error: string;
}

// ── Risk Score ────────────────────────────────────────────────────────────────

export type RiskVerdict =
  | "verified_false"
  | "mixed"
  | "verified_true"
  | "no_clear_verdict"
  | "no_data";

export type RiskLevel = "low" | "moderate" | "high" | "critical";

export interface RiskScore {
  overall: number;            // 0–1
  level: RiskLevel;
  level_label: string;        // "Baixo risco" etc.
  verdict: RiskVerdict;
  verdict_pt: string;         // texto em português
  dimensions: {
    linguistic: number;
    factcheck: number | null; // null se sem dados FC
    coverage: number;
  };
  confidence: number;         // 0–1
  fc_verdict_breakdown: {
    total: number;
    false: number;
    mixed: number;
    true: number;
  };
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
  wikipedia?: {
    pt: WikipediaData;
    en: WikipediaData;
  };
  brazilian_fc?: BrazilianFCData;
  risk_score?: RiskScore;
  domain?: {
    domain: string;
    error: string;
  };
}

// ── Chat ──────────────────────────────────────────────────────────────────────

export interface ChatRawMessage {
  type: string;
  body: string;
  options?: { id: string; title: string }[];
}

export interface ChatStartResponse {
  session_id: string;
  content_id: string;
  state: string;
  messages: ChatRawMessage[];
}

export interface ChatReplyResponse {
  session_id: string;
  state: string;
  messages: ChatRawMessage[];
  analysis_ready: boolean;
  content_id: string;
}

export interface ChatStatusResponse {
  ready: boolean;
  content_id: string;
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
  const url = `${BASE_URL}/analysis/${contentId}`;
  try {
    const res = await fetch(url, {
      cache: "no-store",
    });
    if (!res.ok) return null;
    return res.json() as Promise<AnalysisResult>;
  } catch {
    return null;
  }
}

export async function startChat(
  text: string
): Promise<ChatStartResponse | null> {
  try {
    const res = await fetch(`${BASE_URL}/chat/start`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });
    if (!res.ok) return null;
    return res.json() as Promise<ChatStartResponse>;
  } catch {
    return null;
  }
}

export async function replyChat(
  sessionId: string,
  optionId: string
): Promise<ChatReplyResponse | null> {
  try {
    const res = await fetch(`${BASE_URL}/chat/reply/${sessionId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ option_id: optionId }),
    });
    if (!res.ok) return null;
    return res.json() as Promise<ChatReplyResponse>;
  } catch {
    return null;
  }
}

export async function chatStatus(
  sessionId: string
): Promise<ChatStatusResponse | null> {
  try {
    const res = await fetch(`${BASE_URL}/chat/${sessionId}/status`);
    if (!res.ok) return null;
    return res.json() as Promise<ChatStatusResponse>;
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
