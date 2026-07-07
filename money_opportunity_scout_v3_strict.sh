#!/usr/bin/env bash
set -u

ROOT="/Users/heath/Documents/mathgraph-lean-work"
OUT="$ROOT/artifacts/money_opportunity_scout_v3_strict"

mkdir -p "$OUT"
cd "$ROOT" || exit 1

echo "MathGraph Money Opportunity Scout v3 STRICT — explicit money + judge only"
echo

echo "01 status"
{
  date -u +"%Y-%m-%dT%H:%M:%SZ"
  df -h /
  git status --short
} | tee "$OUT/status_start.txt"

echo
echo "02 strict GitHub searches"

cat > "$OUT/queries.txt" <<'EOF'
bounty in:title,body is:issue is:open updated:>2025-01-01
"$500" in:title,body is:issue is:open updated:>2025-01-01
"$1000" in:title,body is:issue is:open updated:>2025-01-01
"$1,000" in:title,body is:issue is:open updated:>2025-01-01
"USD" "bounty" in:title,body is:issue is:open updated:>2025-01-01
"reward" "test" in:title,body is:issue is:open updated:>2025-01-01
"bounty" "pytest" in:title,body is:issue is:open updated:>2025-01-01
"bounty" "benchmark" in:title,body is:issue is:open updated:>2025-01-01
"bounty" "CI" in:title,body is:issue is:open updated:>2025-01-01
"bounty" "acceptance criteria" in:title,body is:issue is:open updated:>2025-01-01
"bounty" "Lean" in:title,body is:issue is:open updated:>2025-01-01
"bounty" "lake build" in:title,body is:issue is:open updated:>2025-01-01
"paid" "Lean" in:title,body is:issue is:open updated:>2025-01-01
"formal verification" "bounty" in:title,body is:issue is:open updated:>2025-01-01
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
echo "03 strict rank"
python3 - "$OUT" <<'PY'
from pathlib import Path
import json, re, sys
from datetime import datetime, timezone

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

money_patterns = [
  re.compile(r"\$[\s]*([0-9][0-9,]*(?:\.[0-9]+)?)", re.I),
  re.compile(r"\bUSD[\s$]*([0-9][0-9,]*(?:\.[0-9]+)?)", re.I),
  re.compile(r"\b([0-9][0-9,]*(?:\.[0-9]+)?)\s*(?:usd|dollars)\b", re.I),
]

explicit_money_terms = [
  "bounty", "reward", "paid", "payment", "prize", "usd", "$",
]

judge_terms = [
  "acceptance criteria",
  "pytest",
  "unit test",
  "tests pass",
  "failing test",
  "regression test",
  "ci",
  "github actions",
  "benchmark",
  "score",
  "metric",
  "profiler",
  "instruction count",
  "lake build",
  "lean",
  "cargo test",
  "go test",
  "make test",
  "npm test",
  "pnpm test",
  "yarn test",
]

good_surface_terms = [
  "bug", "fix", "validation", "type error", "build fails", "failing",
  "performance", "optimize", "correctness", "invariant", "proof",
  "static export", "deployment", "cannot find module",
]

reject_terms = [
  "system prompt",
  "platform prompt",
  "jailbreak",
  "prompt injection",
  "private key",
  "seed phrase",
  "wallet",
  "mainnet",
  "token",
  "malware",
  "phishing",
  "steal",
  "exploit",
  "rce",
  "remote code execution",
]

