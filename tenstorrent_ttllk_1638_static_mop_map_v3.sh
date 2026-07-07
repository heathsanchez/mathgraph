#!/usr/bin/env bash
set -u

echo "MathGraph Bounty Recon v3 — static MOP/replay-buffer map for tenstorrent/tt-llk #1638"
df -h /
echo

ROOT="$PWD"
REPO="$ROOT/external/bounty_triage_v1/tenstorrent__tt-llk"
OUT="$ROOT/artifacts/bounty_triage_v1/tenstorrent_ttllk_1638_static_mop_map_v3"

mkdir -p "$OUT"

if [ ! -d "$REPO/.git" ]; then
  echo "ERROR missing repo: $REPO"
  exit 1
fi

cd "$REPO"

echo "01 reset repo"
git fetch origin --depth 1 || true
git reset --hard origin/HEAD || true
git clean -fd || true
git status --short | tee "$OUT/status_start.txt"
git log -1 --oneline | tee "$OUT/head.txt"

echo
echo "02 targeted MOP/replay grep"
{
  echo "== MOP exact =="
  grep -RIn --exclude-dir=.git --exclude-dir=build --exclude-dir=node_modules -E "\bMOP\b|\bmop\b|TTI_MOP|MOP_CFG|MOP_HEADER|LOADMACRO|loadmacro|REPLAY|replay" . || true

  echo
  echo "== replay buffer exact =="
  grep -RIn --exclude-dir=.git --exclude-dir=build --exclude-dir=node_modules -E "replay_buf|replay buffer|replay_buf_offset|replay_buf|replayBuffer|REPLAY_BUF|record_replay|record.*replay|replay.*record" . || true

  echo
  echo "== template/config =="
  grep -RIn --exclude-dir=.git --exclude-dir=build --exclude-dir=node_modules -E "ckernel_template|program.*template|template.*program|mop_type|loop_count|zmask|double.*loop|MASK_LOOP|DOUBLE_LOOP" . || true

  echo
  echo "== RISCV instruction objective clues =="
  grep -RIn --exclude-dir=.git --exclude-dir=build --exclude-dir=node_modules -E "riscv.*instruction|RISCV.*instruction|instruction.*count|count.*instruction|perf|cycle|cycles|profile|profiler|marker|MATH_ISOLATE" . || true
} | tee "$OUT/mop_replay_grep.txt"

echo
echo "03 focused file list"
python3 - "$OUT" <<'PY'
from pathlib import Path
import sys

out = Path(sys.argv[1])
txt = (out / "mop_replay_grep.txt").read_text(errors="replace")

files = []
for line in txt.splitlines():
    if line.startswith("./") and ":" in line:
        f = line.split(":", 1)[0]
        if f not in files and Path(f).exists():
            files.append(f)

priority_terms = [
    "ckernel_template",
    "cmath_common",
    "ckernel_ops",
    "ckernel_include",
    "ckernel_instr_params",
    "llk_math_matmul",
    "llk_math_reduce",
    "sfpu_reduce",
    "sfpu_topk",
    "custom_no_mop",
    "perf_",
    "profiler",
    "counters",
]

ranked = []
for f in files:
    score = 0
    low = f.lower()
    for t in priority_terms:
        if t in low:
            score += 10
    if "wormhole_b0" in low:
        score += 5
    if "quasar" in low:
        score += 2
    if "test" in low:
        score += 1
    ranked.append((score, f))

ranked.sort(key=lambda x: (-x[0], x[1]))
chosen = [f for _, f in ranked[:80]]

(out / "mop_candidate_files.txt").write_text("\n".join(chosen) + ("\n" if chosen else ""))
print((out / "mop_candidate_files.txt").read_text())
PY

echo
echo "04 extract high-signal contexts"
python3 - "$OUT" <<'PY'
from pathlib import Path
import sys

out = Path(sys.argv[1])
files = (out / "mop_candidate_files.txt").read_text(errors="replace").splitlines()

terms = [
    "MOP", "mop", "TTI_MOP", "LOADMACRO", "loadmacro",
    "replay", "Replay", "replay_buf", "replay_buf_offset",
    "ckernel_template", "program", "template",
    "loop_count", "mop_type", "MASK_LOOP", "DOUBLE_LOOP",
    "perf", "cycle", "cycles", "instruction", "profiler", "marker",
]

