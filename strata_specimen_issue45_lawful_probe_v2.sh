#!/usr/bin/env bash
set -u

echo "MathGraph Bounty Probe v2 — strata-org/specimen #45 LawfulScorable"
df -h /
echo

ROOT="$PWD"
REPO="$ROOT/external/bounty_triage_v1/strata-org__specimen"
OUT="$ROOT/artifacts/bounty_triage_v1/strata_specimen_issue45_lawful_probe_v2"

mkdir -p "$OUT"

if [ ! -d "$REPO/.git" ]; then
  echo "ERROR missing repo: $REPO"
  exit 1
fi

cd "$REPO"

echo "01 reset repo"
git reset --hard origin/HEAD || true
git clean -fd || true
git status --short | tee "$OUT/status_start.txt"
git log -1 --oneline | tee "$OUT/head.txt"

echo
echo "02 targeted source extraction"
python3 - <<'PY'
from pathlib import Path
import re

out = Path("__OUT__")
PY

python3 - "$OUT" <<'PY'
from pathlib import Path
import re
import sys

out = Path(sys.argv[1])
scoring = Path("Specimen/Scoring.lean")
derive = Path("Specimen/DeriveSchedules.lean")
producer = Path("Specimen/DeriveConstrainedProducer.lean")

def read(p):
    return p.read_text(errors="replace").splitlines()

def write_range(lines, a, b, label):
    xs = [f"===== {label} lines {a}-{b} ====="]
    for i in range(max(1, a), min(len(lines), b) + 1):
        xs.append(f"{i:04d}: {lines[i-1]}")
    xs.append("")
    return "\n".join(xs)

s = read(scoring)
d = read(derive)
p = read(producer)

chunks = []
for a,b,label in [
    (1,90,"Scoring header + Scorable"),
    (90,160,"DefaultScore"),
    (330,380,"WorstLeafScore"),
    (430,465,"DensityScore"),
    (520,545,"UniformDensityScore"),
    (220,245,"mkScorerBundle"),
]:
    chunks.append(write_range(s,a,b,label))

chunks.append(write_range(d,1260,1295,"searchBestScheduleM signature"))
chunks.append(write_range(p,595,625,"DeriveConstrainedProducer searchBestScheduleM call"))

(out / "targeted_context.txt").write_text("\n".join(chunks))
print((out / "targeted_context.txt").read_text())
PY

echo
echo "03 create candidate patches"
python3 - "$OUT" <<'PY'
from pathlib import Path
import sys
import re

out = Path(sys.argv[1])
src = Path("Specimen/Scoring.lean")
orig = src.read_text()

needle = """class Scorable (S : Type) where
  empty : S
  combine : S → S → S
  isBetter : S → S → Bool
  bestOf : List S → S
  uncoveredPenalty : S
  /-- Must be worse than any real schedule under `isBetter`. -/
  worst : S
  badness : S → Float
"""

candidate_class_only = needle + r"""

/-- Laws expected from scoring strategies used by branch-and-bound search.

These laws are packaged separately from `Scorable` so existing scoring strategies
can keep their executable data while proof-carrying uses can request the lawful
interface explicitly. -/
class LawfulScorable (S : Type) [Scorable S] : Prop where
  /-- Adding work to a score should never strictly improve it. -/
  not_isBetter_combine_left : ∀ a b : S, ¬ Scorable.isBetter (Scorable.combine a b) a
  /-- Strict score comparison should be transitive. -/
  isBetter_trans : ∀ a b c : S,
    Scorable.isBetter a b → Scorable.isBetter b c → Scorable.isBetter a c
  /-- `empty` is a left identity for `combine`. -/
  empty_combine : ∀ a : S, Scorable.combine Scorable.empty a = a
  /-- `empty` is a right identity for `combine`. -/
  combine_empty : ∀ a : S, Scorable.combine a Scorable.empty = a
  /-- `worst` should not beat any real score. -/
  not_worst_isBetter : ∀ a : S, ¬ Scorable.isBetter Scorable.worst a
"""

patches = {}

patches["v01_class_only"] = orig.replace(needle, candidate_class_only)

# Conservative: class only + add LawfulScorable constraints nowhere.
# This is likely acceptable as a first PR if maintainers want the interface split.

for name, text in patches.items():
    p = out / f"{name}.lean"
    p.write_text(text)
PY

