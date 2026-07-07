#!/usr/bin/env bash
set -u

ROOT="/Users/heath/Documents/mathgraph-lean-work"
OUT="$ROOT/artifacts/money_opportunity_scout_v4_prize_words"

mkdir -p "$OUT"
cd "$ROOT" || exit 1

echo "MathGraph Money Opportunity Scout v4 — prize/payment/cash/competition/challenge/golf/hackathon"
echo

echo "01 status"
{
  date -u +"%Y-%m-%dT%H:%M:%SZ"
  df -h /
  git status --short
} | tee "$OUT/status_start.txt"

echo
echo "02 GitHub searches with broader money language"

cat > "$OUT/queries.txt" <<'EOF'
prize in:title,body is:issue is:open updated:>2025-01-01
payment in:title,body is:issue is:open updated:>2025-01-01
cash in:title,body is:issue is:open updated:>2025-01-01
competition in:title,body is:issue is:open updated:>2025-01-01
challenge in:title,body is:issue is:open updated:>2025-01-01
hackathon in:title,body is:issue is:open updated:>2025-01-01
"code golf" in:title,body is:issue is:open updated:>2025-01-01
golf in:title,body is:issue is:open updated:>2025-01-01
"cash prize" in:title,body is:issue is:open updated:>2025-01-01
"prize pool" in:title,body is:issue is:open updated:>2025-01-01
"paid challenge" in:title,body is:issue is:open updated:>2025-01-01
"reward" "challenge" in:title,body is:issue is:open updated:>2025-01-01
"winner" "prize" in:title,body is:issue is:open updated:>2025-01-01
"leaderboard" "prize" in:title,body is:issue is:open updated:>2025-01-01
"leaderboard" "competition" in:title,body is:issue is:open updated:>2025-01-01
"benchmark" "competition" in:title,body is:issue is:open updated:>2025-01-01
"benchmark" "challenge" in:title,body is:issue is:open updated:>2025-01-01
"AI challenge" "prize" in:title,body is:issue is:open updated:>2025-01-01
"math challenge" "prize" in:title,body is:issue is:open updated:>2025-01-01
"proof challenge" in:title,body is:issue is:open updated:>2025-01-01
"Lean" "challenge" in:title,body is:issue is:open updated:>2025-01-01
"formal verification" "challenge" in:title,body is:issue is:open updated:>2025-01-01
"bug bounty" in:title,body is:issue is:open updated:>2025-01-01
"performance challenge" in:title,body is:issue is:open updated:>2025-01-01
"optimization challenge" in:title,body is:issue is:open updated:>2025-01-01
"submission" "leaderboard" "prize" in:title,body is:issue is:open updated:>2025-01-01
"submission" "competition" "benchmark" in:title,body is:issue is:open updated:>2025-01-01
EOF

i=0
while IFS= read -r Q; do
  [ -z "$Q" ] && continue
  i=$((i+1))
  SAFE="$(printf "%03d" "$i")"
  echo
  echo "===== query $SAFE: $Q ====="
  gh search issues "$Q" --state open --limit 100 --json repository,title,number,url,body,labels,createdAt,updatedAt,state \
    > "$OUT/search_${SAFE}.json" 2> "$OUT/search_${SAFE}.err" || true

  python3 - "$OUT/search_${SAFE}.json" "$OUT/search_${SAFE}.err" <<'PY'
from pathlib import Path
import json, sys

p = Path(sys.argv[1])
e = Path(sys.argv[2])

if p.exists() and p.stat().st_size:
  try:
    rows = json.loads(p.read_text())
    print("rows", len(rows))
    for r in rows[:8]:
      repo = (r.get("repository") or {}).get("nameWithOwner")
      print("-", repo, "#"+str(r.get("number")), r.get("title"))
  except Exception as ex:
    print("json_error", ex)
else:
  print("search_failed")
  if e.exists():
    print(e.read_text(errors="replace")[:1000])
