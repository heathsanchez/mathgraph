#!/usr/bin/env bash
set -u

echo "MathGraph Bounty Recon v4 — tenstorrent/tt-llk #1638 focused MOP/no-MOP wedge"
df -h /
echo

ROOT="$PWD"
REPO="$ROOT/external/bounty_triage_v1/tenstorrent__tt-llk"
OUT="$ROOT/artifacts/bounty_triage_v1/tenstorrent_ttllk_1638_static_mop_map_v4"

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
git status --short > "$OUT/status_start.txt"
git log -1 --oneline > "$OUT/head.txt"
cat "$OUT/head.txt"

echo
echo "02 verify candidate files exist"
for f in \
  tt_llk_wormhole_b0/llk_lib/experimental/llk_math_matmul_custom_no_mop.h \
  tt_llk_blackhole/llk_lib/experimental/llk_math_matmul_custom_no_mop.h \
  tt_llk_wormhole_b0/llk_lib/llk_math_matmul.h \
  tt_llk_blackhole/llk_lib/llk_math_matmul.h \
  tt_llk_wormhole_b0/common/inc/ckernel_template.h \
  tt_llk_wormhole_b0/common/inc/ckernel_ops.h \
  tt_llk_wormhole_b0/common/inc/ckernel_instr_params.h \
  tests/python_tests/perf_math_matmul.py \
  tests/sources/math_matmul_perf.cpp \
  tests/sources/matmul_perf.cpp \
  tests/helpers/include/perf.h \
  tests/python_tests/helpers/perf.py \
  tests/python_tests/helpers/counters.py \
  docs/performance_counters/performance_counters.md \
; do
  if [ -f "$f" ]; then
    echo "FOUND $f"
  else
    echo "MISS  $f"
  fi
done | tee "$OUT/candidate_presence.txt"

echo
echo "03 focused grep for MOP/no-MOP/matmul/perf"
grep -RIn --exclude-dir=.git --exclude-dir=build \
  -E "custom_no_mop|no.?mop|TTI_MOP|MOP|mop|LOADMACRO|replay|replay_buf|PerfRunType|MATH_ISOLATE|instruction count|Thread instruction counts|Counter IDs 256|INSTRN_THREAD|FPU_INSTRUCTION" \
  tt_llk_wormhole_b0 tt_llk_blackhole tests docs \
  > "$OUT/focused_grep.txt" 2>&1 || true

sed -n '1,260p' "$OUT/focused_grep.txt"

echo
echo "04 extract focused context"
python3 - "$OUT" <<'PY'
from pathlib import Path
import sys

out = Path(sys.argv[1])

files = [
    "tt_llk_wormhole_b0/llk_lib/experimental/llk_math_matmul_custom_no_mop.h",
    "tt_llk_blackhole/llk_lib/experimental/llk_math_matmul_custom_no_mop.h",
    "tt_llk_wormhole_b0/llk_lib/llk_math_matmul.h",
    "tt_llk_blackhole/llk_lib/llk_math_matmul.h",
    "tt_llk_wormhole_b0/common/inc/ckernel_template.h",
    "tt_llk_wormhole_b0/common/inc/ckernel_ops.h",
    "tt_llk_wormhole_b0/common/inc/ckernel_instr_params.h",
    "tests/python_tests/perf_math_matmul.py",
    "tests/sources/math_matmul_perf.cpp",
    "tests/sources/matmul_perf.cpp",
    "tests/helpers/include/perf.h",
    "tests/helpers/include/counters.h",
    "tests/python_tests/helpers/perf.py",
    "tests/python_tests/helpers/counters.py",
    "docs/performance_counters/performance_counters.md",
]

terms = [
    "custom_no_mop", "no-mop", "no mop", "MOP", "mop", "TTI_MOP",
    "LOADMACRO", "replay", "replay_buf", "PerfRunType", "MATH_ISOLATE",
    "Thread instruction counts", "Counter IDs 256", "INSTRN_THREAD",
    "FPU_INSTRUCTION", "instruction count", "cycles",
    "_perf_unpack_matmul_mock", "_perf_math_matmul_mock",
]

chunks = []
for f in files:
    p = Path(f)
    if not p.exists():
        continue
    lines = p.read_text(errors="replace").splitlines()
    hits = []
    for i, line in enumerate(lines, 1):
        low = line.lower()
        if any(t.lower() in low for t in terms):
            hits.append(i)

    chunks.append(f"\n\n===== {f} =====")
    if not hits:
        a, b = 1, min(len(lines), 220)
        for j in range(a, b + 1):
            chunks.append(f"{j:04d}: {lines[j-1]}")
        continue

    used = []
    for i in hits[:30]:
        a = max(1, i - 16)
        b = min(len(lines), i + 32)
        if any(not (b < ua or a > ub) for ua, ub in used):
            continue
        used.append((a, b))
        chunks.append(f"\n--- around line {i} ---")
        for j in range(a, b + 1):
            chunks.append(f"{j:04d}: {lines[j-1]}")

