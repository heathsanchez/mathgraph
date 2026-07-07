#!/usr/bin/env bash
set -euo pipefail

echo "MathGraph tinygrad #3039 Architecture Probe v25"
echo "Goal: no-install probe for whether associative/parallel scan has a small testable patch path."
echo

ROOT="/Users/heath/Documents/mathgraph-lean-work"
REPO="$ROOT/external/cash_win_deep_recon_v24/tinygrad__tinygrad_3039"
OUT="$ROOT/artifacts/tinygrad_3039_arch_probe_v25"
mkdir -p "$OUT"

echo "01 status"
date -u +"%Y-%m-%dT%H:%M:%SZ" | tee "$OUT/status_start.txt"
df -h / | tee "$OUT/df_start.txt"
cd "$ROOT"
git status --short | tee "$OUT/mathgraph_status_start.txt" || true
echo

echo "02 repo gate"
cd "$REPO"
git status --short | tee "$OUT/repo_status_start.txt" || true
git rev-parse HEAD | tee "$OUT/head.txt"
echo

echo "03 source map"
{
  echo "===== top files ====="
  find . -maxdepth 3 -type f | sed 's#^\./##' | sort | head -500
  echo
  echo "===== tensor and op files ====="
  find tinygrad test -type f | grep -E 'tensor|ops|uop|schedule|lower|realize|gradient|test' | sort | head -500
} | tee "$OUT/source_map.txt"
echo

echo "04 scan architecture refs"
{
  echo "===== scan/cumsum/cumprod refs ====="
  grep -RIn --exclude-dir=.git --exclude-dir=.venv --exclude-dir=__pycache__ --exclude-dir=.mypy_cache \
    "cumsum\|cumprod\|associative_scan\|parallel scan\|prefix sum\|scan(" tinygrad test examples extra 2>/dev/null | head -1000 || true
  echo
  echo "===== reduce refs ====="
  grep -RIn --exclude-dir=.git --exclude-dir=.venv --exclude-dir=__pycache__ --exclude-dir=.mypy_cache \
    "ReduceOps\|reduce_axis\|_reduce\|sum(self\|prod(self\|max(self\|where(" tinygrad test 2>/dev/null | head -1000 || true
  echo
  echo "===== mamba refs ====="
  grep -RIn --exclude-dir=.git --exclude-dir=.venv --exclude-dir=__pycache__ --exclude-dir=.mypy_cache \
    "mamba\|selective_scan\|ssm\|state space" tinygrad test examples extra 2>/dev/null | head -1000 || true
} | tee "$OUT/arch_refs.txt"
echo

echo "05 lightweight import verifier"
python3 - <<'PY' > "$OUT/import_probe.out" 2> "$OUT/import_probe.err" || true
import sys
sys.path.insert(0, ".")
try:
    import tinygrad
    print("IMPORT_TINYGRAD_OK", tinygrad)
except Exception as e:
    print("IMPORT_TINYGRAD_FAIL", type(e).__name__, str(e))
try:
    from tinygrad import Tensor
    print("IMPORT_TENSOR_OK", Tensor)
    x = Tensor([1,2,3,4])
    print("TENSOR_CREATE_OK", x)
    for name in ["cumsum", "cumprod"]:
        print(name, hasattr(x, name))
except Exception as e:
    print("TENSOR_PROBE_FAIL", type(e).__name__, str(e))
PY
cat "$OUT/import_probe.out"
cat "$OUT/import_probe.err"
echo

echo "06 inspect likely files"
python3 - "$OUT" <<'PY'
from pathlib import Path
import re, sys, json

out = Path(sys.argv[1])
repo = Path.cwd()

candidates = [
  "tinygrad/tensor.py",
  "tinygrad/ops.py",
  "tinygrad/uop/ops.py",
  "test/test_tensor.py",
  "test/test_ops.py",
]

snaps = out / "snaps"
snaps.mkdir(exist_ok=True)

for rel in candidates:
    p = repo / rel
    if p.exists():
        (snaps / (rel.replace("/", "__") + ".txt")).write_text(p.read_text(errors="replace"))

analysis = {}
for rel in candidates:
    p = repo / rel
    if not p.exists():
        continue
    txt = p.read_text(errors="replace")
    hits = []
    for i, line in enumerate(txt.splitlines(), 1):
        if re.search(r"cumsum|cumprod|sum\(|prod\(|ReduceOps|reduce|scan|where|cat|pad|slice", line):
            hits.append((i, line[:240]))
    analysis[rel] = hits[:300]

(out / "likely_file_hits.json").write_text(json.dumps(analysis, indent=2) + "\n")

md = []
md.append("# tinygrad #3039 Architecture Probe v25")
md.append("")
md.append("## Files inspected")
md.append("")
for rel in candidates:
    md.append(f"- `{rel}` exists: `{(repo / rel).exists()}`")
md.append("")
md.append("## Key hit counts")
md.append("")
for rel, hits in analysis.items():
    md.append(f"- `{rel}`: `{len(hits)}` relevant hits")
md.append("")
md.append("## Initial patch hypothesis")
md.append("")
md.append("Do not implement full Mamba acceleration first. Look for a minimal Tensor-level associative_scan API or a cumsum/cumprod-like primitive with tests. If tinygrad already has cumsum/cumprod, derive the smallest general associative_scan surface from existing scan/reduce machinery. If there is no obvious lowerer path, park before claiming.")
(out / "ARCH_REPORT.md").write_text("\n".join(md) + "\n")
print((out / "ARCH_REPORT.md").read_text())
PY
echo

echo "07 commit artifact"
cd "$ROOT"
git add "$OUT" tinygrad_3039_arch_probe_v25.sh
git commit -m "Probe tinygrad associative scan bounty v25" || true
git push origin local-main || true
echo

echo "08 final"
git status --short
df -h /
echo
echo "Artifacts:"
echo "$OUT/ARCH_REPORT.md"
echo "$OUT/arch_refs.txt"
echo "$OUT/import_probe.out"
echo "$OUT/likely_file_hits.json"
echo "$OUT/source_map.txt"
