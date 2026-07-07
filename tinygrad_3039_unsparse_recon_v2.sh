#!/usr/bin/env bash
set -u

ROOT="/Users/heath/Documents/mathgraph-lean-work"
REPO="$ROOT/external/bounty_triage_v1/tinygrad__tinygrad"
OUT="$ROOT/artifacts/bounty_triage_v1/tinygrad_3039_unsparse_recon_v2"

mkdir -p "$OUT"

echo "MathGraph tinygrad #3039 v2 — unsparse real code checkout + scan surface"
echo

cd "$REPO" || exit 1

echo "01 repo status before"
{
  git rev-parse HEAD
  git status --short
  echo
  echo "sparse-checkout:"
  git sparse-checkout list 2>/dev/null || true
  echo
  echo "disk:"
  df -h /
  du -sh "$REPO" 2>/dev/null || true
} | tee "$OUT/status_before.txt"

echo
echo "02 materialize tinygrad/test directories"
# Keep it targeted rather than full repo to protect disk.
git sparse-checkout set tinygrad test examples docs extra sz.py README.md pyproject.toml 2>&1 | tee "$OUT/sparse_set.log" || {
  echo "[fallback] sparse-checkout set failed; trying disable"
  git sparse-checkout disable 2>&1 | tee "$OUT/sparse_disable.log" || true
}

git checkout master 2>&1 | tee "$OUT/checkout_master.log" || true
git pull --ff-only origin master 2>&1 | tee "$OUT/pull_master.log" || true

echo
echo "03 repo status after"
{
  git rev-parse HEAD
  git status --short
  echo
  echo "top dirs:"
  find . -maxdepth 2 -type d | sed 's#^\./##' | sort | head -200
  echo
  echo "python files count:"
  find tinygrad test -type f -name '*.py' 2>/dev/null | wc -l
  echo
  echo "disk:"
  df -h /
  du -sh "$REPO" 2>/dev/null || true
} | tee "$OUT/status_after.txt"

echo
echo "04 local import smoke"
PYTHONPATH="$REPO" python3 - <<'PY' > "$OUT/import_smoke.out" 2> "$OUT/import_smoke.err" || true
import tinygrad
from tinygrad import Tensor
print("tinygrad", tinygrad.__file__)
print("Tensor", Tensor)
for name in ["cumsum", "cummax", "cumprod", "sum", "where", "cat", "stack"]:
    print(name, hasattr(Tensor, name))
PY

cat "$OUT/import_smoke.out" || true
cat "$OUT/import_smoke.err" || true

echo
echo "05 focused grep"
{
  echo "===== scan/cumsum/prefix/mamba/selective_scan hits ====="
  grep -RInE --exclude-dir=.git --exclude-dir=__pycache__ \
    "associative_scan|parallel_scan|selective_scan|scan\\(|cumsum|cumprod|cummax|prefix|mamba|state space|ssm|recurrence" \
    tinygrad test examples extra docs 2>/dev/null | head -3000

  echo
  echo "===== Tensor method / movement / reduce contexts ====="
  grep -RInE --exclude-dir=.git --exclude-dir=__pycache__ \
    "def cumsum|def cumprod|def cummax|def _pool|def _apply|class Tensor|Reduce|Ops\\.ADD|Ops\\.MUL|Ops\\.MAX|contiguous|permute|pad|cat|stack" \
    tinygrad/tensor.py tinygrad/uop tinygrad/codegen tinygrad/schedule test 2>/dev/null | head -3000
} | tee "$OUT/focused_grep.txt"

echo
echo "06 candidate map"
python3 - "$REPO" "$OUT" <<'PY'
import json, re, sys
from pathlib import Path

repo = Path(sys.argv[1])
out = Path(sys.argv[2])

terms = {
  "associative_scan": 30, "parallel_scan": 30, "selective_scan": 30,
  "cumsum": 24, "cumprod": 20, "cummax": 18, "scan": 10,
  "prefix": 12, "mamba": 20, "ssm": 12, "recurrence": 10,
  "reduce": 8, "ops.add": 8, "ops.mul": 8, "ops.max": 8,
  "tensor": 3, "uop": 4, "schedule": 4, "kernel": 4, "lower": 4,
  "test": 2,
}
roots = ["tinygrad", "test", "examples", "extra", "docs"]
cands = []
for root in roots:
    base = repo / root
    if not base.exists(): continue
    for p in base.rglob("*"):
        if not p.is_file() or p.suffix not in {".py", ".md", ".txt", ".ipynb"}: continue
        try: txt = p.read_text(errors="replace")
        except Exception: continue
        low = txt.lower()
        hits, score = {}, 0
        for t,w in terms.items():
            c = low.count(t)
            if c:
                hits[t] = c
                score += c*w
        if score:
            cands.append({
              "path": str(p.relative_to(repo)),
              "score": score,
              "hits": hits,
              "lines": txt.count("\n")+1,
              "bytes": len(txt.encode(errors="replace")),
            })

cands.sort(key=lambda x: (-x["score"], x["path"]))
(out / "candidate_files.json").write_text(json.dumps(cands[:500], indent=2))

pat = re.compile(r"(associative_scan|parallel_scan|selective_scan|cumsum|cumprod|cummax|scan|prefix|mamba|ssm|recurrence|def sum|def max|Reduce|Ops\.ADD|Ops\.MUL|Ops\.MAX)", re.I)
snips = []
for item in cands[:80]:
    p = repo / item["path"]
    try: lines = p.read_text(errors="replace").splitlines()
    except Exception: continue
    hit_lines = [i for i,l in enumerate(lines) if pat.search(l)]
    if not hit_lines: continue
    snips.append(f"\n\n===== {item['path']} score={item['score']} =====")
    used = []
    for h in hit_lines[:12]:
        start, end = max(0,h-18), min(len(lines),h+28)
        if any(abs(start-s) < 12 for s,e in used): continue
        used.append((start,end))
        snips.append(f"\n--- around line {h+1} ---")
        for i in range(start,end):
            snips.append(f"{i+1:04d}: {lines[i]}")
