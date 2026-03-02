# Building a fake news reporting agent for Brazilian minority communities

A fully functional Fake News Reporting Agent combining a WhatsApp/Telegram chatbot with a web-based analysis platform can be built on an open-source-first stack for **under $100/month at MVP scale**, scaling to $700–1,200/month at 10,000 users. The optimal architecture pairs a Python/FastAPI chatbot service using finite state machines for guided flows with a Next.js 15 progressive web app, backed by PostgreSQL, Redis, and BERTimbau-based NLP models fine-tuned on the Fake.BR corpus. WhatsApp's free service conversation model (user-initiated messages cost nothing) makes this economically viable for underserved communities, while Telegram's completely free Bot API provides a zero-cost secondary channel. Every component below uses production-ready, 2024–2025 technology with specific versions and pricing.

---

## 1. Chatbot architecture: WhatsApp and Telegram as primary channels

### WhatsApp Business Cloud API

WhatsApp dominates Brazil with **120+ million users**, making it the essential channel. The Cloud API (hosted by Meta, replacing the deprecated on-premises option) requires a Meta Developer account, a Business App, a verified phone number, and webhook configuration pointing to a public HTTPS endpoint.

**Pricing changed significantly on July 1, 2025.** The model shifted from conversation-based to per-message pricing across four categories: Marketing (~$0.0625/msg in Brazil), Utility (tiered discounts), Authentication (lowest tier), and Service (**completely free** within the 24-hour window). For a fact-checking chatbot where users initiate conversations, **all service replies are free with no monthly cap** — this is the critical cost advantage. Utility templates sent within the 24-hour customer service window are also free since April 2025.

Interactive message types drive the guided flow: **Quick Reply Buttons** (up to 3 options), **List Messages** (up to 10 items in sections), and Call-to-Action buttons. These eliminate typing burden for users on basic smartphones. Messaging tiers start at 250 unique users/day, scaling to 1,000 after business verification, then 10,000 and 100,000 based on quality signals. Default throughput is **80 messages/second** per phone number.

Webhook configuration requires echoing `hub.challenge` for verification, subscribing to message and status events, and implementing **HMAC-SHA256 signature verification** on every incoming request using the `X-Hub-Signature-256` header. Webhooks retry with backoff for up to 24 hours on failure.

### Telegram Bot API

Telegram Bot API **9.4** (February 2026) is completely free with no per-message charges. Setup takes minutes through @BotFather: create a bot, receive a token, configure commands and menus. The `python-telegram-bot` library (v22.5) provides a production-stable async framework with a built-in `ConversationHandler` that implements state machine patterns natively.

Inline keyboards support `callback_data` for branching logic, `url` for external links, and `web_app` for full HTML5 Mini Apps embedded within Telegram. Rate limits are approximately 30 messages/second globally and 1 message/second per chat. Webhooks (for production, requiring HTTPS) deliver lower latency than long polling (better for development). Bot API 9.4 introduced button styling with custom emoji icons and color options.

### Framework comparison and recommendation

| Framework | Cost | Portuguese | Complexity | Best For |
|-----------|------|-----------|------------|----------|
| **Botpress Cloud** | Free tier (500 msg/mo), $79/mo Plus | Auto-translate | Low | Visual builder, quick MVP |
| **Rasa Pro (CALM)** | Free ≤1K conversations/mo | Via LLM | High (Kubernetes) | Complex NLU, data sovereignty |
| **Dialogflow CX** | $600 free credit, ~$0.005/query | Native PT-BR | Medium | Google Cloud integration |
| **LangChain/LangGraph** | Open source + LLM API costs | Via LLM | High | Maximum flexibility |
| **Custom FSM (Python)** | $0 | N/A (rule-based) | Medium | Budget-optimized, full control |

**For a budget-constrained social impact project, the custom Python FSM approach is optimal.** It eliminates per-interaction AI costs while delivering excellent UX through WhatsApp's interactive buttons and lists. The `transitions` library (v0.9.x) provides a lightweight finite state machine with nested states and transition callbacks. Redis stores session state with TTL matching WhatsApp's 24-hour window. The architecture is: `User → Webhook (FastAPI) → Session Manager (Redis) → FSM Engine → Response Generator → Platform API`.