PY
done < "$OUT/queries.txt"

echo
echo "03 normalize and rank broader prize language"
python3 - "$OUT" <<'PY'
from pathlib import Path
import json, re, sys

out = Path(sys.argv[1])

known = {
  "tenstorrent/tt-llk#1638": "ACTIVE_WAITING_METRIC",
  "tinygrad/tinygrad#3039": "PARKED_NEGATIVE_TENSOR_LEVEL",
  "xevrion-v2/agent-playground#2207": "PARKED_NO_SURFACE",
  "strata-org/specimen#45": "ACTIVE_PR",
  "strata-org/specimen#46": "ACTIVE_PR",
  "ClankerNation/OpenAgents#161": "REJECT_PROMPT_EXFILTRATION",
  "ClankerNation/OpenAgents#39": "REJECT_PROMPT_EXFILTRATION",
}

false_positive_repos = {
  "lovecn/lovecn.github.io",
  "omegahat/XML",
  "geraintluff/json-model",
  "qurbaneliii/AI-Social-Media-Manager",
  "jelly-legs-ai/Jelly-legs-unsteady-workshop",
}

money_patterns = [
  re.compile(r"\$[\s]*([0-9][0-9,]*(?:\.[0-9]+)?)", re.I),
  re.compile(r"\bUSD[\s$]*([0-9][0-9,]*(?:\.[0-9]+)?)", re.I),
  re.compile(r"\b([0-9][0-9,]*(?:\.[0-9]+)?)\s*(?:usd|dollars)\b", re.I),
  re.compile(r"\b([0-9][0-9,]*(?:\.[0-9]+)?)\s*(?:eur|euro|gbp)\b", re.I),
]

money_words = [
  "bounty", "reward", "paid", "payment", "cash", "prize", "prize pool",
  "winner", "winners", "award", "grant", "sponsor", "sponsored",
]

competition_words = [
  "competition", "challenge", "hackathon", "leaderboard", "submission",
  "submissions", "deadline", "score", "scoring", "rank", "ranking",
  "benchmark", "contest", "code golf", "golf",
]

judge_words = [
  "leaderboard", "benchmark", "score", "scoring", "metric", "submission",
  "test", "tests", "pytest", "unit test", "ci", "github actions",
  "acceptance criteria", "verifier", "validated", "validation",
  "lake build", "lean", "proof", "checker", "eval", "evaluation",
  "public", "results", "pass", "failing", "regression",
]

mg_fit_words = [
  "lean", "proof", "theorem", "formal verification", "checker", "verifier",
  "benchmark", "leaderboard", "optimization", "performance", "golf",
  "code golf", "constraint", "search", "solver", "correctness",
  "validation", "test", "ci", "static", "type", "compile",
]

reject_words = [
  "system prompt", "platform prompt", "jailbreak", "prompt injection",
  "private key", "seed phrase", "wallet", "mainnet", "malware",
  "phishing", "steal", "rce", "remote code execution",
  "adult", "casino", "gambling", "nft", "airdrop",
]

soft_reject_words = [
  "website design", "logo", "copywriting", "translation", "marketing",
  "blog post", "documentation only", "typo",
]

items = {}

