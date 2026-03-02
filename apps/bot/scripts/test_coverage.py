"""Test 5 diverse fake news texts and extract key metrics."""
import httpx
import time

BASE = "http://localhost:8000"

TEXTS = [
    # 1. QAnon-style conspiracy PT
    ("Conspiração QAnon (PT)",
     "BOMBA! Descobriram documentos secretos que provam que a elite globalista "
     "controla todos os governos do mundo através de uma agenda oculta. O deep state "
     "não quer que você saiba a verdade. A nova ordem mundial já começou e eles estão "
     "usando a mídia para lavar o cérebro da população. Compartilhem antes que censurem!"),

    # 2. Health misinformation EN
    ("Health misinfo (EN)",
     "EXPOSED: Big pharma has been hiding the cure for cancer for decades! "
     "A doctor friend told me that chemotherapy is poison and lemon water with "
     "baking soda cures cancer naturally. The FDA banned the real treatment because "
     "they make billions from sick people. Do your own research and wake up!"),

    # 3. Election fraud PT
    ("Fraude eleitoral (PT)",
     "As urnas eletrônicas foram fraudadas! Aprovaram de madrugada uma lei secreta "
     "para manipular os votos. Os dados foram manipulados e ninguém fala sobre isso. "
     "O governo esconde a verdade sobre a compra de votos. É tudo uma farsa para "
     "manter a ditadura. Abram os olhos, brasileiros!"),

    # 4. Anti-5G + vaccine conspiracy EN
    ("5G + Vaccine conspiracy (EN)",
     "URGENT WARNING! 5G towers are being used to control the population through "
     "the vaccine microchips! Scientists lie about the safety data which was fabricated. "
     "NASA admitted the truth but mainstream media won't tell you. Children are dying "
     "from the rushed vaccine. They don't want you to know! Share before they delete this!"),

    # 5. Legitimate scientific news PT (should score LOW)
    ("Notícia legítima (PT)",
     "Pesquisadores da Universidade Federal de Minas Gerais publicaram nesta quarta-feira "
     "os resultados de um estudo clínico com 2.400 participantes sobre o uso de um novo "
     "medicamento antiviral. Segundo os autores, o tratamento reduziu em aproximadamente "
     "35% a gravidade dos sintomas em pacientes hospitalizados, embora mais ensaios "
     "clínicos sejam necessários para confirmar a eficácia em diferentes populações. "
     "O artigo foi publicado na revista The Lancet e revisado por pares independentes."),
]

client = httpx.Client(timeout=30)

for i, (label, text) in enumerate(TEXTS, 1):
    print(f"\n{'='*70}")
    print(f"TEST {i}: {label}")
    print(f"{'='*70}")

    # Submit
    r = client.post(f"{BASE}/analyze", json={"text": text})
    if r.status_code != 200:
        print(f"  ERROR: HTTP {r.status_code} -- {r.text}")
        continue
    cid = r.json()["content_id"]
    print(f"  content_id: {cid}")

    # Wait for processing
    time.sleep(8)

    # Fetch result
    r2 = client.get(f"{BASE}/analysis/{cid}")
    if r2.status_code != 200:
        print(f"  ERROR fetching: HTTP {r2.status_code}")
        continue

    d = r2.json()
    risk = d.get("risk_score", {})
    nlp = d.get("nlp", {})
    fc = d.get("fact_check", {})
    gdelt = d.get("gdelt", {})
    wiki = d.get("wikipedia", {})
    bfc = d.get("brazilian_fc", {})

    # Risk score
    print(f"\n  RISK: {risk.get('overall', '?')} ({risk.get('level', '?').upper()}) -- {risk.get('level_label', '')}")
    dims = risk.get("dimensions", {})
    print(f"    linguistic:    {dims.get('linguistic', '?')}")
    print(f"    factcheck:     {dims.get('factcheck', '?')}")
    print(f"    coverage:      {dims.get('coverage', '?')}")
    print(f"    claim_penalty: {dims.get('claim_penalty', '?')}")
    print(f"    confidence:    {risk.get('confidence', '?')}")
    print(f"    verdict:       {risk.get('verdict', '?')} -- {risk.get('verdict_pt', '')}")

    # NLP signals
    urg = nlp.get("urgency", {})
    man = nlp.get("manipulation", {})
    clm = nlp.get("claim_score", nlp.get("claim", {}))
    print(f"\n  NLP:")
    print(f"    urgency:       {urg.get('score', '?')} -- {', '.join(urg.get('evidence', [])[:4])}")
    print(f"    manipulation:  {man.get('score', '?')} -- {', '.join(man.get('evidence', [])[:6])}")
    print(f"    claims:        {clm.get('score', '?')}")
    print(f"    caps_ratio:    {nlp.get('caps_ratio', '?')}")

    # API status
    print(f"\n  APIs:")
    # Fact Check
    fc_pt = fc.get("pt", {})
    fc_en = fc.get("en", {})
    fc_pt_n = len(fc_pt.get("results", []))
    fc_en_n = len(fc_en.get("results", []))
    fc_pt_err = fc_pt.get("error", "")
    fc_en_err = fc_en.get("error", "")
    print(f"    FactCheck PT:  {fc_pt_n} results {f'(error: {fc_pt_err})' if fc_pt_err else ''}")
    print(f"    FactCheck EN:  {fc_en_n} results {f'(error: {fc_en_err})' if fc_en_err else ''}")

    # GDELT
    for lang_key in ["por", "en"]:
        g = gdelt.get(lang_key, {})
        g_n = len(g.get("articles", []))
        g_err = g.get("error", "")
        print(f"    GDELT {lang_key:>3}:     {g_n} articles {f'(error: {g_err})' if g_err else ''}")

    # Wikipedia
    for lang_key in ["pt", "en"]:
        w = wiki.get(lang_key, {})
        w_n = len(w.get("results", []))
        w_err = w.get("error", "")
        print(f"    Wiki {lang_key}:       {w_n} results {f'(error: {w_err})' if w_err else ''}")

    # Brazilian FC
    bfc_n = len(bfc.get("results", []))
    bfc_err = bfc.get("error", "")
    print(f"    BrazilianFC:   {bfc_n} results {f'(error: {bfc_err})' if bfc_err else ''}")

print(f"\n{'='*70}")
print("DONE -- 5 tests complete")
print(f"{'='*70}")
