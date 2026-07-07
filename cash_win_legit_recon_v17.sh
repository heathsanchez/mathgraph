#!/usr/bin/env bash
set -euo pipefail

echo "MathGraph Cash Win Legit Recon v17"
echo "Goal: deep-recon the two best real cash candidates: hledger#1825 and QuantumSavory#131."
echo

ROOT="/Users/heath/Documents/mathgraph-lean-work"
OUT="$ROOT/artifacts/cash_win_legit_recon_v17"
mkdir -p "$OUT"
cd "$ROOT"

echo "01 status"
date -u +"%Y-%m-%dT%H:%M:%SZ" | tee "$OUT/status_start.txt"
df -h / | tee "$OUT/df_start.txt"
git status --short | tee "$OUT/git_status_start.txt" || true
echo

echo "02 candidate issue views"
gh issue view 1825 -R simonmichael/hledger --comments > "$OUT/hledger_1825_issue.txt"
gh issue view 131 -R QuantumSavory/QuantumSavory.jl --comments > "$OUT/quantumsavory_131_issue.txt"
echo "saved issue views"
echo

echo "03 clone/update candidates with blob filtering"
BASE="$ROOT/external/cash_win_legit_recon_v17"
mkdir -p "$BASE"

if [ ! -d "$BASE/simonmichael__hledger_1825/.git" ]; then
  gh repo clone simonmichael/hledger "$BASE/simonmichael__hledger_1825" -- --filter=blob:none
else
  git -C "$BASE/simonmichael__hledger_1825" fetch origin
fi

if [ ! -d "$BASE/QuantumSavory__QuantumSavory.jl_131/.git" ]; then
  gh repo clone QuantumSavory/QuantumSavory.jl "$BASE/QuantumSavory__QuantumSavory.jl_131" -- --filter=blob:none
else
  git -C "$BASE/QuantumSavory__QuantumSavory.jl_131" fetch origin
fi
echo

echo "04 inspect hledger repo surface"
H="$BASE/simonmichael__hledger_1825"
cd "$H"
git rev-parse HEAD | tee "$OUT/hledger_head.txt"
git status --short | tee "$OUT/hledger_status.txt"
{
  echo "===== top files ====="
  find . -maxdepth 3 -type f | sed 's#^\./##' | sort | head -300
  echo
  echo "===== package files ====="
  find . -maxdepth 3 \( -name "stack.yaml" -o -name "cabal.project" -o -name "*.cabal" -o -name "package.yaml" -o -name "Makefile" \) -type f | sort
  echo
  echo "===== watch references ====="
  grep -RIn --exclude-dir=.git --exclude-dir=dist-newstyle --exclude-dir=.stack-work --exclude-dir=artifacts -- "watch" . | head -200 || true
  echo
  echo "===== hfsnotify references ====="
  grep -RIn --exclude-dir=.git --exclude-dir=dist-newstyle --exclude-dir=.stack-work -- "hfsnotify\|fsnotify\|notify" . | head -200 || true
  echo
  echo "===== hledger-ui references ====="
  find . -maxdepth 4 -type f | grep -Ei "hledger-ui|ui|watch|notify|fsnotify" | head -200 || true
} | tee "$OUT/hledger_surface.txt"
echo

echo "05 inspect QuantumSavory repo surface"
Q="$BASE/QuantumSavory__QuantumSavory.jl_131"
cd "$Q"
git rev-parse HEAD | tee "$OUT/quantumsavory_head.txt"
git status --short | tee "$OUT/quantumsavory_status.txt"
{
  echo "===== top files ====="
  find . -maxdepth 3 -type f | sed 's#^\./##' | sort | head -300
  echo
  echo "===== julia/project files ====="
  find . -maxdepth 4 \( -name "Project.toml" -o -name "Manifest.toml" -o -name "*.jl" -o -name "Makefile" -o -name "*.yml" -o -name "*.yaml" \) -type f | sort | head -300
  echo
  echo "===== benchmark references ====="
  grep -RIn --exclude-dir=.git -- "benchmark\|BenchmarkTools\|PkgBenchmark\|AirspeedVelocity\|performance" . | head -300 || true
  echo
  echo "===== workflow references ====="
  find .github -maxdepth 3 -type f -print -exec sed -n '1,220p' {} \; 2>/dev/null || true
} | tee "$OUT/quantumsavory_surface.txt"
echo

echo "06 cheap local verifier availability"
cd "$H"
{
  echo "===== hledger tools ====="
  command -v stack || true
  command -v cabal || true
  command -v ghc || true
  command -v make || true
  echo
  echo "===== hledger README test hints ====="
  grep -RIn --exclude-dir=.git -- "stack test\|cabal test\|make test\|hledger-ui --watch\|--watch" README* doc* */README* 2>/dev/null | head -120 || true
} | tee "$OUT/hledger_verifier_hints.txt"

