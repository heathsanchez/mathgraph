#!/usr/bin/env bash
set -euo pipefail

echo "MathGraph Cash Win Strict Scout v23"
echo "Goal: find fresh real cash wins, avoiding crowded/parked/synthetic bounty routes."
echo

ROOT="/Users/heath/Documents/mathgraph-lean-work"
OUT="$ROOT/artifacts/cash_win_strict_scout_v23"
mkdir -p "$OUT"
cd "$ROOT"

echo "01 status"
date -u +"%Y-%m-%dT%H:%M:%SZ" | tee "$OUT/status_start.txt"
df -h / | tee "$OUT/df_start.txt"
git status --short | tee "$OUT/mathgraph_status_start.txt" || true
echo

echo "02 strict search and enrichment"
python3 - "$OUT" <<'PY'
from pathlib import Path
import subprocess, json, re, time, sys

out = Path(sys.argv[1])

queries = [
    '"bounty" "$100" "test" is:issue is:open',
    '"bounty" "$200" "test" is:issue is:open',
    '"bounty" "$300" "test" is:issue is:open',
    '"bounty" "$400" "test" is:issue is:open',
    '"bounty" "$500" "test" is:issue is:open',
    '"bounty" "$100" "CI" is:issue is:open',
    '"bounty" "$200" "CI" is:issue is:open',
    '"bounty" "$100" "benchmark" is:issue is:open',
    '"bounty" "$200" "benchmark" is:issue is:open',
    '"bounty" "$100" "pytest" is:issue is:open',
    '"bounty" "$200" "pytest" is:issue is:open',
    '"bounty" "$100" "regression" is:issue is:open',
    '"bounty" "$200" "regression" is:issue is:open',
    '"bounty" "$100" "docs" is:issue is:open',
    '"bounty" "$200" "docs" is:issue is:open',
    '"bounty" "$100" "TypeScript" is:issue is:open',
    '"bounty" "$200" "TypeScript" is:issue is:open',
    '"bounty" "$100" "Julia" is:issue is:open',
    '"bounty" "$200" "Julia" is:issue is:open',
    '"bounty" "$100" "Python" is:issue is:open',
    '"bounty" "$200" "Python" is:issue is:open',
    '"bounty" "$100" "bug" "repro" is:issue is:open',
    '"bounty" "$200" "bug" "repro" is:issue is:open',
    '"good first issue" "bounty" "$100" is:issue is:open',
    '"good first issue" "bounty" "$200" is:issue is:open',
]

deny_repo = re.compile(
    r"(agent-playground|BountyScout|bountyscout|Bounty-Hunters|bug-bounty|claude-builders-bounty|"
    r"UnsafeLabs|SecureBananaLabs|xevrion|greyw0rks|dev-kp-eloper|vansh-09|zhangjiayang|"
    r"ai-research|ai-growth-engine|zeroeye|TentOfTrials|Rustchain|rustchain-bounties|"
    r"bitcoin$|mysql$|cobra$|test|playground|bounty-farm|claude)",
    re.I,
)

deny_text = re.compile(
    r"(web3|crypto|token|wallet|airdrop|nft|solidity|smart contract|metamask|casino|gambling|"
    r"prompt injection|jailbreak|exfiltrat|system prompt|private key|seed phrase|ctf|hackathon|"
    r"security bounty|vulnerability|xss|csrf|rce|malware|phishing|calculate the exact value of pi|"
    r"bounty alert|opportunityies|star this repository|test bounty)",
    re.I,
)

parked_urls = {
    "https://github.com/qojulia/QuantumOptics.jl/issues/407",
    "https://github.com/simonmichael/hledger/issues/1825",
    "https://github.com/QuantumSavory/QuantumSavory.jl/issues/131",
    "https://github.com/tscircuit/dsn-converter/issues/54",
    "https://github.com/tenstorrent/tt-metal/issues/1638",
    "https://github.com/tenstorrent/tt-llk/issues/1638",
}

money_re = re.compile(r"\$\s*([0-9][0-9,]{1,7})|([0-9][0-9,]{1,7})\s*(?:USD|dollars)", re.I)
local_re = re.compile(r"(test|pytest|vitest|jest|bun:test|CI|workflow|github actions|benchmark|regression|repro|fixture|docs|documentation|TypeScript|Python|Julia|unit)", re.I)
claim_re = re.compile(r"(claimed|assigned|already working|working on this|PR opened|pull request|submitted PR|bounty is yours|taken)", re.I)
available_re = re.compile(r"(available|unassigned|up for grabs|not assigned|no one is working|still available)", re.I)

def sh(cmd):
    return subprocess.run(cmd, text=True, capture_output=True)