text = "\n".join(chunks) + "\n"
(out / "focused_context.txt").write_text(text)
(out / "focused_context_head.txt").write_text("\n".join(text.splitlines()[:900]) + "\n")
PY

cat "$OUT/focused_context_head.txt"

echo
echo "05 static macro/instruction proxy counts"
python3 - "$OUT" <<'PY'
from pathlib import Path
import sys, re, json
from collections import Counter

out = Path(sys.argv[1])

files = [
    "tt_llk_wormhole_b0/llk_lib/experimental/llk_math_matmul_custom_no_mop.h",
    "tt_llk_blackhole/llk_lib/experimental/llk_math_matmul_custom_no_mop.h",
    "tt_llk_wormhole_b0/llk_lib/llk_math_matmul.h",
    "tt_llk_blackhole/llk_lib/llk_math_matmul.h",
    "tests/sources/math_matmul_perf.cpp",
    "tests/sources/matmul_perf.cpp",
    "tests/helpers/include/perf.h",
]

patterns = {
    "TTI_calls": r"\bTTI_[A-Z0-9_]+\s*(?:\(|;)",
    "MOP": r"\bMOP\b|\bmop\b|TTI_MOP",
    "LOADMACRO": r"LOADMACRO|loadmacro",
    "replay": r"replay|Replay",
    "for_loops": r"\bfor\s*\(",
    "if_constexpr": r"if constexpr",
    "inline_funcs": r"\binline\s+void\b|\bTT_ALWAYS_INLINE\b",
    "perf_markers": r"ZONE_SCOPED|TIMESTAMP|PerfRunType|MATH_ISOLATE",
}

rows = []
for f in files:
    p = Path(f)
    if not p.exists():
        continue
    txt = p.read_text(errors="replace")
    c = {k: len(re.findall(v, txt)) for k, v in patterns.items()}
    c["file"] = f
    c["bytes"] = len(txt.encode())
    c["lines"] = txt.count("\n") + 1
    rows.append(c)

rows.sort(key=lambda r: (-r["MOP"], -r["TTI_calls"], r["file"]))

json_path = out / "static_proxy_counts.json"
tsv_path = out / "static_proxy_counts.tsv"
json_path.write_text(json.dumps(rows, indent=2))

headers = ["file", "lines", "bytes"] + list(patterns.keys())
tsv = ["\t".join(headers)]
for r in rows:
    tsv.append("\t".join(str(r.get(h, "")) for h in headers))
tsv_path.write_text("\n".join(tsv) + "\n")
print(tsv_path.read_text())
PY

echo
echo "06 identify exact local perf command surface"
python3 - "$OUT" <<'PY'
from pathlib import Path
import sys, re, json

out = Path(sys.argv[1])
paths = [
    Path("tests/python_tests/perf_math_matmul.py"),
    Path("tests/python_tests/perf_matmul.py"),
    Path(".cursor/rules/scripts/run_test.sh"),
    Path("docs/tests/getting_started.md"),
    Path(".github/workflows/setup-and-test.yml"),
    Path(".github/workflows/run-perf-tests.yml"),
]
chunks = []
for p in paths:
    if not p.exists():
        continue
    lines = p.read_text(errors="replace").splitlines()
    chunks.append(f"\n===== {p} =====")
    for i, line in enumerate(lines, 1):
        low = line.lower()
        if any(x in low for x in ["pytest", "compile-producer", "compile-consumer", "perf", "math_matmul", "matmul_perf", "run_test.sh"]):
            a = max(1, i - 8)
            b = min(len(lines), i + 18)
            chunks.append(f"\n--- around line {i} ---")
            for j in range(a, b + 1):
                chunks.append(f"{j:04d}: {lines[j-1]}")
            chunks.append("")
text = "\n".join(chunks) + "\n"
(out / "perf_command_surface.txt").write_text(text)
print(text[:18000])
PY

echo
echo "07 create maintainer question and claim/no-claim report"
python3 - "$OUT" <<'PY'
from pathlib import Path
import sys, json

out = Path(sys.argv[1])

presence = (out / "candidate_presence.txt").read_text(errors="replace")
counts = (out / "static_proxy_counts.tsv").read_text(errors="replace") if (out / "static_proxy_counts.tsv").exists() else ""
ctx = (out / "focused_context.txt").read_text(errors="replace") if (out / "focused_context.txt").exists() else ""
cmd = (out / "perf_command_surface.txt").read_text(errors="replace") if (out / "perf_command_surface.txt").exists() else ""
grep = (out / "focused_grep.txt").read_text(errors="replace") if (out / "focused_grep.txt").exists() else ""

has_no_mop = "custom_no_mop" in grep or "custom_no_mop" in presence
has_perf = "perf_math_matmul.py" in presence and "math_matmul_perf.cpp" in presence
has_counter_metric = "Thread instruction counts" in grep or "Counter IDs 256" in grep or "INSTRN_THREAD" in grep
has_runner = "compile-producer" in cmd or "compile-consumer" in cmd

if has_no_mop and has_perf and has_counter_metric and has_runner:
    verdict = "GOOD_BUT_ASK_FOR_SCORING_COMMAND_BEFORE_PATCH"
