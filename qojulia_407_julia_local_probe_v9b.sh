#!/usr/bin/env bash
set -euo pipefail

ROOT="/Users/heath/Documents/mathgraph-lean-work"
REPO_DIR="$ROOT/external/money_gold_recon_v6/qojulia__QuantumOptics.jl_407"
OUT="$ROOT/artifacts/qojulia_407_julia_local_probe_v9b"
JULIA_BIN="${JULIA_BIN:-$HOME/.juliaup/bin/julia}"

mkdir -p "$OUT"
cd "$ROOT"

echo "MathGraph qojulia/QuantumOptics.jl #407 Julia Local Probe v9b"
echo "Goal: repair v9 PATH bug and get real benchmark-suite signal."
echo

echo "01 status"
date -u +"%Y-%m-%dT%H:%M:%SZ" | tee "$OUT/status_start.txt"
df -h / | tee "$OUT/df_start.txt"
git status --short | tee "$OUT/git_status_start.txt" || true
echo

echo "02 locate Julia"
{
  echo "JULIA_BIN=$JULIA_BIN"
  if [ ! -x "$JULIA_BIN" ]; then
    echo "Expected Julia binary not executable: $JULIA_BIN"
    echo "Trying command -v julia..."
    command -v julia || true
    exit 2
  fi
  "$JULIA_BIN" --version
  "$JULIA_BIN" -e 'println("Sys.BINDIR=", Sys.BINDIR); println("VERSION=", VERSION)'
} 2>&1 | tee "$OUT/julia_locate.log"
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

echo "04 write probes"
cat > "$OUT/probe_benchmark_include.jl" <<'JL'
using Pkg
println("Julia version: ", VERSION)
println("Root project before activate: ", Base.active_project())

Pkg.activate("benchmark")
println("Activated benchmark project: ", Base.active_project())

println("Instantiating benchmark project...")
Pkg.instantiate()

println("Loading benchmark/benchmarks.jl ...")
include("benchmark/benchmarks.jl")

println("SUITE type: ", typeof(SUITE))
println("Top-level benchmark groups:")
for k in keys(SUITE)
    println("  - ", repr(k))
end

println("Nested groups:")
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

candidates = [
    ("schroedinger", "base array types", "1//2"),
    ("schroedinger", "qo types", "1//2"),
    ("master", "base array types", "1//2"),
    ("master", "qo types", "1//2"),
]

picked = nothing
for (a,b,c) in candidates
    if haskey(SUITE, a) && haskey(SUITE[a], b) && haskey(SUITE[a][b], c)
        global picked = (a,b,c)
        break
    end
end

if picked === nothing
    println("Available SUITE shape:")
    for a in keys(SUITE)
        println("A=", repr(a), " keys=", collect(keys(SUITE[a])))
    end
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

cat > "$OUT/probe_pkg_status.jl" <<'JL'
using Pkg
Pkg.activate("benchmark")
Pkg.status()
JL

cp "$OUT/probe_benchmark_include.jl" "$REPO_DIR/.mathgraph_probe_benchmark_include.jl"
cp "$OUT/probe_one_tiny_benchmark.jl" "$REPO_DIR/.mathgraph_probe_one_tiny_benchmark.jl"
cp "$OUT/probe_pkg_status.jl" "$REPO_DIR/.mathgraph_probe_pkg_status.jl"
echo "wrote probes"
echo

echo "05 benchmark project status"
cd "$REPO_DIR"
set +e
"$JULIA_BIN" .mathgraph_probe_pkg_status.jl > "$OUT/pkg_status.out" 2> "$OUT/pkg_status.err"
PKG_RC=$?
set -e
echo "pkg status rc=$PKG_RC" | tee "$OUT/pkg_status.rc"
tail -80 "$OUT/pkg_status.out" || true
tail -80 "$OUT/pkg_status.err" || true
echo

echo "06 run benchmark include probe"
set +e
"$JULIA_BIN" .mathgraph_probe_benchmark_include.jl > "$OUT/probe_include.out" 2> "$OUT/probe_include.err"
INCLUDE_RC=$?
set -e
echo "include rc=$INCLUDE_RC" | tee "$OUT/probe_include.rc"
tail -100 "$OUT/probe_include.out" || true
tail -100 "$OUT/probe_include.err" || true
echo

echo "07 run tiny benchmark if include passed"
TINY_RC=999
if [ "$INCLUDE_RC" -eq 0 ]; then
  set +e
  "$JULIA_BIN" .mathgraph_probe_one_tiny_benchmark.jl > "$OUT/probe_tiny.out" 2> "$OUT/probe_tiny.err"
  TINY_RC=$?
  set -e
else
  echo "Skipping tiny benchmark because include failed." > "$OUT/probe_tiny.out"
  : > "$OUT/probe_tiny.err"
fi
echo "tiny rc=$TINY_RC" | tee "$OUT/probe_tiny.rc"
tail -100 "$OUT/probe_tiny.out" || true
tail -100 "$OUT/probe_tiny.err" || true
echo