For the guided questioning flow, model conversations as a tree structure in YAML/JSON where each node contains a prompt, expected input patterns, and child nodes for each response. Branching logic evaluates user responses against conditions and transitions the FSM accordingly. The `python-telegram-bot` ConversationHandler provides this pattern natively for Telegram; for WhatsApp, implement the same pattern against the Cloud API directly.

---

## 2. NLP and AI models purpose-built for Portuguese fake news

### BERTimbau and the Portuguese model ecosystem

**BERTimbau** (`neuralmind/bert-base-portuguese-cased`, 110M parameters) remains the workhorse encoder for Portuguese NLP. Fine-tuning BERTimbau on the **Fake.BR corpus** (7,200 aligned articles, 3,600 true + 3,600 fake) achieves state-of-the-art fake news classification, significantly outperforming traditional ML baselines. The larger variant (`neuralmind/bert-large-portuguese-cased`, 335M parameters) provides better accuracy at higher compute cost.

The Portuguese NLP ecosystem expanded significantly in 2024–2025:

- **Albertina PT-BR** (`PORTULAN/albertina-900m-portuguese-ptbr-encoder-brwac`, 900M params, DeBERTa V2 architecture) offers the largest open encoder model trained on BrWaC (2.7B tokens)
- **Tucano** (`TucanoBR/Tucano-2b4-Instruct`, Apache 2.0) is the **best open-source generative model** for Brazilian Portuguese, trained on GigaVerbo (200B tokens), with instruct-tuned versions preferred over Sabiá-7B in AlpacaEval
- **BERTabaporu** (`pablocosta/bertabaporu-base-uncased`) is a RoBERTa model trained on Portuguese tweets — ideal for social media text analysis
- **Sabiá-3** (Maritaca AI, commercial API only) matches GPT-4o on Brazilian university entrance exams at ~10× lower cost per token

For sentiment analysis, **pysentimiento** (`pysentimiento/bertweet-pt-sentiment`) provides a ready-to-use analyzer: `create_analyzer(task="sentiment", lang="pt")` returns POS/NEG/NEU classifications with confidence scores. Additional datasets include TweetSentBR for social media and the unified Brazilian Portuguese Sentiment Analysis Datasets on Kaggle.

### Detecting emotional manipulation and propaganda

Emotional manipulation detection uses a dual approach. First, identify **propaganda techniques** using XLM-RoBERTa + CRF models trained on the Propaganda Techniques Corpus, which classifies 18 techniques including Appeal to Fear, Loaded Language, Flag-Waving, and Bandwagon. This approach achieves F1=0.67, significantly outperforming GPT-4's F1=0.16 on the same task. Second, detect linguistic markers: hyperbolic/superlative patterns, excessive exclamation marks or ALL CAPS, urgency markers ("compartilhe antes que apaguem!"), appeal to authority without citation, and decontextualized statistics.

The **NILC-Metrix** toolkit from USP provides comprehensive Brazilian Portuguese text analysis metrics including readability, cohesion, and linguistic complexity — useful features for distinguishing legitimate journalism from fabricated content.

### Building the Balance of Evidence system

The Balance of Evidence pipeline operates in five stages. **Claim Processing** decomposes complex claims into atomic sub-claims using Tucano-Instruct or GPT-4, extracts entities with spaCy (`pt_core_news_lg`), and generates search queries. **Evidence Retrieval** queries the Google Fact Check Tools API, Brazilian fact-checker RSS feeds, GDELT, and web search APIs. **Stance Detection** classifies each source as agree/disagree/neutral using XLM-RoBERTa fine-tuned on the FNC-1 dataset or zero-shot NLI via `joeddav/xlm-roberta-large-xnli`. **Evidence Aggregation** computes a weighted score: `balance = Σ(stance × confidence × credibility) / Σ(credibility)`, normalized to a [-1, +1] scale. **Presentation** renders a visual gauge from "Mostly Contradicted" to "Mostly Supported" with drill-down to individual sources.

For stance detection, Dempster-Shafer theory offers an elegant unsupervised approach that handles uncertainty in conflicting evidence through belief functions, avoiding the need for labeled stance data in Portuguese.

---

## 3. Deepfake detection with open-source models

### Current detection landscape

The deepfake detection field faces a critical **cross-dataset generalization gap**: models trained on one dataset (e.g., DFDC) achieving >90% AUC can drop to ~60% on in-the-wild samples. Vision Transformers (ViT, Swin) generalize better than CNNs by capturing global spatial-temporal cues rather than pixel-level noise. The top architectures in 2024–2025 are XceptionNet (balanced performance, low false positives), EfficientNet-B4 (top within-domain accuracy), and GenConViT (ConvNeXt + Swin Transformer hybrid).

