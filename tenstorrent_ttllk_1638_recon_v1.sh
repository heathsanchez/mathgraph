#!/usr/bin/env bash
set -u

echo "MathGraph Bounty Recon v1 — tenstorrent/tt-llk #1638"
echo "Target: Reduce RISCV instructions used to pass tensix instructions using AI/Optimizer"
df -h /
echo

ROOT="$PWD"
REPO="$ROOT/external/bounty_triage_v1/tenstorrent__tt-llk"
OUT="$ROOT/artifacts/bounty_triage_v1/tenstorrent_ttllk_1638_recon_v1"

mkdir -p "$OUT"

if [ ! -d "$REPO/.git" ]; then
  echo "ERROR missing repo: $REPO"
  echo "Run bounty_triage_v1.sh first or clone tenstorrent/tt-llk into:"
  echo "$REPO"
  exit 1
fi

cd "$REPO"

echo "01 reset repo"
git fetch origin --depth 1 || true
git reset --hard origin/HEAD || true
git clean -fd || true

if git sparse-checkout list >/dev/null 2>&1; then
  echo "sparse checkout detected; expanding common source paths"
  git sparse-checkout set \
    README.md readme.md Readme.md \
    .github/workflows \
    src include tests test tt_llk tt_metal llk_lib \
    python pyproject.toml requirements.txt setup.py \
    CMakeLists.txt Makefile \
    docs examples scripts \
    || true
fi

git status --short | tee "$OUT/status_start.txt"
git log -1 --oneline | tee "$OUT/head.txt"
git remote -v | tee "$OUT/remotes.txt"

echo
echo "02 issue snapshot"
gh issue view "https://github.com/tenstorrent/tt-llk/issues/1638" \
  --json title,body,comments,labels,state,updatedAt,url \
  > "$OUT/issue1638_live.json" 2>"$OUT/issue1638_live.err" || true

python3 - "$OUT" <<'PY'
import json, sys
from pathlib import Path
out = Path(sys.argv[1])
p = out / "issue1638_live.json"
if p.exists() and p.stat().st_size:
    data = json.loads(p.read_text())
    print("TITLE:", data.get("title"))
    print("STATE:", data.get("state"))
    print("UPDATED:", data.get("updatedAt"))
    print("LABELS:", ", ".join(x.get("name","") for x in data.get("labels", [])))
    print()
    print((data.get("body") or "")[:5000])
else:
    print("issue fetch failed")
    print((out / "issue1638_live.err").read_text(errors="replace") if (out / "issue1638_live.err").exists() else "")
PY | tee "$OUT/issue1638_body.txt"

echo
echo "03 file inventory"
find . -maxdepth 5 -type f \
  | sed 's#^\./##' \
  | sort \
  | tee "$OUT/files_depth5.txt"

echo
echo "04 project surface"
{
  echo "== README files =="
  for f in README.md readme.md Readme.md docs/README.md; do
    if [ -f "$f" ]; then
      echo
      echo "===== $f ====="
      sed -n '1,220p' "$f"
    fi
  done

  echo
  echo "== package/python/cmake/make files =="
  for f in package.json pyproject.toml requirements.txt setup.py CMakeLists.txt Makefile; do
    if [ -f "$f" ]; then
      echo
      echo "===== $f ====="
      sed -n '1,240p' "$f"
    fi
  done

  echo
  echo "== workflows =="
  find .github/workflows -maxdepth 1 -type f 2>/dev/null | sort | while read f; do
    echo
    echo "===== $f ====="
    sed -n '1,220p' "$f"
  done
} | tee "$OUT/project_surface.txt"

echo
echo "05 grep bounty-relevant terms"
{
  echo "== riscv =="
  grep -RIn --exclude-dir=.git --exclude-dir=.lake --exclude-dir=build --exclude-dir=node_modules -E "riscv|RISCV|RISC-V|RISC" . | head -300 || true
  echo
  echo "== tensix =="
  grep -RIn --exclude-dir=.git --exclude-dir=.lake --exclude-dir=build --exclude-dir=node_modules -E "tensix|Tensix|TENSIX" . | head -300 || true
  echo
  echo "== mop/replay buffer =="
  grep -RIn --exclude-dir=.git --exclude-dir=.lake --exclude-dir=build --exclude-dir=node_modules -E "MOP|mop|replay|Replay|buffer|Buffer" . | head -400 || true
  echo
  echo "== instruction words =="
  grep -RIn --exclude-dir=.git --exclude-dir=.lake --exclude-dir=build --exclude-dir=node_modules -E "instruction|instructions|instr|issue|opcode|op code" . | head -400 || true
  echo
  echo "== tests/benchmarks =="
  grep -RIn --exclude-dir=.git --exclude-dir=.lake --exclude-dir=build --exclude-dir=node_modules -E "pytest|unittest|ctest|benchmark|bench|golden|expected|assert" . | head -400 || true
} | tee "$OUT/relevant_grep.txt"

