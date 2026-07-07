#!/usr/bin/env bash
set -u

ROOT="/Users/heath/Documents/mathgraph-lean-work"
V4="$ROOT/artifacts/bounty_triage_v1/tinygrad_3039_parallel_scan_probe_v4"
OUT="$ROOT/artifacts/bounty_triage_v1/tinygrad_3039_decision_v5"

mkdir -p "$OUT"

echo "MathGraph tinygrad #3039 v5 — decision from parallel scan probe"
echo

echo "01 status"
{
  date -u +"%Y-%m-%dT%H:%M:%SZ"
  df -h /
  git -C "$ROOT" status --short
} | tee "$OUT/status_start.txt"

echo
echo "02 analyze benchmark JSON"
python3 - "$V4" "$OUT" <<'PY'
from pathlib import Path
import sys, json, re, statistics

v4 = Path(sys.argv[1])
out = Path(sys.argv[2])

bench = (v4 / "benchmark_probe.out").read_text(errors="replace") if (v4 / "benchmark_probe.out").exists() else ""
correct = (v4 / "correctness_probe.out").read_text(errors="replace") if (v4 / "correctness_probe.out").exists() else ""
complexity = {}
try:
  complexity = json.loads((v4 / "complexity_proxy.json").read_text())
except Exception:
  pass

m = re.search(r"JSON_RESULT_START\s*(\[.*?\])\s*JSON_RESULT_END", bench, re.S)
rows = json.loads(m.group(1)) if m else []

summary_rows = []
slower_count = 0
faster_count = 0
for r in rows:
  n = r["n"]
  b = r["builtin"]["median"]
  p = r["probe"]["median"]
  ratio = (p / b) if b and p else None
  if ratio is not None:
    if ratio > 1.05: slower_count += 1
    elif ratio < 0.95: faster_count += 1
  summary_rows.append({
    "n": n,
    "builtin_median_s": b,
    "probe_median_s": p,
    "probe_over_builtin_ratio": ratio,
    "builtin_min_s": r["builtin"]["min"],
    "probe_min_s": r["probe"]["min"],
  })

all_ok = "ALL_OK True" in correct
all_slower_or_equal = slower_count >= max(1, len(rows) - 1) and faster_count == 0
has_data = bool(rows)

if all_ok and has_data and all_slower_or_equal:
  verdict = "DO_NOT_PR_THIS_PATCH__NEGATIVE_RESULT_CERTIFIED"
elif all_ok and has_data:
  verdict = "MIXED_RESULT__INSPECT_BEFORE_PR"
else:
  verdict = "BROKEN_PROBE__NO_ACTION"

decision = {
  "verdict": verdict,
  "correctness_passed": all_ok,
  "benchmark_rows": len(rows),
  "probe_slower_count": slower_count,
  "probe_faster_count": faster_count,
  "summary_rows": summary_rows,
  "complexity_proxy": complexity,
}

(out / "decision.json").write_text(json.dumps(decision, indent=2))
print(json.dumps(decision, indent=2))

# markdown table
table = []
table.append("| n | builtin median s | probe median s | probe/builtin |")
table.append("|---:|---:|---:|---:|")
for r in summary_rows:
  ratio = r["probe_over_builtin_ratio"]
  table.append(f"| {r['n']} | {r['builtin_median_s']:.6g} | {r['probe_median_s']:.6g} | {ratio:.3f}x |")
(out / "benchmark_ratio_table.md").write_text("\n".join(table) + "\n")
PY

echo
echo "03 write decision report"
python3 - "$V4" "$OUT" <<'PY'
from pathlib import Path
import sys, json

v4 = Path(sys.argv[1])
out = Path(sys.argv[2])
decision = json.loads((out / "decision.json").read_text())
ratio_table = (out / "benchmark_ratio_table.md").read_text()

def read(path, limit=20000):
  p = Path(path)
  if not p.exists(): return ""
  return p.read_text(errors="replace")[:limit]

verdict = decision["verdict"]

