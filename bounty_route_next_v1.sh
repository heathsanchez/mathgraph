#!/usr/bin/env bash
set -u

ROOT="/Users/heath/Documents/mathgraph-lean-work"
OUT="$ROOT/artifacts/bounty_triage_v1/bounty_route_next_v1"

mkdir -p "$OUT"
cd "$ROOT" || exit 1

echo "MathGraph bounty route next v1 — check parked triggers + choose next work target"
echo

echo "01 status"
{
  date -u +"%Y-%m-%dT%H:%M:%SZ"
  df -h /
  git status --short
} | tee "$OUT/status_start.txt"

echo
echo "02 check active parked routes"

echo "02a Strata PR #46"
gh pr view 46 --repo strata-org/specimen \
  --json number,title,state,isDraft,url,reviewDecision,mergeable,comments,reviews,statusCheckRollup,updatedAt \
  > "$OUT/strata_pr46.json" 2> "$OUT/strata_pr46.err" || true

python3 - "$OUT" <<'PY'
from pathlib import Path
import json, sys

out = Path(sys.argv[1])
p = out / "strata_pr46.json"

if not p.exists() or p.stat().st_size == 0:
  print("strata_pr46: VIEW_FAILED")
  print((out / "strata_pr46.err").read_text(errors="replace") if (out / "strata_pr46.err").exists() else "")
else:
  j = json.loads(p.read_text())
  comments = j.get("comments") or []
  reviews = j.get("reviews") or []
  rollup = j.get("statusCheckRollup") or []
  print(json.dumps({
    "url": j.get("url"),
    "state": j.get("state"),
    "draft": j.get("isDraft"),
    "reviewDecision": j.get("reviewDecision"),
    "mergeable": j.get("mergeable"),
    "comment_count": len(comments),
    "review_count": len(reviews),
    "status_count": len(rollup),
    "updatedAt": j.get("updatedAt"),
  }, indent=2))
PY

echo
echo "02b Tenstorrent issue #1638"
gh issue view 1638 --repo tenstorrent/tt-llk \
  --json number,title,state,url,comments,updatedAt \
  > "$OUT/tenstorrent_1638.json" 2> "$OUT/tenstorrent_1638.err" || true

python3 - "$OUT" <<'PY'
from pathlib import Path
import json, sys, re

out = Path(sys.argv[1])
p = out / "tenstorrent_1638.json"

if not p.exists() or p.stat().st_size == 0:
  print("tenstorrent_1638: VIEW_FAILED")
  print((out / "tenstorrent_1638.err").read_text(errors="replace") if (out / "tenstorrent_1638.err").exists() else "")
else:
  j = json.loads(p.read_text())
  comments = j.get("comments") or []
  my_comment_seen = False
  later_comments = []
  for c in comments:
    body = c.get("body") or ""
    author = (c.get("author") or {}).get("login")
    url = c.get("url")
    if "what exact local command should contributors use as the acceptance metric" in body:
      my_comment_seen = True
      continue
    if my_comment_seen:
      later_comments.append({
        "author": author,
        "createdAt": c.get("createdAt"),
        "url": url,
        "body_excerpt": body[:1200],
      })

  trigger_words = ["counter", "command", "metric", "pytest", "profiler", "instruction", "csv", "measure", "perf", "benchmark"]
  likely_answer = [
    c for c in later_comments
    if any(w in c["body_excerpt"].lower() for w in trigger_words)
  ]

  print(json.dumps({
    "url": j.get("url"),
    "state": j.get("state"),
    "updatedAt": j.get("updatedAt"),
    "comment_count": len(comments),
    "my_comment_seen": my_comment_seen,
    "later_comment_count": len(later_comments),
    "likely_metric_answer_count": len(likely_answer),
    "later_comments": later_comments[-5:],
  }, indent=2))
PY

echo
echo "03 build next-candidate route table"
python3 - "$ROOT" "$OUT" <<'PY'
from pathlib import Path
import json, re, sys

root = Path(sys.argv[1])
out = Path(sys.argv[2])

known_parked = {
  "tenstorrent/tt-llk#1638": "parked_waiting_metric",
  "tinygrad/tinygrad#3039": "parked_tensor_level_negative",
  "xevrion-v2/agent-playground#2207": "parked_no_patch_surface",
  "strata-org/specimen#45": "active_pr_waiting_review",
  "ClankerNation/OpenAgents#161": "red_flag_prompt_exfiltration",
  "ClankerNation/OpenAgents#39": "red_flag_prompt_exfiltration",
}