echo
echo "06 extract candidate files"
python3 - "$OUT" <<'PY'
from pathlib import Path
import re, sys, json

out = Path(sys.argv[1])
grep = (out / "relevant_grep.txt").read_text(errors="replace")
files = []
for line in grep.splitlines():
    if line.startswith("./") and ":" in line:
        f = line.split(":", 1)[0]
        if f not in files and Path(f).exists() and Path(f).is_file():
            files.append(f)

# Filter out huge/noisy generated/dependency-ish files if any.
keep = []
for f in files:
    low = f.lower()
    if any(x in low for x in [".git/", "node_modules/", ".lake/", "build/", "__pycache__"]):
        continue
    try:
        size = Path(f).stat().st_size
    except Exception:
        continue
    if size > 500_000:
        continue
    keep.append(f)

(out / "candidate_files.txt").write_text("\n".join(keep[:120]) + ("\n" if keep else ""))

chunks = []
terms = ["riscv", "RISCV", "RISC-V", "tensix", "Tensix", "MOP", "mop", "replay", "Replay", "instruction", "buffer"]
for f in keep[:80]:
    p = Path(f)
    txt = p.read_text(errors="replace")
    lines = txt.splitlines()
    hit_lines = []
    for i, line in enumerate(lines, 1):
        if any(t in line for t in terms):
            hit_lines.append(i)
    if not hit_lines:
        continue
    chunks.append(f"\n\n===== {f} =====")
    used = set()
    for i in hit_lines[:8]:
        a = max(1, i - 8)
        b = min(len(lines), i + 14)
        key = (a,b)
        if key in used:
            continue
        used.add(key)
        chunks.append(f"\n--- around line {i} ---")
        for j in range(a, b + 1):
            chunks.append(f"{j:04d}: {lines[j-1]}")
(out / "candidate_context.txt").write_text("\n".join(chunks) + "\n")
print((out / "candidate_files.txt").read_text())
PY

sed -n '1,260p' "$OUT/candidate_context.txt" | tee "$OUT/candidate_context_head.txt"

echo
echo "07 detect runnable commands without heavy execution"
python3 - "$OUT" <<'PY'
from pathlib import Path
import json, re, sys

out = Path(sys.argv[1])
files = (out / "files_depth5.txt").read_text(errors="replace").splitlines() if (out / "files_depth5.txt").exists() else []
fset = set(files)

commands = []
notes = []

if "pyproject.toml" in fset:
    commands.append("python -m pytest")
    notes.append("pyproject.toml present")
if "requirements.txt" in fset:
    notes.append("requirements.txt present")
if any(x.startswith("tests/") or x.startswith("test/") for x in files):
    commands.append("python -m pytest tests")
    notes.append("tests directory present")
if "CMakeLists.txt" in fset:
    commands.append("cmake -S . -B build && cmake --build build")
    notes.append("CMake present")
if "Makefile" in fset:
    commands.append("make test || make")
    notes.append("Makefile present")
if any(x.startswith(".github/workflows/") for x in files):
    notes.append("GitHub Actions workflows present")
if any("bench" in x.lower() for x in files):
    notes.append("benchmark files present")

# infer from workflow content
workflow_notes = []
for wf in sorted(Path(".github/workflows").glob("*")) if Path(".github/workflows").exists() else []:
    txt = wf.read_text(errors="replace")
    for pat in ["pytest", "ctest", "cmake", "make ", "python", "pip install"]:
        if pat in txt:
            workflow_notes.append(f"{wf}: contains {pat}")

result = {
    "suggested_commands": list(dict.fromkeys(commands)),
    "notes": notes,
    "workflow_notes": workflow_notes[:80],
}
(out / "runnable_detection.json").write_text(json.dumps(result, indent=2))
print(json.dumps(result, indent=2))
PY | tee "$OUT/runnable_detection.txt"

echo
echo "08 light baseline probes"
python3 - "$OUT" <<'PY'
import subprocess, sys, json, shutil
from pathlib import Path

out = Path(sys.argv[1])
probes = []

# Keep light only. Do not build hardware stack yet.
if Path("requirements.txt").exists() or Path("pyproject.toml").exists():
    if Path("tests").exists():
        probes.append(("pytest_collect", ["python3", "-m", "pytest", "--collect-only", "-q", "tests"], 120))
    elif Path("test").exists():
        probes.append(("pytest_collect", ["python3", "-m", "pytest", "--collect-only", "-q", "test"], 120))

if Path("CMakeLists.txt").exists():
    probes.append(("cmake_help", ["cmake", "-S", ".", "-B", "build-mg-probe", "-LAH"], 180))