**Microsoft Video Authenticator is not publicly available** — it was announced in 2020 but never released as a downloadable tool or API. **Intel FakeCatcher** claims 96% accuracy using photoplethysmography (blood flow analysis) but is enterprise-only and not open source. Neither is viable for integration.

### Practical open-source frameworks

**DeepfakeBench** (`SCLBD/DeepfakeBench`, NeurIPS 2023) is the most comprehensive open-source platform with **36 detectors** (28 image + 8 video) including XceptionNet, EfficientNet, CLIP-based, and Multi-Attention models across 9 datasets. It provides Docker support, pre-trained weights, and LMDB for fast I/O. **DeepSafe** (`siddharthksah/DeepSafe`) offers a fully containerized microservices platform with Nginx, FastAPI, and a meta-learner ensemble — the **best ready-to-deploy option** for web platform integration.

The processing pipeline for integration: user uploads go to S3/MinIO, a Celery + Redis task queue dispatches to GPU workers running XceptionNet or EfficientNet inference, results (confidence score 0–1, GradCAM heatmaps, frame-by-frame timeline for video) are written to PostgreSQL and delivered via WebSocket. Image analysis takes **100–500ms on GPU**; a 30-second video requires 1–5 minutes on a single GPU. For cost-effective GPU inference, **RunPod** offers RTX 4090 at $0.44/hour and **Vast.ai** provides RTX 3090 from $0.16/hour on community nodes.

### Reverse image search integration

Google does not offer a direct reverse image search API, but the **Cloud Vision API's Web Detection** feature finds visually similar images across the web (first 1,000 units/month free, then $1.50–5.00/1K). **TinEye API** provides dedicated reverse image search across 41.9B+ indexed images ($200 for 5,000 searches). For an open-source approach, combine **perceptual hashing** (`imagehash` library — pHash, dHash with Hamming distance threshold of 2–5 for duplicates) with **CLIP embeddings** stored in FAISS for semantic similarity search. This hybrid catches both exact/near duplicates and semantically similar but visually different manipulations.

---

## 4. Algorithmic bias detection and content spread analysis

**AI Fairness 360** (IBM, `pip install aif360`) provides 71 bias metrics and 9 mitigation algorithms across pre-processing, in-processing, and post-processing stages. **Fairlearn** (Microsoft, `pip install fairlearn`) offers `MetricFrame` for disaggregated evaluation across demographic groups and mitigation through `ThresholdOptimizer` and `ExponentiatedGradient`. Both are free, open-source, and scikit-learn compatible. For auditing content recommendation bias, use sock puppet experiments with test accounts representing different demographic profiles, measure content diversity using Shannon entropy of topic distributions, and apply the **RADio metrics** (RecSys 2022) for rank-aware divergence in news recommendations.

For tracking content spread, **CrowdTangle was shut down August 14, 2024** and replaced by Meta Content Library, which is restricted to vetted academic researchers (not available for commercial use). Alternatives include NewsWhip (offers 50% discount for former CrowdTangle users) and BuzzSumo ($199/month). Open-source tools for network analysis include **NetworkX** for graph algorithms (community detection, centrality, information diffusion models), **Gephi** for desktop visualization (handles up to 300K nodes), and **Sigma.js** for web-embedded interactive graphs. Content spread is best visualized as cascade trees showing propagation from original poster through reshares, animated temporal network graphs, and Sankey diagrams showing cross-platform flow.

Filter bubble analysis combines **BERTopic** for topic modeling on content feeds with Shannon entropy measurement of topic distributions. The **SNEEV framework** provides a noise-controlled methodology for isolating personalization effects. Present results to users through a diversity dashboard (0–100% score), topic distribution charts comparing consumed vs. available content, and "perspective nudges" suggesting underexplored viewpoints.

---

## 5. Web platform built for performance on basic smartphones

### Tech stack for the web application

The recommended stack is **Next.js 15** (App Router) with TypeScript, Tailwind CSS v4, and shadcn/ui (built on Radix UI primitives — fully accessible, touch-friendly). Backend uses Next.js Server Actions and API Routes for the web platform, with a separate **Python/FastAPI** service for the chatbot and ML pipeline. **Supabase** provides PostgreSQL + Auth + Realtime + Storage on a generous free tier. **Prisma** ORM (v6/7, now pure TypeScript) handles database interactions. State management uses **Zustand** for client state and **TanStack Query v5** for server state with caching and background refetching.

