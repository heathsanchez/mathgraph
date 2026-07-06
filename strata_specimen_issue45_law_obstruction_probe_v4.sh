#!/usr/bin/env bash
set -u

echo "MathGraph Bounty Probe v4 — clean LawfulScorable counterexample certificate"
df -h /
echo

ROOT="$PWD"
REPO="$ROOT/external/bounty_triage_v1/strata-org__specimen"
OUT="$ROOT/artifacts/bounty_triage_v1/strata_specimen_issue45_law_obstruction_probe_v4"

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
echo "02 create clean Lean obstruction probe"
cat > Specimen/LawfulScorableObstructionProbe.lean <<'LEAN'
import Specimen.Scoring

namespace Scoring

/-
This file is not intended as a repo patch.
It certifies that some plausible global LawfulScorable laws are false
for the current raw score types.
-/

def defaultBeyondWorst : DefaultScore :=
  { checks := 1001, length := 0, unconstrained := 0 }

def worstDefault : DefaultScore :=
  (Scorable.worst : DefaultScore)

def defaultWorstBeatsBeyond : Bool :=
  Scorable.isBetter worstDefault defaultBeyondWorst

def worstLeafBeyondWorst : WorstLeafScore :=
  { checks := 1001, length := 0, unconstrained := 0 }

def worstLeafWorst : WorstLeafScore :=
  (Scorable.worst : WorstLeafScore)

def worstLeafWorstBeatsBeyond : Bool :=
  Scorable.isBetter worstLeafWorst worstLeafBeyondWorst

def uniformBeyondWorst : UniformDensityScore :=
  { density := .Checking, varDeps := 1001 }

def uniformWorst : UniformDensityScore :=
  (Scorable.worst : UniformDensityScore)

def uniformWorstBeatsBeyond : Bool :=
  Scorable.isBetter uniformWorst uniformBeyondWorst

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

/-
DensityScore has an especially direct obstruction.

For generator mode (`forChecker = false`), larger density.toNat is worse.
For checker mode (`forChecker = true`), the comparison reverses density level.
Combining uses OR for `forChecker`, so combine can flip the interpretation
and make the combined score strictly better than the original left score.
-/
def densityA : DensityScore :=
  { density := .Checking, varDeps := 0, forChecker := false }

def densityB : DensityScore :=
  { density := .Total, varDeps := 0, forChecker := true }

def densityCombined : DensityScore :=
  Scorable.combine densityA densityB

def densityCombineImprovesLeft : Bool :=
  Scorable.isBetter densityCombined densityA

-- Boolean certificates.
example : defaultWorstBeatsBeyond = true := by native_decide
example : worstLeafWorstBeatsBeyond = true := by native_decide
example : uniformWorstBeatsBeyond = true := by native_decide
example : defaultCombineImprovesLeft = false := by native_decide
example : worstLeafCombineImprovesLeft = false := by native_decide
example : densityCombineImprovesLeft = true := by native_decide

#eval IO.println "DefaultScore worst beats beyond-worst score:"
#eval IO.println defaultWorstBeatsBeyond

#eval IO.println "WorstLeafScore worst beats beyond-worst score:"
#eval IO.println worstLeafWorstBeatsBeyond

#eval IO.println "UniformDensityScore worst beats beyond-worst score:"
#eval IO.println uniformWorstBeatsBeyond

#eval IO.println "DefaultScore combine improves left:"
#eval IO.println defaultCombineImprovesLeft

#eval IO.println "WorstLeafScore combine improves left:"
#eval IO.println worstLeafCombineImprovesLeft

#eval IO.println "DensityScore combined value:"
#eval IO.println (repr densityCombined)

#eval IO.println "DensityScore combine improves left:"
#eval IO.println densityCombineImprovesLeft

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
PY

echo
echo "04 capture probe file and diff"
cp Specimen/LawfulScorableObstructionProbe.lean "$OUT/LawfulScorableObstructionProbe.lean"
git diff -- Specimen/LawfulScorableObstructionProbe.lean | tee "$OUT/probe.diff"

echo
echo "05 generate report"
python3 - "$OUT" <<'PY'
from pathlib import Path
import sys

