#!/usr/bin/env python3
"""Quick script to display analysis results from the API."""
import json, sys, urllib.request

if len(sys.argv) < 2:
    print("Usage: python3 show_analysis.py <content_id>")
    sys.exit(1)

content_id = sys.argv[1]
url = f"http://localhost:8000/analysis/{content_id}"

try:
    with urllib.request.urlopen(url, timeout=10) as resp:
        d = json.loads(resp.read())
except Exception as e:
    print(f"Error fetching: {e}")
    sys.exit(1)

print("=" * 60)
r = d.get("risk_score", {})
print(f"RISK SCORE: {r.get('overall', '?')} ({r.get('level', '?')})")
print("=" * 60)

print("\n--- NEWS ARTICLES (PT / Brazilian) ---")
por = d.get("gdelt", {}).get("por", {})
arts = por.get("articles", [])
if arts:
    for a in arts[:8]:
        print(f"  [{a.get('domain','')}] {a.get('title','')[:80]}")
        print(f"    -> {a.get('url','')[:100]}")
else:
    print(f"  (none) error={por.get('error','')}")

print("\n--- NEWS ARTICLES (EN / International) ---")
en = d.get("gdelt", {}).get("en", {})
arts_en = en.get("articles", [])
if arts_en:
    for a in arts_en[:5]:
        print(f"  [{a.get('domain','')}] {a.get('title','')[:80]}")
        print(f"    -> {a.get('url','')[:100]}")
else:
    print(f"  (none) error={en.get('error','')}")

print("\n--- FACT CHECKS ---")
any_fc = False
for lang in ["pt", "en"]:
    fc = d.get("fact_check", {}).get(lang, {})
    for c in fc.get("results", [])[:4]:
        any_fc = True
        print(f"  [{lang}] {c.get('text','')[:65]}")
        print(f"    Rating: {c.get('rating','?')} | {c.get('publisher','')}")
        print(f"    -> {c.get('url','')[:100]}")
if not any_fc:
    print("  (none)")

print("\n--- BRAZILIAN FACT-CHECKERS (Aos Fatos / Lupa) ---")
bfc = d.get("brazilian_fc", {})
bfc_results = bfc.get("results", [])
if bfc_results:
    for r3 in bfc_results[:4]:
        print(f"  [{r3.get('source','')}] {r3.get('title','')[:70]}")
        print(f"    -> {r3.get('link','')[:100]}")
else:
    print("  (none)")

print("\n--- WIKIPEDIA ---")
any_wiki = False
for lang in ["pt", "en"]:
    w = d.get("wikipedia", {}).get(lang, {})
    for r2 in w.get("results", [])[:2]:
        any_wiki = True
        print(f"  [{lang}] {r2.get('title','')}")
        print(f"    -> {r2.get('url','')[:100]}")
if not any_wiki:
    print("  (none)")

print("\n--- NLP ---")
nlp = d.get("nlp", {})
print(f"  Language: {nlp.get('language','?')}")
print(f"  Word count: {nlp.get('word_count','?')}")
print(f"  Urgency: {nlp.get('urgency','?')}")
print(f"  Claim: {nlp.get('claim','?')}")
print(f"  Manipulation: {nlp.get('manipulation','?')}")

print("\n" + "=" * 60)
total_news = len(por.get("articles",[])) + len(en.get("articles",[]))
total_fc = sum(len(d.get("fact_check",{}).get(l,{}).get("results",[])) for l in ["pt","en"])
total_bfc = len(bfc_results)
print(f"TOTALS: {total_news} news | {total_fc} fact-checks | {total_bfc} brazilian FC")
print("=" * 60)