For the Balance of Evidence visualization, **Recharts** handles standard charts while **Nivo** or custom D3/Visx renders the evidence spectrum — a horizontal bar from "Strong Contradiction" to "Strong Confirmation" with interactive source drill-down. Evidence cards display supporting (green) and contradicting (red) sources with credibility indicators and publication dates.

### Progressive Web App as the deployment model

PWA is **strongly recommended over native** for this use case. Brazil is Android-dominant, and PWAs work excellently on Chrome Android with full installation, push notifications, offline support, and background sync. iOS support improved significantly since iOS 16.4+ (push notifications now work, though with restrictions). Key advantages: no Play Store dependency, instant updates, smaller storage footprint, and discoverability via search engines.

Implementation uses **Workbox** for service worker management: cache-first for the app shell (instant load), network-first with cache fallback for API data, and stale-while-revalidate for static assets. **@serwist/next** integrates Workbox with Next.js. **Dexie.js** wraps IndexedDB for offline data storage with reactive streams and optional cloud sync. Background Sync API via `workbox-background-sync` queues failed requests for replay when connectivity returns.

### Performance optimization for Brazilian connectivity

Brazil's digital divide is stark: urban areas reach 94.1% connectivity while rural areas lag at 81%, and favela residents depend almost entirely on 3G/4G mobile with speeds far below city averages. The performance budget must target **<200KB compressed initial load, <5s Time to Interactive on 3G, and <2.5s Largest Contentful Paint**.

Optimization strategies: Next.js automatic code splitting per route with `dynamic()` imports for heavy components; Brotli compression (20–30% smaller than gzip); `next/image` for automatic WebP/AVIF conversion with blur placeholders; system fonts to eliminate font download costs; React Server Components to reduce client JavaScript; and skeleton screens (shadcn/ui includes a `Skeleton` component) for perceived performance. Detect the `Save-Data` HTTP header to serve lower-resolution images and disable animations automatically. Deploy on **Vercel** (free hobby tier, São Paulo edge) with **Cloudflare** DNS (free tier, global CDN with São Paulo PoP).

For internationalization, **next-intl** provides type-safe translations with Server Component support, Brazilian locale formatting (DD/MM/YYYY dates, comma decimal separators, R$ currency), and middleware for locale detection. Ensure fonts support full Latin Extended character sets for Portuguese diacritics (á, é, ã, õ, ç).

### Accessibility compliance

Target **WCAG 2.2 Level AA** (released October 2023, ISO/IEC 40500:2025). Brazil's Lei 10.098/2000 and e-MAG standard mandate accessibility aligned with WCAG 2.0 AA for government sites. Key WCAG 2.2 additions include minimum **24×24px touch targets**, focus appearance requirements, accessible authentication (no cognitive function tests), and consistent help placement. shadcn/ui + Radix UI provide accessibility-first components with full ARIA support and keyboard navigation. Test with **axe-core** in development, **eslint-plugin-jsx-a11y** in CI, and **Pa11y** in the deployment pipeline.

---

## 6. Database architecture: PostgreSQL as the single source of truth

### Schema design

PostgreSQL handles all data types through a hybrid relational + JSONB approach that eliminates the need for a separate document store:

**Core tables**: `users` (anonymous_id, metadata JSONB), `conversations` (platform, timestamps), `messages` (role, content, timestamp), `submissions` (content_type, content_url, status). **Fact-checking**: `claims` (original_text, normalized_text, source_url, search_vector tsvector), `verdicts` (claim_id, verdict_type ENUM, confidence_score, explanation), `evidence` (source_id, excerpt, relevance_score, metadata JSONB), `sources` (domain, credibility_score). **Learning**: `learning_modules` (content JSONB), `user_progress` (module_id, status, score), `badges` (criteria JSONB), `quiz_attempts` (answers JSONB).

Key patterns: **tsvector columns with GIN indexes** for full-text Portuguese search on claims; **JSONB columns** for variable ML outputs (NLP scores, deepfake probabilities) avoiding schema rigidity; **table partitioning by time** for messages and analytics; **soft deletes** with `deleted_at` for LGPD compliance; and **pg_trgm extension** for fuzzy matching on typo-tolerant claim search.

