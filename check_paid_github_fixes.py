#!/usr/bin/env python3
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

OUT = Path("artifacts/paid_fix_scout")
OUT.mkdir(parents=True, exist_ok=True)

REPORT = OUT / "paid_fix_scout_report.md"
RAW = OUT / "paid_fix_scout_raw.json"
TS = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

MAX_PER_QUERY = 30

QUERIES = [
    # Lean / formal verification direct
    'Lean bounty is:issue is:open',
    '"Lean 4" bounty is:issue is:open',
    '"Lean" "paid" is:issue is:open',
    '"Lean" "reward" is:issue is:open',
    '"Lean" "Algora" is:issue is:open',
    '"sorry" "Lean" is:issue is:open',
    '"formal verification" bounty is:issue is:open',
    '"theorem proving" bounty is:issue is:open',
    '"proof assistant" bounty is:issue is:open',
    '"Coq" bounty is:issue is:open',
    '"Isabelle" bounty is:issue is:open',
    '"Agda" bounty is:issue is:open',

    # Generic paid issue platforms / labels
    'label:bounty is:issue is:open',
    'label:paid is:issue is:open',
    'label:"💰 bounty" is:issue is:open',
    'label:"bounty" is:issue is:open',
    'label:"good first issue" bounty is:issue is:open',
    '"algora" is:issue is:open',
    '"OnlyDust" is:issue is:open',
    '"Gitcoin" bounty is:issue is:open',
    '"Dework" bounty is:issue is:open',

    # External checker / CI style
    '"bounty" "test suite" is:issue is:open',
    '"bounty" "CI" is:issue is:open',
    '"bounty" "failing tests" is:issue is:open',
    '"paid" "failing tests" is:issue is:open',
    '"reward" "failing tests" is:issue is:open',
    '"bounty" "reproducible" is:issue is:open',
    '"paid" "reproducible" is:issue is:open',

    # Rust / type systems / compilers can be good external-judge terrain
    '"bounty" "type checker" is:issue is:open',
    '"bounty" "compiler" is:issue is:open',
    '"paid" "compiler" is:issue is:open',
    '"bounty" "SMT" is:issue is:open',
    '"bounty" "Z3" is:issue is:open',
]

MONEY_RE = re.compile(
    r'(?i)(?:\$|USD\s*|US\$|€|£)\s?([0-9][0-9,]*(?:\.\d+)?)|([0-9][0-9,]*)\s?(?:USD|dollars|eur|euro|gbp)'
)

GOOD_TERMS = [
    "lean", "lean4", "theorem", "proof", "formal", "verification", "verified",
    "coq", "isabelle", "agda", "smt", "z3", "solver",
    "test", "tests", "ci", "repro", "reproducible", "failing", "spec",
    "type", "compiler", "checker", "benchmark",
    "bounty", "paid", "reward", "algora", "gitcoin", "onlydust",
]

BAD_TERMS = [
    "frontend", "css", "ui", "ux", "design", "translation", "docs only",
    "marketing", "website copy", "logo", "figma",
]

MG_TERMS = [
    "lean", "theorem", "proof", "formal", "verification", "spec",
    "checker", "ci", "failing test", "test suite", "smt", "solver",
    "type checker", "compiler", "benchmark", "reproducible",
]

SECURITY_TERMS = [
    "security", "vulnerability", "xss", "rce", "csrf", "ssrf", "sql injection",
    "bug bounty", "hackerone", "bugcrowd", "cve",
]

def run(cmd, timeout=60):
    try:
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=timeout)
        return p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired:
        return 124, "", "TIMEOUT"

def gh_available():
    rc, out, err = run(["gh", "auth", "status"], timeout=20)
    return rc == 0

def gh_search(query):
    # GitHub Search API caps per_page at 100; keep narrow.
    q = quote(query)
    path = f"/search/issues?q={q}&per_page={MAX_PER_QUERY}&sort=updated&order=desc"
    rc, out, err = run(["gh", "api", path], timeout=60)
    if rc != 0:
        return {"query": query, "error": err.strip(), "items": []}
    try:
        data = json.loads(out)
    except Exception as e:
        return {"query": query, "error": f"json parse error: {e}", "items": []}
    return {"query": query, "error": None, "items": data.get("items", [])}

def text_of(item):
    parts = [
        item.get("title") or "",
        item.get("body") or "",
        " ".join(label.get("name", "") for label in item.get("labels", []) or []),
        item.get("html_url") or "",
    ]
    return "\n".join(parts)

def extract_money(text):
    vals = []
    for m in MONEY_RE.finditer(text):
        raw = m.group(1) or m.group(2)
        if raw:
            try:
                vals.append(float(raw.replace(",", "")))
            except Exception:
                pass
    return max(vals) if vals else None

def repo_from_url(url):
    m = re.search(r"github\.com/([^/]+/[^/]+)/issues/", url)
    return m.group(1) if m else ""

