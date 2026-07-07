#!/usr/bin/env bash
set -euo pipefail

echo "MathGraph Cash Win Scout v16 REST"
echo "Goal: repair v15 zero-result scout by using GitHub REST search directly, then rank live cash/bounty routes."
echo

ROOT="/Users/heath/Documents/mathgraph-lean-work"
OUT="$ROOT/artifacts/cash_win_scout_v16_rest"
mkdir -p "$OUT/raw_search" "$OUT/raw_issue"
cd "$ROOT"

echo "01 status"
date -u +"%Y-%m-%dT%H:%M:%SZ" | tee "$OUT/status_start.txt"
df -h / | tee "$OUT/df_start.txt"
git status --short | tee "$OUT/git_status_start.txt" || true
echo

echo "02 gh auth"
gh api user --jq .login | tee "$OUT/gh_user.txt"
echo

echo "03 REST search GitHub issues"
python3 - <<'PY'
from pathlib import Path
import json
import subprocess
import time
import re

OUT = Path("/Users/heath/Documents/mathgraph-lean-work/artifacts/cash_win_scout_v16_rest")
RAW = OUT / "raw_search"
RAW.mkdir(parents=True, exist_ok=True)

queries = [
    'bounty is:issue is:open',
    '"bug bounty" is:issue is:open',
    '"Bounty $" is:issue is:open',
    '"$100" bounty is:issue is:open',
    '"$200" bounty is:issue is:open',
    '"$300" bounty is:issue is:open',
    '"$400" bounty is:issue is:open',
    '"$500" bounty is:issue is:open',
    '"$1000" bounty is:issue is:open',
    '"bounty:100" is:issue is:open',
    '"bounty:200" is:issue is:open',
    '"bounty:400" is:issue is:open',
    '"bounty_difficulty" is:issue is:open',
    '"good first issue" bounty is:issue is:open',
    '"performance" bounty is:issue is:open',
    '"benchmark" bounty is:issue is:open',
    '"pytest" bounty is:issue is:open',
    '"ci" bounty is:issue is:open',
    '"github actions" bounty is:issue is:open',
    '"julia" bounty is:issue is:open',
    '"lean" bounty is:issue is:open',
    '"solver" bounty is:issue is:open',
    '"optimization" bounty is:issue is:open',
    '"reward" "pull request" is:issue is:open',
    '"paid" "pull request" is:issue is:open',
    '"NumFOCUS" bounty is:issue is:open',
    '"bounty" "makefile" is:issue is:open',
    '"bounty" "benchmark suite" is:issue is:open',
    '"bounty" "failing test" is:issue is:open',
    '"bounty" "unit test" is:issue is:open',
]

dedup = {}
errors = []

for i, q in enumerate(queries, 1):
    print(f"query {i:02d}/{len(queries)}: {q}")
    cmd = [
        "gh", "api", "-X", "GET", "search/issues",
        "-f", f"q={q}",
        "-f", "per_page=100",
        "-f", "sort=updated",
        "-f", "order=desc",
    ]
    p = subprocess.run(cmd, text=True, capture_output=True)
    (RAW / f"query_{i:02d}.out").write_text(p.stdout)
    (RAW / f"query_{i:02d}.err").write_text(p.stderr)
    if p.returncode != 0:
        errors.append({"query": q, "rc": p.returncode, "err": p.stderr[:1000]})
        continue
    try:
        data = json.loads(p.stdout or "{}")
    except Exception as e:
        errors.append({"query": q, "parse_error": str(e), "stdout_head": p.stdout[:1000]})
        continue
    for item in data.get("items", []):
        url = item.get("html_url") or ""
        if url:
            item["_query"] = q
            dedup[url] = item
    time.sleep(0.4)

items = list(dedup.values())
(OUT / "search_errors.json").write_text(json.dumps(errors, indent=2) + "\n")
(OUT / "search_results_dedup.json").write_text(json.dumps(items, indent=2) + "\n")
print("dedup issues", len(items))
print("errors", len(errors))
PY
echo