def repo_num(url):
    m = re.search(r"github\.com/([^/]+/[^/]+)/issues/(\d+)", url)
    if not m:
        return None, None
    return m.group(1), m.group(2)

def money(text):
    vals = []
    for m in money_re.findall(text):
        raw = m[0] or m[1]
        try:
            vals.append(int(raw.replace(",", "")))
        except Exception:
            pass
    vals = [v for v in vals if 20 <= v <= 10000]
    return max(vals) if vals else None

dedup = {}
errors = []

for i, q in enumerate(queries, 1):
    print(f"search {i:02d}/{len(queries)} {q}")
    p = sh(["gh", "api", "-X", "GET", "search/issues", "-f", f"q={q}", "-f", "per_page=60", "-f", "sort=updated", "-f", "order=desc"])
    if p.returncode != 0:
        errors.append({"query": q, "err": p.stderr[:500]})
        continue
    try:
        data = json.loads(p.stdout or "{}")
    except Exception as e:
        errors.append({"query": q, "parse": str(e)})
        continue
    for item in data.get("items", []):
        url = item.get("html_url") or ""
        if not url or url in parked_urls:
            continue
        repo, num = repo_num(url)
        if not repo or deny_repo.search(repo):
            continue
        text = " ".join([
            item.get("title") or "",
            item.get("body") or "",
            " ".join(l.get("name","") for l in item.get("labels", []) if isinstance(l, dict)),
        ])
        if deny_text.search(text):
            continue
        if not money(text):
            continue
        if not local_re.search(text):
            continue
        dedup[url] = {"url": url, "repo": repo, "number": num, "search_text": text[:3000], "search_item": item}
    time.sleep(0.25)

cands = list(dedup.values())[:80]
enriched = []

for i, c in enumerate(cands, 1):
    repo, num = c["repo"], c["number"]
    print(f"enrich {i:02d}/{len(cands)} {repo}#{num}")
    issue_p = sh(["gh", "issue", "view", num, "-R", repo, "--json", "title,url,body,state,labels,assignees,comments,createdAt,updatedAt,author"])
    if issue_p.returncode != 0:
        continue
    repo_p = sh(["gh", "repo", "view", repo, "--json", "nameWithOwner,description,stargazerCount,forkCount,isArchived,isPrivate,pushedAt,primaryLanguage,url"])
    try:
        issue = json.loads(issue_p.stdout or "{}")
        meta = json.loads(repo_p.stdout or "{}") if repo_p.returncode == 0 else {}
    except Exception:
        continue
    issue["_repo"] = repo
    issue["_number"] = num
    issue["_repo_meta"] = meta
    enriched.append(issue)
    time.sleep(0.25)

