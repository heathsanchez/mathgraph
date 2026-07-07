#!/usr/bin/env bash
set -euo pipefail

echo "MathGraph Cash Win Scout v15"
echo "Goal: find more live, patchable, externally verified cash wins."
echo

ROOT="/Users/heath/Documents/mathgraph-lean-work"
OUT="$ROOT/artifacts/cash_win_scout_v15"
mkdir -p "$OUT"
cd "$ROOT"

echo "01 status"
date -u +"%Y-%m-%dT%H:%M:%SZ" | tee "$OUT/status_start.txt"
df -h / | tee "$OUT/df_start.txt"
git status --short | tee "$OUT/git_status_start.txt" || true
echo

echo "02 gh identity"
gh auth status > "$OUT/gh_auth_status.out" 2> "$OUT/gh_auth_status.err" || true
gh api user --jq .login | tee "$OUT/gh_user.txt"
echo

echo "03 live issue search"
python3 - <<'PY'
from pathlib import Path
import json
import subprocess
import time
import re
import hashlib

root = Path("/Users/heath/Documents/mathgraph-lean-work")
out = root / "artifacts" / "cash_win_scout_v15"
raw = out / "raw"
raw.mkdir(parents=True, exist_ok=True)

queries = [
    'is:issue is:open bounty in:title,body archived:false',
    'is:issue is:open "$" bounty in:title,body archived:false',
    'is:issue is:open "bug bounty" in:title,body archived:false',
    'is:issue is:open "bounty:" in:title,body archived:false',
    'is:issue is:open "Bounty $" in:title,body archived:false',
    'is:issue is:open "reward" "PR" in:title,body archived:false',
    'is:issue is:open "cash" "pull request" in:title,body archived:false',
    'is:issue is:open "paid" "issue" "PR" archived:false',
    'is:issue is:open "NumFOCUS" "bounty" archived:false',
    'is:issue is:open "bounty_difficulty" archived:false',
    'is:issue is:open "good first issue" "bounty" archived:false',
    'is:issue is:open "performance" "bounty" archived:false',
    'is:issue is:open "benchmark" "bounty" archived:false',
    'is:issue is:open "optimization" "bounty" archived:false',
    'is:issue is:open "pytest" "bounty" archived:false',
    'is:issue is:open "CI" "bounty" archived:false',
    'is:issue is:open "Julia" "bounty" archived:false',
    'is:issue is:open "Lean" "bounty" archived:false',
    'is:issue is:open "formal verification" "bounty" archived:false',
    'is:issue is:open "solver" "bounty" archived:false',
]

seen = {}
errors = []

for qi, q in enumerate(queries, 1):
    print(f"query {qi}/{len(queries)}: {q}")
    cmd = [
        "gh", "search", "issues", q,
        "--limit", "80",
        "--json", "repository,title,url,number,state,labels,createdAt,updatedAt,comments,author,assignees"
    ]
    p = subprocess.run(cmd, text=True, capture_output=True)
    (raw / f"query_{qi:02d}.out").write_text(p.stdout)
    (raw / f"query_{qi:02d}.err").write_text(p.stderr)
    if p.returncode != 0:
        errors.append({"query": q, "rc": p.returncode, "err": p.stderr})
        continue
    try:
        rows = json.loads(p.stdout or "[]")
    except Exception as e:
        errors.append({"query": q, "parse_error": str(e), "stdout_head": p.stdout[:500]})
        continue
    for r in rows:
        url = r.get("url") or ""
        if not url:
            continue
        seen[url] = r
    time.sleep(0.2)

items = list(seen.values())
(out / "search_errors.json").write_text(json.dumps(errors, indent=2) + "\n")
(out / "search_results_dedup.json").write_text(json.dumps(items, indent=2) + "\n")
print("dedup issues", len(items))
PY
echo

echo "04 enrich top candidates via gh issue view"
python3 - <<'PY'
from pathlib import Path
import json
import subprocess
import re
import time

root = Path("/Users/heath/Documents/mathgraph-lean-work")
out = root / "artifacts" / "cash_win_scout_v15"
raw = out / "raw_issue_views"
raw.mkdir(parents=True, exist_ok=True)

items = json.loads((out / "search_results_dedup.json").read_text())