(out / "candidate_context.txt").write_text("\n".join(snips) + "\n")

summary = {
  "candidate_count": len(cands),
  "top_candidate_files": cands[:50],
  "has_tensor_py": (repo/"tinygrad/tensor.py").exists(),
  "has_tests": (repo/"test").exists(),
}
(out / "analysis_summary.json").write_text(json.dumps(summary, indent=2))
print(json.dumps(summary, indent=2)[:30000])
PY

echo
echo "07 tiny local behavioral probe for existing cumsum"
PYTHONPATH="$REPO" python3 - <<'PY' > "$OUT/cumsum_probe.out" 2> "$OUT/cumsum_probe.err" || true
from tinygrad import Tensor
import time

def show(expr, fn):
    try:
        t0 = time.time()
        y = fn()
        if hasattr(y, "realize"): y.realize()
        print(expr, "OK", "elapsed", round(time.time()-t0, 6), "shape", getattr(y, "shape", None))
    except Exception as e:
        print(expr, "FAIL", type(e).__name__, str(e)[:500])

x = Tensor.arange(16)
show("Tensor.arange(16).cumsum()", lambda: x.cumsum())
show("Tensor.arange(16).reshape(4,4).cumsum(axis=0)", lambda: Tensor.arange(16).reshape(4,4).cumsum(axis=0))
show("Tensor.arange(16).reshape(4,4).cumsum(axis=1)", lambda: Tensor.arange(16).reshape(4,4).cumsum(axis=1))
PY

cat "$OUT/cumsum_probe.out" || true
cat "$OUT/cumsum_probe.err" || true

echo
echo "08 generate report"
python3 - "$OUT" <<'PY'
import json
import sys
from pathlib import Path

out = Path(sys.argv[1])

def read(name, limit=None):
    p = out / name
    if not p.exists(): return ""
    s = p.read_text(errors="replace")
    return s if limit is None else s[:limit]

def load(name, default):
    try: return json.loads((out/name).read_text())
    except Exception: return default

summary = load("analysis_summary.json", {})
smoke = read("import_smoke.out") + read("import_smoke.err")
probe = read("cumsum_probe.out") + read("cumsum_probe.err")
top = summary.get("top_candidate_files", [])

has_import = "tinygrad" in smoke and "Tensor" in smoke and "ModuleNotFoundError" not in smoke
has_cumsum = "cumsum True" in smoke
probe_ok = "cumsum() OK" in probe or "cumsum(axis" in probe
has_candidates = bool(top)

if has_import and has_cumsum and has_candidates:
    verdict = "PATCH_PROBE_NEXT"
else:
    verdict = "RECON_STILL_BLOCKED"

lines = []
lines.append("# tinygrad/tinygrad #3039 Unsparse Recon v2")
lines.append("")
lines.append("## Verdict")
lines.append("")
lines.append(f"`{verdict}`")
lines.append("")
lines.append("## Correction")
lines.append("")
lines.append("v1 was a false negative: the local checkout was sparse/top-level only. v2 materialized `tinygrad/` and `test/` before scanning.")
lines.append("")
lines.append("## Signals")
lines.append("")
lines.append(f"- local import works: `{has_import}`")
lines.append(f"- Tensor has cumsum: `{has_cumsum}`")
lines.append(f"- cumsum behavioral probe: `{probe_ok}`")
lines.append(f"- candidate files found: `{summary.get('candidate_count')}`")
lines.append("")
lines.append("## Top candidate files")
lines.append("")
lines.append("```json")
lines.append(json.dumps(top[:40], indent=2))
lines.append("```")
lines.append("")
lines.append("## Import smoke")
lines.append("")
lines.append("```text")
lines.append(smoke[:8000])
lines.append("```")
lines.append("")
lines.append("## Cumsum probe")
lines.append("")
lines.append("```text")
lines.append(probe[:8000])
lines.append("```")
lines.append("")
lines.append("## Candidate context")
lines.append("")
lines.append("```text")
lines.append(read("candidate_context.txt", 50000))
lines.append("```")
lines.append("")
lines.append("## Next action")
lines.append("")
if verdict == "PATCH_PROBE_NEXT":
    lines.append("Build a tiny benchmark and patch probe around existing `Tensor.cumsum`. Goal: understand whether current implementation is serial-ish and whether a tree/associative scan route can improve graph depth or runtime.")
else:
    lines.append("Do not patch yet; inspect sparse/materialization failure.")
lines.append("")
(out/"REPORT.md").write_text("\n".join(lines) + "\n")
print((out/"REPORT.md").read_text())
PY

echo
echo "09 commit artifact"
cd "$ROOT" || exit 1
git add "$OUT" tinygrad_3039_unsparse_recon_v2.sh
git commit -m "Add tinygrad issue3039 unsparse recon v2" || true
git push origin local-main || true

echo
echo "10 final status"
git status --short
df -h /
du -sh "$REPO" 2>/dev/null || true
echo
echo "Artifacts:"
echo "$OUT/REPORT.md"
echo "$OUT/analysis_summary.json"
echo "$OUT/candidate_context.txt"
echo "$OUT/cumsum_probe.out"
