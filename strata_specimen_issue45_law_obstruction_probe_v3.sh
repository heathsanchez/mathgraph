#!/usr/bin/env bash
set -u

echo "MathGraph Bounty Probe v3 — strata/specimen LawfulScorable law obstruction certifier"
df -h /
echo

ROOT="$PWD"
REPO="$ROOT/external/bounty_triage_v1/strata-org__specimen"
OUT="$ROOT/artifacts/bounty_triage_v1/strata_specimen_issue45_law_obstruction_probe_v3"

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
echo "02 create Lean obstruction probe"
cat > Specimen/LawfulScorableObstructionProbe.lean <<'LEAN'
import Specimen.Scoring

namespace Scoring

def defaultBeyondWorst : DefaultScore :=
  { checks := 1001, length := 0, unconstrained := 0 }

def worstDefault : DefaultScore :=
  Scorable.worst

def defaultWorstBeatsBeyond : Bool :=
  Scorable.isBetter worstDefault defaultBeyondWorst

def worstLeafBeyondWorst : WorstLeafScore :=
  { checks := 1001, length := 0, unconstrained := 0 }

def worstLeafWorst : WorstLeafScore :=
  Scorable.worst

def worstLeafWorstBeatsBeyond : Bool :=
  Scorable.isBetter worstLeafWorst worstLeafBeyondWorst

def defaultA : DefaultScore :=
  { checks := 1, length := 1, unconstrained := 0 }

def defaultB : DefaultScore :=
  { checks := 1, length := 0, unconstrained := 0 }

def defaultCombineImprovesLeft : Bool :=
  Scorable.isBetter (Scorable.combine defaultA defaultB) defaultA

def worstLeafA : WorstLeafScore :=
  { checks := 1, length := 1, unconstrained := 0 }

def worstLeafB : WorstLeafScore :=
  { checks := 0, length := 2, unconstrained := 0 }

def worstLeafCombineImprovesLeft : Bool :=
  Scorable.isBetter (Scorable.combine worstLeafA worstLeafB) worstLeafA

def densityA : DensityScore :=
  { density := .Checking, varDeps := 0, forChecker := false }

def densityB : DensityScore :=
  { density := .Total, varDeps := 0, forChecker := true }

def densityCombined : DensityScore :=
  Scorable.combine densityA densityB

def densityCombineImprovesLeft : Bool :=
  Scorable.isBetter densityCombined densityA

def uniformBeyondWorst : UniformDensityScore :=
  { density := .Checking, varDeps := 1001 }

def uniformWorst : UniformDensityScore :=
  Scorable.worst

def uniformWorstBeatsBeyond : Bool :=
  Scorable.isBetter uniformWorst uniformBeyondWorst

#eval IO.println s!"DefaultScore: isBetter worst {{checks:=1001}} = {defaultWorstBeatsBeyond}"
#eval IO.println s!"WorstLeafScore: isBetter worst {{checks:=1001}} = {worstLeafWorstBeatsBeyond}"
#eval IO.println s!"DefaultScore: isBetter (combine a b) a = {defaultCombineImprovesLeft}"
#eval IO.println s!"WorstLeafScore: isBetter (combine a b) a = {worstLeafCombineImprovesLeft}"
#eval IO.println s!"DensityScore combine example = {repr densityCombined}"
#eval IO.println s!"DensityScore: isBetter (combine a b) a = {densityCombineImprovesLeft}"
#eval IO.println s!"UniformDensityScore: isBetter worst {{varDeps:=1001}} = {uniformWorstBeatsBeyond}"

-- These examples intentionally show where the proposed universal laws are too strong.
-- If any of the following evaluate to true, then the corresponding universal negation
-- cannot hold over the raw score type.

end Scoring
LEAN

echo
echo "03 run Lean probe"
python3 - "$OUT" <<'PY'
import subprocess
import sys
from pathlib import Path

out = Path(sys.argv[1])

cmds = [
    ("lean_probe", ["lake", "env", "lean", "Specimen/LawfulScorableObstructionProbe.lean"], 180),
    ("lake_build_with_probe", ["lake", "build"], 420),
]