BAD_RE = re.compile(
    r"(web3|crypto|token|airdrop|wallet|metamask|nft|solidity|smart contract|"
    r"prompt injection|jailbreak|exfiltrat|system prompt|private key|seed phrase|"
    r"ctf|hackathon|ethdenver|exploit|vulnerability|xss|csrf|rce|malware|phishing|"
    r"casino|betting|gambling|adult|nsfw|onlyfans|weapon|firearm|drug|thc|cbd)",
    re.I,
)
GOOD_RE = re.compile(
    r"(test|pytest|ci|benchmark|performance|perf|optimi[sz]e|solver|lean|julia|python|"
    r"reproducible|failing|regression|docs|makefile|workflow|github actions|type|lint|"
    r"formal|proof|counterexample|parser|compiler|memory|speed|timeout|local)",
    re.I,
)
MONEY_RE = re.compile(
    r"(?:\$|USD\s*)\s*([0-9][0-9,]{1,8})(?:\.\d+)?|"
    r"([0-9][0-9,]{1,8})\s*(?:USD|dollars)|"
    r"bounty[:\s/\-]*([0-9][0-9,]{1,8})",
    re.I,
)
CLAIM_RE = re.compile(r"(assigned|claimed|already working|taken|bounty is now yours|PR submitted|pull request ready|assigned to)", re.I)
UNCLAIM_RE = re.compile(r"(unassigned|not assigned|no one|available|open for|up for grabs|looking for someone)", re.I)

def repo_from_url(url):
    m = re.search(r"github\.com/([^/]+/[^/]+)/issues/(\d+)", url)
    if not m:
        return None, None
    return m.group(1), int(m.group(2))

def labels_text(x):
    labels = x.get("labels") or []
    parts = []
    for l in labels:
        if isinstance(l, dict):
            parts.append(l.get("name",""))
        else:
            parts.append(str(l))
    return " ".join(parts)

candidates = []
for item in items:
    title = item.get("title") or ""
    url = item.get("url") or ""
    label_text = labels_text(item)
    base_text = " ".join([title, label_text])
    if BAD_RE.search(base_text):
        continue
    repo, number = repo_from_url(url)
    if not repo:
        continue
    rough_money = MONEY_RE.findall(base_text)
    rough_good = GOOD_RE.search(base_text)
    if not rough_money and "bounty" not in base_text.lower() and not rough_good:
        continue
    candidates.append(item)

# Prefer likely useful candidates, cap issue view calls.
def rough_score(item):
    title = item.get("title") or ""
    label = labels_text(item)
    text = f"{title} {label}"
    s = 0
    if MONEY_RE.search(text): s += 20
    if re.search(r"\$[0-9]", text): s += 15
    if re.search(r"bounty", text, re.I): s += 15
    if GOOD_RE.search(text): s += 10
    if BAD_RE.search(text): s -= 100
    return s

candidates = sorted(candidates, key=rough_score, reverse=True)[:80]
enriched = []

for i, item in enumerate(candidates, 1):
    url = item.get("url") or ""
    repo, number = repo_from_url(url)
    print(f"view {i}/{len(candidates)} {repo}#{number}")
    cmd = ["gh", "issue", "view", str(number), "-R", repo, "--json", "title,url,body,state,labels,assignees,comments,createdAt,updatedAt,author"]
    p = subprocess.run(cmd, text=True, capture_output=True)
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "__", f"{repo}_{number}")[:120]
    (raw / f"{slug}.out").write_text(p.stdout)
    (raw / f"{slug}.err").write_text(p.stderr)
    if p.returncode != 0:
        continue
    try:
        data = json.loads(p.stdout or "{}")
    except Exception:
        continue
    data["_repo"] = repo
    data["_number"] = number
    enriched.append(data)
    time.sleep(0.2)

(out / "issue_views.json").write_text(json.dumps(enriched, indent=2) + "\n")
print("enriched", len(enriched))
PY
echo

echo "05 score and rank"
python3 - <<'PY'
from pathlib import Path
import json
import re
from collections import Counter

root = Path("/Users/heath/Documents/mathgraph-lean-work")
out = root / "artifacts" / "cash_win_scout_v15"
items = json.loads((out / "issue_views.json").read_text())