### Why not MongoDB

PostgreSQL's native JSONB support with GIN indexing negates MongoDB's primary advantage. Adding MongoDB would mean two data stores to maintain, loss of relational integrity across fact-check data, and increased operational complexity. PostgreSQL's built-in full-text search is sufficient for up to ~500K documents with 5–10ms query times. Only add **Elasticsearch** (or the ParadeDB pg_search extension for Lucene-grade BM25 within PostgreSQL) when scaling beyond this threshold.

**Redis** is essential for session management (30-minute sliding TTL), caching (fact-check results at 24–72 hour TTL, source credibility at 7-day TTL), and powering **BullMQ** job queues. Expected cache hit rates: 70–85% for fact-check results (users search for the same viral claims), 90%+ for source credibility, delivering **60–75% DB load reduction**.

### Data pipeline

The content processing pipeline flows: REST API intake → schema validation and file type checking → BullMQ dispatch (Redis-backed, with job priorities and retries) → parallel analysis workers (text extraction, NLP analysis, source verification, deepfake detection, cross-reference with existing fact-checks) → PostgreSQL storage → user notification via WebSocket or push. File storage uses **S3** (5GB free tier) with pre-signed URLs for direct upload. For self-hosted S3 compatibility ensuring Brazilian data residency, **MinIO** is the open-source alternative.

---

## 7. LGPD compliance and security for vulnerable populations

### LGPD technical requirements

Brazil's Lei Geral de Proteção de Dados (Law 13.709/2018) applies to any organization processing personal data of individuals in Brazil. Critical requirements for this platform: identify a legal basis per processing activity (consent for optional features, legitimate interest for core fact-checking — requiring a RIPD/DPIA); implement all **9 data subject rights** from Article 18 with a **15-day response deadline**; appoint a DPO (small-scale agents under R$4.8M revenue are exempt unless processing high-risk data like AI); maintain Records of Processing Activities (Article 37); and implement breach notification within **3 business days** to ANPD with a 5-year minimum incident log retention.

LGPD classifies **racial and ethnic origin as sensitive data** — directly relevant for a platform serving minority communities. Cross-border data transfers require ANPD-approved Standard Contractual Clauses (Resolution 19/2024). Penalties reach **2% of Brazilian revenue, capped at R$50 million per violation**. ANPD demonstrated willingness to act in 2024–2025, suspending Meta and X Corp operations for violations.

### Anonymization and encryption

Layer **k-anonymity** (k≥10 for small community datasets) with **differential privacy** (epsilon ≥ 1.0 for published analytics). Use **ARX** (Java, open-source) for k-anonymity/l-diversity/t-closeness and **OpenDP** (Rust/Python) for differential privacy. Never store phone numbers with query content — separate identity from activity using pseudonymous IDs. Suppress location data that could identify small communities. Strip metadata from forwarded messages.

Encrypt data at rest with **AES-256-GCM** for sensitive database fields using AWS KMS for key management. Enforce **TLS 1.3** for all transit with HSTS headers. WhatsApp provides Signal Protocol E2E encryption for personal chats, but Business API messages pass through Meta's servers — implement your own field-level encryption for stored conversation data. Use `crypto.subtle` (Web Crypto API) for browser-side encryption and **libsodium** for server-side operations.

### Threat model for minority users

The STRIDE analysis identifies critical threats: **government surveillance** of fact-checking service users (mitigate with data minimization, no login required, anonymized logs); **doxxing** of users who report misinformation (mitigate by never creating public profiles, separating identity from activity); **adversarial data poisoning** to discredit the platform (mitigate with multi-source verification, human review, anomaly detection on credibility scores); and **metadata analysis** revealing behavioral patterns even without content (mitigate by aggregating logs, adding noise to timestamps, minimizing retention). Webhook endpoints must verify HMAC-SHA256 signatures, reject requests older than 5 minutes (replay prevention), and implement idempotency keys.

---

## 8. Cloud infrastructure optimized for a Brazilian startup

### AWS as primary cloud with São Paulo region

All three major providers have full São Paulo regions (AWS sa-east-1 with 3 AZs, GCP southamerica-east1, Azure brazilsouth). **AWS is recommended** for the broadest service ecosystem, strongest Portuguese documentation, and the most accessible startup credits: **AWS Activate Founders** provides $1,000 immediately (no affiliation needed), Portfolio tier offers up to $100,000 with accelerator backing, and the **Impact Accelerator** specifically targets social impact and underrepresented founders with up to $1M in credits.

