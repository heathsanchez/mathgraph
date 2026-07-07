#!/usr/bin/env bash
set -u

ROOT="/Users/heath/Documents/mathgraph-lean-work"
REPO="$ROOT/external/bounty_triage_v1/tinygrad__tinygrad_v3"
OUT="$ROOT/artifacts/bounty_triage_v1/tinygrad_3039_parallel_scan_probe_v4"

mkdir -p "$OUT"

echo "MathGraph tinygrad #3039 v4 — parallel scan probe"
echo

echo "01 status"
{
  date -u +"%Y-%m-%dT%H:%M:%SZ"
  df -h /
  git -C "$ROOT" status --short
  echo
  echo "repo:"
  git -C "$REPO" rev-parse HEAD 2>/dev/null || true
  du -sh "$REPO" 2>/dev/null || true
} | tee "$OUT/status_start.txt"

cd "$REPO" || exit 1

echo
echo "02 extract exact cumsum source"
python3 - "$REPO" "$OUT" <<'PY'
from pathlib import Path
import sys, re, json

repo = Path(sys.argv[1])
out = Path(sys.argv[2])
p = repo / "tinygrad/tensor.py"
txt = p.read_text(errors="replace")
lines = txt.splitlines()

targets = ["def cumsum", "def cummax", "def cumprod", "def sum", "def pad", "def shrink", "def reshape", "def where"]
chunks = []
found = {}
for target in targets:
    found[target] = []
    for i, l in enumerate(lines):
        if target in l:
            found[target].append(i + 1)
            chunks.append(f"\n===== {target} around line {i+1} =====")
            for j in range(max(0, i - 35), min(len(lines), i + 110)):
                chunks.append(f"{j+1:04d}: {lines[j]}")
            break

(out / "tensor_relevant_source.txt").write_text("\n".join(chunks) + "\n")
(out / "source_locations.json").write_text(json.dumps(found, indent=2))
print((out / "tensor_relevant_source.txt").read_text(errors="replace")[:50000])
PY

echo
echo "03 write experimental parallel scan helper"
cat > "$OUT/parallel_scan_probe.py" <<'PY'
from __future__ import annotations

def _norm_axis(axis: int, ndim: int) -> int:
  return axis + ndim if axis < 0 else axis

def _shift_right_zero(x, axis: int, offset: int):
  """Shift tensor right along axis by offset, filling left side with zero."""
  axis = _norm_axis(axis, len(x.shape))
  pads = [(0, 0)] * len(x.shape)
  pads[axis] = (offset, 0)
  y = x.pad(tuple(pads))

  slices = [(0, s) for s in x.shape]
  return y.shrink(tuple(slices))

def hillis_steele_cumsum(x, axis: int = 0):
  """Inclusive parallel-prefix sum using log2(n) staged shifted adds."""
  axis = _norm_axis(axis, len(x.shape))
  n = x.shape[axis]
  y = x
  step = 1
  while step < n:
    y = y + _shift_right_zero(y, axis, step)
    step *= 2
  return y
PY

cat "$OUT/parallel_scan_probe.py"

echo
echo "04 correctness probe"
PYTHONPATH="$REPO:$OUT" python3 - <<'PY' > "$OUT/correctness_probe.out" 2> "$OUT/correctness_probe.err" || true
from tinygrad import Tensor
from parallel_scan_probe import hillis_steele_cumsum

def tolist(t):
  return t.realize().numpy().tolist()

cases = [
  ("1d_1", Tensor.arange(1), 0),
  ("1d_2", Tensor.arange(2), 0),
  ("1d_3", Tensor.arange(3), 0),
  ("1d_4", Tensor.arange(4), 0),
  ("1d_7", Tensor.arange(7), 0),
  ("1d_16", Tensor.arange(16), 0),
  ("2d_axis0", Tensor.arange(12).reshape(3, 4), 0),
  ("2d_axis1", Tensor.arange(12).reshape(3, 4), 1),
  ("2d_axis_neg1", Tensor.arange(12).reshape(3, 4), -1),
]