def score_item(item):
    text = text_of(item)
    low = text.lower()
    labels = [l.get("name", "") for l in item.get("labels", []) or []]
    money = extract_money(text)

    score = 0
    reasons = []

    if money:
        if money >= 1000:
            score += 35
            reasons.append(f"payout≈{money:g}")
        elif money >= 250:
            score += 20
            reasons.append(f"payout≈{money:g}")
        else:
            score += 10
            reasons.append(f"payout≈{money:g}")

    if any(t in low for t in ["bounty", "paid", "reward", "algora", "gitcoin", "onlydust"]):
        score += 20
        reasons.append("explicit paid/bounty signal")

    mg_hits = [t for t in MG_TERMS if t in low]
    if mg_hits:
        score += min(30, 5 * len(mg_hits))
        reasons.append("MG-fit: " + ", ".join(mg_hits[:6]))

    if any(t in low for t in ["failing test", "test suite", "ci", "reproducible", "benchmark"]):
        score += 20
        reasons.append("external judge/test signal")

    if any(t in low for t in SECURITY_TERMS):
        score -= 15
        reasons.append("security lane; higher reputation risk")

    if any(t in low for t in BAD_TERMS):
        score -= 20
        reasons.append("low MG-fit/product/UI/docs signal")

    comments = item.get("comments", 0) or 0
    if comments > 20:
        score -= 5
        reasons.append("crowded issue")
    elif comments <= 3:
        score += 5
        reasons.append("low competition")

    state_reason = item.get("state_reason")
    if state_reason:
        score -= 10
        reasons.append(f"state_reason={state_reason}")

    return score, reasons, money

def classify(item, score, reasons):
    text = text_of(item).lower()
    if score >= 65:
        return "GOLD"
    if score >= 45:
        return "PROMISING"
    if score >= 25:
        return "MAYBE"
    return "LOW"

def main():
    if not gh_available():
        print("ERROR: gh CLI is not authenticated. Run: gh auth login", file=sys.stderr)
        sys.exit(1)

    all_results = []
    seen = set()

    for idx, q in enumerate(QUERIES, 1):
        print(f"[{idx}/{len(QUERIES)}] {q}")
        res = gh_search(q)
        if res.get("error"):
            print("  error:", res["error"][:200])
        for item in res.get("items", []):
            url = item.get("html_url")
            if not url or url in seen:
                continue
            seen.add(url)
            score, reasons, money = score_item(item)
            all_results.append({
                "query": q,
                "score": score,
                "class": classify(item, score, reasons),
                "money": money,
                "reasons": reasons,
                "title": item.get("title"),
                "url": url,
                "repo": repo_from_url(url),
                "updated_at": item.get("updated_at"),
                "created_at": item.get("created_at"),
                "comments": item.get("comments"),
                "labels": [l.get("name") for l in item.get("labels", []) or []],
                "body_snippet": (item.get("body") or "")[:800],
            })
        time.sleep(0.3)

    all_results.sort(key=lambda x: (x["score"], x.get("money") or 0), reverse=True)

    RAW.write_text(json.dumps(all_results, indent=2), encoding="utf-8")

    gold = [r for r in all_results if r["class"] == "GOLD"]
    promising = [r for r in all_results if r["class"] == "PROMISING"]
    maybe = [r for r in all_results if r["class"] == "MAYBE"]

    lines = []
    lines.append("# Paid GitHub Fix Scout")
    lines.append("")
    lines.append(f"Generated: {TS}")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Unique issues found: {len(all_results)}")
    lines.append(f"- GOLD: {len(gold)}")
    lines.append(f"- PROMISING: {len(promising)}")
    lines.append(f"- MAYBE: {len(maybe)}")
    lines.append("")
    lines.append("## Best Targets")
    lines.append("")

    for r in all_results[:40]:
        lines.append(f"### {r['class']} · score {r['score']} · {r['title']}")
        lines.append("")
        lines.append(f"- Repo: `{r['repo']}`")
        lines.append(f"- URL: {r['url']}")
        lines.append(f"- Updated: {r['updated_at']}")
        lines.append(f"- Comments: {r['comments']}")
        if r["money"]:
            lines.append(f"- Detected payout: `{r['money']:g}`")
        lines.append(f"- Labels: `{', '.join([x for x in r['labels'] if x])}`")
        lines.append(f"- Matched query: `{r['query']}`")
        lines.append("- Reasons:")
        for reason in r["reasons"][:8]:
            lines.append(f"  - {reason}")
        snippet = (r["body_snippet"] or "").strip().replace("\r", "")
        if snippet:
            snippet = "\n".join(snippet.splitlines()[:8])
            lines.append("")
            lines.append("Snippet:")
            lines.append("")
            lines.append("```text")
            lines.append(snippet[:1000])
            lines.append("```")
        lines.append("")

    lines.append("## MathGraph Triage Rule")
    lines.append("")
    lines.append("Prioritize issues with:")
    lines.append("")
    lines.append("- payout or explicit bounty")
    lines.append("- local test/checker/CI reproduction")
    lines.append("- small patch surface")
    lines.append("- no security disclosure risk")
    lines.append("- proof/spec/type/checker/failing-test flavor")
    lines.append("")
    lines.append("Avoid:")
    lines.append("")
    lines.append("- vague security reports")
    lines.append("- UI/design/docs-only work")
    lines.append("- issues with no local judge")
    lines.append("- crowded issues with many active solvers")
    lines.append("")

    REPORT.write_text("\n".join(lines), encoding="utf-8")

    print()
    print(f"Wrote: {REPORT}")
    print(f"Wrote: {RAW}")
    print()
    print("Top 10:")
    for r in all_results[:10]:
        money = f" payout≈{r['money']:g}" if r["money"] else ""
        print(f"- [{r['class']}] score={r['score']}{money} {r['repo']} :: {r['title']}")
        print(f"  {r['url']}")

if __name__ == "__main__":
    main()