echo "08 inspect patch surface"
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
  echo "===== benchmark/benchmarks.jl head ====="
  sed -n '1,180p' benchmark/benchmarks.jl || true
  echo
  echo "===== README / CLAUDE benchmark docs ====="
  grep -Rni --exclude-dir=.git "benchmark" README.md CLAUDE.md docs/src docs 2>/dev/null | head -100 || true
} > "$OUT/workflow_and_docs_surface.txt"
cat "$OUT/workflow_and_docs_surface.txt" | head -260
echo

echo "09 classify"
cd "$ROOT"
python3 - <<'PY'
from pathlib import Path
import json

out = Path("/Users/heath/Documents/mathgraph-lean-work/artifacts/qojulia_407_julia_local_probe_v9b")

def read(name):
    p = out / name
    return p.read_text(errors="replace") if p.exists() else ""

pkg_rc = read("pkg_status.rc").strip()
include_rc = read("probe_include.rc").strip()
tiny_rc = read("probe_tiny.rc").strip()

pkg_ok = pkg_rc.endswith("=0")
include_ok = include_rc.endswith("=0")
tiny_ok = tiny_rc.endswith("=0")

if include_ok and tiny_ok:
    verdict = "PATCH_NEXT_SMOKE_RUNNER_AND_CI"
elif include_ok and not tiny_ok:
    verdict = "PATCH_NEXT_TINY_EXECUTION_REPAIR"
elif pkg_ok and not include_ok:
    verdict = "PATCH_NEXT_BENCHMARK_LOAD_REPAIR"
else:
    verdict = "PATCH_NEXT_PROJECT_INSTANTIATE_REPAIR"

decision = {
    "verdict": verdict,
    "issue": "https://github.com/qojulia/QuantumOptics.jl/issues/407",
    "claim": "https://github.com/qojulia/QuantumOptics.jl/issues/407#issuecomment-4900216240",
    "julia_path_bug_repaired": True,
    "pkg_ok": pkg_ok,
    "include_ok": include_ok,
    "tiny_benchmark_ok": tiny_ok,
    "pkg_rc": pkg_rc,
    "include_rc": include_rc,
    "tiny_rc": tiny_rc,
}

(out / "decision.json").write_text(json.dumps(decision, indent=2) + "\n")

md = []
md.append("# qojulia #407 Julia Local Probe v9b")
md.append("")
md.append("## Verdict")
md.append("")
md.append(f"`{verdict}`")
md.append("")
md.append("## Result")
md.append("")
md.append(f"- benchmark project status: `{pkg_rc}`")
md.append(f"- benchmark include/load: `{include_rc}`")
md.append(f"- one tiny benchmark: `{tiny_rc}`")
md.append("")
md.append("## Corrected interpretation")
md.append("")
if verdict == "PATCH_NEXT_SMOKE_RUNNER_AND_CI":
    md.append("The existing benchmark suite loads and a tiny benchmark runs. v10 should add a narrow smoke runner, docs, and safe CI wiring.")
elif verdict == "PATCH_NEXT_TINY_EXECUTION_REPAIR":
    md.append("The suite loads, but executing a tiny benchmark fails. v10 should repair benchmark execution, then add the smoke runner.")
elif verdict == "PATCH_NEXT_BENCHMARK_LOAD_REPAIR":
    md.append("The benchmark project instantiates, but `benchmark/benchmarks.jl` does not load. v10 should repair import/API drift first.")
else:
    md.append("The benchmark project itself does not instantiate. v10 should repair benchmark dependencies/compat first.")
md.append("")
md.append("## v10 patch route")
md.append("")
md.append("1. Work on a branch in the external QuantumOptics checkout.")
md.append("2. Patch only the narrow smoke path first.")
md.append("3. Verify locally with Julia 1.10.")
md.append("4. Open PR only if local smoke passes.")
md.append("")
md.append("## Files")
md.append("")
md.append("- `pkg_status.out` / `pkg_status.err`")
md.append("- `probe_include.out` / `probe_include.err`")
md.append("- `probe_tiny.out` / `probe_tiny.err`")
md.append("- `workflow_and_docs_surface.txt`")
md.append("- `decision.json`")
md.append("")
(out / "PROBE_REPORT.md").write_text("\n".join(md) + "\n")
print((out / "PROBE_REPORT.md").read_text())
PY
echo

echo "10 cleanup probe files"
rm -f "$REPO_DIR/.mathgraph_probe_benchmark_include.jl" "$REPO_DIR/.mathgraph_probe_one_tiny_benchmark.jl" "$REPO_DIR/.mathgraph_probe_pkg_status.jl"
git -C "$REPO_DIR" status --short | tee "$OUT/external_repo_status_after_cleanup.txt"
echo

echo "11 commit artifact"
cd "$ROOT"
git add "$OUT" qojulia_407_julia_local_probe_v9b.sh
git commit -m "Repair qojulia Julia probe path v9b" || true
git push origin local-main || true
echo

echo "12 final"
git status --short
df -h /
echo
echo "Artifacts:"
echo "$OUT/PROBE_REPORT.md"
echo "$OUT/decision.json"
echo "$OUT/pkg_status.out"
echo "$OUT/pkg_status.err"
echo "$OUT/probe_include.out"
echo "$OUT/probe_include.err"
echo "$OUT/probe_tiny.out"
echo "$OUT/probe_tiny.err"
echo "$OUT/workflow_and_docs_surface.txt"