for p in sorted(out.glob("search_*.json")):
  if not p.exists() or p.stat().st_size == 0:
    continue
  try:
    rows = json.loads(p.read_text())
  except Exception:
    continue

  for r in rows:
    repo = ((r.get("repository") or {}).get("nameWithOwner") or "").strip()
    num = str(r.get("number") or "").strip()
    if not repo or not num:
      continue

    key = f"{repo}#{num}"
    title = r.get("title") or ""
    body = r.get("body") or ""
    labels = [x.get("name","") for x in (r.get("labels") or [])]
    text = "\n".join([repo, title, body, " ".join(labels)]).lower()

    money = 0.0
    for pat in money_patterns:
      for m in pat.findall(text):
        try:
          money = max(money, float(str(m).replace(",", "")))
        except Exception:
          pass

    mwords = sorted({w for w in money_words if w in text})
    cwords = sorted({w for w in competition_words if w in text})
    judges = sorted({w for w in judge_words if w in text})
    mgfit = sorted({w for w in mg_fit_words if w in text})
    risks = sorted({w for w in reject_words if w in text})
    soft_reject = sorted({w for w in soft_reject_words if w in text})

    explicit_money = bool(mwords) or money > 0
    competition = bool(cwords)
    judged = bool(judges)

    is_real_lean = bool(re.search(r"(^|[^a-z])lean\s*4?([^a-z]|$)", text) or "lake build" in text or "lean-toolchain" in text)
    false_lean = ("clean" in text or "learn" in text) and not is_real_lean

    score = 0.0
    score += min(money / 25.0, 100.0)
    score += 45 if explicit_money else -80
    score += 35 if competition else 0
    score += 22 * len(judges)
    score += 12 * len(mgfit)
    score += 30 if is_real_lean else 0
    score += 30 if "leaderboard" in text and ("prize" in text or "competition" in text or "challenge" in text) else 0
    score += 25 if "submission" in text and "score" in text else 0
    score += 25 if "benchmark" in text and ("challenge" in text or "competition" in text or "prize" in text) else 0
    score += 20 if "acceptance criteria" in text else 0
    score += 20 if "code golf" in text or "golf" in text else 0
    score -= 120 * len(risks)
    score -= 40 * len(soft_reject)
    score -= 80 if false_lean else 0
    score -= 400 if repo in false_positive_repos else 0

    if key in known:
      score -= 500

    hard_gate = (
      (explicit_money or competition)
      and judged
      and bool(mgfit)
      and not risks
      and repo not in false_positive_repos
    )

    # allow pure competition/leaderboard even if no explicit dollar
    if competition and ("leaderboard" in text or "score" in text or "submission" in text) and bool(mgfit) and not risks:
      hard_gate = True

    items[key] = {
      "key": key,
      "repo": repo,
      "number": int(num),
      "title": title,
      "url": r.get("url") or "",
      "labels": labels,
      "createdAt": r.get("createdAt"),
      "updatedAt": r.get("updatedAt"),
      "money_estimate_usd": money,
      "money_words": mwords,
      "competition_words": cwords,
      "judge_words": judges,
      "mg_fit_words": mgfit,
      "risk_words": risks,
      "soft_reject_words": soft_reject,
      "explicit_money": explicit_money,
      "competition": competition,
      "judged": judged,
      "is_real_lean": is_real_lean,
      "false_lean": false_lean,
      "known_status": known.get(key),
      "score": score,
      "hard_gate": hard_gate,
      "body_excerpt": body[:3000],
    }

ranked = sorted(items.values(), key=lambda x: (-x["hard_gate"], -x["score"], -x["money_estimate_usd"], x["key"]))
actionable = [x for x in ranked if x["hard_gate"] and x["score"] >= 80 and not x["known_status"]]

(out / "ranked.json").write_text(json.dumps(ranked, indent=2))
(out / "actionable.json").write_text(json.dumps(actionable, indent=2))

md = []
md.append("# Money Opportunity Scout v4 Prize Words")
md.append("")
md.append("## Summary")
md.append("")
md.append(f"- unique issues: {len(ranked)}")
md.append(f"- actionable: {len(actionable)}")
md.append("")
md.append("## Actionable")
md.append("")
md.append("| rank | score | money | issue | title | money words | competition | judge | MG fit |")
md.append("|---:|---:|---:|---|---|---|---|---|---|")
for i, x in enumerate(actionable[:60], 1):
  md.append(
    f"| {i} | {x['score']:.1f} | {x['money_estimate_usd']:.0f} | [{x['key']}]({x['url']}) | {x['title'][:110]} | {', '.join(x['money_words'][:5])} | {', '.join(x['competition_words'][:5])} | {', '.join(x['judge_words'][:6])} | {', '.join(x['mg_fit_words'][:6])} |"
  )