Apply for all three credit programs simultaneously — they don't conflict. Google Cloud for Startups offers up to $350,000 over 2 years for AI-first startups. Microsoft for Startups provides $1,000–$5,000 for self-funded companies.

### Hybrid serverless + container deployment

| Component | Deployment | Rationale |
|-----------|-----------|-----------|
| Chatbot webhooks | AWS Lambda | Event-driven, auto-scales, ~200-500ms cold start |
| Web platform API | ECS Fargate | Steady traffic, warm DB connections |
| ML inference workers | ECS Fargate | Long-running, memory-intensive |
| Background jobs (BullMQ) | ECS Fargate | Always-on queue processors |
| Static frontend | S3 + CloudFront | 1TB/month free CDN transfer |
| Scheduled tasks | Lambda + EventBridge | Cost-effective cron replacement |

Use **ARM/Graviton** instances from day one for **20–40% cost savings**. Lambda handles chatbot webhooks efficiently — serverless is cheaper below ~15 requests/second; above that threshold, migrate to Fargate containers.

### Cost estimates by scale

| Scale | Monthly Cost | Key Components |
|-------|-------------|----------------|
| **MVP (100 users)** | **$0–50** | Free tiers + Activate credits cover everything |
| **Growth (1K users)** | **$150–300** | EC2 t3.small, RDS t3.small, ElastiCache |
| **Scale (10K users)** | **$700–1,200** | Multiple Fargate tasks, RDS t3.medium + read replica, ML inference |

São Paulo region pricing runs ~20–30% above US East, offset by Activate credits for 6–18 months.

### CI/CD and observability

**GitHub Actions** (free for public repos, 2,000 min/month private) handles the pipeline: lint/test → security scan (Trivy, npm audit) → Docker build → push to ECR → Terraform plan → deploy staging → manual approval → blue/green production deploy via ECS. **Terraform** manages infrastructure as code with remote state in S3 + DynamoDB locking.

The monitoring stack costs **$0/month**: Grafana Cloud forever-free tier (10K metrics, 50GB logs), Sentry Developer plan (free error tracking + performance), UptimeRobot (50 monitors free), and Healthchecks.io (20 cron monitors free). Custom Prometheus metrics track `factcheck_request_total`, `factcheck_response_time_seconds`, `factcheck_cache_hit_ratio`, and `user_engagement_score`.

---

## 9. API integrations for fact-checking and trend monitoring

### Fact-checking APIs (all free or low-cost)

The **Google Fact Check Tools API** is free with no per-query charge, returning ClaimReview data from IFCN-certified fact-checkers filtered by language (`languageCode=pt`). **ClaimBuster** (free API key from UT Arlington) scores text 0–1 for check-worthiness with 74% recall and 79% precision, though it's English-focused and needs adaptation for Portuguese. Brazilian fact-checkers **Agência Lupa**, **Aos Fatos**, **Comprova** (24+ media outlets), and **Fato ou Fake** (Globo) all use IFCN-standard ClaimReview markup that can be scraped and aggregated into a local database.

The **GDELT Project** provides entirely free APIs monitoring 65 machine-translated languages with excellent Brazilian coverage — the DOC 2.0 API offers full-text search across a rolling 3-month window with tone analysis and timeline visualization. For domain verification, **WhoisXML API** offers 500 free WHOIS lookups/month on signup, with Domain Reputation scoring, WHOIS History, and SSL Certificate analysis. Fake news domain patterns to flag: domains under 6 months old with high social sharing, free TLDs (.tk, .ml, .cf), missing SSL, and frequent DNS changes.

### Social media monitoring for the Trend Radar

Twitter/X API pricing has become prohibitive: the Basic tier costs $200/month for just 10,000 tweets. Third-party providers like TwitterAPI.io offer ~96% cheaper access. **Reddit API** provides free access with 100 requests/minute for monitoring r/brasil and r/brasilivre. **YouTube Data API v3** offers 10,000 free units/day. For Google Trends, **pytrends** (Python) scrapes the interface freely but may break with UI changes — GDELT provides a more reliable alternative for trend analysis.

### Additional integrations