elif has_no_mop and has_perf:
    verdict = "PROMISING_STATIC_WEDGE_RUNTIME_UNCLEAR"
else:
    verdict = "PARK"

comment = """I did a focused static pass on #1638 and found what looks like a good first wedge: the matmul MOP/no-MOP surface, especially the existing `llk_math_matmul_custom_no_mop.h` experimental headers plus the `perf_math_matmul.py` / `math_matmul_perf.cpp` performance tests.

I also found the hardware counter docs/code that mention thread instruction counts, including the counter IDs in the performance counter path. Before attempting a patch, what exact local command should contributors use as the acceptance metric for this bounty?

Specifically:
1. Should we optimize/measure `tests/python_tests/perf_math_matmul.py` first, or another preferred op?
2. Should the score be taken from `pytest --compile-producer/--compile-consumer -m perf`, a performance counter CSV, profiler output, or CI device perf results?
3. For the objective “minimize RISCV instructions,” which counter/report column should be treated as canonical?
4. Is the existing `llk_math_matmul_custom_no_mop.h` path an acceptable starting point for a small PR, or do you prefer changes in the generic MOP/replay-buffer template code?

I can produce a small before/after patch once the exact scoring command and target op are confirmed.
"""

(out / "maintainer_question.md").write_text(comment)

lines = []
lines.append("# tenstorrent/tt-llk #1638 Static MOP Map v4")
lines.append("")
lines.append("## Verdict")
lines.append("")
lines.append(f"`{verdict}`")
lines.append("")
lines.append("## What we found")
lines.append("")
lines.append("- Existing MOP/no-MOP wedge: `" + str(has_no_mop) + "`")
lines.append("- Matmul perf test surface: `" + str(has_perf) + "`")
lines.append("- Thread instruction counter references: `" + str(has_counter_metric) + "`")
lines.append("- Compile producer/consumer command surface: `" + str(has_runner) + "`")
lines.append("")
lines.append("## Interpretation")
lines.append("")
lines.append("This is now a real technical bounty surface, but still not claimable without the exact scoring command.")
lines.append("")
lines.append("The likely first patch target is matmul, because the repo already has:")
lines.append("")
lines.append("- `tt_llk_wormhole_b0/llk_lib/experimental/llk_math_matmul_custom_no_mop.h`")
lines.append("- `tt_llk_blackhole/llk_lib/experimental/llk_math_matmul_custom_no_mop.h`")
lines.append("- `tests/python_tests/perf_math_matmul.py`")
lines.append("- `tests/sources/math_matmul_perf.cpp`")
lines.append("- perf/counter infrastructure including thread instruction count references")
lines.append("")
lines.append("## Next action")
lines.append("")
lines.append("Post/ask the maintainer question unless you already have `ttexalens`/device simulator access.")
lines.append("")
lines.append("## Maintainer question")
lines.append("")
lines.append("```text")
lines.append(comment.strip())
lines.append("```")
lines.append("")
lines.append("## Static proxy counts")
lines.append("")
lines.append("```text")
lines.append(counts[:12000])
lines.append("```")
lines.append("")
lines.append("## Candidate presence")
lines.append("")
lines.append("```text")
lines.append(presence)
lines.append("```")
lines.append("")
lines.append("## Perf command surface excerpt")
lines.append("")
lines.append("```text")
lines.append(cmd[:16000])
lines.append("```")
lines.append("")
lines.append("## Focused context excerpt")
lines.append("")
lines.append("```text")
lines.append(ctx[:24000])
lines.append("```")
lines.append("")
(out / "REPORT.md").write_text("\n".join(lines) + "\n")
print((out / "REPORT.md").read_text())
PY

echo
echo "08 optional dry-run comment poster"
cat > "$OUT/post_question.sh" <<'POSTSH'
#!/usr/bin/env bash
set -u
ROOT="/Users/heath/Documents/mathgraph-lean-work"
OUT="$ROOT/artifacts/bounty_triage_v1/tenstorrent_ttllk_1638_static_mop_map_v4"
COMMENT="$OUT/maintainer_question.md"

if [ "${POST:-0}" = "1" ]; then
  gh issue comment "https://github.com/tenstorrent/tt-llk/issues/1638" --body-file "$COMMENT"
else
  echo "DRY RUN ONLY. To post:"
  echo "POST=1 bash $OUT/post_question.sh"
  echo
  cat "$COMMENT"
fi
POSTSH
chmod +x "$OUT/post_question.sh"
bash "$OUT/post_question.sh"

echo
echo "09 commit artifact"
cd "$ROOT"
git add "$OUT" tenstorrent_ttllk_1638_static_mop_map_v4.sh
git commit -m "Add tenstorrent tt-llk focused MOP wedge v4" || true
git push origin local-main || true

echo
echo "10 final status"
git status --short
df -h /
du -sh "$REPO" 2>/dev/null || true
echo
echo "Artifacts:"
echo "$OUT/REPORT.md"
echo "$OUT/maintainer_question.md"
echo "$OUT/static_proxy_counts.tsv"
echo "$OUT/focused_context.txt"