chunks = []
for f in files:
    p = Path(f)
    if not p.exists() or not p.is_file():
        continue
    try:
        if p.stat().st_size > 900_000:
            continue
        lines = p.read_text(errors="replace").splitlines()
    except Exception:
        continue

    hits = []
    for i, line in enumerate(lines, 1):
        if any(t in line for t in terms):
            hits.append(i)
    if not hits:
        continue

    chunks.append(f"\n\n===== {f} =====")
    used = []
    for i in hits[:18]:
        a = max(1, i - 12)
        b = min(len(lines), i + 22)
        if any(not (b < ua or a > ub) for ua, ub in used):
            continue
        used.append((a, b))
        chunks.append(f"\n--- around line {i} ---")
        for j in range(a, b + 1):
            chunks.append(f"{j:04d}: {lines[j-1]}")
(out / "mop_candidate_context.txt").write_text("\n".join(chunks) + "\n")
print("\n".join(chunks[:900]))
PY | tee "$OUT/mop_candidate_context_head.txt"

echo
echo "05 static count/proxy analysis"
python3 - "$OUT" <<'PY'
from pathlib import Path
import sys, re, json
from collections import Counter, defaultdict

out = Path(sys.argv[1])

source_files = []
for root in ["tt_llk_wormhole_b0", "tt_llk_blackhole", "tt_llk_quasar", "tests"]:
    rp = Path(root)
    if rp.exists():
        source_files.extend([p for p in rp.rglob("*") if p.is_file() and p.suffix in [".h", ".hpp", ".cpp", ".py", ".yaml", ".md", ".sh"]])

patterns = {
    "TTI_MOP": r"\bTTI_MOP\b",
    "MOP": r"\bMOP\b|\bmop\b",
    "LOADMACRO": r"LOADMACRO|loadmacro",
    "replay": r"replay|Replay",
    "replay_buf": r"replay_buf|replay buffer|replay_buf_offset",
    "TTI_instr": r"\bTTI_[A-Z0-9_]+\s*\(",
    "SFPU_instr": r"\bTTI_SFP[A-Z0-9_]+\s*\(",
    "STALLWAIT": r"STALLWAIT|TTI_STALLWAIT",
    "SEMWAIT": r"SEMWAIT|TTI_SEMWAIT",
}

rows = []
file_hits = defaultdict(Counter)

for p in source_files:
    try:
        txt = p.read_text(errors="replace")
    except Exception:
        continue
    if len(txt) > 1_500_000:
        continue
    c = Counter()
    for name, pat in patterns.items():
        c[name] = len(re.findall(pat, txt))
    if sum(c.values()):
        file_hits[str(p)] = c
        rows.append({
            "file": str(p),
            **dict(c),
            "total_signal": sum(c.values()),
        })

rows.sort(key=lambda r: (-r["MOP"], -r["replay"], -r["TTI_instr"], r["file"]))

(out / "static_signal_counts.json").write_text(json.dumps(rows, indent=2))

tsv = ["file\t" + "\t".join(patterns.keys()) + "\ttotal_signal"]
for r in rows[:200]:
    tsv.append(r["file"] + "\t" + "\t".join(str(r[k]) for k in patterns.keys()) + "\t" + str(r["total_signal"]))
(out / "static_signal_counts.tsv").write_text("\n".join(tsv) + "\n")

print("\n".join(tsv[:80]))
PY | tee "$OUT/static_signal_counts_head.tsv"

echo
echo "06 inspect likely source files directly"
for f in \
  tt_llk_wormhole_b0/common/inc/ckernel_template.h \
  tt_llk_wormhole_b0/common/inc/cmath_common.h \
  tt_llk_wormhole_b0/common/inc/ckernel_ops.h \
  tt_llk_wormhole_b0/common/inc/ckernel_include.h \
  tt_llk_wormhole_b0/common/inc/ckernel_instr_params.h \
  tt_llk_wormhole_b0/llk_lib/llk_math_matmul.h \
  tt_llk_wormhole_b0/llk_lib/experimental/llk_math_matmul_custom_no_mop.h \
  tt_llk_wormhole_b0/common/inc/sfpu/ckernel_sfpu_reduce.h \
  tests/python_tests/perf_math_matmul.py \
  tests/python_tests/helpers/perf.py \
  tests/python_tests/helpers/counters.py \
  docs/performance_counters/performance_counters.md \
  .cursor/rules/scripts/run_test.sh \
; do
  if [ -f "$f" ]; then
    echo
    echo "===== $f ====="
    sed -n '1,260p' "$f"
  fi
done | tee "$OUT/focused_file_dump.txt"

