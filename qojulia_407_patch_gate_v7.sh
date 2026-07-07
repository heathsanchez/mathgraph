#!/usr/bin/env bash
set -u

ROOT="/Users/heath/Documents/mathgraph-lean-work"
RUN="qojulia_407_patch_gate_v7"
OUT="$ROOT/artifacts/$RUN"
REPO_DIR="$ROOT/external/money_gold_recon_v6/qojulia__QuantumOptics.jl_407"
REPO="qojulia/QuantumOptics.jl"
ISSUE="407"

mkdir -p "$OUT"
cd "$ROOT" || exit 1

echo "MathGraph qojulia/QuantumOptics.jl #407 Patch Gate v7"
echo "Goal: decide patch / question / park for \$400 benchmark-suite bounty."
echo

echo "01 status + cleanup raw v5 search junk"
date -u +"%Y-%m-%dT%H:%M:%SZ"
df -h /
git status --short

# Safe cleanup: these were explicitly uncommitted raw search result files from v5.
find "$ROOT/artifacts/prize_cash_challenge_scout_v5_compact" \
  -maxdepth 1 -type f \( -name 'search_*.json' -o -name 'search_*.err' \) \
  -print -delete 2>/dev/null || true

echo
echo "status after cleanup"
git status --short

echo
echo "02 fetch issue + comments"
gh issue view "$ISSUE" -R "$REPO" \
  --json url,title,body,state,labels,comments,assignees,createdAt,updatedAt \
  > "$OUT/issue.json" 2> "$OUT/issue.err" || true

python3 - "$OUT" <<'PY'
import json, sys, pathlib, textwrap
out = pathlib.Path(sys.argv[1])
try:
    issue = json.loads((out/"issue.json").read_text())
except Exception as e:
    print("issue json parse failed", e)
    issue = {}

summary = {
    "url": issue.get("url"),
    "title": issue.get("title"),
    "state": issue.get("state"),
    "labels": [x.get("name") for x in issue.get("labels", [])],
    "assignees": [x.get("login") for x in issue.get("assignees", [])],
    "comment_count": len(issue.get("comments", []) or []),
    "createdAt": issue.get("createdAt"),
    "updatedAt": issue.get("updatedAt"),
}
(out/"issue_summary.json").write_text(json.dumps(summary, indent=2))
print(json.dumps(summary, indent=2))

body = issue.get("body") or ""
comments = issue.get("comments") or []
md = []
md.append("# qojulia/QuantumOptics.jl #407 Issue Packet")
md.append("")
md.append(f"URL: {issue.get('url')}")
md.append(f"Title: {issue.get('title')}")
md.append(f"State: {issue.get('state')}")
md.append(f"Labels: {', '.join(summary['labels'])}")
md.append(f"Assignees: {', '.join(summary['assignees']) or '(none)'}")
md.append("")
md.append("## Body")
md.append("")
md.append(body)
md.append("")
md.append("## Comments")
md.append("")
for c in comments:
    md.append(f"### {c.get('author',{}).get('login','unknown')} — {c.get('createdAt')}")
    md.append("")
    md.append(c.get("body") or "")
    md.append("")
(out/"ISSUE_PACKET.md").write_text("\n".join(md))
print("\n--- issue body excerpt ---")
print(body[:3000])
PY

echo
echo "03 clone/update repo"
if [ ! -d "$REPO_DIR/.git" ]; then
  mkdir -p "$(dirname "$REPO_DIR")"
  git clone --depth 1 --filter=blob:none "https://github.com/$REPO.git" "$REPO_DIR" > "$OUT/clone.log" 2>&1 || true
else
  git -C "$REPO_DIR" fetch --depth 1 origin > "$OUT/git_fetch.log" 2>&1 || true
  git -C "$REPO_DIR" checkout FETCH_HEAD > "$OUT/git_checkout.log" 2>&1 || true
fi

git -C "$REPO_DIR" rev-parse HEAD > "$OUT/head.txt" 2>&1 || true
cat "$OUT/head.txt"

echo
echo "04 inventory benchmark/test/CI surface"
{
  echo "===== top files ====="
  find "$REPO_DIR" -maxdepth 4 -type f \
    | sed "s#$REPO_DIR/##" \
    | sort \
    | head -300

  echo
  echo "===== benchmark files ====="
  find "$REPO_DIR" -maxdepth 6 -type f \
    | grep -Ei 'benchmark|benchmarks|perf|performance|PkgBenchmark|Aqua|JET|runtests|Project.toml|Manifest.toml|\.github/workflows' \
    | sed "s#$REPO_DIR/##" \
    | sort \
    | head -300

  echo
  echo "===== workflows ====="
  find "$REPO_DIR/.github/workflows" -maxdepth 2 -type f 2>/dev/null \
    | sed "s#$REPO_DIR/##" \
    | sort
} | tee "$OUT/inventory.txt"

echo
echo "05 focused grep"
{
  echo "===== issue terms in repo ====="
  grep -RInE 'benchmark|PkgBenchmark|CI|GitHub Actions|workflow|runtests|performance|regression|bounty|Aqua|JET|JuliaFormatter|CompatHelper' \
    "$REPO_DIR" \
    --exclude-dir=.git --exclude='Manifest.toml' 2>/dev/null \
    | head -400

  echo
  echo "===== Project.toml files ====="
  find "$REPO_DIR" -name Project.toml -type f -maxdepth 6 -print | while read p; do
    echo
    echo "--- ${p#$REPO_DIR/} ---"
    sed -n '1,220p' "$p"
  done

  echo
  echo "===== existing benchmark dirs ====="
  find "$REPO_DIR" -maxdepth 4 -type d | grep -Ei 'bench|perf' | sed "s#$REPO_DIR/##" | sort
} > "$OUT/grep.txt"

