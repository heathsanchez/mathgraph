#!/usr/bin/env bash
set -euo pipefail

echo "MathGraph qojulia/QuantumOptics.jl #407 Smoke Runner Patch v10"
echo "Goal: add narrow benchmark smoke runner + safe CI + docs; run locally; do not PR unless OPEN_QOJULIA_PR=1."
echo

ROOT="/Users/heath/Documents/mathgraph-lean-work"
REPO="qojulia/QuantumOptics.jl"
ISSUE="407"
REPO_DIR="$ROOT/external/money_gold_recon_v6/qojulia__QuantumOptics.jl_407"
OUT="$ROOT/artifacts/qojulia_407_smoke_runner_patch_v10"
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
  echo "Julia not found. Expected ~/.juliaup/bin/julia from v9b." | tee "$OUT/julia_error.txt"
  exit 1
fi
echo "JULIA_BIN=$JULIA_BIN" | tee "$OUT/julia_locate.txt"
"$JULIA_BIN" --version | tee -a "$OUT/julia_locate.txt"
echo

echo "03 refresh external repo"
if [ ! -d "$REPO_DIR/.git" ]; then
  mkdir -p "$(dirname "$REPO_DIR")"
  gh repo clone "$REPO" "$REPO_DIR" -- --filter=blob:none
fi

git -C "$REPO_DIR" fetch origin master | tee "$OUT/git_fetch.log"
git -C "$REPO_DIR" checkout master | tee "$OUT/git_checkout_master.log"
git -C "$REPO_DIR" pull --ff-only origin master | tee "$OUT/git_pull.log"
git -C "$REPO_DIR" rev-parse HEAD | tee "$OUT/head_base.txt"
git -C "$REPO_DIR" checkout -B "$BRANCH" origin/master | tee "$OUT/git_checkout_branch.log"
echo

echo "04 write benchmark smoke runner"
mkdir -p "$REPO_DIR/benchmark"

cat > "$REPO_DIR/benchmark/run_smoke.jl" <<'JL'
#!/usr/bin/env julia

# Lightweight benchmark smoke gate for CI and local development.
#
# This is intentionally not a full performance benchmark. Its job is to keep the
# benchmark project from bitrotting by checking that the benchmark environment
# instantiates, the benchmark suite loads, and at least one tiny benchmark can run.
#
# Local command from repository root:
#
#     julia --project=benchmark benchmark/run_smoke.jl
#
# Optional environment variables:
#
#     QO_BENCHMARK_SMOKE_GROUP=schroedinger
#     QO_BENCHMARK_SMOKE_KIND="base array types"
#     QO_BENCHMARK_SMOKE_SIZE="1//2"

using Pkg

Pkg.activate(@__DIR__)
Pkg.instantiate()

include(joinpath(@__DIR__, "benchmarks.jl"))

if !isdefined(Main, :SUITE)
    error("benchmark/benchmarks.jl did not define Main.SUITE")
end

using BenchmarkTools

const GROUP = get(ENV, "QO_BENCHMARK_SMOKE_GROUP", "schroedinger")
const KIND = get(ENV, "QO_BENCHMARK_SMOKE_KIND", "base array types")
const SIZE = get(ENV, "QO_BENCHMARK_SMOKE_SIZE", "1//2")

function _require_key(container, key, label)
    if !haskey(container, key)
        available = join(string.(collect(keys(container))), ", ")
        error("Missing benchmark $label key '$key'. Available: $available")
    end
    return container[key]
end

group_suite = _require_key(SUITE, GROUP, "group")
kind_suite = _require_key(group_suite, KIND, "kind")
bench = _require_key(kind_suite, SIZE, "size")

println("QuantumOptics benchmark smoke")
println("Julia version: ", VERSION)
println("Benchmark project: ", Base.active_project())
println("Selected benchmark: ", repr((GROUP, KIND, SIZE)))

trial = run(bench; samples=1, evals=1, seconds=1)
display(trial)
println()
println("BENCHMARK_SMOKE_OK")
JL

chmod +x "$REPO_DIR/benchmark/run_smoke.jl"
echo "wrote benchmark/run_smoke.jl" | tee "$OUT/write_smoke_runner.txt"
echo

echo "05 write safe benchmark smoke workflow"
mkdir -p "$REPO_DIR/.github/workflows"

cat > "$REPO_DIR/.github/workflows/benchmark-smoke.yml" <<'YAML'
name: Benchmark Smoke

on:
  pull_request:
    branches: [master, main]
  push:
    branches: [master, main]
  workflow_dispatch:

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}-${{ github.run_number }}
  cancel-in-progress: ${{ startsWith(github.ref, 'refs/pull/') }}

jobs:
  benchmark-smoke:
    name: Julia benchmark smoke
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: julia-actions/setup-julia@v3
        with:
          version: '1'
      - uses: actions/cache@v5
        env:
          cache-name: benchmark-smoke-artifacts
        with:
          path: ~/.julia/artifacts
          key: ${{ runner.os }}-${{ env.cache-name }}-${{ hashFiles('Project.toml', 'benchmark/Project.toml') }}
          restore-keys: |
            ${{ runner.os }}-${{ env.cache-name }}-
            ${{ runner.os }}-
      - name: Run benchmark smoke gate
        run: julia --project=benchmark benchmark/run_smoke.jl
YAML