echo
echo "04 probe class-only patch"
cp "$OUT/v01_class_only.lean" Specimen/Scoring.lean

python3 - "$OUT" <<'PY'
import subprocess
import sys
from pathlib import Path

out = Path(sys.argv[1])

for cmd_name, cmd, timeout in [
    ("lean_scoring", ["lake", "env", "lean", "Specimen/Scoring.lean"], 180),
    ("lake_build", ["lake", "build"], 420),
]:
    print(f"\n=== {cmd_name} ===")
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

    (out / f"{cmd_name}.returncode.txt").write_text(str(rc) + "\n")
    (out / f"{cmd_name}.log").write_text(log)
    (out / f"{cmd_name}.tail").write_text("\n".join(log.splitlines()[-220:]) + "\n")
    print((out / f"{cmd_name}.tail").read_text())
    print(f"{cmd_name}_rc={rc}")

    if rc != 0:
        break
PY

RC_LEAN="$(cat "$OUT/lean_scoring.returncode.txt" 2>/dev/null || echo missing)"
RC_BUILD="$(cat "$OUT/lake_build.returncode.txt" 2>/dev/null || echo missing)"

echo
echo "05 diff and report"
git diff -- Specimen/Scoring.lean | tee "$OUT/v01_class_only.diff"

python3 - "$OUT" "$RC_LEAN" "$RC_BUILD" <<'PY'
from pathlib import Path
import sys
import json

out = Path(sys.argv[1])
rc_lean = sys.argv[2]
rc_build = sys.argv[3]

issue_body = ""
p = out / "issue45_live.json"
if p.exists() and p.stat().st_size:
    try:
        issue_body = json.loads(p.read_text()).get("body", "") or ""
    except Exception:
        pass

ctx = (out / "targeted_context.txt").read_text(errors="replace") if (out / "targeted_context.txt").exists() else ""
diff = (out / "v01_class_only.diff").read_text(errors="replace") if (out / "v01_class_only.diff").exists() else ""

lines = []
lines.append("# strata-org/specimen #45 LawfulScorable Probe v2")
lines.append("")
lines.append("## Result")
lines.append("")
lines.append(f"- `lake env lean Specimen/Scoring.lean` rc: `{rc_lean}`")
lines.append(f"- `lake build` rc: `{rc_build}`")
lines.append("")
if rc_lean == "0" and rc_build == "0":
    lines.append("Verdict: `CLASS_ONLY_COMPILES`")
    lines.append("")
    lines.append("This gives a clean first PR surface: define `LawfulScorable` as a proof-carrying interface without yet forcing it through the scheduler.")
else:
    lines.append("Verdict: `CLASS_ONLY_FAILED`")
    lines.append("")
    lines.append("Inspect the Lean tail logs before proceeding.")
lines.append("")
lines.append("## Why this is the right first cut")
lines.append("")
lines.append("- The issue asks for a law-carrying scorer interface.")
lines.append("- The current `Scorable` class is executable only.")
lines.append("- Built-in scorer names in the issue appear partly stale: `GradedUniformDensityScore`, `BoundedGradedScore`, and `SourceQualityScore` were not found.")
lines.append("- The live repo has `DefaultScore`, `WorstLeafScore`, `DensityScore`, and `UniformDensityScore`.")
lines.append("- A class-only PR is low-risk and lets maintainers confirm the intended law shape before we prove all instances.")
lines.append("")
lines.append("## Candidate diff")
lines.append("")
lines.append("```diff")
lines.append(diff[:6000])
lines.append("```")
lines.append("")
lines.append("## Targeted source context")
lines.append("")
lines.append("```text")
lines.append(ctx[:12000])
lines.append("```")
lines.append("")
(out / "REPORT.md").write_text("\n".join(lines) + "\n")
print((out / "REPORT.md").read_text())
PY

echo
echo "06 restore repo"
git reset --hard origin/HEAD || true
git clean -fd || true

echo
echo "07 commit artifact"
cd "$ROOT"
git add "$OUT" strata_specimen_issue45_lawful_probe_v2.sh
git commit -m "Add strata specimen issue45 LawfulScorable probe v2" || true
git push origin local-main || true

echo
echo "08 final status"
git status --short
df -h /
du -sh "$REPO" 2>/dev/null || true
echo
echo "Artifacts:"
echo "$OUT/REPORT.md"
echo "$OUT/v01_class_only.diff"
echo "$OUT/targeted_context.txt"