For OCR on forwarded images, **Tesseract.js** runs free in browser/Node.js supporting 100+ languages, with Google Cloud Vision's free tier (1,000/month) as fallback for complex layouts. Voice message transcription uses **OpenAI Whisper API** at $0.006/minute with excellent Portuguese support, or GPT-4o Mini Transcribe at half that cost. URL shortener resolution requires no API — a simple HTTP HEAD request following redirects resolves shortened URLs before domain reputation checks.

---

## 10. Architecture decision matrix and implementation roadmap

### Complete technology stack summary

| Layer | Technology | Version | Cost | Complexity |
|-------|-----------|---------|------|------------|
| **Chatbot runtime** | Python + FastAPI | 3.11+ / 0.115+ | Free | Medium |
| **WhatsApp** | Cloud API | Latest | Free (service msgs) | Medium |
| **Telegram** | python-telegram-bot | 22.5 | Free | Low |
| **State machine** | transitions library | 0.9.x | Free | Low |
| **Web frontend** | Next.js + shadcn/ui | 15 / Latest | Free | Medium |
| **Backend DB** | PostgreSQL (Supabase) | 16+ | Free tier | Low |
| **Cache/Queue** | Redis + BullMQ | 7+ / 5+ | ~$12–15/mo | Low |
| **NLP encoder** | BERTimbau | base | Free | Medium |
| **Generative LLM** | Tucano-Instruct | 2b4 | Free (self-hosted) | High |
| **Sentiment** | pysentimiento | 0.7+ | Free | Low |
| **Deepfake detection** | DeepfakeBench/DeepSafe | Latest | Free + GPU costs | High |
| **Reverse image** | imagehash + CLIP + FAISS | Latest | Free | Medium |
| **Bias detection** | Fairlearn + AIF360 | Latest | Free | Medium |
| **Fact-check API** | Google Fact Check Tools | v1alpha1 | Free | Low |
| **News monitoring** | GDELT Project | v2 | Free | Low |
| **Cloud** | AWS (sa-east-1) | — | $0–50/mo MVP | Medium |
| **CI/CD** | GitHub Actions + Terraform | Latest | Free | Medium |
| **Monitoring** | Grafana Cloud + Sentry | Free tiers | Free | Low |

### Implementation phases

**Phase 1 (Months 1–3)**: Build the chatbot with guided questioning flows on WhatsApp and Telegram using the FSM pattern. Implement basic fact-check lookup against Google Fact Check Tools API and GDELT. Deploy on AWS free tier. **Estimated cost: $0–20/month.**

**Phase 2 (Months 4–6)**: Launch the web platform (Next.js PWA) with the Balance of Evidence visualization, basic educational modules with quizzes, and source credibility display. Fine-tune BERTimbau on Fake.BR corpus. **Estimated cost: $50–100/month.**

**Phase 3 (Months 7–12)**: Integrate deepfake detection (DeepSafe on RunPod serverless), add the Trend Radar using GDELT + YouTube + Reddit APIs, implement gamification and spaced repetition for media literacy, and deploy algorithmic bias analysis tools. **Estimated cost: $150–300/month.**

**Phase 4 (Year 2)**: Scale ML models, build the local fact-check database aggregating Brazilian sources, implement advanced content spread visualization with NetworkX/Sigma.js, and optimize for 10K+ users with read replicas and auto-scaling. **Estimated cost: $700–1,200/month** — offset by cloud credits and grants.

## Conclusion

The most consequential architectural decision is **prioritizing WhatsApp's free service conversation model** as the primary channel — this makes the platform economically sustainable at any scale for a population that overwhelmingly communicates through WhatsApp. The second critical choice is **PostgreSQL as a unified data store** using JSONB for semi-structured ML outputs, avoiding the operational complexity of a polyglot persistence layer at early stage. The third is the **PWA approach over native apps**, which eliminates app store dependencies while serving users on budget Android devices with spotty connectivity.

The open-source NLP ecosystem for Brazilian Portuguese matured significantly in 2024–2025, with BERTimbau, Albertina, and Tucano providing a complete pipeline from text classification through generative claim decomposition — all at zero licensing cost. The genuine technical challenges lie in cross-dataset generalization for deepfake detection, Portuguese-language claim verification (where training data remains scarce), and protecting minority users from the adversarial threats that make their data uniquely sensitive under LGPD's classification of racial/ethnic origin as sensitive data. Building for these constraints from day one — differential privacy, data minimization, identity-activity separation — is not optional but foundational.