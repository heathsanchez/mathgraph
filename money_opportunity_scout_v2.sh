#!/usr/bin/env bash
set -u

ROOT="/Users/heath/Documents/mathgraph-lean-work"
OUT="$ROOT/artifacts/money_opportunity_scout_v2"

mkdir -p "$OUT"
cd "$ROOT" || exit 1

echo "MathGraph Money Opportunity Scout v2 — find more, but only real judged routes"
echo

echo "01 status"
{
  date -u +"%Y-%m-%dT%H:%M:%SZ"
  df -h /
  git status --short
} | tee "$OUT/status_start.txt"

echo
echo "02 GitHub issue searches"

cat > "$OUT/queries.txt" <<'EOF'
bounty Lean proof repair
bounty Lean4 proof
bounty formal verification
bounty theorem proving
bounty lake build Lean
paid Lean proof
paid formal verification
reward Lean theorem
reward proof assistant
"help wanted" "Lean 4" "sorry"
"good first issue" "Lean 4" theorem
"help wanted" "lake build"
"bounty" "pytest" "benchmark"
"bounty" "performance" "benchmark" "local"
"bounty" "failing test"
"bounty" "validation" "test"
"bounty" "CI" "fix"
EOF

i=0
while IFS= read -r Q; do
  [ -z "$Q" ] && continue
  i=$((i+1))
  SAFE="$(printf "%03d" "$i")"
  echo
  echo "===== query $SAFE: $Q ====="
  gh search issues "$Q" --state open --limit 50 --json repository,title,number,url,body,labels,createdAt,updatedAt,state \
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
    for r in rows[:5]:
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
echo "03 normalize, rank, and filter"
python3 - "$OUT" <<'PY'
from pathlib import Path
import json, re, sys
from collections import defaultdict

out = Path(sys.argv[1])

known_bad_or_parked = {
  "tenstorrent/tt-llk#1638": "already_active_waiting_metric",
  "tinygrad/tinygrad#3039": "already_parked_tensor_level_negative",
  "xevrion-v2/agent-playground#2207": "already_parked_no_patch_surface",
  "strata-org/specimen#45": "already_active_pr",
  "strata-org/specimen#46": "already_active_pr",
  "ClankerNation/OpenAgents#161": "prompt_exfiltration_risk",
  "ClankerNation/OpenAgents#39": "prompt_exfiltration_risk",
}

money_patterns = [
  re.compile(r"\$[\s]*([0-9][0-9,]*(?:\.[0-9]+)?)", re.I),
  re.compile(r"\bUSD[\s]*([0-9][0-9,]*(?:\.[0-9]+)?)", re.I),
  re.compile(r"\b([0-9][0-9,]*(?:\.[0-9]+)?)\s*(?:usd|dollars)\b", re.I),
]

strong_positive = [
  "bounty", "reward", "paid", "$", "usd",
  "failing test", "failing tests", "regression", "ci", "benchmark",
  "pytest", "lake build", "lean", "lean4", "proof", "theorem",
  "sorry", "admit", "formal verification", "verifier", "acceptance criteria",
  "reproduce", "local", "unit test", "cargo test", "go test", "make test",
  "performance", "validation", "invariant", "correctness",
]

hard_judge = [
  "lake build", "lean", "pytest", "cargo test", "go test", "make test",
  "benchmark", "ci", "unit test", "tests", "verifier", "reproduce",
]

risk_terms = [
  "system prompt", "platform prompt", "jailbreak", "prompt injection",
  "private key", "seed phrase", "wallet", "mainnet", "exploit",
  "rce", "remote code execution", "malware", "phishing", "steal",
  "token", "api key", "credential",
]

