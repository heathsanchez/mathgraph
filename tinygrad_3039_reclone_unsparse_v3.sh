#!/usr/bin/env bash
set -u

ROOT="/Users/heath/Documents/mathgraph-lean-work"
OLD="$ROOT/external/bounty_triage_v1/tinygrad__tinygrad"
REPO="$ROOT/external/bounty_triage_v1/tinygrad__tinygrad_v3"
OUT="$ROOT/artifacts/bounty_triage_v1/tinygrad_3039_reclone_unsparse_v3"

mkdir -p "$OUT" "$ROOT/external/bounty_triage_v1"

echo "MathGraph tinygrad #3039 v3 — clean targeted sparse reclone"
echo

echo "01 disk/status"
{
  date -u +"%Y-%m-%dT%H:%M:%SZ"
  df -h /
  git -C "$ROOT" status --short
  du -sh "$OLD" 2>/dev/null || true
  du -sh "$REPO" 2>/dev/null || true
} | tee "$OUT/status_start.txt"

echo
echo "02 remove failed tinygrad_v3 if present"
rm -rf "$REPO"

echo
echo "03 clone sparse tinygrad"
git clone --depth=1 --filter=blob:none --sparse https://github.com/tinygrad/tinygrad.git "$REPO" 2>&1 | tee "$OUT/git_clone.log"

cd "$REPO" || exit 1

echo
echo "04 set non-cone sparse checkout"
# Non-cone allows files and globs. This avoids the sz.py cone-mode failure.
git sparse-checkout set --no-cone \
  "/tinygrad/" \
  "/test/" \
  "/examples/" \
  "/extra/" \
  "/docs/" \
  "/README.md" \
  "/pyproject.toml" \
  "/sz.py" \
  2>&1 | tee "$OUT/sparse_set_no_cone.log"

echo
echo "05 verify materialization"
{
  echo "HEAD:"
  git rev-parse HEAD
  echo
  echo "sparse list:"
  git sparse-checkout list || true
  echo
  echo "top:"
  find . -maxdepth 2 -type d | sed 's#^\./##' | sort | head -200
  echo
  echo "files:"
  ls -la | head -100
  echo
  echo "python file counts:"
  find tinygrad test -type f -name '*.py' 2>/dev/null | wc -l
  echo
  echo "key files:"
  for f in tinygrad/tensor.py tinygrad/uop/ops.py tinygrad/schedule/rangeify.py test/test_tiny.py test/test_ops.py pyproject.toml README.md; do
    if [ -e "$f" ]; then echo "FOUND $f"; else echo "MISSING $f"; fi
  done
  echo
  echo "disk:"
  df -h /
  du -sh "$REPO" 2>/dev/null || true
} | tee "$OUT/materialization_status.txt"

echo
echo "06 issue view"
gh issue view 3039 --repo tinygrad/tinygrad --json number,title,state,url,labels,comments,body,updatedAt \
  > "$OUT/issue_view.json" 2> "$OUT/issue_view.err" || true

python3 - "$OUT" <<'PY'
import json, sys
from pathlib import Path
out = Path(sys.argv[1])
try:
    data = json.loads((out/"issue_view.json").read_text())
except Exception as e:
    print({"issue_view_ok": False, "error": repr(e)})
    raise SystemExit
summary = {
    "number": data.get("number"),
    "title": data.get("title"),
    "state": data.get("state"),
    "url": data.get("url"),
    "labels": [x.get("name") for x in data.get("labels", [])],
    "comment_count": len(data.get("comments", [])),
    "updatedAt": data.get("updatedAt"),
}
(out/"issue_summary.json").write_text(json.dumps(summary, indent=2))
(out/"issue_body.md").write_text(data.get("body") or "")
(out/"issue_comments.md").write_text("\n\n---\n\n".join(
    (c.get("body") or "") for c in data.get("comments", [])
))
print(json.dumps(summary, indent=2))
PY

echo
echo "07 import smoke"
PYTHONPATH="$REPO" python3 - <<'PY' > "$OUT/import_smoke.out" 2> "$OUT/import_smoke.err" || true
import tinygrad
from tinygrad import Tensor
print("tinygrad_file", tinygrad.__file__)
print("Tensor", Tensor)
for name in ["cumsum", "cummax", "cumprod", "sum", "where", "cat", "stack", "pad", "permute", "reshape", "contiguous"]:
    print(name, hasattr(Tensor, name))