echo
echo "07 classify target"
python3 - "$OUT" <<'PY'
from pathlib import Path
import json, sys

out = Path(sys.argv[1])
counts = []
p = out / "static_signal_counts.json"
if p.exists():
    counts = json.loads(p.read_text())

top = counts[:30]
ctx = (out / "mop_candidate_context.txt").read_text(errors="replace") if (out / "mop_candidate_context.txt").exists() else ""
dump = (out / "focused_file_dump.txt").read_text(errors="replace") if (out / "focused_file_dump.txt").exists() else ""

has_mop_sources = any(r.get("MOP",0) or r.get("TTI_MOP",0) for r in counts)
has_replay = any(r.get("replay",0) or r.get("replay_buf",0) for r in counts)
has_perf = "perf" in ctx.lower() or "performance" in dump.lower()
has_no_mop = "custom_no_mop" in ctx or "custom_no_mop" in dump
has_test_runner = "pytest --compile-producer" in ctx or "compile-producer" in dump

if has_mop_sources and has_replay and has_test_runner:
    verdict = "LOCAL_STATIC_MAP_FOUND_BUT_RUNTIME_BLOCKED"
elif has_mop_sources and has_replay:
    verdict = "STATIC_MAP_FOUND_NEEDS_JUDGE"
else:
    verdict = "PARK"

lines = []
lines.append("# tenstorrent/tt-llk #1638 Static MOP Map v3")
lines.append("")
lines.append("## Verdict")
lines.append("")
lines.append(f"`{verdict}`")
lines.append("")
lines.append("## Signals")
lines.append("")
lines.append(f"- MOP sources found: `{has_mop_sources}`")
lines.append(f"- Replay-buffer references found: `{has_replay}`")
lines.append(f"- Perf/counter references found: `{has_perf}`")
lines.append(f"- Existing no-MOP matmul reference found: `{has_no_mop}`")
lines.append(f"- Compile-producer/consumer test runner found: `{has_test_runner}`")
lines.append("")
lines.append("## Top static signal files")
lines.append("")
for r in top:
    bits = []
    for k in ["TTI_MOP", "MOP", "LOADMACRO", "replay", "replay_buf", "TTI_instr", "SFPU_instr"]:
        if r.get(k, 0):
            bits.append(f"{k}={r[k]}")
    lines.append(f"- `{r['file']}` — " + ", ".join(bits))
lines.append("")
lines.append("## Decision")
lines.append("")
if verdict == "LOCAL_STATIC_MAP_FOUND_BUT_RUNTIME_BLOCKED":
    lines.append("This bounty is technically real, but acceptance likely needs repo-specific simulator/runtime setup. Do not claim yet.")
    lines.append("")
    lines.append("Best next move is to ask the maintainer for the exact local scoring command and a starting op/kernel, or park and move to easier bounty.")
elif verdict == "STATIC_MAP_FOUND_NEEDS_JUDGE":
    lines.append("The source surface is identifiable, but the judge/metric is not yet operational. Park unless maintainer gives a local command.")
else:
    lines.append("Park. Too much missing local-verifier surface.")
lines.append("")
lines.append("## Maintainer question draft")
lines.append("")
lines.append("```text")
lines.append("I did a first static pass on #1638 and found the MOP/replay-buffer surface, including the architecture LLK headers and the compile-producer/compile-consumer test runner. Before attempting a patch, what exact command or benchmark should contributors use to measure the RISCV instruction count reduction for a candidate op?")
lines.append("")
lines.append("Is there a preferred starting kernel/op for this bounty, and is the expected validation `pytest --compile-producer/--compile-consumer`, a perf counter report, or another simulator/hardware run?")
lines.append("```")
lines.append("")
lines.append("## Top context excerpt")
lines.append("")
lines.append("```text")
lines.append(ctx[:18000])
lines.append("```")
lines.append("")
(out / "REPORT.md").write_text("\n".join(lines) + "\n")
print((out / "REPORT.md").read_text())
PY

echo
echo "08 commit artifact"
cd "$ROOT"
git add "$OUT" tenstorrent_ttllk_1638_static_mop_map_v3.sh
git commit -m "Add tenstorrent tt-llk static MOP map v3" || true
git push origin local-main || true

echo
echo "09 final status"
git status --short
df -h /
du -sh "$REPO" 2>/dev/null || true
echo
echo "Artifacts:"
echo "$OUT/REPORT.md"
echo "$OUT/static_signal_counts.tsv"
echo "$OUT/mop_candidate_context.txt"
