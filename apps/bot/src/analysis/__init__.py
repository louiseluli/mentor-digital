"""
analysis/ — Módulo de análise de conteúdo (Fase 3)

3.1  fact_checker.py     → Google Fact Check Tools API
3.2  domain_checker.py   → RDAP, VirusTotal, urlscan.io, Open PageRank  (próxima fase)
3.3  gdelt.py            → GDELT DOC API                                 (próxima fase)
3.4  nlp.py              → Hugging Face Inference API                    (próxima fase)

O orquestrador (analysis_service.py) chama todos em paralelo e agrega resultados.
Os resultados são armazenados em ConversationContext.analysis_results (persistido no Redis).
A exibição ao usuário é responsabilidade da plataforma web (Fase 5).
"""