BAD_RE = re.compile(
    r"(web3|crypto|token|airdrop|wallet|metamask|nft|solidity|smart contract|"
    r"prompt injection|jailbreak|exfiltrat|system prompt|private key|seed phrase|"
    r"ctf|hackathon|ethdenver|exploit|vulnerability|xss|csrf|rce|malware|phishing|"
    r"casino|betting|gambling|adult|nsfw|onlyfans|weapon|firearm|drug|thc|cbd)",
    re.I,
)
GOOD_LOCAL_RE = re.compile(
    r"(pytest|test|tests|ci|github actions|benchmark|makefile|local|reproducible|"
    r"julia|python|lean|cargo test|npm test|go test|lake build|unit test|workflow)",
    re.I,
)
PATCH_SURFACE_RE = re.compile(
    r"(fix|implement|add|update|refactor|optimi[sz]e|reduce|speed|benchmark|workflow|ci|docs|makefile|test|solver|parser|compiler)",
    re.I,
)
CLAIM_RE = re.compile(r"(assigned to|assigned|claimed|taken|already working|bounty is now yours|PR submitted|pull request ready|has already been working)", re.I)
UNCLAIM_RE = re.compile(r"(unassigned|not assigned|no one|available|up for grabs|open for|looking for someone|if .* available)", re.I)
MONEY_PATTERNS = [
    re.compile(r"\$\s*([0-9][0-9,]{1,8})(?:\.\d+)?", re.I),
    re.compile(r"USD\s*([0-9][0-9,]{1,8})(?:\.\d+)?", re.I),
    re.compile(r"([0-9][0-9,]{1,8})\s*(?:USD|dollars)", re.I),
    re.compile(r"bounty[:\s/\-]*([0-9][0-9,]{1,8})", re.I),
]

def labels_text(x):
    labels = x.get("labels") or []
    parts = []
    for l in labels:
        if isinstance(l, dict):
            parts.append(l.get("name",""))
        else:
            parts.append(str(l))
    return " ".join(parts)

def comments_text(x):
    parts = []
    for c in x.get("comments") or []:
        if isinstance(c, dict):
            parts.append(c.get("body","") or "")
    return "\n".join(parts)

def money_amount(text):
    vals = []
    for pat in MONEY_PATTERNS:
        for m in pat.findall(text):
            if isinstance(m, tuple):
                m = next((z for z in m if z), "")
            if not m:
                continue
            try:
                vals.append(int(str(m).replace(",", "")))
            except Exception:
                pass
    vals = [v for v in vals if 1 <= v <= 200000]
    return max(vals) if vals else None