false_positive_repos = {
  "lovecn/lovecn.github.io",
  "omegahat/XML",
  "geraintluff/json-model",
  "qurbaneliii/AI-Social-Media-Manager",
}

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
    updated = r.get("updatedAt") or ""

    text = "\n".join([repo, title, body, " ".join(labels)]).lower()

    money = 0.0
    for pat in money_patterns:
      for m in pat.findall(text):
        try:
          money = max(money, float(str(m).replace(",", "")))
        except Exception:
          pass

    explicit_money = any(t in text for t in explicit_money_terms) or money > 0
    judges = sorted({t for t in judge_terms if t in text})
    surfaces = sorted({t for t in good_surface_terms if t in text})
    risks = sorted({t for t in reject_terms if t in text})

    is_real_lean = bool(re.search(r"(^|[^a-z])lean\s*4?([^a-z]|$)", text) or "lake build" in text or "lean-toolchain" in text)
    false_lean = ("clean" in text or "learn" in text) and not is_real_lean

    score = 0.0
    score += min(money / 25.0, 80.0)
    score += 40 if explicit_money else -200
    score += 18 * len(judges)
    score += 8 * len(surfaces)
    score += 35 if is_real_lean else 0
    score += 25 if "acceptance criteria" in text else 0
    score += 25 if "benchmark" in text and explicit_money else 0
    score += 20 if "bounty" in text else 0
    score -= 120 * len(risks)
    score -= 80 if false_lean else 0
    score -= 300 if repo in false_positive_repos else 0

    if key in known:
      score -= 500

    # hard gate: explicit money and either judge or substantial bounty/acceptance text
    hard_gate = explicit_money and (bool(judges) or "acceptance criteria" in text or money >= 500)
    if risks:
      hard_gate = False
    if repo in false_positive_repos:
      hard_gate = False

    items[key] = {
      "key": key,
      "repo": repo,
      "number": int(num),
      "title": title,
      "url": r.get("url") or "",
      "labels": labels,
      "createdAt": r.get("createdAt"),
      "updatedAt": updated,
      "money_estimate_usd": money,
      "explicit_money": explicit_money,
      "judge_terms": judges,
      "surface_terms": surfaces,
      "risk_terms": risks,
      "is_real_lean": is_real_lean,
      "false_lean": false_lean,
      "known_status": known.get(key),
      "score": score,
      "hard_gate": hard_gate,
      "body_excerpt": body[:2500],
    }

ranked = sorted(items.values(), key=lambda x: (-x["hard_gate"], -x["score"], -x["money_estimate_usd"], x["key"]))
actionable = [x for x in ranked if x["hard_gate"] and x["score"] >= 40 and not x["known_status"]]

(out / "ranked.json").write_text(json.dumps(ranked, indent=2))
(out / "actionable.json").write_text(json.dumps(actionable, indent=2))

md = []
md.append("# Money Opportunity Scout v3 STRICT")
md.append("")
md.append("## Summary")
md.append("")
md.append(f"- unique issues: {len(ranked)}")
md.append(f"- actionable strict: {len(actionable)}")
md.append("")
md.append("## Actionable strict")
md.append("")
md.append("| rank | score | money | issue | title | judges | surface |")
md.append("|---:|---:|---:|---|---|---|---|")
for i, x in enumerate(actionable[:40], 1):
  md.append(f"| {i} | {x['score']:.1f} | {x['money_estimate_usd']:.0f} | [{x['key']}]({x['url']}) | {x['title'][:120]} | {', '.join(x['judge_terms'][:7])} | {', '.join(x['surface_terms'][:7])} |")
md.append("")
md.append("## Known / parked hits")
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
for i, x in enumerate(ranked[:80], 1):
  md.append(f"| {i} | {x['hard_gate']} | {x['score']:.1f} | {x['money_estimate_usd']:.0f} | [{x['key']}]({x['url']}) | {x['title'][:100]} | {', '.join(x['risk_terms'])} | {x['known_status'] or ''} |")
md.append("")
(out / "REPORT.md").write_text("\n".join(md) + "\n")
print((out / "REPORT.md").read_text())
PY

echo
echo "04 make recon script for strict actionable top 8"
python3 - "$OUT" <<'PY'
from pathlib import Path
import json, re, sys

out = Path(sys.argv[1])
actionable = json.loads((out / "actionable.json").read_text())
top = actionable[:8]
(out / "top_recon_targets.json").write_text(json.dumps(top, indent=2))

script = out / "run_strict_recon.sh"