rows = []
for x in enriched:
    repo = x.get("_repo")
    num = x.get("_number")
    meta = x.get("_repo_meta") or {}
    title = x.get("title") or ""
    body = x.get("body") or ""
    comments = "\n".join((c.get("body","") or "") for c in (x.get("comments") or []) if isinstance(c, dict))
    labels = " ".join(l.get("name","") for l in (x.get("labels") or []) if isinstance(l, dict))
    text = "\n".join([title, labels, body, comments[:6000]])
    amount = money(text)
    assignees = [a.get("login") for a in (x.get("assignees") or []) if isinstance(a, dict)]

    stars = meta.get("stargazerCount") or 0
    archived = bool(meta.get("isArchived"))
    private = bool(meta.get("isPrivate"))
    lang = ((meta.get("primaryLanguage") or {}).get("name") or "")
    pushed = meta.get("pushedAt") or ""

    score = 0
    reasons = []

    if amount:
        score += min(40, amount // 20)
        reasons.append(f"money=${amount}")
    if stars >= 50:
        score += 20; reasons.append(f"stars={stars}")
    elif stars >= 10:
        score += 10; reasons.append(f"stars={stars}")
    else:
        score -= 15; reasons.append(f"low-stars={stars}")

    if local_re.search(text):
        score += 25; reasons.append("local-verifier-surface")
    if re.search(r"(fixture|repro|regression|failing test|unit test|benchmark|CI|workflow)", text, re.I):
        score += 15; reasons.append("specific-test-surface")
    if re.search(r"(TypeScript|Python|Julia|JavaScript|Rust|Go)", text, re.I) or lang in {"TypeScript","JavaScript","Python","Julia","Rust","Go"}:
        score += 10; reasons.append(f"stack={lang or 'mentioned'}")
    if available_re.search(text):
        score += 10; reasons.append("availability-language")
    if assignees:
        score -= 30; reasons.append("assigned")
    if claim_re.search(text):
        score -= 25; reasons.append("claim-pr-risk")
    if archived or private:
        score -= 100; reasons.append("archived/private")
    if deny_text.search(text) or deny_repo.search(repo):
        score -= 100; reasons.append("deny-filter")

    verdict = "PROMOTE_RECON" if score >= 55 and not assignees else "MAYBE" if score >= 35 else "PARK"
    rows.append({
        "verdict": verdict,
        "score": score,
        "amount": amount,
        "repo": repo,
        "number": num,
        "title": title,
        "url": x.get("url"),
        "stars": stars,
        "language": lang,
        "assignees": assignees,
        "pushedAt": pushed,
        "reasons": reasons,
        "snippet": re.sub(r"\s+", " ", body or comments).strip()[:700],
    })

rows.sort(key=lambda r: (r["verdict"] != "PROMOTE_RECON", -r["score"], -(r["amount"] or 0), -r["stars"], r["repo"]))
promoted = [r for r in rows if r["verdict"] == "PROMOTE_RECON"]
maybe = [r for r in rows if r["verdict"] == "MAYBE"]

(out / "search_errors.json").write_text(json.dumps(errors, indent=2) + "\n")
(out / "strict_candidates.json").write_text(json.dumps(rows, indent=2) + "\n")

md = []
md.append("# Cash Win Strict Scout v23")
md.append("")
md.append("## Verdict")
md.append("")
md.append(f"- Enriched candidates: `{len(enriched)}`")
md.append(f"- Promoted: `{len(promoted)}`")
md.append(f"- Maybe: `{len(maybe)}`")
md.append("")
md.append("## Promoted")
md.append("")
for i, r in enumerate(promoted[:20], 1):
    md.append(f"### {i}. {r['repo']}#{r['number']} - {r['title']}")
    md.append("")
    md.append(f"- Score: `{r['score']}`")
    md.append(f"- Money: `${r['amount']}`")
    md.append(f"- Stars: `{r['stars']}`")
    md.append(f"- Language: `{r['language']}`")
    md.append(f"- URL: {r['url']}")
    md.append(f"- Reasons: {', '.join(r['reasons'])}")
    md.append(f"- Snippet: {r['snippet']}")
    md.append("")
md.append("## Maybe")
md.append("")
for i, r in enumerate(maybe[:20], 1):
    md.append(f"{i}. `{r['score']}` ${r['amount']} stars={r['stars']} - {r['repo']}#{r['number']} - {r['title']} - {r['url']}")
md.append("")
(out / "STRICT_GOLD_LIST.md").write_text("\n".join(md) + "\n")
print((out / "STRICT_GOLD_LIST.md").read_text())
PY
echo

echo "03 create recon commands"
python3 - "$OUT" <<'PY'
from pathlib import Path
import json, sys

out = Path(sys.argv[1])
rows = json.loads((out / "strict_candidates.json").read_text())
top = [r for r in rows if r["verdict"] == "PROMOTE_RECON"][:8]

md = []
md.append("# Strict Scout v23 Recon Queue")
md.append("")
for i, r in enumerate(top, 1):
    safe = r["repo"].replace("/", "__")
    md.append(f"## {i}. {r['repo']}#{r['number']}")
    md.append("")
    md.append(f"- {r['title']}")
    md.append(f"- {r['url']}")
    md.append(f"- score `{r['score']}`, amount `${r['amount']}`, stars `{r['stars']}`")
    md.append("")
    md.append("```bash")
    md.append(f'REPO="{r["repo"]}"')
    md.append(f'ISSUE="{r["number"]}"')
    md.append(f'DIR="/Users/heath/Documents/mathgraph-lean-work/external/cash_win_strict_v23/{safe}_{r["number"]}"')
    md.append('mkdir -p "$(dirname "$DIR")"')
    md.append('if [ ! -d "$DIR/.git" ]; then gh repo clone "$REPO" "$DIR" -- --filter=blob:none; else git -C "$DIR" fetch origin; fi')
    md.append('gh issue view "$ISSUE" -R "$REPO" --comments')
    md.append('find "$DIR" -maxdepth 3 -type f | sed "s#^$DIR/##" | head -250')
    md.append("```")
    md.append("")
(out / "RECON_QUEUE.md").write_text("\n".join(md) + "\n")
print((out / "RECON_QUEUE.md").read_text())
PY
echo

echo "04 commit artifact"
cd "$ROOT"
git add "$OUT" cash_win_strict_scout_v23.sh
git commit -m "Run strict cash win scout v23" || true
git push origin local-main || true
echo

echo "05 final"
git status --short
df -h /
echo
echo "Artifacts:"
echo "$OUT/STRICT_GOLD_LIST.md"
echo "$OUT/RECON_QUEUE.md"
echo "$OUT/strict_candidates.json"
echo "$OUT/search_errors.json"
