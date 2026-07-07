#!/usr/bin/env bash
set -euo pipefail

ROOT="/Users/heath/Documents/mathgraph-lean-work"
REPO_DIR="$ROOT/external/money_gold_recon_v6/qojulia__QuantumOptics.jl_407"
OUT="$ROOT/artifacts/qojulia_407_julia_local_probe_v9"
ISSUE_URL="https://github.com/qojulia/QuantumOptics.jl/issues/407"
CLAIM_URL="https://github.com/qojulia/QuantumOptics.jl/issues/407#issuecomment-4900216240"

mkdir -p "$OUT"
cd "$ROOT"

echo "MathGraph qojulia/QuantumOptics.jl #407 Julia Local Probe v9"
echo "Goal: install/locate Julia, verify benchmark project, and decide if v10 patch is safe."
echo

echo "01 status"
date -u +"%Y-%m-%dT%H:%M:%SZ" | tee "$OUT/status_start.txt"
df -h / | tee "$OUT/df_start.txt"
git status --short | tee "$OUT/git_status_start.txt" || true
echo

echo "02 ensure Julia 1.10 via juliaup"
{
  set +e
  command -v julia
  JRC=$?
  command -v juliaup
  URC=$?
  set -e

  if [ "$JRC" -ne 0 ]; then
    echo "julia not found."
    if [ "$URC" -ne 0 ]; then
      echo "juliaup not found; installing juliaup non-interactively."
      curl -fsSL https://install.julialang.org | sh -s -- -y --default-channel=1.10
    else
      echo "juliaup found."
    fi
    export PATH="$HOME/.juliaup/bin:$PATH"
  else
    echo "julia found: $(command -v julia)"
  fi

  export PATH="$HOME/.juliaup/bin:$PATH"

  if command -v juliaup >/dev/null 2>&1; then
    juliaup add 1.10 || true
    juliaup default 1.10 || true
  fi

  echo "PATH=$PATH"
  command -v julia || true
  julia --version || true
} 2>&1 | tee "$OUT/julia_install.log"
echo

echo "03 refresh QuantumOptics checkout"
if [ ! -d "$REPO_DIR/.git" ]; then
  mkdir -p "$(dirname "$REPO_DIR")"
  git clone --filter=blob:none "https://github.com/qojulia/QuantumOptics.jl.git" "$REPO_DIR" 2>&1 | tee "$OUT/clone.log"
else
  git -C "$REPO_DIR" fetch origin 2>&1 | tee "$OUT/git_fetch.log" || true
  git -C "$REPO_DIR" checkout master 2>&1 | tee "$OUT/git_checkout.log" || true
  git -C "$REPO_DIR" pull --ff-only origin master 2>&1 | tee "$OUT/git_pull.log" || true
fi
git -C "$REPO_DIR" rev-parse HEAD | tee "$OUT/head.txt"
echo

echo "04 write Julia probe scripts"
cat > "$OUT/probe_benchmark_include.jl" <<'JL'
using Pkg
println("Julia version: ", VERSION)
println("Project: ", Base.active_project())

Pkg.activate("benchmark")
Pkg.instantiate()

println("Activated benchmark project: ", Base.active_project())
println("Loading benchmark/benchmarks.jl ...")
include("benchmark/benchmarks.jl")

println("SUITE type: ", typeof(SUITE))
println("Top-level benchmark groups:")
for k in keys(SUITE)
    println("  - ", repr(k))
end

expected = ["schroedinger", "master", "stochastic_schroedinger", "stochastic_master"]
println("Expected old prob_list labels:")
for k in expected
    println("  ", k, " present=", haskey(SUITE, k))
end

println("Actual nested groups:")
for k in keys(SUITE)
    println("GROUP ", repr(k), " => ", collect(keys(SUITE[k])))
end

println("INCLUDE_OK")
JL

cat > "$OUT/probe_one_tiny_benchmark.jl" <<'JL'
using Pkg
Pkg.activate("benchmark")
Pkg.instantiate()
include("benchmark/benchmarks.jl")