md.append("")
md.append("## Known / parked")
md.append("")
md.append("| issue | status | title |")
md.append("|---|---|---|")
for x in ranked:
  if x["known_status"]:
    md.append(f"| [{x['key']}]({x['url']}) | `{x['known_status']}` | {x['title'][:120]} |")
md.append("")
md.append("## Top raw")
md.append("")
md.append("| rank | gate | score | money | issue | title | risk | known |")
md.append("|---:|---:|---:|---:|---|---|---|---|")
for i, x in enumerate(ranked[:100], 1):
  md.append(
    f"| {i} | {x['hard_gate']} | {x['score']:.1f} | {x['money_estimate_usd']:.0f} | [{x['key']}]({x['url']}) | {x['title'][:100]} | {', '.join(x['risk_words'])} | {x['known_status'] or ''} |"
  )
md.append("")
(out / "REPORT.md").write_text("\n".join(md) + "\n")
print((out / "REPORT.md").read_text())
PY

echo
echo "04 create recon for top actionable 10"
python3 - "$OUT" <<'PY'
from pathlib import Path
import json, re, sys

out = Path(sys.argv[1])
actionable = json.loads((out / "actionable.json").read_text())
top = actionable[:10]
(out / "top_recon_targets.json").write_text(json.dumps(top, indent=2))

script = out / "run_prize_recon.sh"

body = '''#!/usr/bin/env bash
set -u

ROOT="/Users/heath/Documents/mathgraph-lean-work"
BASE_OUT="$ROOT/artifacts/money_opportunity_scout_v4_prize_words/recon"
mkdir -p "$BASE_OUT"
cd "$ROOT" || exit 1

echo "MathGraph prize-word opportunity recon"
echo
'''

