#!/usr/bin/env python3
"""Live test: 3 new claims + new endpoints (balance, feedback, learning)."""

import json
import time
import requests

BASE = "http://localhost:8000"

def analyze(label, text):
    print("=" * 70)
    print(f"CLAIM: {label}")
    print("=" * 70)
    t0 = time.time()
    r = requests.post(f"{BASE}/analyze", json={"text": text, "platform": "web"}, timeout=120)
    elapsed = time.time() - t0
    if r.status_code != 200:
        print(f"  ERROR {r.status_code}: {r.text}")
        return None
    content_id = r.json()["content_id"]
    print(f"  Analyze POST: {r.status_code} | Time: {elapsed:.1f}s | content_id: {content_id}")

    # Now fetch the full result
    r2 = requests.get(f"{BASE}/analysis/{content_id}", timeout=10)
    if r2.status_code != 200:
        print(f"  Fetch ERROR {r2.status_code}: {r2.text}")
        return content_id
    d = r2.json()

    rs = d.get("risk_score", {})
    nlp = d.get("nlp", {})
    fc_pt = d.get("fact_check", {}).get("pt", {}).get("results", [])
    fc_en = d.get("fact_check", {}).get("en", {}).get("results", [])
    gn = d.get("google_news", {})
    gn_pt = gn.get("pt", {}).get("articles", []) if gn else []
    gn_en = gn.get("en", {}).get("articles", []) if gn else []
    wiki_pt = (d.get("wikipedia", {}).get("pt") or {}).get("results", [])
    wiki_en = (d.get("wikipedia", {}).get("en") or {}).get("results", [])
    br_fc = (d.get("brazilian_fc") or {}).get("results", [])

    print(f"  Risk: {rs.get('overall','?')} ({(rs.get('level','?')).upper()}) | Confidence: {rs.get('confidence','?')}")
    print(f"  Verdict: {rs.get('verdict_pt','?')}")
    urg = nlp.get('urgency', {})
    man = nlp.get('manipulation', {})
    clm = nlp.get('claim', {})
    print(f"  NLP: urgency={urg.get('score','?')}, manipulation={man.get('score','?')}, claim={clm.get('score','?')}")
    print(f"  Language: {nlp.get('language', '?')} | Words: {nlp.get('word_count', '?')}")
    print(f"  Sources: FC={len(fc_pt)}pt+{len(fc_en)}en, GoogleNews={len(gn_pt)}pt+{len(gn_en)}en, Wiki={len(wiki_pt)}pt+{len(wiki_en)}en, BrFC={len(br_fc)}")
    print()
    return content_id


def test_balance(content_id, label):
    print(f"--- Balance of Evidence for '{label}' ---")
    r = requests.get(f"{BASE}/balance/{content_id}", timeout=30)
    if r.status_code != 200:
        print(f"  ERROR {r.status_code}: {r.text}")
        return
    b = r.json()
    print(f"  Balance score: {b['balance_score']}")
    print(f"  Total sources: {b['total_sources']}")
    print(f"  Supporting: {len(b['supporting'])} | Contradicting: {len(b['contradicting'])} | Neutral: {len(b['neutral'])}")
    print(f"  FC verdict: {b.get('fact_checker_verdict', 'N/A')}")
    print(f"  Risk level: {b.get('risk_level', 'N/A')} | Overall: {b.get('risk_overall', 'N/A')}")
    print()


def test_feedback():
    print("--- Feedback Submission ---")
    r = requests.post(f"{BASE}/feedback", json={
        "content_id": "test-live",
        "usefulness_rating": 5,
        "feeling_after": "empowered",
        "would_recommend": True,
    }, timeout=10)
    print(f"  POST /feedback → {r.status_code}: {r.json()}")

    r2 = requests.post(f"{BASE}/feedback", json={
        "usefulness_rating": 4,
        "feeling_after": "grateful",
        "would_recommend": True,
    }, timeout=10)
    print(f"  POST /feedback → {r2.status_code}: {r2.json()}")

    r3 = requests.post(f"{BASE}/feedback", json={
        "usefulness_rating": 3,
        "feeling_after": "confused",
        "would_recommend": False,
    }, timeout=10)
    print(f"  POST /feedback → {r3.status_code}: {r3.json()}")

    # Summary
    rs = requests.get(f"{BASE}/feedback/summary", timeout=10)
    s = rs.json()
    print(f"\n  GET /feedback/summary:")
    print(f"    Total: {s['total']} | Avg rating: {s['avg_rating']}")
    print(f"    Would recommend: {s['would_recommend_pct']}%")
    print(f"    Feelings: {s['feeling_distribution']}")
    print()