all_ok = True
for name, x, axis in cases:
  got = tolist(hillis_steele_cumsum(x, axis))
  exp = tolist(x.cumsum(axis=axis))
  ok = got == exp
  all_ok = all_ok and ok
  print(name, "axis", axis, "ok", ok, "expected", exp, "got", got)

print("ALL_OK", all_ok)
PY
cat "$OUT/correctness_probe.out" || true
cat "$OUT/correctness_probe.err" || true

echo
echo "05 benchmark probe"
PYTHONPATH="$REPO:$OUT" python3 - <<'PY' > "$OUT/benchmark_probe.out" 2> "$OUT/benchmark_probe.err" || true
from tinygrad import Tensor
from parallel_scan_probe import hillis_steele_cumsum
import time, json, statistics, gc

sizes = [16, 32, 64, 128, 256, 512, 1024]
runs = 3
rows = []

def bench(label, fn):
  times = []
  err = None
  for _ in range(runs):
    try:
      gc.collect()
      t0 = time.perf_counter()
      y = fn()
      y.realize()
      _ = y.numpy()
      times.append(time.perf_counter() - t0)
    except Exception as e:
      err = type(e).__name__ + ": " + str(e)[:500]
      break
  return {
    "label": label,
    "ok": err is None,
    "err": err,
    "runs": times,
    "median": statistics.median(times) if times else None,
    "min": min(times) if times else None,
  }

for n in sizes:
  x = Tensor.arange(n)
  b0 = bench("builtin_cumsum", lambda x=x: x.cumsum())
  b1 = bench("hillis_steele_probe", lambda x=x: hillis_steele_cumsum(x))
  row = {"n": n, "builtin": b0, "probe": b1}
  rows.append(row)
  print(json.dumps(row, indent=2))

print("JSON_RESULT_START")
print(json.dumps(rows, indent=2))
print("JSON_RESULT_END")
PY
cat "$OUT/benchmark_probe.out" || true
cat "$OUT/benchmark_probe.err" || true

echo
echo "06 static graph/source complexity proxy"
python3 - "$REPO" "$OUT" <<'PY'
from pathlib import Path
import json, re, sys

repo = Path(sys.argv[1])
out = Path(sys.argv[2])

tensor = (repo / "tinygrad/tensor.py").read_text(errors="replace")
probe = (out / "parallel_scan_probe.py").read_text(errors="replace")

def method_body(src, name):
  lines = src.splitlines()
  start = None
  for i, l in enumerate(lines):
    if re.match(rf"\s+def {name}\(", l):
      start = i
      break
  if start is None:
    return ""
  indent = len(lines[start]) - len(lines[start].lstrip())
  end = len(lines)
  for j in range(start + 1, len(lines)):
    if lines[j].strip() and (len(lines[j]) - len(lines[j].lstrip())) <= indent and lines[j].lstrip().startswith("def "):
      end = j
      break
  return "\n".join(lines[start:end])

builtin = method_body(tensor, "cumsum")
counts = {}
for label, src in [("builtin_cumsum", builtin), ("probe_hillis_steele", probe)]:
  counts[label] = {
    "chars": len(src),
    "lines": src.count("\n") + 1 if src else 0,
    "pad": src.count(".pad"),
    "shrink": src.count(".shrink"),
    "sum": src.count(".sum"),
    "cat": src.count(".cat"),
    "where": src.count(".where"),
    "while": src.count("while "),
    "for": src.count("for "),
    "add_ops": src.count("+"),
    "pool": src.count("_pool") + src.count("pool"),
    "cum": src.count("cum"),
  }

(out / "complexity_proxy.json").write_text(json.dumps(counts, indent=2))
print(json.dumps(counts, indent=2))
PY

echo
echo "07 optional patch sketch"
cat > "$OUT/PATCH_SKETCH.md" <<'MD'
# tinygrad #3039 patch sketch

This probe does not patch tinygrad yet. It tests whether tinygrad's existing primitives can express a log-depth inclusive scan.

Candidate helper:

    def _shift_right_zero(x, axis, offset):
      pads = [(0, 0)] * len(x.shape)
      pads[axis] = (offset, 0)
      y = x.pad(tuple(pads))
      return y.shrink(tuple((0, s) for s in x.shape))

    def hillis_steele_cumsum(x, axis=0):
      y = x
      step = 1
      while step < x.shape[axis]:
        y = y + _shift_right_zero(y, axis, step)
        step *= 2
      return y