# Pick the smallest intended benchmark if present. This is deliberately tiny:
# it checks that the suite is runnable, not that timing numbers are stable.
candidates = [
    ("schroedinger", "base array types", "1//2"),
    ("schroedinger", "qo types", "1//2"),
    ("master", "base array types", "1//2"),
]

picked = nothing
for (a,b,c) in candidates
    if haskey(SUITE, a) && haskey(SUITE[a], b) && haskey(SUITE[a][b], c)
        global picked = (a,b,c)
        break
    end
end

if picked === nothing
    error("No tiny benchmark candidate found in SUITE")
end

a,b,c = picked
println("Running tiny benchmark candidate: ", picked)
bench = SUITE[a][b][c]
tune!(bench)
result = run(bench; seconds=0.25, samples=1, evals=1)
println(result)
println("TINY_BENCHMARK_OK")
JL

cp "$OUT/probe_benchmark_include.jl" "$REPO_DIR/.mathgraph_probe_benchmark_include.jl"
cp "$OUT/probe_one_tiny_benchmark.jl" "$REPO_DIR/.mathgraph_probe_one_tiny_benchmark.jl"
echo "wrote probes"
echo

echo "05 run benchmark include probe"
cd "$REPO_DIR"
set +e
julia .mathgraph_probe_benchmark_include.jl > "$OUT/probe_include.out" 2> "$OUT/probe_include.err"
INCLUDE_RC=$?
set -e
echo "include rc=$INCLUDE_RC" | tee "$OUT/probe_include.rc"
tail -80 "$OUT/probe_include.out" || true
tail -80 "$OUT/probe_include.err" || true
echo

echo "06 run one tiny benchmark probe only if include passed"
TINY_RC=999
if [ "$INCLUDE_RC" -eq 0 ]; then
  set +e
  julia .mathgraph_probe_one_tiny_benchmark.jl > "$OUT/probe_tiny.out" 2> "$OUT/probe_tiny.err"
  TINY_RC=$?
  set -e
else
  echo "Skipping tiny benchmark because include failed." > "$OUT/probe_tiny.out"
  : > "$OUT/probe_tiny.err"
fi
echo "tiny rc=$TINY_RC" | tee "$OUT/probe_tiny.rc"
tail -80 "$OUT/probe_tiny.out" || true
tail -80 "$OUT/probe_tiny.err" || true
echo

echo "07 inspect workflow safety"
cd "$REPO_DIR"
{
  echo "===== benchmark workflow ====="
  sed -n '1,220p' .github/workflows/benchmark.yml || true
  echo
  echo "===== CI workflow head ====="
  sed -n '1,180p' .github/workflows/ci.yml || true
  echo
  echo "===== benchmark Project.toml ====="
  cat benchmark/Project.toml || true
  echo
  echo "===== README benchmark mention ====="
  grep -Rni --exclude-dir=.git "benchmark" README.md CLAUDE.md docs/src docs 2>/dev/null | head -80 || true
} > "$OUT/workflow_and_docs_surface.txt"
cat "$OUT/workflow_and_docs_surface.txt" | head -220
echo

echo "08 classify"
cd "$ROOT"
python3 - <<'PY'
from pathlib import Path
import json

out = Path("/Users/heath/Documents/mathgraph-lean-work/artifacts/qojulia_407_julia_local_probe_v9")

def read(name):
    p = out / name
    return p.read_text(errors="replace") if p.exists() else ""

include_rc = read("probe_include.rc").strip()
tiny_rc = read("probe_tiny.rc").strip()
include_ok = include_rc.endswith("=0")
tiny_ok = tiny_rc.endswith("=0")

include_out = read("probe_include.out") + "\n" + read("probe_include.err")
tiny_out = read("probe_tiny.out") + "\n" + read("probe_tiny.err")

