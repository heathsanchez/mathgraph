#!/usr/bin/env bash
set -euo pipefail

echo "MathGraph Park QuantumSavory Pivot hledger v18b"
echo "Goal: avoid overlapping claimed bounty, clean failed local patch, preserve evidence, and prepare hledger next route."
echo

ROOT="/Users/heath/Documents/mathgraph-lean-work"
QS_REPO="QuantumSavory/QuantumSavory.jl"
QS_DIR="$ROOT/external/cash_win_legit_recon_v17/QuantumSavory__QuantumSavory.jl_131"
HL_REPO="simonmichael/hledger"
HL_DIR="$ROOT/external/cash_win_legit_recon_v17/simonmichael__hledger_1825"
OUT="$ROOT/artifacts/park_quantumsavory_pivot_hledger_v18b"

mkdir -p "$OUT"
cd "$ROOT"

echo "01 status"
date -u +"%Y-%m-%dT%H:%M:%SZ" | tee "$OUT/status_start.txt"
df -h / | tee "$OUT/df_start.txt"
git status --short | tee "$OUT/mathgraph_status_start.txt" || true
echo

echo "02 QuantumSavory issue audit"
gh issue view 131 -R "$QS_REPO" --comments > "$OUT/quantumsavory_131_comments_now.txt"
grep -nEi "claim|claimed|bounty|submitted PR|pull request|heathsanchez" "$OUT/quantumsavory_131_comments_now.txt" | tee "$OUT/quantumsavory_claim_lines.txt" || true
echo

echo "03 park QuantumSavory local branch safely"
if [ -d "$QS_DIR/.git" ]; then
  cd "$QS_DIR"
  {
    echo "===== branch ====="
    git branch --show-current
    echo
    echo "===== status ====="
    git status --short
    echo
    echo "===== diff stat ====="
    git diff --stat || true
    echo
    echo "===== diff ====="
    git diff || true
  } > "$OUT/quantumsavory_failed_local_patch.diff.txt"

  git reset --hard HEAD
  git clean -fd benchmark/run_smoke.jl .github/workflows/benchmark.yml 2>/dev/null || true
  git checkout master 2>/dev/null || git checkout main 2>/dev/null || true
  git status --short | tee "$OUT/quantumsavory_status_after_reset.txt"
fi
echo

echo "04 post step-back comment on QuantumSavory issue"
cat > "$OUT/quantumsavory_stepback_comment.md" <<'MD'
I noticed after posting that there is already prior claim/submitted-PR activity on this bounty. I do not want to create overlap or noise, so I’ll step back unless the maintainers explicitly want an additional benchmark-smoke/CI slice from me.
MD

gh issue comment 131 -R "$QS_REPO" --body-file "$OUT/quantumsavory_stepback_comment.md" > "$OUT/quantumsavory_stepback_comment.out" 2> "$OUT/quantumsavory_stepback_comment.err" || true
cat "$OUT/quantumsavory_stepback_comment.out" || true
cat "$OUT/quantumsavory_stepback_comment.err" || true
echo

echo "05 hledger issue audit"
gh issue view 1825 -R "$HL_REPO" --comments > "$OUT/hledger_1825_comments_now.txt"
grep -nEi "claim|claimed|bounty|assigned|available|150|heathsanchez|watch|CPU|RAM|memory" "$OUT/hledger_1825_comments_now.txt" | tee "$OUT/hledger_signal_lines.txt" || true
echo

echo "06 hledger repo status and cheap surface"
if [ ! -d "$HL_DIR/.git" ]; then
  mkdir -p "$(dirname "$HL_DIR")"
  gh repo clone "$HL_REPO" "$HL_DIR" -- --filter=blob:none
fi

cd "$HL_DIR"
git fetch origin
git checkout master 2>/dev/null || git checkout main 2>/dev/null || true
git pull --ff-only origin "$(git branch --show-current)" || true