def test_learning():
    print("--- Learning Modules ---")
    r = requests.get(f"{BASE}/learning/modules", timeout=10)
    modules = r.json().get("modules", [])
    print(f"  GET /learning/modules → {len(modules)} modules found")
    for m in modules:
        print(f"    [{m['difficulty']}] {m['title']} ({m['estimated_minutes']}min) — topic: {m['topic']}")

    if modules:
        slug = modules[0]["slug"] if modules else None
        if slug:
            print(f"\n  GET /learning/modules/{slug}:")
            r2 = requests.get(f"{BASE}/learning/modules/{slug}", timeout=10)
            mod = r2.json()
            sections = mod.get("content", [])
            print(f"    Title: {mod['title']}")
            print(f"    Sections: {len(sections)}")
            for s in sections:
                print(f"      - [{s.get('type', '?')}] {s.get('title', 'N/A')}")

    # Test progress update
    print(f"\n  POST /learning/progress (in_progress):")
    rp = requests.post(f"{BASE}/learning/progress", json={
        "user_id": "test-user-live",
        "module_slug": modules[0]["slug"] if modules else "vies-de-confirmacao",
        "status": "in_progress",
    }, timeout=10)
    print(f"    → {rp.status_code}: {rp.json()}")

    print(f"  POST /learning/progress (completed):")
    rp2 = requests.post(f"{BASE}/learning/progress", json={
        "user_id": "test-user-live",
        "module_slug": modules[0]["slug"] if modules else "vies-de-confirmacao",
        "status": "completed",
        "score": 0.8,
        "quiz_answers": {"q1": 0, "q2": 1},
    }, timeout=10)
    print(f"    → {rp2.status_code}: {rp2.json()}")
    print()


def test_analytics():
    print("--- Analytics Summary (merged Redis + DB + Feedback) ---")
    r = requests.get(f"{BASE}/analytics/summary?days=30", timeout=10)
    s = r.json()
    print(f"  Total analyses: {s.get('total', 0)}")
    print(f"  By risk level: {s.get('by_risk_level', {})}")
    print(f"  By platform: {s.get('by_platform', {})}")
    print(f"  FC coverage: {s.get('fact_check_coverage', 0)}")

    persistent = s.get("persistent")
    if persistent:
        print(f"  [DB] Persistent analyses: {persistent.get('total_analyses', 0)}")
        print(f"  [DB] By risk: {persistent.get('by_risk_level', {})}")
        print(f"  [DB] Avg confidence: {persistent.get('avg_confidence', 0)}")
        print(f"  [DB] Total evidence items: {persistent.get('total_evidence_items', 0)}")

    feedback = s.get("feedback")
    if feedback:
        print(f"  [FB] Total feedback: {feedback.get('total', 0)}")
        print(f"  [FB] Avg rating: {feedback.get('avg_rating', 0)}")
        print(f"  [FB] Would recommend: {feedback.get('would_recommend_pct', 0)}%")
    print()


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("  MENTOR DIGITAL — LIVE TEST SESSION")
    print("=" * 70 + "\n")

    # ── 3 New Claims ──

    cid1 = analyze(
        "5G causa câncer (hoax viral WhatsApp)",
        "URGENTE!!! Cientistas confirmaram que as torres de 5G causam câncer "
        "no cérebro! O governo está escondendo isso de todos nós!!! "
        "Compartilhe antes que apaguem!!!"
    )

    cid2 = analyze(
        "Vacina da dengue mata crianças (desinformação saúde)",
        "A vacina contra a dengue está matando crianças no Brasil! Já são "
        "mais de 500 mortes que a mídia não noticia! Os laboratórios estão "
        "lucrando bilhões com a vida dos nossos filhos! NÃO VACINE SEU FILHO!"
    )

    cid3 = analyze(
        "Terra plana comprovada (conspiração)",
        "Finalmente provaram que a terra é plana! A NASA admitiu que todas "
        "as fotos do espaço são montagens feitas em computador. Assista o "
        "documentário completo e descubra a verdade que eles escondem de você."
    )

    # ── Test Balance of Evidence ──
    print("\n" + "=" * 70)
    print("  TESTING NEW ENDPOINTS")
    print("=" * 70 + "\n")

    test_balance(cid1, "5G")
    test_balance(cid2, "Vacina dengue")
    test_balance(cid3, "Terra plana")

    # ── Test Feedback ──
    test_feedback()

    # ── Test Learning ──
    test_learning()

    # ── Test Analytics ──
    test_analytics()

    print("=" * 70)
    print("  ALL LIVE TESTS COMPLETED")
    print("=" * 70)
