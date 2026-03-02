"""Quick test of the 3 claims to verify NLP detection quality."""
import sys
sys.path.insert(0, "/Users/louisesfer/Documents/Programming/fake_news_detector/apps/bot")

from src.analysis.nlp import analyze_text

claims = [
    ("Claim 1 - Anti-vax PT",
     "A Pfizer foi OBRIGADA a revelar documentos secretos que provam que a vacina causa doenças autoimunes em 78%% dos vacinados. Médicos renomados estão sendo silenciados pela mídia. COMPARTILHE antes que apaguem!! Eles não querem que você saiba a verdade. Proteja suas crianças AGORA!"),
    ("Claim 2 - Climate EN",
     "EXPOSED: NASA scientists caught manipulating temperature data to support the global warming hoax. Exposed internal documents reveal billions in funding depend on keeping the lie alive. The mainstream media REFUSES to cover this. Top researchers have been fired for speaking out. Share this before Big Tech censors it!"),
    ("Claim 3 - Financial scam PT",
     "Cientistas descobrem planta amazônica que cura diabetes em 15 dias! A indústria farmacêutica esconde essa informação porque perderia BILHÕES. Estudos comprovam 100%% de eficácia. Governo e Anvisa tentam proibir. Compre agora pelo link exclusivo antes que tirem do ar. Milhares já foram curados!"),
]

for name, text in claims:
    r = analyze_text(text)
    print(f"\n{'='*60}")
    print(f"{name}")
    print(f"  Urgency:      {r.urgency.score:.2f}")
    print(f"  Manipulation: {r.manipulation.score:.2f}")
    print(f"  Claim:        {r.claim.score:.2f}")
    print(f"  Signals:")
    for e in r.urgency.evidence:
        print(f"    [U] {e}")
    for e in r.manipulation.evidence:
        print(f"    [M] {e}")
    for e in r.claim.evidence:
        print(f"    [C] {e}")