echo "04 enrich candidate issues"
python3 - <<'PY'
from pathlib import Path
import json
import subprocess
import re
import time

OUT = Path("/Users/heath/Documents/mathgraph-lean-work/artifacts/cash_win_scout_v16_rest")
RAW = OUT / "raw_issue"
RAW.mkdir(parents=True, exist_ok=True)

items = json.loads((OUT / "search_results_dedup.json").read_text())

BAD_TITLE = re.compile(r"(web3|crypto|token|airdrop|wallet|metamask|nft|solidity|smart contract|prompt injection|jailbreak|exfiltrat|system prompt|private key|seed phrase|ctf|hackathon|ethdenver|casino|gambling|adult|nsfw|weapon|drug|thc|cbd)", re.I)
GOOD_TITLE = re.compile(r"(bounty|\$|reward|paid|benchmark|performance|pytest|test|ci|workflow|julia|lean|solver|optimization|makefile|docs)", re.I)

def repo_num(url):
    m = re.search(r"github\.com/([^/]+/[^/]+)/issues/(\d+)", url)
    if not m:
        return None, None
    return m.group(1), int(m.group(2))

pre = []
for item in items:
    title = item.get("title") or ""
    body = item.get("body") or ""
    labels = " ".join((l.get("name", "") for l in item.get("labels", []) if isinstance(l, dict)))
    text = f"{title} {labels} {body[:500]}"
    if BAD_TITLE.search(text):
        continue
    if GOOD_TITLE.search(text):
        pre.append(item)

def rough_score(item):
    title = item.get("title") or ""
    body = item.get("body") or ""
    labels = " ".join((l.get("name", "") for l in item.get("labels", []) if isinstance(l, dict)))
    text = f"{title} {labels} {body[:1000]}"
    s = 0
    if re.search(r"\$[0-9]", text): s += 30
    if re.search(r"bounty", text, re.I): s += 20
    if re.search(r"benchmark|performance|pytest|test|ci|workflow|julia|lean|solver|makefile", text, re.I): s += 20
    if re.search(r"assigned|claimed|taken", text, re.I): s -= 20
    if BAD_TITLE.search(text): s -= 100
    return s

pre = sorted(pre, key=rough_score, reverse=True)[:120]
enriched = []
for i, item in enumerate(pre, 1):
    url = item.get("html_url") or ""
    repo, num = repo_num(url)
    if not repo:
        continue
    print(f"view {i:03d}/{len(pre)} {repo}#{num}")
    cmd = ["gh", "issue", "view", str(num), "-R", repo, "--json", "title,url,body,state,labels,assignees,comments,createdAt,updatedAt,author"]
    p = subprocess.run(cmd, text=True, capture_output=True)
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "__", f"{repo}_{num}")[:150]
    (RAW / f"{slug}.out").write_text(p.stdout)
    (RAW / f"{slug}.err").write_text(p.stderr)
    if p.returncode != 0:
        continue
    try:
        data = json.loads(p.stdout or "{}")
    except Exception:
        continue
    data["_repo"] = repo
    data["_number"] = num
    data["_search_url"] = url
    enriched.append(data)
    time.sleep(0.25)

(OUT / "issue_views.json").write_text(json.dumps(enriched, indent=2) + "\n")
print("enriched", len(enriched))
PY
echo

echo "05 score candidates"
python3 - <<'PY'
from pathlib import Path
import json
import re
from collections import Counter

OUT = Path("/Users/heath/Documents/mathgraph-lean-work/artifacts/cash_win_scout_v16_rest")
items = json.loads((OUT / "issue_views.json").read_text())