out = Path(sys.argv[1])
log = (out / "lean_probe.log").read_text(errors="replace") if (out / "lean_probe.log").exists() else ""
rc = (out / "lean_probe.returncode.txt").read_text().strip() if (out / "lean_probe.returncode.txt").exists() else "missing"
build_rc = (out / "lake_build_with_probe.returncode.txt").read_text().strip() if (out / "lake_build_with_probe.returncode.txt").exists() else "missing"
probe = (out / "LawfulScorableObstructionProbe.lean").read_text(errors="replace") if (out / "LawfulScorableObstructionProbe.lean").exists() else ""

lines = []
lines.append("# strata-org/specimen #45 LawfulScorable Obstruction Probe v4")
lines.append("")
lines.append("## Result")
lines.append("")
lines.append(f"- `lake env lean Specimen/LawfulScorableObstructionProbe.lean` rc: `{rc}`")
lines.append(f"- `lake build` with probe file rc: `{build_rc}`")
lines.append("")
if rc == "0":
    lines.append("Verdict: `CERTIFIED_COUNTEREXAMPLES`")
else:
    lines.append("Verdict: `PROBE_FAILED`")
lines.append("")
lines.append("## Eval output")
lines.append("")
lines.append("```text")
lines.append(log.strip())
lines.append("```")
lines.append("")
lines.append("## What this proves")
lines.append("")
lines.append("The currently obvious global `LawfulScorable` laws are too strong for the raw score types.")
lines.append("")
lines.append("Counterexamples certified by Lean:")
lines.append("")
lines.append("1. `worst` is a finite sentinel, not a true top element.")
lines.append("   For `DefaultScore`, `WorstLeafScore`, and `UniformDensityScore`, a raw score with `1001` can be worse than the `{ ... := 1000 }` sentinel, so `Scorable.isBetter worst largerScore = true`.")
lines.append("")
lines.append("2. `DensityScore.combine` can strictly improve the left score.")
lines.append("   `combine` uses `forChecker := a.forChecker || b.forChecker`, while `Ord DensityScore` reverses density ordering when `forChecker = true`. This permits `isBetter (combine a b) a = true`.")
lines.append("")
lines.append("Therefore a class with laws like:")
lines.append("")
lines.append("```lean")
lines.append("∀ a b, ¬ Scorable.isBetter (Scorable.combine a b) a")
lines.append("∀ a, ¬ Scorable.isBetter Scorable.worst a")
lines.append("```")
lines.append("")
lines.append("cannot be instantiated for the current raw score types without changing semantics, adding validity predicates, or weakening the laws.")
lines.append("")
lines.append("## Recommended action")
lines.append("")
lines.append("Do not open a PR claiming full `LawfulScorable` instances yet.")
lines.append("")
lines.append("Best move is a maintainer comment asking for the intended law domain:")
lines.append("")
lines.append("```text")
lines.append("I started implementing `LawfulScorable` for #45 and found two design constraints before opening a PR.")
lines.append("")
lines.append("First, `worst` is currently a finite sentinel such as `{ checks := 1000 }`, while the raw score types admit larger scores, so `isBetter worst { checks := 1001 }` can evaluate to true. That means a global law like `∀ a, ¬ isBetter worst a` is not valid over all inhabitants.")
lines.append("")
lines.append("Second, for `DensityScore`, `combine` can flip `forChecker` to true, and the ordering reverses density interpretation in checker mode. I found a small example where `isBetter (combine a b) a = true`, so the monotonicity law is also not globally valid for the raw type.")
lines.append("")
lines.append("Should `LawfulScorable` quantify over a validity predicate / scheduler-produced scores, should `worst` become a true top element, or should the intended laws be weaker?")
lines.append("```")
lines.append("")
lines.append("## Probe source")
lines.append("")
lines.append("```lean")
lines.append(probe)
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
git add "$OUT" strata_specimen_issue45_law_obstruction_probe_v4.sh
git commit -m "Add strata specimen issue45 certified law obstruction probe v4" || true
git push origin local-main || true

echo
echo "08 final status"
git status --short
df -h /
du -sh "$REPO" 2>/dev/null || true
echo
echo "Artifacts:"
echo "$OUT/REPORT.md"
echo "$OUT/LawfulScorableObstructionProbe.lean"