echo "wrote .github/workflows/benchmark-smoke.yml" | tee "$OUT/write_workflow.txt"
echo

echo "06 patch docs idempotently"
python3 - <<'PY'
from pathlib import Path

repo = Path("/Users/heath/Documents/mathgraph-lean-work/external/money_gold_recon_v6/qojulia__QuantumOptics.jl_407")
readme = repo / "README.md"
text = readme.read_text()

marker = "* Benchmarks: https://github.com/qojulia/QuantumOptics.jl-benchmarks"
insert = """* Benchmark smoke check for contributors:

      julia --project=benchmark benchmark/run_smoke.jl

  This command is a lightweight gate that instantiates the benchmark environment,
  loads the benchmark suite, and runs one tiny benchmark. It is intended to catch
  benchmark-suite bitrot in pull requests; full comparative benchmark reports are
  still maintained separately.
"""

if "benchmark/run_smoke.jl" not in text:
    if marker in text:
        text = text.replace(marker, marker + "\n" + insert)
    else:
        text += "\n\n## Benchmarks\n\n" + insert
    readme.write_text(text)
PY

grep -nE "benchmark/run_smoke.jl|Benchmark smoke" "$REPO_DIR/README.md" | tee "$OUT/docs_patch_grep.txt"
echo

echo "07 run local smoke"
cd "$REPO_DIR"
set +e
"$JULIA_BIN" --project=benchmark benchmark/run_smoke.jl > "$OUT/local_smoke.out" 2> "$OUT/local_smoke.err"
SMOKE_RC=$?
set -e
echo "$SMOKE_RC" | tee "$OUT/local_smoke.rc"
echo "smoke rc=$SMOKE_RC"
tail -100 "$OUT/local_smoke.out" || true
tail -100 "$OUT/local_smoke.err" || true
echo

echo "08 inspect patch"
{
  echo "===== git diff stat ====="
  git diff --stat
  echo
  echo "===== git diff ====="
  git diff -- benchmark/run_smoke.jl .github/workflows/benchmark-smoke.yml README.md
  echo
  echo "===== external repo status ====="
  git status --short
} | tee "$OUT/patch_diff.txt"
echo

echo "09 decide and commit external patch"
python3 - <<PY
import json
from pathlib import Path

out = Path("$OUT")
rc = int((out / "local_smoke.rc").read_text().strip())
decision = {
    "repo": "$REPO",
    "issue": $ISSUE,
    "branch": "$BRANCH",
    "smoke_rc": rc,
    "local_smoke_passed": rc == 0,
    "patch_files": [
        "benchmark/run_smoke.jl",
        ".github/workflows/benchmark-smoke.yml",
        "README.md",
    ],
    "verdict": "COMMIT_PATCH_AND_OPTIONAL_DRAFT_PR" if rc == 0 else "DO_NOT_PR_LOCAL_SMOKE_FAILED",
}
(out / "decision.json").write_text(json.dumps(decision, indent=2) + "\\n")

md = []
md.append("# qojulia #407 Smoke Runner Patch v10")
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
md.append("## PR rule")
md.append("")
md.append("Open a draft PR only if local smoke passed and you intentionally rerun with:")
md.append("")
md.append("`OPEN_QOJULIA_PR=1 bash qojulia_407_smoke_runner_patch_v10.sh`")
md.append("")
(out / "PATCH_REPORT.md").write_text("\\n".join(md) + "\\n")
print((out / "PATCH_REPORT.md").read_text())
PY

if [ "$SMOKE_RC" -eq 0 ]; then
  git add benchmark/run_smoke.jl .github/workflows/benchmark-smoke.yml README.md
  git commit -m "Add benchmark smoke gate" | tee "$OUT/external_commit.out" || true
  git rev-parse HEAD | tee "$OUT/head_patch.txt"
else
  echo "Local smoke failed; not committing external patch." | tee "$OUT/external_commit.out"
fi
echo

echo "10 optional push/open draft PR"
cd "$REPO_DIR"
if [ "$SMOKE_RC" -eq 0 ] && [ "${OPEN_QOJULIA_PR:-0}" = "1" ]; then
  echo "OPEN_QOJULIA_PR=1 set; preparing fork remote and draft PR"
  if ! git remote get-url heath >/dev/null 2>&1; then
    gh repo fork "$REPO" --remote --remote-name heath --clone=false | tee "$OUT/gh_fork.out" 2> "$OUT/gh_fork.err" || true
  fi

  git push -u heath "$BRANCH" | tee "$OUT/external_push.out" 2> "$OUT/external_push.err"

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
  echo "To open a draft PR after inspecting artifacts:"
  echo "OPEN_QOJULIA_PR=1 bash qojulia_407_smoke_runner_patch_v10.sh"
fi
echo

echo "11 commit MathGraph artifact"
cd "$ROOT"
git add "$OUT" qojulia_407_smoke_runner_patch_v10.sh
git commit -m "Patch qojulia benchmark smoke gate v10" || true
git push origin local-main || true
echo

echo "12 final"
git status --short
df -h /
echo
echo "Artifacts:"
echo "$OUT/PATCH_REPORT.md"
echo "$OUT/decision.json"
echo "$OUT/local_smoke.out"
echo "$OUT/local_smoke.err"
echo "$OUT/patch_diff.txt"
echo "$OUT/external_commit.out"
echo "$OUT/pr_create.out"