vague_terms = [
  "improve agent", "make better", "enhance", "refactor entire",
  "large rewrite", "roadmap", "discussion", "proposal",
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
    url = r.get("url") or ""
    text = " ".join([repo, title, body, " ".join(labels)]).lower()

    money = 0.0
    for pat in money_patterns:
      for m in pat.findall(text):
        try:
          money = max(money, float(m.replace(",", "")))
        except Exception:
          pass

    pos = sorted({t for t in strong_positive if t in text})
    judge = sorted({t for t in hard_judge if t in text})
    risk = sorted({t for t in risk_terms if t in text})
    vague = sorted({t for t in vague_terms if t in text})

    score = 0.0
    score += min(money / 50.0, 60.0)
    score += 8 * len(pos)
    score += 12 * len(judge)
    if money >= 250:
      score += 20
    if money >= 1000:
      score += 30
    if "lean" in text or "lean4" in text or "lake build" in text:
      score += 35
    if "sorry" in text or "admit" in text:
      score += 25
    if "benchmark" in text and ("bounty" in text or money > 0):
      score += 20
    if "acceptance criteria" in text:
      score += 20
    if "help wanted" in text:
      score += 8
    score -= 80 * len(risk)
    score -= 15 * len(vague)

    parked = known_bad_or_parked.get(key)
    if parked:
      score -= 500

    items[key] = {
      "key": key,
      "repo": repo,
      "number": int(num),
      "title": title,
      "url": url,
      "labels": labels,
      "createdAt": r.get("createdAt"),
      "updatedAt": r.get("updatedAt"),
      "money_estimate_usd": money,
      "score": score,
      "positive_terms": pos,
      "judge_terms": judge,
      "risk_terms": risk,
      "vague_terms": vague,
      "parked": parked,
      "body_excerpt": body[:2500],
    }

ranked = sorted(items.values(), key=lambda x: (-x["score"], -x["money_estimate_usd"], x["repo"], x["number"]))
actionable = [
  x for x in ranked
  if not x["parked"]
  and not x["risk_terms"]
  and x["score"] >= 35
  and (x["judge_terms"] or x["money_estimate_usd"] >= 250 or "lean" in " ".join(x["positive_terms"]))
]

(out / "ranked_opportunities.json").write_text(json.dumps(ranked, indent=2))
(out / "actionable_opportunities.json").write_text(json.dumps(actionable, indent=2))

md = []
md.append("# Money Opportunity Scout v2")
md.append("")
md.append("## Summary")
md.append("")
md.append(f"- total unique issues: {len(ranked)}")
md.append(f"- actionable after filter: {len(actionable)}")
md.append("")
md.append("## Top actionable")
md.append("")
md.append("| rank | score | money | issue | title | judge terms | flags |")
md.append("|---:|---:|---:|---|---|---|---|")
for i, x in enumerate(actionable[:40], 1):
  md.append(
    f"| {i} | {x['score']:.1f} | {x['money_estimate_usd']:.0f} | [{x['key']}]({x['url']}) | {x['title'][:110]} | {', '.join(x['judge_terms'][:6])} | {', '.join(x['positive_terms'][:8])} |"
  )
md.append("")
md.append("## Top raw")
md.append("")
md.append("| rank | score | money | issue | title | parked | risk |")
md.append("|---:|---:|---:|---|---|---|---|")
for i, x in enumerate(ranked[:60], 1):
  md.append(
    f"| {i} | {x['score']:.1f} | {x['money_estimate_usd']:.0f} | [{x['key']}]({x['url']}) | {x['title'][:100]} | {x['parked'] or ''} | {', '.join(x['risk_terms'])} |"
  )
md.append("")
(out / "REPORT.md").write_text("\n".join(md) + "\n")

print((out / "REPORT.md").read_text())
PY

echo
echo "04 choose top 5 recon targets"
python3 - "$OUT" <<'PY'
from pathlib import Path
import json, sys, re

out = Path(sys.argv[1])
actionable = json.loads((out / "actionable_opportunities.json").read_text())

top = actionable[:5]
(out / "top5_recon_targets.json").write_text(json.dumps(top, indent=2))

print(json.dumps([
  {
    "rank": i+1,
    "key": x["key"],
    "score": x["score"],
    "money": x["money_estimate_usd"],
    "title": x["title"],
    "url": x["url"],
  }
  for i, x in enumerate(top)
], indent=2))
PY

echo
echo "05 generate multi-recon script for top 5"
python3 - "$OUT" <<'PY'
from pathlib import Path
import json, re, sys

out = Path(sys.argv[1])
top = json.loads((out / "top5_recon_targets.json").read_text())

script = out / "run_top5_recon.sh"

entries = []
for x in top:
  repo = x["repo"]
  num = str(x["number"])
  safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", repo.replace("/", "__") + "_" + num)
  entries.append((repo, num, safe))

body = r'''#!/usr/bin/env bash
set -u

ROOT="/Users/heath/Documents/mathgraph-lean-work"
BASE_OUT="$ROOT/artifacts/money_opportunity_scout_v2/recon"
mkdir -p "$BASE_OUT"
cd "$ROOT" || exit 1

echo "MathGraph top-5 opportunity recon"
echo

'''

for repo, num, safe in entries:
  body += f'''
echo
echo "===================================================================================================="
echo "RECON {repo} #{num}"
echo "===================================================================================================="

REPO_NAME="{repo}"
ISSUE_NUM="{num}"
SAFE="{safe}"
LOCAL_REPO="$ROOT/external/money_opportunity_scout_v2/$SAFE"
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
  print(json.dumps(summary, indent=2))
else:
  print("issue view failed")
  print((out / "issue.err").read_text(errors="replace") if (out / "issue.err").exists() else "")
PY2

echo
echo "02 clone/update shallow"
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
  find . -maxdepth 3 -type f | sed 's#^./##' | sort | head -600
  echo
  echo "build/test files"
  find . -maxdepth 5 -type f \\( -name 'lakefile.toml' -o -name 'lakefile.lean' -o -name 'lean-toolchain' -o -name 'package.json' -o -name 'pyproject.toml' -o -name 'Cargo.toml' -o -name 'go.mod' -o -name 'Makefile' -o -name '.github' -o -name 'README*' \\) | sort
}} > "$OUT/inventory.txt" 2>&1

echo
echo "04 grep judge and surface"
{{
  echo "===== judge hits ====="
  grep -RInE --exclude-dir=.git --exclude-dir=.lake --exclude-dir=node_modules --exclude-dir=target --exclude-dir=dist --exclude-dir=build \\
    "lake build|lean-toolchain|sorry|admit|pytest|unittest|vitest|jest|cargo test|go test|make test|benchmark|criterion|CI|workflow|failing|regression" . 2>/dev/null | head -2500

  echo
  echo "===== issue/surface hits ====="
  grep -RInE --exclude-dir=.git --exclude-dir=.lake --exclude-dir=node_modules --exclude-dir=target --exclude-dir=dist --exclude-dir=build \\
    "bounty|reward|TODO|FIXME|validate|validation|proof|theorem|invariant|correctness|performance|optimize|bug|error|failing|regression" . 2>/dev/null | head -2500
}} > "$OUT/grep.txt" 2>&1

echo
echo "05 classify"
python3 - "$OUT" <<'PY2'
from pathlib import Path
import json, sys, re

out = Path(sys.argv[1])
issue = {{}}
try:
  issue = json.loads((out / "issue_summary.json").read_text())
except Exception:
  pass

body = (out / "issue_body.md").read_text(errors="replace") if (out / "issue_body.md").exists() else ""
inv = (out / "inventory.txt").read_text(errors="replace") if (out / "inventory.txt").exists() else ""
grep = (out / "grep.txt").read_text(errors="replace") if (out / "grep.txt").exists() else ""
text = "\\n".join([body, inv, grep]).lower()

has_lean = any(x in text for x in ["lean-toolchain", "lakefile", "lake build", ".lean", "sorry", "admit"])
has_tests = any(x in text for x in ["pytest", "unittest", "vitest", "jest", "cargo test", "go test", "make test", "lake build"])
has_benchmark = "benchmark" in text or "criterion" in text
has_money = "bounty" in text or "$" in text or "reward" in text or "paid" in text
has_surface = len(grep.strip()) > 800
risk = any(x in text for x in ["system prompt", "private key", "seed phrase", "jailbreak", "malware", "phishing"])
no_surface = not has_surface

if risk:
  verdict = "PARK_RISK"
elif has_lean and has_tests and has_surface:
  verdict = "PROMOTE_LEAN_RECON"
elif has_money and has_tests and has_surface:
  verdict = "PROMOTE_MONEY_RECON"
elif has_tests and has_surface:
  verdict = "MAYBE_RECON"
elif no_surface:
  verdict = "PARK_NO_SURFACE"
else:
  verdict = "MAYBE_NEEDS_MANUAL_READ"

decision = {{
  "verdict": verdict,
  "issue": issue,
  "has_lean": has_lean,
  "has_tests": has_tests,
  "has_benchmark": has_benchmark,
  "has_money": has_money,
  "has_surface": has_surface,
  "risk": risk,
}}

(out / "decision.json").write_text(json.dumps(decision, indent=2))

lines = []
lines.append("# Recon Report")
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
lines.append("## Issue body excerpt")
lines.append("")
lines.append(body[:7000])
lines.append("")
lines.append("## Inventory excerpt")
lines.append("")
lines.append(inv[:9000])
lines.append("")
lines.append("## Grep excerpt")
lines.append("")
lines.append(grep[:18000])
lines.append("")
(out / "REPORT.md").write_text("\\n".join(lines) + "\\n")
print((out / "REPORT.md").read_text()[:12000])
PY2

cd "$ROOT" || exit 1
'''
script.write_text(body)
script.chmod(0o755)

print(script)
PY

echo
echo "06 commit scout artifacts"
git add "$OUT" money_opportunity_scout_v2.sh
git commit -m "Add money opportunity scout v2" || true
git push origin local-main || true

echo
echo "07 run top5 recon now"
bash "$OUT/run_top5_recon.sh"

echo
echo "08 summarize top5 recon"
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
    "has_lean": j.get("has_lean"),
    "has_tests": j.get("has_tests"),
    "has_money": j.get("has_money"),
    "has_surface": j.get("has_surface"),
    "risk": j.get("risk"),
  })