body = '''#!/usr/bin/env bash
set -u

ROOT="/Users/heath/Documents/mathgraph-lean-work"
BASE_OUT="$ROOT/artifacts/money_opportunity_scout_v3_strict/recon"
mkdir -p "$BASE_OUT"
cd "$ROOT" || exit 1

echo "MathGraph strict money recon"
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
LOCAL_REPO="$ROOT/external/money_opportunity_scout_v3_strict/$SAFE"
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
  find . -maxdepth 4 -type f | sed 's#^./##' | sort | head -1000
  echo
  echo "build/test files"
  find . -maxdepth 6 -type f \\( -name 'lakefile.toml' -o -name 'lakefile.lean' -o -name 'lean-toolchain' -o -name 'package.json' -o -name 'pnpm-lock.yaml' -o -name 'yarn.lock' -o -name 'package-lock.json' -o -name 'pyproject.toml' -o -name 'requirements.txt' -o -name 'Cargo.toml' -o -name 'go.mod' -o -name 'Makefile' -o -name 'README*' \\) | sort
  echo
  echo "workflows"
  find .github/workflows -type f 2>/dev/null | sort
}} > "$OUT/inventory.txt" 2>&1

echo
echo "04 grep focused"
{{
  echo "===== issue terms ====="
  cat "$OUT/issue_body.md" 2>/dev/null || true

  echo
  echo "===== judge hits ====="
  grep -RInE --exclude-dir=.git --exclude-dir=.lake --exclude-dir=node_modules --exclude-dir=target --exclude-dir=dist --exclude-dir=build \\
    "pytest|unittest|vitest|jest|npm test|pnpm test|yarn test|cargo test|go test|make test|lake build|benchmark|criterion|CI|workflow|acceptance|failing|regression|Cannot find module|static export|output: export|github pages|pages artifact" . 2>/dev/null | head -2500

  echo
  echo "===== patch surface hits ====="
  grep -RInE --exclude-dir=.git --exclude-dir=.lake --exclude-dir=node_modules --exclude-dir=target --exclude-dir=dist --exclude-dir=build \\
    "TODO|FIXME|validate|validation|proof|theorem|invariant|correctness|performance|optimize|bug|error|failing|regression|static export|dynamic|api route|Cannot find module|Pages" . 2>/dev/null | head -2500
}} > "$OUT/grep.txt" 2>&1

echo
echo "05 local cheap commands"
{{
  echo "pwd=$(pwd)"
  echo
  if [ -f package.json ]; then
    echo "root package.json scripts:"
    node -e 'const p=require("./package.json"); console.log(JSON.stringify(p.scripts||{{}},null,2))' 2>/dev/null || cat package.json | head -120
  fi
  if [ -f aria-frontend/package.json ]; then
    echo
    echo "aria-frontend package.json scripts:"
    node -e 'const p=require("./aria-frontend/package.json"); console.log(JSON.stringify(p.scripts||{{}},null,2))' 2>/dev/null || cat aria-frontend/package.json | head -120
  fi
  if [ -f lean-toolchain ]; then
    echo
    echo "lean-toolchain:"
    cat lean-toolchain
  fi
  if [ -f lakefile.toml ] || [ -f lakefile.lean ]; then
    echo
    echo "lake build available"
  fi
}} > "$OUT/cheap_commands.txt" 2>&1

echo
echo "06 classify manual"
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
cheap = (out / "cheap_commands.txt").read_text(errors="replace") if (out / "cheap_commands.txt").exists() else ""
text = "\\n".join([body, inv, grep, cheap]).lower()

has_explicit_acceptance = "acceptance criteria" in text or "acceptance" in text
has_local_command = any(x in text for x in ["npm test", "pnpm test", "yarn test", "pytest", "cargo test", "go test", "lake build", "benchmark"])
has_ci = ".github/workflows" in text or "github actions" in text or "workflow" in text
has_concrete_error = any(x in text for x in ["cannot find module", "static export", "failing", "build fails", "regression", "error"])
has_money = any(x in text for x in ["bounty", "reward", "paid", "usd", "$"])
risk = any(x in text for x in ["system prompt", "private key", "seed phrase", "jailbreak", "malware", "phishing", "token", "wallet", "mainnet"])

if risk:
  verdict = "PARK_RISK"
elif has_money and has_explicit_acceptance and (has_local_command or has_ci) and has_concrete_error:
  verdict = "PATCH_CANDIDATE"
elif has_money and (has_local_command or has_ci) and has_concrete_error:
  verdict = "RECON_CANDIDATE"
elif has_money:
  verdict = "ASK_FOR_VERIFIER_OR_PARK"
else:
  verdict = "PARK_NO_MONEY"

decision = {{
  "verdict": verdict,
  "issue": issue,
  "has_explicit_acceptance": has_explicit_acceptance,
  "has_local_command": has_local_command,
  "has_ci": has_ci,
  "has_concrete_error": has_concrete_error,
  "has_money": has_money,
  "risk": risk,
}}

(out / "decision.json").write_text(json.dumps(decision, indent=2))

lines = []
lines.append("# Strict Recon Report")
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
lines.append(cheap[:8000])
lines.append("")
lines.append("## Issue body")
lines.append("")
lines.append(body[:10000])
lines.append("")
lines.append("## Inventory excerpt")
lines.append("")
lines.append(inv[:10000])
lines.append("")
lines.append("## Grep excerpt")
lines.append("")
lines.append(grep[:20000])
lines.append("")
(out / "REPORT.md").write_text("\\n".join(lines) + "\\n")
print((out / "REPORT.md").read_text()[:16000])
PY2

cd "$ROOT" || exit 1
'''

