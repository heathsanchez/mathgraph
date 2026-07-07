#!/usr/bin/env bash
set -euo pipefail
echo "MathGraph qojulia/QuantumOptics.jl #407 Smoke Runner Patch v10b"
echo "Goal: repair v10 artifact/report quoting bug; verify patch; optionally push/open draft PR."
echo
ROOT="/Users/heath/Documents/mathgraph-lean-work"
REPO="qojulia/QuantumOptics.jl"
ISSUE="407"
REPO_DIR="$ROOT/external/money_gold_recon_v6/qojulia__QuantumOptics.jl_407"
OUT="$ROOT/artifacts/qojulia_407_smoke_runner_patch_v10b"
BRANCH="heath/benchmark-smoke-407"
JULIA_BIN="${JULIA_BIN:-$HOME/.juliaup/bin/julia}"
mkdir -p "$OUT"
cd "$ROOT"
echo "01 status"
date -u +"%Y-%m-%dT%H:%M:%SZ" | tee "$OUT/status_start.txt"
df -h / | tee "$OUT/df_start.txt"
git status --short | tee "$OUT/mathgraph_status_start.txt"
echo
echo "02 locate Julia"
if [ ! -x "$JULIA_BIN" ]; then
  JULIA_BIN="$(command -v julia || true)"
fi
if [ -z "${JULIA_BIN:-}" ] || [ ! -x "$JULIA_BIN" ]; then
  echo "Julia not found." | tee "$OUT/julia_error.txt"
  exit 1
fi
echo "JULIA_BIN=$JULIA_BIN" | tee "$OUT/julia_locate.txt"
"$JULIA_BIN" --version | tee -a "$OUT/julia_locate.txt"
echo
echo "03 inspect external repo patch"
cd "$REPO_DIR"
git status --short | tee "$OUT/external_status_start.txt"
git branch --show-current | tee "$OUT/external_branch.txt"
git rev-parse HEAD | tee "$OUT/external_head_start.txt"
git log --oneline -5 | tee "$OUT/external_log.txt"
echo
echo "04 ensure expected files exist"
test -f benchmark/run_smoke.jl
test -f .github/workflows/benchmark-smoke.yml
test -f README.md
grep -n "benchmark/run_smoke.jl" README.md | tee "$OUT/readme_smoke_grep.txt"
grep -n "BENCHMARK_SMOKE_OK" benchmark/run_smoke.jl | tee "$OUT/runner_ok_grep.txt"
echo
echo "05 rerun local smoke verifier"
set +e
"$JULIA_BIN" --project=benchmark benchmark/run_smoke.jl > "$OUT/local_smoke.out" 2> "$OUT/local_smoke.err"
SMOKE_RC=$?
set -e
echo "$SMOKE_RC" | tee "$OUT/local_smoke.rc"
echo "smoke rc=$SMOKE_RC"
tail -100 "$OUT/local_smoke.out" || true
tail -100 "$OUT/local_smoke.err" || true
echo
echo "06 collect clean patch diff"
{
  echo "===== git show --stat HEAD ====="
  git show --stat --oneline HEAD
  echo
  echo "===== git show HEAD -- benchmark/run_smoke.jl .github/workflows/benchmark-smoke.yml README.md ====="
  git show -- benchmark/run_smoke.jl .github/workflows/benchmark-smoke.yml README.md
  echo
  echo "===== status ====="
  git status --short
} | tee "$OUT/patch_show.txt"
echo
echo "07 write clean decision/report without shell expansion"
python3 - "$OUT" "$REPO" "$ISSUE" "$BRANCH" "$SMOKE_RC" <<'PY'
import json
import sys
from pathlib import Path
out = Path(sys.argv[1])
repo = sys.argv[2]
issue = int(sys.argv[3])
branch = sys.argv[4]
rc = int(sys.argv[5])
decision = {
    "repo": repo,
    "issue": issue,
    "branch": branch,
    "smoke_rc": rc,
    "local_smoke_passed": rc == 0,
    "external_head": (out / "external_head_start.txt").read_text().strip() if (out / "external_head_start.txt").exists() else None,
    "patch_files": [
        "benchmark/run_smoke.jl",
        ".github/workflows/benchmark-smoke.yml",
        "README.md"
    ],
    "v10_problem": "The original v10 patch committed successfully, but its artifact report was corrupted because a Python heredoc was unquoted and Bash expanded backticks/braces inside it.",
    "verdict": "READY_TO_PUSH_DRAFT_PR" if rc == 0 else "DO_NOT_PR_LOCAL_SMOKE_FAILED"
}
(out / "decision.json").write_text(json.dumps(decision, indent=2) + "\n")
md = []
md.append("# qojulia #407 Smoke Runner Patch v10b")
md.append("")
md.append("## Verdict")
md.append("")
md.append(f"`{decision['verdict']}`")
md.append("")
md.append("## Local verifier")
md.append("")
md.append(f"- `julia --project=benchmark benchmark/run_smoke.jl`: rc `{rc}`")
md.append("")
md.append("## Patch")
md.append("")
md.append("- Adds `benchmark/run_smoke.jl` as a lightweight benchmark-suite bitrot gate.")
md.append("- Adds `.github/workflows/benchmark-smoke.yml` on normal `pull_request`, `push`, and `workflow_dispatch`.")
md.append("- Documents the smoke command in `README.md`.")
md.append("")
md.append("## Why v10b exists")
md.append("")
md.append("The v10 external patch was valid and committed, but the MathGraph artifact report was corrupted by shell expansion inside an unquoted Python heredoc. v10b regenerates the report with a quoted-safe Python call and re-verifies the local smoke gate.")
md.append("")
md.append("## PR rule")
md.append("")
md.append("Open a draft PR only by rerunning with:")
md.append("")
md.append("`OPEN_QOJULIA_PR=1 bash qojulia_407_smoke_runner_patch_v10b.sh`")
md.append("")
(out / "PATCH_REPORT.md").write_text("\n".join(md) + "\n")
print((out / "PATCH_REPORT.md").read_text())
PY
echo
echo "08 optional push/open draft PR"
cd "$REPO_DIR"
if [ "$SMOKE_RC" -eq 0 ] && [ "${OPEN_QOJULIA_PR:-0}" = "1" ]; then
  echo "OPEN_QOJULIA_PR=1 set; preparing fork remote and draft PR"
  if ! git remote get-url heath >/dev/null 2>&1; then
    gh repo fork "$REPO" --remote --remote-name heath --clone=false > "$OUT/gh_fork.out" 2> "$OUT/gh_fork.err" || true
  fi
  git push -u heath "$BRANCH" > "$OUT/external_push.out" 2> "$OUT/external_push.err"
  cat > "$OUT/PR_BODY.md" <<'MD'