rows = []
for x in items:
    title = x.get("title") or ""
    body = x.get("body") or ""
    labels = labels_text(x)
    comments = comments_text(x)
    repo = x.get("_repo") or ""
    num = x.get("_number") or ""
    url = x.get("url") or ""
    assignees = x.get("assignees") or []
    text = "\n".join([title, labels, body, comments[:4000]])
    lower = text.lower()
    amount = money_amount(text)

    score = 0
    reasons = []

    if amount:
        score += min(60, 20 + amount // 50)
        reasons.append(f"money≈${amount}")
    elif "bounty" in lower:
        score += 18
        reasons.append("bounty-mentioned")
    else:
        score -= 20

    if GOOD_LOCAL_RE.search(text):
        score += 25
        reasons.append("local/test/benchmark surface")

    if PATCH_SURFACE_RE.search(text):
        score += 15
        reasons.append("patch surface")

    if re.search(r"(julia|lean|python|pytest|benchmark|ci|workflow|makefile)", text, re.I):
        score += 12
        reasons.append("stack fit")

    if assignees:
        score -= 30
        reasons.append("assigned")

    if CLAIM_RE.search(comments + "\n" + body):
        score -= 25
        reasons.append("claim/assigned language")

    if UNCLAIM_RE.search(comments + "\n" + body):
        score += 15
        reasons.append("available language")

    if BAD_RE.search(text):
        score -= 100
        reasons.append("risk-filter hit")

    if re.search(r"(hardware|gpu|device|cloud access|requires access)", text, re.I):
        score -= 15
        reasons.append("possible hardware dependency")

    if re.search(r"(security|vulnerability|exploit|private|credential)", text, re.I):
        score -= 40
        reasons.append("security risk")

    if re.search(r"(hackathon|2023|2022|2021)", text, re.I):
        score -= 20
        reasons.append("stale/hackathon risk")

    if amount and amount < 25:
        score -= 15
        reasons.append("low payout")

    verdict = "PROMOTE_RECON" if score >= 45 else "MAYBE" if score >= 25 else "PARK"
    if BAD_RE.search(text):
        verdict = "REJECT_RISK"
    if assignees and score < 60:
        verdict = "PARK_ASSIGNED"

    snippet = re.sub(r"\s+", " ", (body or comments or "")).strip()[:500]
    rows.append({
        "score": score,
        "verdict": verdict,
        "amount": amount,
        "repo": repo,
        "number": num,
        "title": title,
        "url": url,
        "labels": labels,
        "assignees": [a.get("login") if isinstance(a, dict) else str(a) for a in assignees],
        "updatedAt": x.get("updatedAt"),
        "reasons": reasons,
        "snippet": snippet,
    })

rows.sort(key=lambda r: (r["verdict"] != "PROMOTE_RECON", -r["score"], -(r["amount"] or 0), r["updatedAt"] or ""), reverse=False)
(out / "ranked_candidates.json").write_text(json.dumps(rows, indent=2) + "\n")

promoted = [r for r in rows if r["verdict"] == "PROMOTE_RECON"]
maybe = [r for r in rows if r["verdict"] == "MAYBE"]

md = []
md.append("# Cash Win Scout v15")
md.append("")
md.append("## Filter")
md.append("")
md.append("Real-money/public-bounty candidates ranked for: local testability, patch surface, stack fit, external verification, and low weirdness.")
md.append("")
md.append("## Top promoted candidates")
md.append("")
for i, r in enumerate(promoted[:20], 1):
    amount = f"${r['amount']}" if r["amount"] else "amount unclear"
    md.append(f"### {i}. {r['repo']}#{r['number']} — {r['title']}")
    md.append("")
    md.append(f"- Verdict: `{r['verdict']}`")
    md.append(f"- Score: `{r['score']}`")
    md.append(f"- Money: `{amount}`")
    md.append(f"- URL: {r['url']}")
    md.append(f"- Reasons: {', '.join(r['reasons'])}")
    if r["assignees"]:
        md.append(f"- Assignees: {', '.join(r['assignees'])}")
    md.append(f"- Snippet: {r['snippet']}")
    md.append("")
md.append("## Maybe candidates")
md.append("")
for i, r in enumerate(maybe[:20], 1):
    amount = f"${r['amount']}" if r["amount"] else "amount unclear"
    md.append(f"{i}. `{r['score']}` {amount} — {r['repo']}#{r['number']} — {r['title']} — {r['url']}")
md.append("")
md.append("## Counts")
md.append("")
counts = Counter(r["verdict"] for r in rows)
for k, v in counts.items():
    md.append(f"- {k}: {v}")
md.append("")
(out / "GOLD_LIST.md").write_text("\n".join(md) + "\n")

print((out / "GOLD_LIST.md").read_text())
PY
echo

echo "06 create recon commands for top 10"
python3 - <<'PY'
from pathlib import Path
import json

root = Path("/Users/heath/Documents/mathgraph-lean-work")
out = root / "artifacts" / "cash_win_scout_v15"
rows = json.loads((out / "ranked_candidates.json").read_text())
promoted = [r for r in rows if r["verdict"] == "PROMOTE_RECON"][:10]

lines = []
lines.append("# Top recon queue")
lines.append("")
for i, r in enumerate(promoted, 1):
    safe_repo = r["repo"].replace("/", "__")
    issue = r["number"]
    lines.append(f"## {i}. {r['repo']}#{issue}")
    lines.append("")
    lines.append(f"- {r['title']}")
    lines.append(f"- {r['url']}")
    lines.append("")
    lines.append("```bash")
    lines.append(f'REPO="{r["repo"]}"')
    lines.append(f'ISSUE="{issue}"')
    lines.append(f'DIR="/Users/heath/Documents/mathgraph-lean-work/external/cash_win_scout_v15/{safe_repo}_{issue}"')
    lines.append('mkdir -p "$(dirname "$DIR")"')
    lines.append('if [ ! -d "$DIR/.git" ]; then gh repo clone "$REPO" "$DIR" -- --filter=blob:none; else git -C "$DIR" fetch origin; fi')
    lines.append('gh issue view "$ISSUE" -R "$REPO" --comments')
    lines.append('find "$DIR" -maxdepth 3 -type f | sed "s#^$DIR/##" | head -200')
    lines.append("```")
    lines.append("")

(out / "RECON_QUEUE.md").write_text("\n".join(lines) + "\n")
print((out / "RECON_QUEUE.md").read_text())
PY
echo

echo "07 commit scout artifact"
cd "$ROOT"
git add "$OUT" cash_win_scout_v15.sh
git commit -m "Run cash win scout v15" || true
git push origin local-main || true
echo

echo "08 final"
git status --short
df -h /
echo
echo "Artifacts:"
echo "$OUT/GOLD_LIST.md"
echo "$OUT/RECON_QUEUE.md"
echo "$OUT/ranked_candidates.json"
echo "$OUT/search_results_dedup.json"
echo "$OUT/issue_views.json"