If correctness passes, the next real PR shape is one of:

1. Add a private helper for associative scan over addition and route Tensor.cumsum through it for supported static-shape cases.
2. Add Tensor.associative_scan(fn, axis=0) with cumsum as the first use case.
3. Add an experimental helper plus tests first, then optimize lowering/codegen after maintainer feedback.

A draft PR is only worthwhile if the probe shows correctness and either:
- better runtime for meaningful sizes, or
- clearer graph depth / operation-count improvement over the current implementation.
MD

echo
echo "08 generate report"
python3 - "$OUT" <<'PY'
import json, sys
from pathlib import Path

out = Path(sys.argv[1])

def read(name, limit=None):
  p = out / name
  if not p.exists():
    return ""
  s = p.read_text(errors="replace")
  return s if limit is None else s[:limit]

correct = read("correctness_probe.out") + read("correctness_probe.err")
bench = read("benchmark_probe.out") + read("benchmark_probe.err")
source = read("tensor_relevant_source.txt", 35000)
complexity = {}
try:
  complexity = json.loads((out / "complexity_proxy.json").read_text())
except Exception:
  pass

all_ok = "ALL_OK True" in correct
bench_has_json = "JSON_RESULT_START" in bench
probe_worked = all_ok and bench_has_json
verdict = "PROMOTE_TO_PATCH_DESIGN_V5" if probe_worked else "FIX_PROBE_FIRST"

lines = []
lines.append("# tinygrad/tinygrad #3039 Parallel Scan Probe v4")
lines.append("")
lines.append("## Verdict")
lines.append("")
lines.append(f"`{verdict}`")
lines.append("")
lines.append("## Result")
lines.append("")
lines.append(f"- correctness passed: `{all_ok}`")
lines.append(f"- benchmark produced data: `{bench_has_json}`")
lines.append(f"- probe route usable: `{probe_worked}`")
lines.append("")
lines.append("## Interpretation")
lines.append("")
if probe_worked:
  lines.append("The existing tinygrad primitives can express a Hillis-Steele/tree-style inclusive cumsum. Next step is a surgical patch design against Tensor.cumsum or a new associative_scan helper, with tests.")
else:
  lines.append("The candidate route failed locally. Inspect the error before touching tinygrad source.")
lines.append("")
lines.append("## Complexity proxy")
lines.append("")
lines.append("JSON:")
lines.append(json.dumps(complexity, indent=2))
lines.append("")
lines.append("## Correctness probe")
lines.append("")
lines.append(correct[:20000])
lines.append("")
lines.append("## Benchmark probe")
lines.append("")
lines.append(bench[:30000])
lines.append("")
lines.append("## Relevant Tensor source")
lines.append("")
lines.append(source)
lines.append("")
lines.append("## Patch sketch")
lines.append("")
lines.append(read("PATCH_SKETCH.md", 12000))
lines.append("")
lines.append("## Next action")
lines.append("")
if probe_worked:
  lines.append("Run v5: create a small branch, add a guarded associative_scan/cumsum patch plus tests, run targeted tests, and only then decide whether to open a draft PR to lock the bounty.")
else:
  lines.append("Do not patch. Repair the probe first.")
lines.append("")
(out / "REPORT.md").write_text("\n".join(lines) + "\n")
print((out / "REPORT.md").read_text())
PY

echo
echo "09 commit artifact"
cd "$ROOT" || exit 1
git add "$OUT" tinygrad_3039_parallel_scan_probe_v4.sh
git commit -m "Add tinygrad issue3039 parallel scan probe v4" || true
git push origin local-main || true

echo
echo "10 final status"
git status --short
df -h /
du -sh "$REPO" 2>/dev/null || true
echo
echo "Artifacts:"
echo "$OUT/REPORT.md"
echo "$OUT/parallel_scan_probe.py"
echo "$OUT/correctness_probe.out"
echo "$OUT/benchmark_probe.out"
echo "$OUT/tensor_relevant_source.txt"
echo "$OUT/complexity_proxy.json"