## Summary

Adds a lightweight benchmark smoke gate for the existing `benchmark/` suite.

This is intentionally narrow for the first step of #407:

- instantiate the benchmark project
- load `benchmark/benchmarks.jl`
- run one tiny benchmark path
- fail CI if the benchmark suite no longer loads or cannot run a minimal benchmark

## Local verification

    julia --project=benchmark benchmark/run_smoke.jl

The smoke runner prints `BENCHMARK_SMOKE_OK` on success.

## Scope

This PR does not attempt the full comparative benchmark report against QuTiP / QuantumToolbox.jl yet. It is meant to establish the small PR-safe CI gate first, so the benchmark suite stops silently bitrotting.
MD
  gh pr create \
    -R "$REPO" \
    --head "heathsanchez:$BRANCH" \
    --base master \
    --draft \
    --title "Add benchmark smoke gate" \
    --body-file "$OUT/PR_BODY.md" \
    > "$OUT/pr_create.out" 2> "$OUT/pr_create.err" || true
  cat "$OUT/pr_create.out" || true
  cat "$OUT/pr_create.err" || true
else
  echo "Dry run / local patch only."
  echo "To open draft PR:"
  echo "OPEN_QOJULIA_PR=1 bash qojulia_407_smoke_runner_patch_v10b.sh"
fi
echo
echo "09 commit MathGraph artifact"
cd "$ROOT"
git add "$OUT" qojulia_407_smoke_runner_patch_v10b.sh
git commit -m "Repair qojulia benchmark smoke artifact v10b" || true
git push origin local-main || true
echo
echo "10 final"
git status --short
df -h /
echo
echo "Artifacts:"
echo "$OUT/PATCH_REPORT.md"
echo "$OUT/decision.json"
echo "$OUT/local_smoke.out"
echo "$OUT/local_smoke.err"
echo "$OUT/patch_show.txt"
echo "$OUT/pr_create.out"
