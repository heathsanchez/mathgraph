#!/usr/bin/env python3
import json
import re
from pathlib import Path
from datetime import datetime, timezone

RAW = Path("artifacts/paid_fix_scout/paid_fix_scout_raw.json")
OUT = Path("artifacts/paid_fix_scout")
REPORT = OUT / "paid_fix_scout_refined_report.md"
JSON_OUT = OUT / "paid_fix_scout_refined.json"

if not RAW.exists():
    raise SystemExit(f"Missing {RAW}")

rows = json.loads(RAW.read_text())

REAL_BOUNTY_PATTERNS = [
    r"(?i)\bbounty\b",
    r"(?i)\bpaid\b",
    r"(?i)\breward\b",
    r"(?i)\bpayment\b",
    r"(?i)\bpr bounty\b",
    r"(?i)\bbounty\s*\$",
    r"(?i)\[\s*bounty",
    r"(?i)algora",
    r"(?i)gitcoin",
    r"(?i)onlydust",
]

FALSE_POSITIVE_PATTERNS = [
    r"(?i)daily brief",
    r"(?i)proposal",
    r"(?i)\brfp-\d+",
    r"(?i)use cases",
    r"(?i)investment",
    r"(?i)hackathon prep",
    r"(?i)judge questions",
    r"(?i)portfolio",
    r"(?i)paper fills",
    r"(?i)alpaca_paper",
    r"(?i)security audit required before deployment",
    r"(?i)calculate the exact value of pi",
    r"(?i)whitepaper",
    r"(?i)marketing",
    r"(?i)grant proposal",
]

EXTERNAL_JUDGE_PATTERNS = [
    r"(?i)test",
    r"(?i)tests",
    r"(?i)test suite",
    r"(?i)ci",
    r"(?i)benchmark",
    r"(?i)reproduce",
    r"(?i)reproducible",
    r"(?i)failing",
    r"(?i)pass",
    r"(?i)acceptance",
    r"(?i)instructions",
    r"(?i)optimizer",
]

MG_FIT_PATTERNS = [
    r"(?i)\blean\b",
    r"(?i)lean 4",
    r"(?i)formal verification",
    r"(?i)theorem",
    r"(?i)proof",
    r"(?i)sorry",
    r"(?i)coq",
    r"(?i)isabelle",
    r"(?i)agda",
    r"(?i)smt",
    r"(?i)\bz3\b",
    r"(?i)solver",
    r"(?i)type checker",
    r"(?i)compiler",
    r"(?i)optimization",
    r"(?i)optimizer",
    r"(?i)spec",
    r"(?i)index",
    r"(?i)bound",
    r"(?i)constraint",
    r"(?i)search",
]

RISK_PATTERNS = [
    r"(?i)security",
    r"(?i)vulnerability",
    r"(?i)exploit",
    r"(?i)xss",
    r"(?i)rce",
    r"(?i)cve",
    r"(?i)audit",
    r"(?i)crypto",
    r"(?i)dex",
    r"(?i)wallet",
    r"(?i)smart contract",
]

def text(r):
    return "\n".join([
        r.get("title") or "",
        r.get("body_snippet") or "",
        " ".join(r.get("labels") or []),
        r.get("url") or "",
        r.get("repo") or "",
    ])

def has_any(patterns, s):
    return any(re.search(p, s) for p in patterns)

def hits(patterns, s):
    return [p for p in patterns if re.search(p, s)]

def money_score(r):
    m = r.get("money")
    if not m:
        return 0
    if m >= 5000:
        return 25
    if m >= 1000:
        return 20
    if m >= 250:
        return 12
    return 5