risk_terms = [
  "system prompt", "platform prompt", "initialization prompt", "jailbreak",
  "private key", "seed phrase", "wallet", "exploit", "rce", "remote code execution",
  "crypto bounty", "mainnet", "steal", "phishing", "malware",
]

good_terms = [
  "test", "tests", "failing", "bug", "validation", "type", "lint",
  "performance", "benchmark", "proof", "lean", "invariant", "correctness",
  "local", "repro", "regression", "unit", "ci",
]

files = [
  root / "artifacts/paid_fix_scout/paid_fix_scout_refined.json",
  root / "artifacts/paid_fix_scout/paid_fix_scout_raw.json",
  root / "artifacts/bounty_triage_v1/bounty_triage_raw.json",
]

data = None
src = None
for f in files:
  if f.exists():
    try:
      data = json.loads(f.read_text(errors="replace"))
      src = f
      break
    except Exception:
      pass

items = []

def norm_repo_issue(x):
  repo = x.get("repo") or x.get("full") or x.get("repository") or ""
  num = x.get("issue") or x.get("number") or x.get("issue_number") or ""
  full = str(repo)
  if "#" in full and not num:
    parts = full.split("#")
    full = parts[0].strip()
    num = parts[-1].strip()
  return full, str(num)

def flatten(obj):
  if isinstance(obj, list):
    return obj
  if isinstance(obj, dict):
    for k in ["results", "items", "issues", "ranked", "candidates"]:
      if isinstance(obj.get(k), list):
        return obj[k]
    # maybe dict keyed by issue
    vals = list(obj.values())
    if vals and all(isinstance(v, dict) for v in vals):
      return vals
  return []

if data is not None:
  for x in flatten(data):
    if not isinstance(x, dict):
      continue
    repo, num = norm_repo_issue(x)
    if not repo or not num:
      continue
    key = f"{repo}#{num}"

    title = str(x.get("title") or x.get("name") or "")
    url = str(x.get("url") or "")
    body = str(x.get("body") or x.get("summary") or x.get("description") or "")
    verdict = str(x.get("verdict") or x.get("label") or x.get("assessment", {}).get("verdict") or "")
    score = x.get("score")
    if score is None:
      score = x.get("assessment", {}).get("score")
    try:
      score = float(score)
    except Exception:
      score = 0.0

    money = x.get("money")
    if money is None:
      money = x.get("assessment", {}).get("money")
    try:
      money = float(money or 0)
    except Exception:
      money = 0.0

    text = " ".join([repo, num, title, body, verdict]).lower()
    risk = [t for t in risk_terms if t in text]
    good = [t for t in good_terms if t in text]
    parked = known_parked.get(key)

    route_score = score
    route_score += min(money / 100.0, 30.0)
    route_score += 4 * len(set(good))
    route_score -= 40 * len(set(risk))
    if parked:
      route_score -= 1000
    if "bounty" in text:
      route_score += 5
    if "good first issue" in text:
      route_score += 6
    if "documentation" in text or "docs" in text:
      route_score -= 8

    items.append({
      "key": key,
      "repo": repo,
      "issue": num,
      "title": title,
      "url": url,
      "verdict": verdict,
      "base_score": score,
      "money": money,
      "route_score": route_score,
      "good_terms": sorted(set(good)),
      "risk_terms": sorted(set(risk)),
      "parked": parked,
    })

items.sort(key=lambda r: (-r["route_score"], -r["money"], r["key"]))

top = items[:40]
actionable = [x for x in items if not x["parked"] and not x["risk_terms"]][:25]

result = {
  "source": str(src) if src else None,
  "candidate_count": len(items),
  "top_40": top,
  "actionable_25": actionable,
}
(out / "route_table.json").write_text(json.dumps(result, indent=2))

md = []
md.append("# Bounty Route Next v1")
md.append("")
md.append("## Source")
md.append("")
md.append(str(src) if src else "No local scout JSON found.")
md.append("")
md.append("## Known parked / active routes")
md.append("")
for k, v in known_parked.items():
  md.append(f"- `{k}` — `{v}`")