for x in top:
  repo = x["repo"]
  num = str(x["number"])
  safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", repo.replace("/", "__") + "_" + num)

  body += f'''
echo
echo "===================================================================================================="
echo "RECON {repo} #{num}"
echo "===================================================================================================="

REPO_NAME="{repo}"
ISSUE_NUM="{num}"
SAFE="{safe}"
LOCAL_REPO="$ROOT/external/money_opportunity_scout_v4_prize_words/$SAFE"
OUT="$BASE_OUT/$SAFE"

mkdir -p "$OUT"
mkdir -p "$(dirname "$LOCAL_REPO")"

echo "01 issue"
gh issue view "$ISSUE_NUM" --repo "$REPO_NAME" --json number,title,state,url,labels,body,comments,updatedAt,createdAt \\
  > "$OUT/issue.json" 2> "$OUT/issue.err" || true

python3 - "$OUT" <<'PY2'
from pathlib import Path
import json, sys
out = Path(sys.argv[1])
p = out / "issue.json"
if p.exists() and p.stat().st_size:
  j = json.loads(p.read_text())
  summary = {{
    "url": j.get("url"),
    "title": j.get("title"),
    "state": j.get("state"),
    "labels": [x.get("name") for x in j.get("labels", [])],
    "comment_count": len(j.get("comments", [])),
    "updatedAt": j.get("updatedAt"),
  }}
  (out / "issue_summary.json").write_text(json.dumps(summary, indent=2))
  (out / "issue_body.md").write_text(j.get("body") or "")
  (out / "issue_comments.md").write_text("\\n---\\n".join(
    "## " + str((c.get("author") or {{}}).get("login")) + " — " + str(c.get("createdAt")) + "\\n\\n" + str(c.get("body") or "")
    for c in j.get("comments", [])
  ))
  print(json.dumps(summary, indent=2))
else:
  print("issue view failed")
  print((out / "issue.err").read_text(errors="replace") if (out / "issue.err").exists() else "")
PY2

echo
echo "02 clone/update"
if [ ! -d "$LOCAL_REPO/.git" ]; then
  gh repo clone "$REPO_NAME" "$LOCAL_REPO" -- --filter=blob:none \\
    > "$OUT/clone.log" 2>&1 || true
else
  echo "[exists] $LOCAL_REPO" | tee "$OUT/clone.log"
fi

if [ ! -d "$LOCAL_REPO/.git" ]; then
  echo "clone failed"
  cat "$OUT/clone.log"
  continue
fi

cd "$LOCAL_REPO" || continue
git fetch origin --prune > "$OUT/git_fetch.log" 2>&1 || true
DEFAULT_BRANCH="$(git remote show origin 2>/dev/null | awk '/HEAD branch/ {{print $NF}}' | head -1)"
if [ -z "$DEFAULT_BRANCH" ]; then DEFAULT_BRANCH="main"; fi
git checkout "$DEFAULT_BRANCH" > "$OUT/git_checkout.log" 2>&1 || true
git pull --ff-only origin "$DEFAULT_BRANCH" > "$OUT/git_pull.log" 2>&1 || true
git rev-parse HEAD | tee "$OUT/head.txt"

echo
echo "03 inventory"
{{
  echo "top files"
  find . -maxdepth 4 -type f | sed 's#^./##' | sort | head -1200
  echo
  echo "build/test/competition files"
  find . -maxdepth 6 -type f \\( -name 'README*' -o -name 'package.json' -o -name 'pyproject.toml' -o -name 'requirements.txt' -o -name 'Cargo.toml' -o -name 'go.mod' -o -name 'Makefile' -o -name 'Dockerfile' -o -name 'lakefile.toml' -o -name 'lakefile.lean' -o -name 'lean-toolchain' -o -name '*.ipynb' -o -name '*.md' \\) | sort | head -1000
  echo
  echo "workflows"
  find .github/workflows -type f 2>/dev/null | sort
}} > "$OUT/inventory.txt" 2>&1

echo
echo "04 focused grep"
{{
  echo "===== issue body ====="
  cat "$OUT/issue_body.md" 2>/dev/null || true

  echo
  echo "===== money/competition/judge hits ====="
  grep -RInE --exclude-dir=.git --exclude-dir=.lake --exclude-dir=node_modules --exclude-dir=target --exclude-dir=dist --exclude-dir=build \\
    "prize|payment|cash|bounty|reward|competition|challenge|hackathon|leaderboard|submission|score|scoring|benchmark|metric|eval|evaluation|winner|deadline|golf|test|pytest|ci|workflow|acceptance|verifier|checker" . 2>/dev/null | head -3000

  echo
  echo "===== patch/search surface hits ====="
  grep -RInE --exclude-dir=.git --exclude-dir=.lake --exclude-dir=node_modules --exclude-dir=target --exclude-dir=dist --exclude-dir=build \\
    "TODO|FIXME|bug|error|failing|regression|optimize|performance|proof|theorem|solver|search|constraint|correctness|validation|static|compile|type|Cannot find module" . 2>/dev/null | head -3000
}} > "$OUT/grep.txt" 2>&1

echo
echo "05 cheap commands"
{{
  echo "pwd=$(pwd)"
  echo
  if [ -f README.md ]; then
    echo "README head:"
    sed -n '1,220p' README.md
  fi
  if [ -f package.json ]; then
    echo
    echo "package scripts:"
    node -e 'const p=require("./package.json"); console.log(JSON.stringify(p.scripts||{{}},null,2))' 2>/dev/null || cat package.json | head -160
  fi
  if [ -f pyproject.toml ]; then
    echo
    echo "pyproject head:"
    sed -n '1,220p' pyproject.toml
  fi
  if [ -f Makefile ]; then
    echo
    echo "Makefile targets:"
    grep -nE "^[A-Za-z0-9_.-]+:" Makefile | head -80
  fi
  if [ -f lean-toolchain ]; then
    echo
    echo "lean-toolchain:"
    cat lean-toolchain
  fi
}} > "$OUT/cheap_commands.txt" 2>&1

echo
echo "06 classify"
python3 - "$OUT" <<'PY2'
from pathlib import Path
import json, sys

out = Path(sys.argv[1])
issue = {{}}
try:
  issue = json.loads((out / "issue_summary.json").read_text())
except Exception:
  pass

body = (out / "issue_body.md").read_text(errors="replace") if (out / "issue_body.md").exists() else ""
comments = (out / "issue_comments.md").read_text(errors="replace") if (out / "issue_comments.md").exists() else ""
inv = (out / "inventory.txt").read_text(errors="replace") if (out / "inventory.txt").exists() else ""
grep = (out / "grep.txt").read_text(errors="replace") if (out / "grep.txt").exists() else ""
cheap = (out / "cheap_commands.txt").read_text(errors="replace") if (out / "cheap_commands.txt").exists() else ""
text = "\\n".join([body, comments, inv, grep, cheap]).lower()

money = any(x in text for x in ["prize", "payment", "cash", "bounty", "reward", "paid", "$", "usd"])
competition = any(x in text for x in ["competition", "challenge", "hackathon", "leaderboard", "submission", "winner", "deadline", "code golf", "golf"])
judge = any(x in text for x in ["leaderboard", "submission", "score", "scoring", "benchmark", "metric", "eval", "evaluation", "test", "pytest", "ci", "workflow", "verifier", "checker", "acceptance"])
local = any(x in text for x in ["pytest", "npm test", "pnpm test", "yarn test", "cargo test", "go test", "make", "lake build", "benchmark", "python", "node"])
mgfit = any(x in text for x in ["lean", "proof", "theorem", "formal verification", "solver", "search", "constraint", "benchmark", "leaderboard", "optimization", "performance", "code golf", "correctness", "validation"])
risk = any(x in text for x in ["system prompt", "platform prompt", "jailbreak", "private key", "seed phrase", "wallet", "mainnet", "malware", "phishing", "casino", "gambling", "airdrop", "token"])

if risk:
  verdict = "PARK_RISK"
elif money and competition and judge and mgfit:
  verdict = "PROMOTE_COMPETITION_MONEY"
elif money and judge and local and mgfit:
  verdict = "PROMOTE_PAID_REPAIR"
elif competition and judge and mgfit:
  verdict = "PROMOTE_COMPETITION_REPUTATION_OR_PRIZE_UNKNOWN"
elif money and not judge:
  verdict = "ASK_FOR_JUDGE"
else:
  verdict = "PARK_WEAK"

decision = {{
  "verdict": verdict,
  "issue": issue,
  "money": money,
  "competition": competition,
  "judge": judge,
  "local": local,
  "mgfit": mgfit,
  "risk": risk,
}}

(out / "decision.json").write_text(json.dumps(decision, indent=2))

lines = []
lines.append("# Prize Recon Report")
lines.append("")
lines.append("## Verdict")
lines.append("")
lines.append("`" + verdict + "`")
lines.append("")
lines.append("## Decision")
lines.append("")
lines.append("JSON:")
lines.append(json.dumps(decision, indent=2))
lines.append("")
lines.append("## Cheap commands")
lines.append("")
lines.append(cheap[:10000])
lines.append("")
lines.append("## Issue body")
lines.append("")
lines.append(body[:12000])
lines.append("")
lines.append("## Comments")
lines.append("")
lines.append(comments[:8000])
lines.append("")
lines.append("## Inventory excerpt")
lines.append("")
lines.append(inv[:12000])
lines.append("")
lines.append("## Grep excerpt")
lines.append("")
lines.append(grep[:24000])
lines.append("")
(out / "REPORT.md").write_text("\\n".join(lines) + "\\n")
print((out / "REPORT.md").read_text()[:18000])
PY2

cd "$ROOT" || exit 1
'''