BAD_RE = re.compile(r"(web3|crypto|token|airdrop|wallet|metamask|nft|solidity|smart contract|prompt injection|jailbreak|exfiltrat|system prompt|private key|seed phrase|ctf|hackathon|ethdenver|exploit|vulnerability|xss|csrf|rce|malware|phishing|casino|betting|gambling|adult|nsfw|onlyfans|weapon|firearm|drug|thc|cbd)", re.I)
GOOD_RE = re.compile(r"(pytest|test|tests|ci|github actions|benchmark|performance|perf|makefile|local|reproducible|julia|python|lean|cargo test|npm test|go test|lake build|unit test|workflow|solver|parser|compiler|docs|documentation)", re.I)
PATCH_RE = re.compile(r"(fix|implement|add|update|repair|refactor|optimi[sz]e|reduce|speed|benchmark|workflow|ci|docs|makefile|test|solver|parser|compiler|support)", re.I)
CLAIM_RE = re.compile(r"(assigned to|assigned|claimed|taken|already working|bounty is now yours|PR submitted|pull request ready|has already been working|the bounty is now yours)", re.I)
UNCLAIM_RE = re.compile(r"(unassigned|not assigned|no one|available|up for grabs|open for|looking for someone|if .* available|currently claimed by no one)", re.I)
MONEY_PATTERNS = [
    re.compile(r"\$\s*([0-9][0-9,]{1,8})(?:\.\d+)?", re.I),
    re.compile(r"USD\s*([0-9][0-9,]{1,8})(?:\.\d+)?", re.I),
    re.compile(r"([0-9][0-9,]{1,8})\s*(?:USD|dollars)", re.I),
    re.compile(r"bounty[:\s/\-]*([0-9][0-9,]{1,8})", re.I),
]

def labels_text(x):
    labels = x.get("labels") or []
    return " ".join(l.get("name", "") for l in labels if isinstance(l, dict))

def comments_text(x):
    return "\n".join((c.get("body", "") or "") for c in (x.get("comments") or []) if isinstance(c, dict))

def money(text):
    vals = []
    for pat in MONEY_PATTERNS:
        for m in pat.findall(text):
            if isinstance(m, tuple):
                m = next((z for z in m if z), "")
            try:
                vals.append(int(str(m).replace(",", "")))
            except Exception:
                pass
    vals = [v for v in vals if 10 <= v <= 200000]
    return max(vals) if vals else None