PY
cat "$OUT/import_smoke.out" || true
cat "$OUT/import_smoke.err" || true

echo
echo "08 focused grep"
{
  echo "===== scan/cumsum/prefix/mamba/selective_scan hits ====="
  grep -RInE --exclude-dir=.git --exclude-dir=__pycache__ \
    "associative_scan|parallel_scan|selective_scan|scan\\(|cumsum|cumprod|cummax|prefix|mamba|state space|ssm|recurrence" \
    tinygrad test examples extra docs 2>/dev/null | head -5000

  echo
  echo "===== tensor/uop/reduce context hits ====="
  grep -RInE --exclude-dir=.git --exclude-dir=__pycache__ \
    "def cumsum|def cumprod|def cummax|def sum|def max|class Tensor|Reduce|Ops\\.ADD|Ops\\.MUL|Ops\\.MAX|contiguous|permute|pad|cat|stack|reshape" \
    tinygrad/tensor.py tinygrad/uop tinygrad/codegen tinygrad/schedule test 2>/dev/null | head -5000
} | tee "$OUT/focused_grep.txt"

echo
echo "09 candidate map"
python3 - "$REPO" "$OUT" <<'PY'
import json, re, sys
from pathlib import Path

repo = Path(sys.argv[1])
out = Path(sys.argv[2])

terms = {
  "associative_scan": 40, "parallel_scan": 40, "selective_scan": 40,
  "cumsum": 30, "cumprod": 24, "cummax": 22, "scan": 12,
  "prefix": 16, "mamba": 28, "ssm": 16, "recurrence": 14,
  "reduce": 10, "ops.add": 10, "ops.mul": 10, "ops.max": 10,
  "tensor": 4, "uop": 5, "schedule": 5, "kernel": 5, "lower": 5,
  "test": 3,
}

roots = ["tinygrad", "test", "examples", "extra", "docs"]
cands = []
for root in roots:
    base = repo / root
    if not base.exists(): continue
    for p in base.rglob("*"):
        if not p.is_file() or p.suffix not in {".py", ".md", ".txt"}: continue
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
(out / "candidate_files.json").write_text(json.dumps(cands[:800], indent=2))

pat = re.compile(r"(associative_scan|parallel_scan|selective_scan|cumsum|cumprod|cummax|scan|prefix|mamba|ssm|recurrence|def sum|def max|Reduce|Ops\.ADD|Ops\.MUL|Ops\.MAX)", re.I)
snips = []
for item in cands[:120]:
    p = repo / item["path"]
    try: lines = p.read_text(errors="replace").splitlines()
    except Exception: continue
    hit_lines = [i for i,l in enumerate(lines) if pat.search(l)]
    if not hit_lines: continue
    snips.append(f"\n\n===== {item['path']} score={item['score']} =====")
    used = []
    for h in hit_lines[:16]:
        start, end = max(0,h-22), min(len(lines),h+36)
        if any(abs(start-s) < 16 for s,e in used): continue
        used.append((start,end))
        snips.append(f"\n--- around line {h+1} ---")
        for i in range(start,end):
            snips.append(f"{i+1:04d}: {lines[i]}")
(out / "candidate_context.txt").write_text("\n".join(snips) + "\n")

summary = {
  "candidate_count": len(cands),
  "top_candidate_files": cands[:80],
  "has_tensor_py": (repo/"tinygrad/tensor.py").exists(),
  "has_tests": (repo/"test").exists(),
}
(out / "analysis_summary.json").write_text(json.dumps(summary, indent=2))
print(json.dumps(summary, indent=2)[:40000])
PY

echo
echo "10 cumsum behavioral probe"
PYTHONPATH="$REPO" python3 - <<'PY' > "$OUT/cumsum_probe.out" 2> "$OUT/cumsum_probe.err" || true
from tinygrad import Tensor
import time

def show(expr, fn):
    try:
        t0 = time.time()
        y = fn()
        if hasattr(y, "realize"): y.realize()
        val = None
        try: val = y.numpy().tolist()
        except Exception: pass
        print(expr, "OK", "elapsed", round(time.time()-t0, 6), "shape", getattr(y, "shape", None), "val", str(val)[:200])
    except Exception as e:
        print(expr, "FAIL", type(e).__name__, str(e)[:800])