sed -n '1,260p' "$OUT/grep.txt"

echo
echo "06 cheap local Julia probe"
{
  echo "pwd=$REPO_DIR"
  if command -v julia >/dev/null 2>&1; then
    echo "julia found:"
    julia --version
    echo
    echo "Pkg status, no instantiate:"
    cd "$REPO_DIR" && julia --project=. -e 'using Pkg; Pkg.status()' 2>&1
  else
    echo "julia not installed on this machine."
    echo "No local Julia judge can run yet."
  fi
} | tee "$OUT/julia_probe.txt"

echo
echo "07 classify and write patch plan"
python3 - "$OUT" "$REPO_DIR" <<'PY'
import json, pathlib, re, sys

out = pathlib.Path(sys.argv[1])
repo = pathlib.Path(sys.argv[2])

issue = json.loads((out/"issue.json").read_text())
body = issue.get("body") or ""
comments = "\n\n".join((c.get("body") or "") for c in issue.get("comments", []) or [])
text = (body + "\n" + comments).lower()

inventory = (out/"inventory.txt").read_text(errors="replace").lower()
grep = (out/"grep.txt").read_text(errors="replace").lower()
julia_probe = (out/"julia_probe.txt").read_text(errors="replace").lower()

has_bounty = "bounty:400" in str(issue.get("labels", [])).lower() or "$400" in text or "[$400]" in text
has_benchmark_surface = "benchmark" in inventory or "benchmark" in grep or "pkgbenchmark" in grep
has_ci = ".github/workflows" in inventory or "github actions" in grep or "workflow" in grep
julia_installed = "julia found:" in julia_probe
assigned = bool(issue.get("assignees"))
mentions_claimed = any(w in comments.lower() for w in ["i'll take", "working on", "claimed", "assigned", "opened pr", "pull request"])

# Conservative gate:
if assigned or mentions_claimed:
    verdict = "ASK_OR_PARK_ALREADY_CLAIMED"
elif has_bounty and has_benchmark_surface and has_ci:
    verdict = "PATCHABLE_AFTER_READING_EXACT_BENCHMARK_REQUEST"
else:
    verdict = "ASK_FOR_SCOPE_OR_PARK"

decision = {
    "verdict": verdict,
    "has_bounty": has_bounty,
    "has_benchmark_surface": has_benchmark_surface,
    "has_ci": has_ci,
    "julia_installed": julia_installed,
    "assigned": assigned,
    "mentions_claimed_or_pr": mentions_claimed,
    "url": issue.get("url"),
    "title": issue.get("title"),
}
(out/"decision.json").write_text(json.dumps(decision, indent=2))

plan = []
plan.append("# qojulia #407 Patch Gate v7")
plan.append("")
plan.append("## Verdict")
plan.append("")
plan.append(f"`{verdict}`")
plan.append("")
plan.append("## Decision JSON")
plan.append("")
plan.append("```json")
plan.append(json.dumps(decision, indent=2))
plan.append("```")
plan.append("")
plan.append("## What to do next")
plan.append("")
if verdict == "PATCHABLE_AFTER_READING_EXACT_BENCHMARK_REQUEST":
    plan.append("Proceed to v8 focused patch design, but do not open PR until the exact benchmark expectation is extracted from `ISSUE_PACKET.md`.")
    plan.append("")
    plan.append("Likely patch shape:")
    plan.append("")
    plan.append("1. Add or update benchmark project/files.")
    plan.append("2. Add benchmark CI job that is lightweight enough for PRs.")
    plan.append("3. Add docs explaining local benchmark command.")
    plan.append("4. Run formatting/tests if Julia is available; otherwise create a maintainer question asking for expected command/output.")
elif verdict == "ASK_OR_PARK_ALREADY_CLAIMED":
    plan.append("Do not patch blind. Read comments; if already assigned or PR exists, ask whether a narrow subtask is still useful.")
else:
    plan.append("Do not patch yet. Ask maintainer for exact benchmark command, expected CI behavior, and whether the bounty is still open.")
plan.append("")
plan.append("## Suggested maintainer question")
plan.append("")
plan.append("> I’m looking at the $400 benchmark-suite bounty. Before patching, can you confirm the expected local command and CI behavior? For example, should this add a lightweight benchmark smoke job to GitHub Actions, a full PkgBenchmark suite, or both? I can keep the first PR narrow: benchmark project + reproducible command + CI smoke gate.")
plan.append("")
plan.append("## Files to read")
plan.append("")
plan.append("- `ISSUE_PACKET.md`")
plan.append("- `inventory.txt`")
plan.append("- `grep.txt`")
plan.append("- `julia_probe.txt`")
(out/"PATCH_PLAN.md").write_text("\n".join(plan) + "\n")
print((out/"PATCH_PLAN.md").read_text())
PY

echo
echo "08 commit artifact"
git add "$OUT" qojulia_407_patch_gate_v7.sh
git commit -m "Gate qojulia QuantumOptics benchmark bounty v7" || true
git push origin local-main || true

echo
echo "09 final"
git status --short
df -h /
echo
echo "Artifacts:"
echo "$OUT/ISSUE_PACKET.md"
echo "$OUT/PATCH_PLAN.md"
echo "$OUT/decision.json"
echo "$OUT/grep.txt"
echo "$OUT/julia_probe.txt"