script.write_text(body)
script.chmod(0o755)
print(script)
PY

echo
echo "05 commit strict scout"
git add "$OUT" money_opportunity_scout_v3_strict.sh
git commit -m "Add strict money opportunity scout v3" || true
git push origin local-main || true

echo
echo "06 run strict recon"
bash "$OUT/run_strict_recon.sh"

echo
echo "07 summarize strict recon"
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
    "acceptance": j.get("has_explicit_acceptance"),
    "local": j.get("has_local_command"),
    "ci": j.get("has_ci"),
    "error": j.get("has_concrete_error"),
    "money": j.get("has_money"),
    "risk": j.get("risk"),
  })

prio = {
  "PATCH_CANDIDATE": 0,
  "RECON_CANDIDATE": 1,
  "ASK_FOR_VERIFIER_OR_PARK": 2,
  "PARK_NO_MONEY": 3,
  "PARK_RISK": 4,
}
rows.sort(key=lambda r: prio.get(r["verdict"], 99))

(out / "strict_recon_summary.json").write_text(json.dumps(rows, indent=2))

md = []
md.append("# Strict Recon Summary")
md.append("")
md.append("| rank | verdict | issue | acceptance | local | ci | error | money | risk | artifact |")
md.append("|---:|---|---|---:|---:|---:|---:|---:|---:|---|")
for i, r in enumerate(rows, 1):
  md.append(f"| {i} | `{r['verdict']}` | [{r['title']}]({r['url']}) | {r['acceptance']} | {r['local']} | {r['ci']} | {r['error']} | {r['money']} | {r['risk']} | `{r['dir']}/REPORT.md` |")

md.append("")
md.append("## Next action")
md.append("")
if rows and rows[0]["verdict"] == "PATCH_CANDIDATE":
  md.append(f"Patch candidate: {rows[0]['url']}")
  md.append("")
  md.append(f"Read: `{rows[0]['dir']}/REPORT.md`")
elif rows and rows[0]["verdict"] == "RECON_CANDIDATE":
  md.append(f"Manual recon candidate: {rows[0]['url']}")
  md.append("")
  md.append(f"Read: `{rows[0]['dir']}/REPORT.md`")
else:
  md.append("No safe patch candidate found. Return to current PR queue and Tenstorrent metric watch.")
md.append("")

(out / "STRICT_RECON_SUMMARY.md").write_text("\n".join(md) + "\n")
print((out / "STRICT_RECON_SUMMARY.md").read_text())
PY

echo
echo "08 commit strict recon"
git add "$OUT"
git commit -m "Run strict money opportunity recon v3" || true
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
echo "$OUT/STRICT_RECON_SUMMARY.md"
echo "$OUT/recon"