results = {}
for name, cmd, timeout in probes:
    print(f"\n=== {name} ===")
    try:
        p = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
        rc = p.returncode
        log = p.stdout
    except subprocess.TimeoutExpired as e:
        rc = 124
        log = e.stdout or ""
        if isinstance(log, bytes):
            log = log.decode(errors="replace")
        log += "\nTIMEOUT\n"
    (out / f"{name}.returncode.txt").write_text(str(rc) + "\n")
    (out / f"{name}.log").write_text(log)
    (out / f"{name}.tail").write_text("\n".join(log.splitlines()[-220:]) + "\n")
    results[name] = {"rc": rc, "cmd": cmd}
    print((out / f"{name}.tail").read_text())
    print(f"{name}_rc={rc}")

(out / "light_probe_results.json").write_text(json.dumps(results, indent=2))
PY

echo
echo "09 generate report"
python3 - "$OUT" <<'PY'
from pathlib import Path
import json, sys

out = Path(sys.argv[1])

issue = {}
p = out / "issue1638_live.json"
if p.exists() and p.stat().st_size:
    try:
        issue = json.loads(p.read_text())
    except Exception:
        issue = {}

title = issue.get("title", "[Bounty $1000] Reduce RISCV instructions used to pass on tensix instructions using AI/Optimizer.")
body = issue.get("body", "") or ""
labels = ", ".join(x.get("name","") for x in issue.get("labels", []))
comments = issue.get("comments", []) or []

files = (out / "candidate_files.txt").read_text(errors="replace") if (out / "candidate_files.txt").exists() else ""
ctx = (out / "candidate_context_head.txt").read_text(errors="replace") if (out / "candidate_context_head.txt").exists() else ""
runnable = (out / "runnable_detection.txt").read_text(errors="replace") if (out / "runnable_detection.txt").exists() else ""
light = (out / "light_probe_results.json").read_text(errors="replace") if (out / "light_probe_results.json").exists() else "{}"

lines = []
lines.append("# tenstorrent/tt-llk #1638 Recon v1")
lines.append("")
lines.append("## Issue")
lines.append("")
lines.append(f"- Title: {title}")
lines.append(f"- Labels: {labels}")
lines.append(f"- Comments: {len(comments)}")
lines.append("")
lines.append("## Bounty fit")
lines.append("")
lines.append("Verdict: `INSPECT_DEEPER_BEFORE_CLAIMING`")
lines.append("")
lines.append("Why it fits MathGraph:")
lines.append("")
lines.append("- It is a bounded optimization/search problem.")
lines.append("- The objective is measurable: reduce RISCV instructions while preserving tensix instruction sequence.")
lines.append("- There are explicit constraints around replay buffer usage.")
lines.append("- The likely winning loop is residual search over equivalent encodings, with local tests/benchmarks as judge.")
lines.append("")
lines.append("Main risk:")
lines.append("")
lines.append("- The repo may require specialized Tenstorrent hardware or domain knowledge to validate true performance.")
lines.append("- Do not claim/lock bounty until local objective and acceptance test are clear.")
lines.append("")
lines.append("## Issue body excerpt")
lines.append("")
lines.append("```text")
lines.append(body[:4000])
lines.append("```")
lines.append("")
lines.append("## Candidate files")
lines.append("")
if files.strip():
    for line in files.splitlines()[:80]:
        lines.append(f"- `{line}`")
else:
    lines.append("- No candidate files detected")
lines.append("")
lines.append("## Runnable detection")
lines.append("")
lines.append("```json")
lines.append(runnable[:5000])
lines.append("```")
lines.append("")
lines.append("## Light probe results")
lines.append("")
lines.append("```json")
lines.append(light[:4000])
lines.append("```")
lines.append("")
lines.append("## Candidate context excerpt")
lines.append("")
lines.append("```text")
lines.append(ctx[:12000])
lines.append("```")
lines.append("")
lines.append("## Next decision")
lines.append("")
lines.append("Proceed only if the next recon can identify:")
lines.append("")
lines.append("1. the exact MOP/replay-buffer source files,")
lines.append("2. the exact baseline instruction-count metric,")
lines.append("3. a local simulator/test/benchmark that can compare before/after,")
lines.append("4. one small op/kernel where a patch can be attempted.")
lines.append("")
lines.append("If any of these are missing, park this bounty and inspect tinygrad or xevrion instead.")
lines.append("")
(out / "REPORT.md").write_text("\n".join(lines) + "\n")
print((out / "REPORT.md").read_text())
PY

echo
echo "10 cleanup cmake probe build if present"
rm -rf build-mg-probe || true

echo
echo "11 commit artifact"
cd "$ROOT"
git add "$OUT" tenstorrent_ttllk_1638_recon_v1.sh
git commit -m "Add tenstorrent tt-llk 1638 bounty recon v1" || true
git push origin local-main || true

echo
echo "12 final status"
git status --short
df -h /
du -sh "$REPO" 2>/dev/null || true
echo
echo "Artifacts:"
echo "$OUT/REPORT.md"
echo "$OUT/candidate_context.txt"
echo "$OUT/relevant_grep.txt"