show("Tensor.arange(16).cumsum()", lambda: Tensor.arange(16).cumsum())
show("Tensor.arange(16).reshape(4,4).cumsum(axis=0)", lambda: Tensor.arange(16).reshape(4,4).cumsum(axis=0))
show("Tensor.arange(16).reshape(4,4).cumsum(axis=1)", lambda: Tensor.arange(16).reshape(4,4).cumsum(axis=1))
show("Tensor.ones(32).cumsum()", lambda: Tensor.ones(32).cumsum())
PY
cat "$OUT/cumsum_probe.out" || true
cat "$OUT/cumsum_probe.err" || true

echo
echo "11 inspect exact Tensor.cumsum source"
python3 - "$REPO" "$OUT" <<'PY'
from pathlib import Path
import re, sys

repo = Path(sys.argv[1])
out = Path(sys.argv[2])
p = repo / "tinygrad/tensor.py"
text = p.read_text(errors="replace") if p.exists() else ""
lines = text.splitlines()
needles = ["def cumsum", "def cummax", "def cumprod", "def sum", "def _pool"]
chunks = []
for needle in needles:
    for i,l in enumerate(lines):
        if needle in l:
            chunks.append(f"\n===== {needle} around line {i+1} =====")
            for j in range(max(0,i-30), min(len(lines), i+90)):
                chunks.append(f"{j+1:04d}: {lines[j]}")
            break
(out/"tensor_scan_source.txt").write_text("\n".join(chunks) + "\n")
print((out/"tensor_scan_source.txt").read_text())
PY

echo
echo "12 generate report"
python3 - "$OUT" <<'PY'
import json, sys
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
issue = load("issue_summary.json", {})
smoke = read("import_smoke.out") + read("import_smoke.err")
probe = read("cumsum_probe.out") + read("cumsum_probe.err")
top = summary.get("top_candidate_files", [])

has_import = "tinygrad_file" in smoke and "ModuleNotFoundError" not in smoke
has_cumsum = "cumsum True" in smoke
probe_ok = "cumsum() OK" in probe or "cumsum(axis" in probe
has_candidates = bool(top)

if has_import and has_cumsum and has_candidates:
    verdict = "PATCH_PROBE_NEXT"
else:
    verdict = "RECON_STILL_BLOCKED"

lines = []
lines.append("# tinygrad/tinygrad #3039 Reclone Unsparse Recon v3")
lines.append("")
lines.append("## Verdict")
lines.append("")
lines.append(f"`{verdict}`")
lines.append("")
lines.append("## Issue")
lines.append("")
lines.append("```json")
lines.append(json.dumps(issue, indent=2))
lines.append("```")
lines.append("")
lines.append("## Signals")
lines.append("")
lines.append(f"- local import works: `{has_import}`")
lines.append(f"- Tensor has cumsum: `{has_cumsum}`")
lines.append(f"- cumsum behavioral probe: `{probe_ok}`")
lines.append(f"- has `tinygrad/tensor.py`: `{summary.get('has_tensor_py')}`")
lines.append(f"- has `test/`: `{summary.get('has_tests')}`")
lines.append(f"- candidate files found: `{summary.get('candidate_count')}`")
lines.append("")
lines.append("## Top candidate files")
lines.append("")
lines.append("```json")
lines.append(json.dumps(top[:60], indent=2))
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
lines.append(probe[:10000])
lines.append("```")
lines.append("")
lines.append("## Tensor scan source")
lines.append("")
lines.append("```text")
lines.append(read("tensor_scan_source.txt", 30000))
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
    lines.append("Build a tiny before/after metric harness around existing `Tensor.cumsum`, then attempt the smallest associative/tree-scan improvement or draft PR if progress is meaningful.")
else:
    lines.append("Still blocked. Do not patch.")
lines.append("")
(out/"REPORT.md").write_text("\n".join(lines) + "\n")
print((out/"REPORT.md").read_text())
PY

echo
echo "13 commit artifact"
cd "$ROOT" || exit 1
git add "$OUT" tinygrad_3039_reclone_unsparse_v3.sh
git commit -m "Add tinygrad issue3039 reclone unsparse recon v3" || true
git push origin local-main || true

echo
echo "14 final status"
git status --short
df -h /
du -sh "$REPO" 2>/dev/null || true
echo
echo "Artifacts:"
echo "$OUT/REPORT.md"
echo "$OUT/analysis_summary.json"
echo "$OUT/candidate_context.txt"
echo "$OUT/tensor_scan_source.txt"
echo "$OUT/cumsum_probe.out"
