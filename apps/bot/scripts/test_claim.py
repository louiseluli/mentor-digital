#!/usr/bin/env python3
"""Submit text for analysis and display results."""
import json, sys, time, urllib.request

if len(sys.argv) < 2:
    print("Usage: python3 test_claim.py 'your claim text here'")
    sys.exit(1)

text = " ".join(sys.argv[1:])
print(f"\n>>> Submitting: {text[:80]}...")

# Submit
data = json.dumps({"text": text}).encode()
req = urllib.request.Request(
    "http://localhost:8000/analyze",
    data=data,
    headers={"Content-Type": "application/json"},
)
with urllib.request.urlopen(req, timeout=15) as resp:
    result = json.loads(resp.read())
cid = result["content_id"]
print(f">>> content_id: {cid}")
print(f">>> Web URL: http://localhost:3001/analise/{cid}")
print(">>> Waiting 12s for analysis...")
time.sleep(12)

# Fetch
url = f"http://localhost:8000/analysis/{cid}"
with urllib.request.urlopen(url, timeout=10) as resp:
    d = json.loads(resp.read())

print("=" * 60)
r = d.get("risk_score", {})
print(f"RISK: {r.get('overall', '?')} ({r.get('level', '?')})")
print("=" * 60)

print("\n--- NEWS (PT) ---")
por = d.get("gdelt", {}).get("por", {})
for a in por.get("articles", [])[:6]:
    print(f"  [{a.get('domain','')}] {a.get('title','')[:75]}")
if not por.get("articles"):
    print(f"  (none) {por.get('error','')}")

print("\n--- NEWS (EN) ---")
en = d.get("gdelt", {}).get("en", {})
for a in en.get("articles", [])[:5]:
    print(f"  [{a.get('domain','')}] {a.get('title','')[:75]}")
if not en.get("articles"):
    print(f"  (none) {en.get('error','')}")

print("\n--- FACT CHECKS ---")
any_fc = False
for lang in ["pt", "en"]:
    for c in d.get("fact_check", {}).get(lang, {}).get("results", [])[:3]:
        any_fc = True
        rating = c.get("rating", "?")
        print(f"  [{lang}] {c.get('text','')[:55]} | {rating}")
if not any_fc:
    print("  (none)")

print("\n--- BRAZILIAN FC ---")
bfc = d.get("brazilian_fc", {}).get("results", [])
for r3 in bfc[:3]:
    print(f"  [{r3.get('source','')}] {r3.get('title','')[:65]}")
if not bfc:
    print("  (none)")

print("\n--- WIKIPEDIA ---")
for lang in ["pt", "en"]:
    for r2 in d.get("wikipedia", {}).get(lang, {}).get("results", [])[:2]:
        print(f"  [{lang}] {r2.get('title','')}")

nlp = d.get("nlp", {})
print(f"\n--- NLP: lang={nlp.get('language','?')} words={nlp.get('word_count','?')} ---")

total = len(por.get("articles",[])) + len(en.get("articles",[]))
print(f"\n{'='*60}")
print(f"TOTALS: {total} news | fact-checks found | Web: http://localhost:3001/analise/{cid}")
print(f"{'='*60}\n")