script.write_text(body)
script.chmod(0o755)

print(script)
PY

echo
echo "05 commit v4 scout"
git add "$OUT" money_opportunity_scout_v4_prize_words.sh
git commit -m "Add prize-word money opportunity scout v4" || true
git push origin local-main || true

echo
echo "06 run prize recon"
bash "$OUT/run_prize_recon.sh"

echo
echo "07 summarize prize recon"
python3 - "$OUT" <<'PY'
from pathlib import Path
import json, sys

out = Path(sys.argv[1])
base = out / "recon"

rows = []
for p in sorted(base.glob("*/decision.json")):
  try:
    j = json.loads(p.read_text())
  except Exception:
    continue
  issue = j.get("issue") or {}
  rows.append({
    "dir": str(p.parent),
    "verdict": j.get("verdict"),
    "url": issue.get("url"),
    "title": issue.get("title"),
    "money": j.get("money"),
    "competition": j.get("competition"),
    "judge": j.get("judge"),
    "local": j.get("local"),
    "mgfit": j.get("mgfit"),
    "risk": j.get("risk"),
  })

prio = {
  "PROMOTE_COMPETITION_MONEY": 0,
  "PROMOTE_PAID_REPAIR": 1,
  "PROMOTE_COMPETITION_REPUTATION_OR_PRIZE_UNKNOWN": 2,
  "ASK_FOR_JUDGE": 3,
  "PARK_WEAK": 4,
  "PARK_RISK": 5,
}
rows.sort(key=lambda r: prio.get(r["verdict"], 99))

