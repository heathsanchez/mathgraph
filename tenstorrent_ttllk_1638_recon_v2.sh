#!/usr/bin/env bash
set -u

echo "MathGraph Bounty Recon v2 — tenstorrent/tt-llk #1638"
echo "Fixes v1 heredoc/tee syntax and sparse-checkout expansion"
df -h /
echo

ROOT="$PWD"
REPO="$ROOT/external/bounty_triage_v1/tenstorrent__tt-llk"
OUT="$ROOT/artifacts/bounty_triage_v1/tenstorrent_ttllk_1638_recon_v2"

mkdir -p "$OUT"

if [ ! -d "$REPO/.git" ]; then
  echo "ERROR missing repo: $REPO"
  exit 1
fi

cd "$REPO"

echo "01 reset repo and disable sparse checkout"
git fetch origin --depth 1 || true
git reset --hard origin/HEAD || true
git clean -fd || true

if git sparse-checkout list >/dev/null 2>&1; then
  echo "disabling sparse checkout"
  git sparse-checkout disable || true
fi

git status --short | tee "$OUT/status_start.txt"
git log -1 --oneline | tee "$OUT/head.txt"
git remote -v | tee "$OUT/remotes.txt"

echo
echo "02 issue snapshot"
gh issue view "https://github.com/tenstorrent/tt-llk/issues/1638" \
  --json title,body,comments,labels,state,updatedAt,url \
  > "$OUT/issue1638_live.json" 2>"$OUT/issue1638_live.err" || true

python3 - "$OUT" <<'PY' | tee "$OUT/issue1638_body.txt"
import json
import sys
from pathlib import Path

out = Path(sys.argv[1])
p = out / "issue1638_live.json"

if p.exists() and p.stat().st_size:
    data = json.loads(p.read_text())
    print("TITLE:", data.get("title"))
    print("STATE:", data.get("state"))
    print("UPDATED:", data.get("updatedAt"))
    print("LABELS:", ", ".join(x.get("name","") for x in data.get("labels", [])))
    print("COMMENTS:", len(data.get("comments", []) or []))
    print()
    print((data.get("body") or "")[:7000])
else:
    print("issue fetch failed")
    err = out / "issue1638_live.err"
    if err.exists():
        print(err.read_text(errors="replace"))
PY

echo
echo "03 file inventory"
find . -maxdepth 7 -type f \
  | sed 's#^\./##' \
  | sort \
  | tee "$OUT/files_depth7.txt"

echo
echo "04 project surface"
{
  echo "== top-level =="
  find . -maxdepth 2 -type f | sed 's#^\./##' | sort | head -300

  echo
  echo "== README/docs/project files =="
  for f in README.md readme.md Readme.md docs/README.md package.json pyproject.toml requirements.txt setup.py CMakeLists.txt Makefile; do
    if [ -f "$f" ]; then
      echo
      echo "===== $f ====="
      sed -n '1,260p' "$f"
    fi
  done

  echo
  echo "== workflows =="
  find .github/workflows -maxdepth 1 -type f 2>/dev/null | sort | while read f; do
    echo
    echo "===== $f ====="
    sed -n '1,260p' "$f"
  done
} | tee "$OUT/project_surface.txt"

echo
echo "05 grep bounty-relevant terms"
{
  echo "== riscv =="
  grep -RIn --exclude-dir=.git --exclude-dir=build --exclude-dir=node_modules -E "riscv|RISCV|RISC-V|RISC" . | head -500 || true
  echo
  echo "== tensix =="
  grep -RIn --exclude-dir=.git --exclude-dir=build --exclude-dir=node_modules -E "tensix|Tensix|TENSIX" . | head -500 || true
  echo
  echo "== mop / replay / buffer =="
  grep -RIn --exclude-dir=.git --exclude-dir=build --exclude-dir=node_modules -E "MOP|mop|replay|Replay|buffer|Buffer" . | head -700 || true
  echo
  echo "== instruction terms =="
  grep -RIn --exclude-dir=.git --exclude-dir=build --exclude-dir=node_modules -E "instruction|instructions|instr|opcode|op code|issue" . | head -700 || true
  echo
  echo "== tt llk kernel op =="
  grep -RIn --exclude-dir=.git --exclude-dir=build --exclude-dir=node_modules -E "llk|LLK|kernel|Kernel|op_|math|sfpu|SFPU" . | head -700 || true
  echo
  echo "== tests/benchmarks/golden =="
  grep -RIn --exclude-dir=.git --exclude-dir=build --exclude-dir=node_modules -E "pytest|unittest|ctest|benchmark|bench|golden|expected|assert|compare" . | head -700 || true
} | tee "$OUT/relevant_grep.txt"