rows = []
for x in items:
    title = x.get("title") or ""
    body = x.get("body") or ""
    comments = comments_text(x)
    labels = labels_text(x)
    assignees = x.get("assignees") or []
    repo = x.get("_repo") or ""
    num = x.get("_number") or ""
    url = x.get("url") or x.get("_search_url") or ""
    text = "\n".join([title, labels, body, comments[:5000]])
    amount = money(text)
    score = 0
    reasons = []

    if amount:
        score += min(70, 20 + amount // 40)
        reasons.append(f"money≈${amount}")
    elif "bounty" in text.lower():
        score += 18
        reasons.append("bounty-mentioned")
    else:
        score -= 20

    if GOOD_RE.search(text):
        score += 28
        reasons.append("local/test/benchmark surface")
    if PATCH_RE.search(text):
        score += 15
        reasons.append("patchable wording")
    if re.search(r"(julia|lean|python|pytest|benchmark|ci|workflow|makefile)", text, re.I):
        score += 14
        reasons.append("stack fit")
    if UNCLAIM_RE.search(text):
        score += 15
        reasons.append("available language")
    if assignees:
        score -= 25
        reasons.append("assigned")
    if CLAIM_RE.search(comments + "\n" + body):
        score -= 25
        reasons.append("claim/assigned language")
    if re.search(r"(hardware|gpu|device|cloud access|requires access)", text, re.I):
        score -= 15
        reasons.append("possible hardware dependency")
    if re.search(r"(security|vulnerability|exploit|private|credential)", text, re.I):
        score -= 40
        reasons.append("security risk")
    if BAD_RE.search(text):
        score -= 100
        reasons.append("risk-filter hit")
    if amount and amount < 50:
        score -= 10
        reasons.append("low payout")

    verdict = "PROMOTE_RECON" if score >= 50 else "MAYBE" if score >= 25 else "PARK"
    if BAD_RE.search(text):
        verdict = "REJECT_RISK"
    if assignees and score < 65:
        verdict = "PARK_ASSIGNED"

    snippet = re.sub(r"\s+", " ", (body or comments or "")).strip()[:700]
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

rows.sort(key=lambda r: (-r["score"], -(r["amount"] or 0), r["repo"], r["number"]))
(OUT / "ranked_candidates.json").write_text(json.dumps(rows, indent=2) + "\n")

promoted = [r for r in rows if r["verdict"] == "PROMOTE_RECON"]
maybe = [r for r in rows if r["verdict"] == "MAYBE"]

md = []
md.append("# Cash Win Scout v16 REST")
md.append("")
md.append("## Verdict")
md.append("")
md.append(f"- Dedup search results: `{len(json.loads((OUT / 'search_results_dedup.json').read_text()))}`")
md.append(f"- Enriched issue views: `{len(items)}`")
md.append(f"- Promoted recon candidates: `{len(promoted)}`")
md.append("")
md.append("## Top promoted candidates")
md.append("")
for i, r in enumerate(promoted[:25], 1):
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
for i, r in enumerate(maybe[:25], 1):
    amount = f"${r['amount']}" if r["amount"] else "amount unclear"
    md.append(f"{i}. `{r['score']}` {amount} — {r['repo']}#{r['number']} — {r['title']} — {r['url']}")
md.append("")
md.append("## Counts")
md.append("")
for k, v in Counter(r["verdict"] for r in rows).items():
    md.append(f"- {k}: {v}")
md.append("")
(OUT / "GOLD_LIST.md").write_text("\n".join(md) + "\n")
print((OUT / "GOLD_LIST.md").read_text())
PY
echo

echo "06 recon queue"
python3 - <<'PY'
from pathlib import Path
import json

OUT = Path("/Users/heath/Documents/mathgraph-lean-work/artifacts/cash_win_scout_v16_rest")
rows = json.loads((OUT / "ranked_candidates.json").read_text())
top = [r for r in rows if r["verdict"] == "PROMOTE_RECON"][:12]

md = []
md.append("# Cash Win Scout v16 Recon Queue")
md.append("")
for i, r in enumerate(top, 1):
    safe = r["repo"].replace("/", "__")
    md.append(f"## {i}. {r['repo']}#{r['number']}")
    md.append("")
    md.append(f"- {r['title']}")
    md.append(f"- {r['url']}")
    md.append(f"- score `{r['score']}`, amount `{r['amount']}`")
    md.append("")
    md.append("```bash")
    md.append(f'REPO="{r["repo"]}"')
    md.append(f'ISSUE="{r["number"]}"')
    md.append(f'DIR="/Users/heath/Documents/mathgraph-lean-work/external/cash_win_scout_v16/{safe}_{r["number"]}"')
    md.append('mkdir -p "$(dirname "$DIR")"')
    md.append('if [ ! -d "$DIR/.git" ]; then gh repo clone "$REPO" "$DIR" -- --filter=blob:none; else git -C "$DIR" fetch origin; fi')
    md.append('gh issue view "$ISSUE" -R "$REPO" --comments')
    md.append('find "$DIR" -maxdepth 3 -type f | sed "s#^$DIR/##" | head -250')
    md.append("```")
    md.append("")
(OUT / "RECON_QUEUE.md").write_text("\n".join(md) + "\n")
print((OUT / "RECON_QUEUE.md").read_text())
PY
echo

echo "07 commit artifact"
cd "$ROOT"
git add "$OUT" cash_win_scout_v16_rest.sh
git commit -m "Run cash win scout v16 REST" || true
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