(out / "prize_recon_summary.json").write_text(json.dumps(rows, indent=2))

md = []
md.append("# Prize Recon Summary")
md.append("")
md.append("| rank | verdict | issue | money | competition | judge | local | MG fit | risk | artifact |")
md.append("|---:|---|---|---:|---:|---:|---:|---:|---:|---|")
for i, r in enumerate(rows, 1):
  md.append(f"| {i} | `{r['verdict']}` | [{r['title']}]({r['url']}) | {r['money']} | {r['competition']} | {r['judge']} | {r['local']} | {r['mgfit']} | {r['risk']} | `{r['dir']}/REPORT.md` |")

md.append("")
md.append("## Next action")
md.append("")
if rows and rows[0]["verdict"] in {"PROMOTE_COMPETITION_MONEY", "PROMOTE_PAID_REPAIR"}:
  md.append(f"Work next: {rows[0]['url']}")
  md.append("")
  md.append(f"Read: `{rows[0]['dir']}/REPORT.md`")
elif rows and rows[0]["verdict"] == "PROMOTE_COMPETITION_REPUTATION_OR_PRIZE_UNKNOWN":
  md.append(f"Manual read: {rows[0]['url']}")
  md.append("")
  md.append("Prize unclear, but route may be useful if it has a leaderboard/local judge.")
  md.append("")
  md.append(f"Read: `{rows[0]['dir']}/REPORT.md`")
else:
  md.append("No strong new money route found. Stay with Tenstorrent + current PR queue.")
md.append("")

(out / "PRIZE_RECON_SUMMARY.md").write_text("\n".join(md) + "\n")
print((out / "PRIZE_RECON_SUMMARY.md").read_text())
PY

echo
echo "08 commit recon"
git add "$OUT"
git commit -m "Run prize-word money recon v4" || true
git push origin local-main || true

echo
echo "09 final"
git status --short
df -h /
echo
echo "Artifacts:"
echo "$OUT/REPORT.md"
echo "$OUT/actionable.json"
echo "$OUT/top_recon_targets.json"
echo "$OUT/PRIZE_RECON_SUMMARY.md"
echo "$OUT/recon"