echo
echo "06 extract candidate files/context"
python3 - "$OUT" <<'PY'
from pathlib import Path
import sys

out = Path(sys.argv[1])
grep = (out / "relevant_grep.txt").read_text(errors="replace")

files = []
for line in grep.splitlines():
    if line.startswith("./") and ":" in line:
        f = line.split(":", 1)[0]
        if f not in files and Path(f).exists() and Path(f).is_file():
            files.append(f)

keep = []
for f in files:
    low = f.lower()
    if any(x in low for x in [".git/", "node_modules/", "build/", "__pycache__"]):
        continue
    try:
        size = Path(f).stat().st_size
    except Exception:
        continue
    if size > 700_000:
        continue
    keep.append(f)

(out / "candidate_files.txt").write_text("\n".join(keep[:180]) + ("\n" if keep else ""))

terms = [
    "riscv", "RISCV", "RISC-V", "tensix", "Tensix", "TENSIX",
    "MOP", "mop", "replay", "Replay", "buffer", "Buffer",
    "instruction", "instructions", "instr", "opcode",
    "llk", "LLK", "kernel", "Kernel", "sfpu", "SFPU"
]

chunks = []
for f in keep[:100]:
    p = Path(f)
    try:
        txt = p.read_text(errors="replace")
    except Exception:
        continue
    lines = txt.splitlines()
    hit_lines = []
    for i, line in enumerate(lines, 1):
        if any(t in line for t in terms):
            hit_lines.append(i)
    if not hit_lines:
        continue
    chunks.append(f"\n\n===== {f} =====")
    used = []
    for i in hit_lines[:10]:
        a = max(1, i - 8)
        b = min(len(lines), i + 16)
        if any(not (b < ua or a > ub) for ua, ub in used):
            continue
        used.append((a,b))
        chunks.append(f"\n--- around line {i} ---")
        for j in range(a, b + 1):
            chunks.append(f"{j:04d}: {lines[j-1]}")
(out / "candidate_context.txt").write_text("\n".join(chunks) + "\n")

print("Candidate files:")
print((out / "candidate_files.txt").read_text())
PY

sed -n '1,320p' "$OUT/candidate_context.txt" | tee "$OUT/candidate_context_head.txt"

echo
echo "07 detect runnable commands"
python3 - "$OUT" <<'PY' | tee "$OUT/runnable_detection.txt"
from pathlib import Path
import json
import sys

out = Path(sys.argv[1])
files = (out / "files_depth7.txt").read_text(errors="replace").splitlines() if (out / "files_depth7.txt").exists() else []
fset = set(files)

commands = []
notes = []

if "pyproject.toml" in fset:
    commands.append("python3 -m pytest")
    notes.append("pyproject.toml present")
if "requirements.txt" in fset:
    notes.append("requirements.txt present")
if any(x.startswith("tests/") for x in files):
    commands.append("python3 -m pytest tests")
    notes.append("tests directory present")
if any(x.startswith("test/") for x in files):
    commands.append("python3 -m pytest test")
    notes.append("test directory present")
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

workflow_notes = []
wfdir = Path(".github/workflows")
if wfdir.exists():
    for wf in sorted(wfdir.glob("*")):
        txt = wf.read_text(errors="replace")
        for pat in ["pytest", "ctest", "cmake", "make ", "python", "pip install", "ninja"]:
            if pat in txt:
                workflow_notes.append(f"{wf}: contains {pat}")

result = {
    "suggested_commands": list(dict.fromkeys(commands)),
    "notes": notes,
    "workflow_notes": workflow_notes[:120],
}
(out / "runnable_detection.json").write_text(json.dumps(result, indent=2))
print(json.dumps(result, indent=2))
PY

echo
echo "08 light baseline probes"
python3 - "$OUT" <<'PY'
import subprocess
import sys
import json
from pathlib import Path

out = Path(sys.argv[1])
probes = []