md.append("")
md.append("## Top actionable candidates")
md.append("")
md.append("| rank | route score | money | issue | title | flags |")
md.append("|---:|---:|---:|---|---|---|")
for i, r in enumerate(actionable[:20], 1):
  flags = ",".join(r["good_terms"][:6])
  md.append(f"| {i} | {r['route_score']:.1f} | {r['money']:.0f} | `{r['key']}` | {r['title'][:120]} | {flags} |")
md.append("")
md.append("## Top raw candidates including parked/risky")
md.append("")
md.append("| rank | route score | money | issue | title | parked | risk |")
md.append("|---:|---:|---:|---|---|---|---|")
for i, r in enumerate(top[:25], 1):
  md.append(f"| {i} | {r['route_score']:.1f} | {r['money']:.0f} | `{r['key']}` | {r['title'][:100]} | {r['parked'] or ''} | {','.join(r['risk_terms'])} |")
md.append("")
(out / "ROUTE_TABLE.md").write_text("\n".join(md) + "\n")

print((out / "ROUTE_TABLE.md").read_text())
PY

echo
echo "04 select next target for recon"
python3 - "$OUT" <<'PY'
from pathlib import Path
import json, sys

out = Path(sys.argv[1])
data = json.loads((out / "route_table.json").read_text())
actionable = data.get("actionable_25") or []

if actionable:
  pick = actionable[0]
else:
  pick = None

(out / "next_pick.json").write_text(json.dumps(pick or {}, indent=2))
print(json.dumps(pick or {"error": "no actionable pick"}, indent=2))
PY

echo
echo "05 generate next recon script if a pick exists"
python3 - "$OUT" <<'PY'
from pathlib import Path
import json, re, sys

out = Path(sys.argv[1])
pick = json.loads((out / "next_pick.json").read_text())
if not pick:
  print("No pick; no recon generated.")
  raise SystemExit(0)

repo = pick["repo"]
issue = pick["issue"]
safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", repo.replace("/", "__") + "_" + issue)
script = out / f"next_recon_{safe}.sh"