priority = {
  "PROMOTE_LEAN_RECON": 0,
  "PROMOTE_MONEY_RECON": 1,
  "MAYBE_RECON": 2,
  "MAYBE_NEEDS_MANUAL_READ": 3,
  "PARK_NO_SURFACE": 4,
  "PARK_RISK": 5,
}
rows.sort(key=lambda r: priority.get(r["verdict"], 99))

(out / "top5_recon_summary.json").write_text(json.dumps(rows, indent=2))

md = []
md.append("# Top 5 Recon Summary")
md.append("")
md.append("| rank | verdict | issue | lean | tests | money | surface | risk | artifact |")
md.append("|---:|---|---|---:|---:|---:|---:|---:|---|")
for i, r in enumerate(rows, 1):
  md.append(f"| {i} | `{r['verdict']}` | [{r['title']}]({r['url']}) | {r['has_lean']} | {r['has_tests']} | {r['has_money']} | {r['has_surface']} | {r['risk']} | `{r['dir']}/REPORT.md` |")
md.append("")
if rows:
  top = rows[0]
  md.append("## Next action")
  md.append("")
  if top["verdict"] in {"PROMOTE_LEAN_RECON", "PROMOTE_MONEY_RECON"}:
    md.append(f"Work next: {top['url']}")
    md.append("")
    md.append(f"Read: `{top['dir']}/REPORT.md`")
  else:
    md.append("No automatic patch target. Manual read top MAYBE or run broader scout.")
md.append("")

(out / "TOP5_RECON_SUMMARY.md").write_text("\n".join(md) + "\n")
print((out / "TOP5_RECON_SUMMARY.md").read_text())
PY

echo
echo "09 commit recon artifacts"
git add "$OUT"
git commit -m "Run top5 money opportunity recon v2" || true
git push origin local-main || true

echo
echo "10 final"
git status --short
df -h /
echo
echo "Artifacts:"
echo "$OUT/REPORT.md"
echo "$OUT/actionable_opportunities.json"
echo "$OUT/top5_recon_targets.json"
echo "$OUT/TOP5_RECON_SUMMARY.md"
echo "$OUT/recon"