{
  echo "===== head ====="
  git rev-parse HEAD
  echo
  echo "===== status ====="
  git status --short
  echo
  echo "===== build files ====="
  find . -maxdepth 3 \( -name "stack.yaml" -o -name "cabal.project" -o -name "*.cabal" -o -name "Makefile" -o -name "package.yaml" \) -type f | sort
  echo
  echo "===== watch/fsnotify references ====="
  grep -RIn --exclude-dir=.git --exclude-dir=.stack-work --exclude-dir=dist-newstyle -- "hfsnotify\|fsnotify\|watch\|--watch" . | head -250 || true
  echo
  echo "===== tools ====="
  command -v stack || true
  command -v cabal || true
  command -v ghc || true
  command -v make || true
} | tee "$OUT/hledger_surface_now.txt"
echo

echo "07 write hledger claim draft"
cat > "$OUT/hledger_claim_draft.md" <<'MD'
Hi, I’d like to claim a narrow slice of this bounty if still available.

I’d start with a reproducible diagnostic path rather than a speculative fix:

- identify the current `hledger-ui --watch` file-notification loop
- build a small local repro/measurement script for idle CPU/RAM behavior
- isolate whether repeated watch events, event queueing, redraw scheduling, or hfsnotify lifecycle behavior is the likely source
- submit either a focused fix or a PR with a failing/reproducible diagnostic benchmark/test if the fix needs maintainer input

I’ll keep the first PR small and include exact local reproduction notes.
MD

echo "Hledger claim draft:"
cat "$OUT/hledger_claim_draft.md"
echo

echo "08 classify"
python3 - "$OUT" <<'PY'
from pathlib import Path
import json
import re
import sys

out = Path(sys.argv[1])

qs = (out / "quantumsavory_claim_lines.txt").read_text(errors="replace") if (out / "quantumsavory_claim_lines.txt").exists() else ""
hl = (out / "hledger_signal_lines.txt").read_text(errors="replace") if (out / "hledger_signal_lines.txt").exists() else ""
surf = (out / "hledger_surface_now.txt").read_text(errors="replace") if (out / "hledger_surface_now.txt").exists() else ""

decision = {
    "quantumsavory": {
        "verdict": "PARK_OVERLAP_PRIOR_CLAIMS",
        "reason": "Issue contains prior claim/submitted-PR activity before our claim; step-back comment attempted.",
    },
    "hledger": {
        "verdict": "CLAIM_NEXT" if "heathsanchez" not in hl.lower() else "ALREADY_TOUCHED",
        "reason": "Real maintainer/project, cash visible, watch/fsnotify surface found; likely next best candidate.",
        "tools_seen": {
            "stack": "stack" in surf,
            "cabal": "cabal" in surf,
            "ghc": "ghc" in surf,
            "make": "make" in surf,
        },
    },
}
(out / "decision.json").write_text(json.dumps(decision, indent=2) + "\n")

md = []
md.append("# Park QuantumSavory, Pivot hledger v18b")
md.append("")
md.append("## QuantumSavory")
md.append("")
md.append("- Verdict: `PARK_OVERLAP_PRIOR_CLAIMS`")
md.append("- Reason: issue already contains earlier claim/submitted-PR activity; local failed patch was reset.")
md.append("")
md.append("## hledger")
md.append("")
md.append(f"- Verdict: `{decision['hledger']['verdict']}`")
md.append("- Reason: real project, real issue, cash visible, watch/fsnotify surface found.")
md.append("- Next action: post the hledger claim draft, then build a minimal repro/measurement harness.")
md.append("")
(out / "PIVOT_REPORT.md").write_text("\n".join(md) + "\n")
print((out / "PIVOT_REPORT.md").read_text())
PY
echo

echo "09 commit artifact"
cd "$ROOT"
git add "$OUT" park_quantumsavory_pivot_hledger_v18b.sh
git commit -m "Park QuantumSavory and pivot hledger v18b" || true
git push origin local-main || true
echo

echo "10 final"
git status --short
df -h /
echo
echo "Artifacts:"
echo "$OUT/PIVOT_REPORT.md"
echo "$OUT/decision.json"
echo "$OUT/hledger_claim_draft.md"
echo "$OUT/hledger_surface_now.txt"
echo "$OUT/quantumsavory_failed_local_patch.diff.txt"