for name, cmd, timeout in cmds:
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
    print((out / f"{name}.tail").read_text())
    print(f"{name}_rc={rc}")

echo
PY

echo
echo "04 capture diff"
git diff -- Specimen/LawfulScorableObstructionProbe.lean Specimen/Scoring.lean | tee "$OUT/probe.diff"

echo
echo "05 generate report"
python3 - "$OUT" <<'PY'
from pathlib import Path
import sys
import re

out = Path(sys.argv[1])
log = (out / "lean_probe.log").read_text(errors="replace") if (out / "lean_probe.log").exists() else ""
rc = (out / "lean_probe.returncode.txt").read_text().strip() if (out / "lean_probe.returncode.txt").exists() else "missing"
build_rc = (out / "lake_build_with_probe.returncode.txt").read_text().strip() if (out / "lake_build_with_probe.returncode.txt").exists() else "missing"
diff = (out / "probe.diff").read_text(errors="replace") if (out / "probe.diff").exists() else ""

eval_lines = [line for line in log.splitlines() if ":" in line and ("Score" in line or "DensityScore" in line)]

lines = []
lines.append("# strata-org/specimen #45 Law Obstruction Probe v3")
lines.append("")
lines.append("## Result")
lines.append("")
lines.append(f"- Lean probe rc: `{rc}`")
lines.append(f"- Lake build with probe rc: `{build_rc}`")
lines.append("")
lines.append("## Evaluated law probes")
lines.append("")
lines.append("```text")
lines.extend(eval_lines if eval_lines else log.splitlines()[-80:])
lines.append("```")
lines.append("")
lines.append("## Interpretation")
lines.append("")
lines.append("The class-only `LawfulScorable` interface compiles, but some obvious universal laws are likely too strong over the raw score types.")
lines.append("")
lines.append("Key obstruction:")
lines.append("")
lines.append("```text")
lines.append("Scorable.worst is a fixed finite sentinel, e.g. checks := 1000.")
lines.append("The raw score type allows larger values, e.g. checks := 1001.")
lines.append("Therefore `isBetter worst largerScore` can evaluate to true.")
lines.append("So the law `∀ a, ¬ isBetter worst a` is not valid over all inhabitants of the score type.")
lines.append("```")
lines.append("")
lines.append("This suggests the issue needs one of these designs:")
lines.append("")
lines.append("1. weaken the law to apply only to scheduler-produced/valid scores;")
lines.append("2. add bounded-score validity predicates;")
lines.append("3. redefine `worst` as an actual top element, e.g. an `Option`/`WithTop` style score;")
lines.append("4. keep `LawfulScorable` as an interface first, then negotiate exact law fields with maintainers.")
lines.append("")
lines.append("## Best PR strategy")
lines.append("")
lines.append("Open a small PR adding only the proof-carrying `LawfulScorable` interface, with a comment that instance proofs require clarifying the intended domain of `worst` and valid scores.")
lines.append("")
lines.append("This is better than forcing false laws or adding weak placeholders.")
lines.append("")
lines.append("## Maintainer question draft")
lines.append("")
lines.append("```text")
lines.append("I started implementing `LawfulScorable`. A class-only interface compiles cleanly, but I found one design point before proving instances: `worst` is currently a finite sentinel such as `{ checks := 1000 }`, while the raw score type admits larger scores such as `{ checks := 1001 }`. So a universal law like `∀ a, ¬ isBetter worst a` is not true over all inhabitants of the score type.")
lines.append("")
lines.append("Should the laws quantify only over scheduler-produced/valid scores, should we add a validity predicate/bounded-score invariant, or should `worst` be represented as a true top element?")
lines.append("```")
lines.append("")
lines.append("## Probe diff")
lines.append("")
lines.append("```diff")
lines.append(diff[:8000])
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
git add "$OUT" strata_specimen_issue45_law_obstruction_probe_v3.sh
git commit -m "Add strata specimen issue45 law obstruction probe v3" || true
git push origin local-main || true

echo
echo "08 final status"
git status --short
df -h /
du -sh "$REPO" 2>/dev/null || true
echo
echo "Artifacts:"
echo "$OUT/REPORT.md"
echo "$OUT/lean_probe.log"