cd "$Q"
{
  echo "===== QuantumSavory tools ====="
  command -v julia || true
  [ -x "$HOME/.juliaup/bin/julia" ] && echo "$HOME/.juliaup/bin/julia" || true
  command -v make || true
  echo
  echo "===== QuantumSavory test hints ====="
  grep -RIn --exclude-dir=.git -- "Pkg.test\|julia --project\|BenchmarkTools\|benchmark" README* docs* test* benchmark* .github 2>/dev/null | head -160 || true
} | tee "$OUT/quantumsavory_verifier_hints.txt"
echo

echo "07 classify"
python3 - "$OUT" <<'PY'
from pathlib import Path
import json
import re
import sys

out = Path(sys.argv[1])

h_issue = (out / "hledger_1825_issue.txt").read_text(errors="replace")
q_issue = (out / "quantumsavory_131_issue.txt").read_text(errors="replace")
h_surface = (out / "hledger_surface.txt").read_text(errors="replace")
q_surface = (out / "quantumsavory_surface.txt").read_text(errors="replace")
h_hints = (out / "hledger_verifier_hints.txt").read_text(errors="replace")
q_hints = (out / "quantumsavory_verifier_hints.txt").read_text(errors="replace")

def has(s, pat):
    return bool(re.search(pat, s, re.I))

rows = []

h_score = 0
h_reasons = []
if "$150" in h_issue or "150" in h_issue:
    h_score += 20; h_reasons.append("cash visible")
if "not assigned" in h_issue.lower() or "unassigned" in h_issue.lower() or "available" in h_issue.lower():
    h_score += 10; h_reasons.append("appears available")
if has(h_surface, "hfsnotify|fsnotify|watch"):
    h_score += 25; h_reasons.append("watch implementation surface found")
if has(h_hints, "stack|cabal|make"):
    h_score += 15; h_reasons.append("local verifier tools/hints found")
if has(h_issue, "CPU|RAM|memory|days|watch"):
    h_score += 15; h_reasons.append("clear repro target")
if has(h_issue, "assigned|claimed|already working"):
    h_score -= 20; h_reasons.append("possible claim language")
rows.append({
    "repo": "simonmichael/hledger",
    "issue": 1825,
    "url": "https://github.com/simonmichael/hledger/issues/1825",
    "score": h_score,
    "verdict": "CLAIM_OR_REPRO_NEXT" if h_score >= 55 else "RECON_MORE",
    "reasons": h_reasons,
    "next": "Ask to claim one $150 sub-bounty or build minimal --watch CPU/RAM repro harness."
})

q_score = 0
q_reasons = []
if "$200" in q_issue or "200" in q_issue:
    q_score += 20; q_reasons.append("cash visible")
if has(q_issue, "claim exclusive time|claims are encouraged"):
    q_score += 10; q_reasons.append("explicit claim process")
if has(q_surface, "BenchmarkTools|benchmark|performance"):
    q_score += 25; q_reasons.append("benchmark surface found")
if has(q_hints, "julia --project|Pkg.test|BenchmarkTools"):
    q_score += 20; q_reasons.append("local Julia verifier likely")
if has(q_issue, "assigned|claimed|already working|bounty is now yours"):
    q_score -= 25; q_reasons.append("possible claim language")
rows.append({
    "repo": "QuantumSavory/QuantumSavory.jl",
    "issue": 131,
    "url": "https://github.com/QuantumSavory/QuantumSavory.jl/issues/131",
    "score": q_score,
    "verdict": "CLAIM_NEXT" if q_score >= 55 else "RECON_MORE",
    "reasons": q_reasons,
    "next": "Post claim comment, then make benchmark-suite PR."
})

rows.sort(key=lambda r: -r["score"])
(out / "decision.json").write_text(json.dumps(rows, indent=2) + "\n")

md = []
md.append("# Cash Win Legit Recon v17")
md.append("")
md.append("## Ranked verdict")
md.append("")
for i, r in enumerate(rows, 1):
    md.append(f"### {i}. {r['repo']}#{r['issue']}")
    md.append("")
    md.append(f"- Verdict: `{r['verdict']}`")
    md.append(f"- Score: `{r['score']}`")
    md.append(f"- URL: {r['url']}")
    md.append(f"- Reasons: {', '.join(r['reasons'])}")
    md.append(f"- Next: {r['next']}")
    md.append("")
md.append("## Recommendation")
md.append("")
md.append("Prefer QuantumSavory if the goal is fastest transfer from the qojulia benchmark work. Prefer hledger if the issue looks unclaimed and local Haskell tooling is already available.")
md.append("")
(out / "RECON_REPORT.md").write_text("\n".join(md) + "\n")
print((out / "RECON_REPORT.md").read_text())
PY
echo

echo "08 commit artifact"
cd "$ROOT"
git add "$OUT" cash_win_legit_recon_v17.sh
git commit -m "Deep recon legit cash wins v17" || true
git push origin local-main || true
echo

echo "09 final"
git status --short
df -h /
echo
echo "Artifacts:"
echo "$OUT/RECON_REPORT.md"
echo "$OUT/decision.json"
echo "$OUT/hledger_1825_issue.txt"
echo "$OUT/quantumsavory_131_issue.txt"
echo "$OUT/hledger_surface.txt"
echo "$OUT/quantumsavory_surface.txt"