if Path("tests").exists():
    probes.append(("pytest_collect_tests", ["python3", "-m", "pytest", "--collect-only", "-q", "tests"], 120))
if Path("test").exists():
    probes.append(("pytest_collect_test", ["python3", "-m", "pytest", "--collect-only", "-q", "test"], 120))
if Path("CMakeLists.txt").exists():
    probes.append(("cmake_config_probe", ["cmake", "-S", ".", "-B", "build-mg-probe", "-LAH"], 180))
if Path("Makefile").exists():
    probes.append(("make_dry_help", ["make", "-n"], 60))

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
    (out / f"{name}.tail").write_text("\n".join(log.splitlines()[-240:]) + "\n")
    results[name] = {"rc": rc, "cmd": cmd}
    print((out / f"{name}.tail").read_text())
    print(f"{name}_rc={rc}")

(out / "light_probe_results.json").write_text(json.dumps(results, indent=2))
PY

echo
echo "09 generate report"
python3 - "$OUT" <<'PY'
from pathlib import Path
import json
import sys

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

candidate_count = len([x for x in files.splitlines() if x.strip()])

if candidate_count == 0:
    verdict = "PARK_OR_FULL_CLONE_REQUIRED"
elif "riscv" in ctx.lower() and ("mop" in ctx.lower() or "replay" in ctx.lower()):
    verdict = "INSPECT_DEEPER"
else:
    verdict = "MAYBE_HARDWARE_DOMAIN_RISK"

lines = []
lines.append("# tenstorrent/tt-llk #1638 Recon v2")
lines.append("")
lines.append("## Issue")
lines.append("")
lines.append(f"- Title: {title}")
lines.append(f"- Labels: {labels}")
lines.append(f"- Comments: {len(comments)}")
lines.append("")
lines.append("## Verdict")
lines.append("")
lines.append(f"`{verdict}`")
lines.append("")
lines.append("## Bounty fit")
lines.append("")
lines.append("Why it fits MathGraph:")
lines.append("")
lines.append("- bounded optimization/search problem")
lines.append("- measurable objective: reduce RISCV instructions")
lines.append("- semantic constraint: preserve tensix instruction sequence")
lines.append("- resource constraint: limited replay buffer usage")
lines.append("")
lines.append("Main risk:")
lines.append("")
lines.append("- may need Tenstorrent hardware/domain simulator for acceptance")
lines.append("- may not have an obvious local judge")
lines.append("- high codebase-specific knowledge burden")
lines.append("")
lines.append("## Issue body excerpt")
lines.append("")
lines.append("```text")
lines.append(body[:5000])
lines.append("```")
lines.append("")
lines.append("## Candidate files")
lines.append("")
if files.strip():
    for line in files.splitlines()[:120]:
        lines.append(f"- `{line}`")
else:
    lines.append("- No candidate files detected")
lines.append("")
lines.append("## Runnable detection")
lines.append("")
lines.append("```json")
lines.append(runnable[:7000])
lines.append("```")
lines.append("")
lines.append("## Light probe results")
lines.append("")
lines.append("```json")
lines.append(light[:5000])
lines.append("```")
lines.append("")
lines.append("## Candidate context excerpt")
lines.append("")
lines.append("```text")
lines.append(ctx[:16000])
lines.append("```")
lines.append("")
lines.append("## Next decision")
lines.append("")
lines.append("Proceed only if the next step identifies all four:")
lines.append("")
lines.append("1. exact MOP/replay-buffer source files")
lines.append("2. exact baseline RISCV instruction-count metric")
lines.append("3. local simulator/test/benchmark for before/after")
lines.append("4. one small op/kernel where a safe patch can be attempted")
lines.append("")
lines.append("If not, park this bounty and move to `xevrion-v2/agent-playground #2207` for easy cash or `tinygrad #3039` for prestige.")
lines.append("")
(out / "REPORT.md").write_text("\n".join(lines) + "\n")
print((out / "REPORT.md").read_text())
PY

echo
echo "10 cleanup probe build"
rm -rf build-mg-probe || true

echo
echo "11 commit artifact"
cd "$ROOT"
git add "$OUT" tenstorrent_ttllk_1638_recon_v2.sh
git commit -m "Add tenstorrent tt-llk 1638 bounty recon v2" || true
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