script.write_text(f'''#!/usr/bin/env bash
set -u

ROOT="/Users/heath/Documents/mathgraph-lean-work"
OWNER_REPO="{repo}"
ISSUE_NUM="{issue}"
SAFE="{safe}"
REPO="$ROOT/external/bounty_triage_v1/$SAFE"
OUT="$ROOT/artifacts/bounty_triage_v1/next_recon_$SAFE"

mkdir -p "$OUT"

echo "MathGraph next bounty recon — $OWNER_REPO #$ISSUE_NUM"
echo

cd "$ROOT" || exit 1

echo "01 status"
{{
  date -u +"%Y-%m-%dT%H:%M:%SZ"
  df -h /
  git status --short
}} | tee "$OUT/status_start.txt"

echo
echo "02 clone/update"
mkdir -p "$(dirname "$REPO")"
if [ ! -d "$REPO/.git" ]; then
  gh repo clone "$OWNER_REPO" "$REPO" -- --filter=blob:none 2>&1 | tee "$OUT/clone.log"
else
  echo "[exists] $REPO"
fi

cd "$REPO" || exit 1
git remote -v | tee "$OUT/remotes.txt"
git fetch origin --prune 2>&1 | tee "$OUT/git_fetch.log" || true
DEFAULT_BRANCH="$(git remote show origin 2>/dev/null | awk '/HEAD branch/ {{print $NF}}' | head -1)"
if [ -z "$DEFAULT_BRANCH" ]; then DEFAULT_BRANCH="main"; fi
git checkout "$DEFAULT_BRANCH" 2>&1 | tee "$OUT/git_checkout.log" || true
git pull --ff-only origin "$DEFAULT_BRANCH" 2>&1 | tee "$OUT/git_pull.log" || true
git rev-parse HEAD | tee "$OUT/head.txt"

echo
echo "03 issue view"
gh issue view "$ISSUE_NUM" --repo "$OWNER_REPO" --json number,title,state,url,labels,body,comments,updatedAt,createdAt \\
  > "$OUT/issue_view.json" 2> "$OUT/issue_view.err" || true

python3 - "$OUT" <<'PY2'
from pathlib import Path
import json, sys

out = Path(sys.argv[1])
p = out / "issue_view.json"
if p.exists() and p.stat().st_size:
  j = json.loads(p.read_text())
  summary = {{
    "number": j.get("number"),
    "title": j.get("title"),
    "state": j.get("state"),
    "url": j.get("url"),
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
  print((out / "issue_view.err").read_text(errors="replace") if (out / "issue_view.err").exists() else "")
PY2

echo
echo "04 project inventory"
{{
  echo "top files:"
  find . -maxdepth 3 -type f | sed 's#^./##' | sort | head -500
  echo
  echo "package/build files:"
  find . -maxdepth 4 -type f \\( -name 'package.json' -o -name 'pyproject.toml' -o -name 'setup.py' -o -name 'Cargo.toml' -o -name 'lakefile.toml' -o -name 'lean-toolchain' -o -name 'go.mod' -o -name 'Makefile' -o -name 'README*' \\) | sort
}} | tee "$OUT/project_inventory.txt"

echo
echo "05 grep for local judge and patch surface"
{{
  echo "===== test/build/ci hits ====="
  grep -RInE --exclude-dir=.git --exclude-dir=node_modules --exclude-dir=.venv --exclude-dir=target --exclude-dir=dist --exclude-dir=build \\
    "pytest|unittest|vitest|jest|mocha|cargo test|lake build|go test|make test|CI|workflow|failing|regression|benchmark|perf|lint|typecheck" . 2>/dev/null | head -2000

  echo
  echo "===== issue keyword hits ====="
  grep -RInE --exclude-dir=.git --exclude-dir=node_modules --exclude-dir=.venv --exclude-dir=target --exclude-dir=dist --exclude-dir=build \\
    "bounty|TODO|FIXME|validate|validation|error|bug|invariant|proof|score|test|failing|performance|optimize|regression" . 2>/dev/null | head -2000
}} | tee "$OUT/focused_grep.txt"

echo
echo "06 classify"
python3 - "$OUT" <<'PY2'
from pathlib import Path
import json, sys, re

out = Path(sys.argv[1])

issue = {{}}
try:
  issue = json.loads((out / "issue_summary.json").read_text())
except Exception:
  pass

inv = (out / "project_inventory.txt").read_text(errors="replace") if (out / "project_inventory.txt").exists() else ""
grep = (out / "focused_grep.txt").read_text(errors="replace") if (out / "focused_grep.txt").exists() else ""
body = (out / "issue_body.md").read_text(errors="replace") if (out / "issue_body.md").exists() else ""
text = "\\n".join([inv, grep, body]).lower()

has_tests = any(x in text for x in ["pytest", "unittest", "vitest", "jest", "cargo test", "lake build", "go test", "make test"])
has_patch_surface = len(grep.strip()) > 500
risky = any(x in text for x in ["system prompt", "private key", "seed phrase", "malware", "phishing"])
bounty = "bounty" in text

if risky:
  verdict = "PARK_RISKY"
elif has_tests and has_patch_surface:
  verdict = "PROMISING_RECON"
elif has_patch_surface:
  verdict = "MAYBE_NEEDS_TEST_SURFACE"
else:
  verdict = "PARK_NO_SURFACE"

decision = {{
  "verdict": verdict,
  "issue": issue,
  "has_tests": has_tests,
  "has_patch_surface": has_patch_surface,
  "risky": risky,
  "bounty": bounty,
}}
(out / "decision.json").write_text(json.dumps(decision, indent=2))

lines = []
lines.append("# Next Recon " + str(issue.get("url") or ""))
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
lines.append(body[:8000])
lines.append("")
lines.append("## Grep excerpt")
lines.append("")
lines.append(grep[:16000])
lines.append("")
(out / "REPORT.md").write_text("\\n".join(lines) + "\\n")
print((out / "REPORT.md").read_text())
PY2

echo
echo "07 commit artifacts"
cd "$ROOT" || exit 1
git add "$OUT" "$0"
git commit -m "Recon next bounty target $OWNER_REPO issue$ISSUE_NUM" || true
git push origin local-main || true

echo
echo "08 final"
git status --short
df -h /
echo "$OUT/REPORT.md"
''')

print(str(script))
print(script.read_text()[:4000])
PY

echo
echo "06 commit router artifact"
git add "$OUT" bounty_route_next_v1.sh
git commit -m "Add bounty route next v1" || true
git push origin local-main || true

echo
echo "07 final"
git status --short
df -h /
echo
echo "Artifacts:"
echo "$OUT/ROUTE_TABLE.md"
echo "$OUT/route_table.json"
echo "$OUT/next_pick.json"
echo "$OUT"
echo
echo "To run selected recon, inspect generated script:"
find "$OUT" -maxdepth 1 -name 'next_recon_*.sh' -print