lines = []
lines.append("# tinygrad/tinygrad #3039 Decision v5")
lines.append("")
lines.append("## Verdict")
lines.append("")
lines.append(f"`{verdict}`")
lines.append("")
lines.append("## Meaning")
lines.append("")
lines.append("The Hillis-Steele/tree-style cumsum probe is correct, but it is not a bounty-grade patch because the existing `Tensor.cumsum` is faster in the local warm benchmark.")
lines.append("")
lines.append("This is still useful: it converts the tinygrad route from vague hope into a certified negative result. The simple Tensor-level tree scan is not the portal.")
lines.append("")
lines.append("## Benchmark ratio")
lines.append("")
lines.append(ratio_table)
lines.append("")
lines.append("## Decision")
lines.append("")
lines.append("- Do not open a PR with this patch.")
lines.append("- Do not claim or lock the bounty from this result.")
lines.append("- Keep the artifact as a Lawbook/Obstruction entry: naive Tensor-level Hillis-Steele cumsum is correct but too slow.")
lines.append("- Tinygrad remains possible only with a lower-level codegen/scheduler primitive, not with repeated `pad + shrink + add` at Tensor level.")
lines.append("")
lines.append("## MathGraph classification")
lines.append("")
lines.append("- Residual: fast general associative scan for tinygrad.")
lines.append("- Portal tried: Tensor-level Hillis-Steele scan via shifted adds.")
lines.append("- Certificate: correctness passes against `Tensor.cumsum`.")
lines.append("- Obstruction: performance loses to existing implementation; graph construction and repeated materialization overhead dominate.")
lines.append("- Next route: park tinygrad unless we inspect codegen/UOp-level scan lowering.")
lines.append("")
lines.append("## Next routing")
lines.append("")
lines.append("1. Return to Tenstorrent if the maintainer answers with a concrete scoring command.")
lines.append("2. Return to Strata/specimen if we want a MathGraph-native formal verification PR.")
lines.append("3. Only continue tinygrad if we are willing to work below Tensor-level APIs in scheduler/UOps/codegen.")
lines.append("")
lines.append("## Raw decision JSON")
lines.append("")
lines.append("```json")
lines.append(json.dumps(decision, indent=2))
lines.append("```")
lines.append("")
lines.append("## Prior correctness probe excerpt")
lines.append("")
lines.append("```text")
lines.append(read(v4 / "correctness_probe.out", 12000))
lines.append("```")
lines.append("")
lines.append("## Prior benchmark excerpt")
lines.append("")
lines.append("```text")
lines.append(read(v4 / "benchmark_probe.out", 20000))
lines.append("```")
lines.append("")
(out / "REPORT.md").write_text("\n".join(lines) + "\n")
print((out / "REPORT.md").read_text())
PY

echo
echo "04 optional maintainer note draft, not posted"
cat > "$OUT/optional_tinygrad_comment.md" <<'MD'
I tested a simple Tensor-level Hillis-Steele/tree-style inclusive cumsum as a first pass for #3039. It was correct against `Tensor.cumsum`, but locally it was slower than the existing implementation across small powers of two, because repeated `pad + shrink + add` at Tensor level creates too much overhead.

So I’m not opening a PR from that route. The next plausible route seems lower-level: adding a scheduler/UOp/codegen primitive for associative scan rather than composing it from existing Tensor ops. If there’s a preferred lowering target or benchmark for this bounty, I can aim at that.
MD

cat "$OUT/optional_tinygrad_comment.md"

echo
echo "05 commit artifact"
cd "$ROOT" || exit 1
git add "$OUT" tinygrad_3039_decision_v5.sh
git commit -m "Certify tinygrad issue3039 Tensor-level scan obstruction" || true
git push origin local-main || true

echo
echo "06 final status"
git status --short
df -h /
echo
echo "Artifacts:"
echo "$OUT/REPORT.md"
echo "$OUT/decision.json"
echo "$OUT/benchmark_ratio_table.md"
echo "$OUT/optional_tinygrad_comment.md"
