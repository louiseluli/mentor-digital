#!/usr/bin/env python3
"""Submit multiple claims in batch, wait, then display all results."""
import json, sys, time, urllib.request

CLAIMS = [
    # 1. COVID/Health - PT
    "Ivermectina cura COVID-19 e o governo está escondendo isso da população brasileira",

    # 2. Climate conspiracy - EN
    "Climate change is a hoax invented by China to destroy American manufacturing industry",

    # 3. Political - PT (Brazilian politics)
    "Lula assinou decreto secreto para confiscar terras rurais em todo o Brasil a partir de 2026",

    # 4. 5G/Tech conspiracy - EN
    "5G towers cause cancer and radiation sickness according to leaked WHO documents",

    # 5. Election fraud - PT
    "Urnas eletrônicas no Brasil foram hackeadas nas eleições de 2022 por hackers venezuelanos",

    # 6. NASA asteroid - EN (improved query test)
    "NASA confirmed asteroid heading towards Earth will cause mass extinction event in 2027",

    # 7. Food/Health - PT
    "Agrotóxicos no arroz brasileiro causam câncer em 80% dos consumidores segundo pesquisadores da USP",

    # 8. True but alarming news - PT (should get LOW risk)
    "Desmatamento na Amazônia aumentou nos últimos anos segundo dados do INPE",
]

print(f"Submitting {len(CLAIMS)} claims...\n")

results = []
for i, text in enumerate(CLAIMS, 1):
    data = json.dumps({"text": text}).encode()
    req = urllib.request.Request(
        "http://localhost:8000/analyze",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            r = json.loads(resp.read())
        cid = r["content_id"]
        print(f"  [{i}] {text[:60]}... -> {cid[:8]}")
        results.append((i, text, cid))
    except Exception as e:
        print(f"  [{i}] ERROR: {e}")
        results.append((i, text, None))
    time.sleep(2)  # stagger submissions to avoid overloading

print(f"\nWaiting 20s for all analyses to complete...")
time.sleep(20)

print("\n" + "=" * 70)

for idx, text, cid in results:
    if not cid:
        print(f"\n[{idx}] SKIPPED (submission error)")
        continue

    url = f"http://localhost:8000/analysis/{cid}"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            d = json.loads(resp.read())
    except Exception as e:
        print(f"\n[{idx}] FETCH ERROR: {e}")
        continue

    r = d.get("risk_score", {})
    por = d.get("gdelt", {}).get("por", {})
    en = d.get("gdelt", {}).get("en", {})
    total_news = len(por.get("articles", [])) + len(en.get("articles", []))
    total_fc = sum(
        len(d.get("fact_check", {}).get(l, {}).get("results", []))
        for l in ["pt", "en"]
    )
    bfc = len(d.get("brazilian_fc", {}).get("results", []))
    wiki = sum(
        len(d.get("wikipedia", {}).get(l, {}).get("results", []))
        for l in ["pt", "en"]
    )
    nlp = d.get("nlp", {})

    level = r.get("level", "?")
    score = r.get("overall", 0)
    level_emoji = {"critical": "🔴", "high": "🟠", "moderate": "🟡", "low": "🟢"}.get(level, "⚪")

    print(f"\n{'─' * 70}")
    print(f"[{idx}] {text[:65]}...")
    print(f"    {level_emoji} Risk: {score:.3f} ({level})")
    print(f"    📰 News: {total_news} | ✅ FC: {total_fc} | 🇧🇷 BrFC: {bfc} | 📚 Wiki: {wiki}")
    print(f"    🗣️ Lang: {nlp.get('language','?')} | Words: {nlp.get('word_count','?')}")
    print(f"    🌐 Web: http://localhost:3001/analise/{cid}")

    # Show top 3 news sources
    all_arts = por.get("articles", []) + en.get("articles", [])
    if all_arts:
        print(f"    Sources: {', '.join(a.get('domain','') for a in all_arts[:5])}")

    # Show fact-check verdicts
    for lang in ["pt", "en"]:
        for c in d.get("fact_check", {}).get(lang, {}).get("results", [])[:2]:
            print(f"    FC [{lang}]: {c.get('text','')[:50]} → {c.get('rating','?')}")

print(f"\n{'=' * 70}")
print("DONE — open the Web URLs above in your browser to see the full analysis pages")
print(f"{'=' * 70}\n")