refined = []
for r in rows:
    s = text(r)
    false_pos = has_any(FALSE_POSITIVE_PATTERNS, s)
    real_bounty = has_any(REAL_BOUNTY_PATTERNS, s)
    external_judge = has_any(EXTERNAL_JUDGE_PATTERNS, s)
    mg_fit = hits(MG_FIT_PATTERNS, s)
    risk = hits(RISK_PATTERNS, s)

    score = 0
    reasons = []

    if false_pos:
        score -= 80
        reasons.append("likely false positive / not a concrete paid fix")

    if real_bounty:
        score += 35
        reasons.append("explicit bounty/paid/reward signal")

    if external_judge:
        score += 25
        reasons.append("external judge/test/benchmark signal")

    if mg_fit:
        score += min(35, 5 * len(mg_fit))
        reasons.append("MathGraph-fit terms present")

    score += money_score(r)
    if r.get("money"):
        reasons.append(f"detected money≈{r['money']:g}")

    comments = r.get("comments") or 0
    if comments >= 50:
        score -= 15
        reasons.append("crowded issue")
    elif comments <= 5:
        score += 8
        reasons.append("low competition")

    if risk:
        score -= 12
        reasons.append("security/crypto risk lane")

    title = r.get("title") or ""
    if "bounty" in title.lower():
        score += 15
        reasons.append("bounty appears in title")

    if not real_bounty and r.get("money"):
        score -= 25
        reasons.append("money detected but no explicit bounty language")

    if score >= 70:
        klass = "GOLD"
    elif score >= 45:
        klass = "PROMISING"
    elif score >= 25:
        klass = "MAYBE"
    else:
        klass = "LOW"

    rr = dict(r)
    rr["refined_score"] = score
    rr["refined_class"] = klass
    rr["refined_reasons"] = reasons
    rr["likely_false_positive"] = false_pos
    rr["has_real_bounty_language"] = real_bounty
    rr["has_external_judge_signal"] = external_judge
    rr["risk_terms"] = risk
    refined.append(rr)

refined.sort(key=lambda x: (x["refined_score"], x.get("money") or 0), reverse=True)
JSON_OUT.write_text(json.dumps(refined, indent=2), encoding="utf-8")

lines = []
lines.append("# Refined Paid GitHub Fix Scout")
lines.append("")
lines.append(f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
lines.append("")
lines.append("## Summary")
lines.append("")
for klass in ["GOLD", "PROMISING", "MAYBE", "LOW"]:
    lines.append(f"- {klass}: {sum(1 for r in refined if r['refined_class'] == klass)}")
lines.append("")
lines.append("## Best Realistic Targets")
lines.append("")

for r in [x for x in refined if x["refined_class"] in ("GOLD", "PROMISING")][:40]:
    lines.append(f"### {r['refined_class']} · refined score {r['refined_score']} · {r['title']}")
    lines.append("")
    lines.append(f"- Repo: `{r['repo']}`")
    lines.append(f"- URL: {r['url']}")
    lines.append(f"- Updated: {r['updated_at']}")
    lines.append(f"- Comments: {r['comments']}")
    if r.get("money"):
        lines.append(f"- Detected money: `{r['money']:g}`")
    lines.append(f"- Labels: `{', '.join([x for x in r.get('labels', []) if x])}`")
    lines.append("- Refined reasons:")
    for reason in r["refined_reasons"]:
        lines.append(f"  - {reason}")
    snippet = (r.get("body_snippet") or "").strip()
    if snippet:
        lines.append("")
        lines.append("Snippet:")
        lines.append("")
        lines.append("```text")
        lines.append("\n".join(snippet.splitlines()[:10])[:1200])
        lines.append("```")
    lines.append("")

lines.append("## Immediate Manual Triage")
lines.append("")
lines.append("Open the top 5 and answer:")
lines.append("")
lines.append("1. Is payment real and specific?")
lines.append("2. Is there a local judge/test/benchmark?")
lines.append("3. Can a patch be attempted in 1–2 days?")
lines.append("4. Is the issue not security-disclosure sensitive?")
lines.append("5. Is competition low enough?")
lines.append("")
lines.append("Best MathGraph fit is not biggest payout. Best fit is: concrete bounty + local checker + small patch surface + fast feedback.")
lines.append("")

REPORT.write_text("\n".join(lines), encoding="utf-8")

print(f"Wrote: {REPORT}")
print(f"Wrote: {JSON_OUT}")
print()
print("Top 20 refined:")
for r in refined[:20]:
    money = f" money≈{r['money']:g}" if r.get("money") else ""
    print(f"- [{r['refined_class']}] score={r['refined_score']}{money} {r['repo']} :: {r['title']}")
    print(f"  {r['url']}")