if include_ok and tiny_ok:
    verdict = "PATCH_NEXT_SMOKE_RUNNER_AND_CI"
elif include_ok and not tiny_ok:
    verdict = "PATCH_NEXT_BENCHMARK_RUNNER_BROKEN_AT_EXECUTION"
else:
    verdict = "PATCH_NEXT_BENCHMARK_PROJECT_LOAD_REPAIR"

decision = {
    "verdict": verdict,
    "issue": "https://github.com/qojulia/QuantumOptics.jl/issues/407",
    "claim": "https://github.com/qojulia/QuantumOptics.jl/issues/407#issuecomment-4900216240",
    "include_ok": include_ok,
    "tiny_benchmark_ok": tiny_ok,
    "include_rc": include_rc,
    "tiny_rc": tiny_rc,
}

(out / "decision.json").write_text(json.dumps(decision, indent=2) + "\n")

md = []
md.append("# qojulia #407 Julia Local Probe v9")
md.append("")
md.append("## Verdict")
md.append("")
md.append(f"`{verdict}`")
md.append("")
md.append("## Result")
md.append("")
md.append(f"- benchmark include/load: `{include_rc}`")
md.append(f"- one tiny benchmark: `{tiny_rc}`")
md.append(f"- claim posted: https://github.com/qojulia/QuantumOptics.jl/issues/407#issuecomment-4900216240")
md.append("")
md.append("## Interpretation")
md.append("")
if verdict == "PATCH_NEXT_SMOKE_RUNNER_AND_CI":
    md.append("The existing benchmark suite loads and at least one tiny benchmark runs. v10 should add a narrow smoke-runner script, docs, and safer CI wiring.")
elif verdict == "PATCH_NEXT_BENCHMARK_RUNNER_BROKEN_AT_EXECUTION":
    md.append("The benchmark suite loads, but executing a tiny benchmark fails. v10 should repair benchmark execution first, then add a smoke runner.")
else:
    md.append("The benchmark project or benchmark file does not load. v10 should first repair imports/dependencies/API drift before touching CI.")
md.append("")
md.append("## v10 patch shape")
md.append("")
md.append("1. Add `benchmark/run_smoke.jl` or equivalent narrow runner.")
md.append("2. Make the runner select a tiny subset and fail if the suite cannot load/run.")
md.append("3. Add a documented local command.")
md.append("4. Add or adjust GitHub Actions so PRs run only the smoke gate; full benchmark remains manual/scheduled.")
md.append("5. Do not implement QuTiP/QuantumToolbox comparative benchmark yet unless maintainer confirms that should be first.")
md.append("")
md.append("## Files")
md.append("")
md.append("- `probe_include.out` / `probe_include.err`")
md.append("- `probe_tiny.out` / `probe_tiny.err`")
md.append("- `workflow_and_docs_surface.txt`")
md.append("- `decision.json`")
md.append("")
(out / "PROBE_REPORT.md").write_text("\n".join(md) + "\n")
print((out / "PROBE_REPORT.md").read_text())
PY
echo

echo "09 cleanup probe files from external repo"
rm -f "$REPO_DIR/.mathgraph_probe_benchmark_include.jl" "$REPO_DIR/.mathgraph_probe_one_tiny_benchmark.jl"
git -C "$REPO_DIR" status --short | tee "$OUT/external_repo_status_after_cleanup.txt"
echo

echo "10 commit artifact"
cd "$ROOT"
git add "$OUT" qojulia_407_julia_local_probe_v9.sh
git commit -m "Probe qojulia benchmark suite locally v9" || true
git push origin local-main || true
echo

echo "11 final"
git status --short
df -h /
echo
echo "Artifacts:"
echo "$OUT/PROBE_REPORT.md"
echo "$OUT/decision.json"
echo "$OUT/probe_include.out"
echo "$OUT/probe_include.err"
echo "$OUT/probe_tiny.out"
echo "$OUT/probe_tiny.err"
echo "$OUT/workflow_and_docs_surface.txt"
