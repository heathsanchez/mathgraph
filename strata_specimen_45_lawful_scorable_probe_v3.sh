#!/usr/bin/env bash
set -u

ROOT="/Users/heath/Documents/mathgraph-lean-work"
REPO="$ROOT/external/bounty_triage_v1/strata-org__specimen"
OUT="$ROOT/artifacts/bounty_triage_v1/strata_specimen_45_lawful_scorable_probe_v3"

mkdir -p "$OUT"

echo "MathGraph Strata/specimen #45 v3 — LawfulScorable compile probe"
echo

echo "01 status"
{
  date -u +"%Y-%m-%dT%H:%M:%SZ"
  df -h /
  git -C "$ROOT" status --short
} | tee "$OUT/status_start.txt"

echo
echo "02 repo update"
if [ ! -d "$REPO/.git" ]; then
  mkdir -p "$(dirname "$REPO")"
  git clone --filter=blob:none https://github.com/strata-org/specimen.git "$REPO" | tee "$OUT/git_clone.log"
fi

cd "$REPO" || exit 1
git fetch origin | tee "$OUT/git_fetch.log"
DEFAULT_BRANCH="$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's#refs/remotes/origin/##')"
if [ -z "$DEFAULT_BRANCH" ]; then DEFAULT_BRANCH="main"; fi
git checkout "$DEFAULT_BRANCH" | tee "$OUT/git_checkout.log"
git pull --ff-only origin "$DEFAULT_BRANCH" | tee "$OUT/git_pull.log"
git reset --hard "origin/$DEFAULT_BRANCH" | tee "$OUT/git_reset.log"
git clean -fd | tee "$OUT/git_clean.log"
git rev-parse HEAD | tee "$OUT/head.txt"

echo
echo "03 baseline Lean check"
{
  echo "lean-toolchain:"
  cat lean-toolchain || true
  echo
  echo "lakefile:"
  sed -n '1,160p' lakefile.toml || true
  echo
  echo "baseline Scoring.lean:"
  lake env lean Specimen/Scoring.lean
  echo "rc=$?"
} > "$OUT/baseline_scoring_check.txt" 2>&1
tail -80 "$OUT/baseline_scoring_check.txt"

echo
echo "04 extract current scoring context"
python3 - "$REPO" "$OUT" <<'PY'
from pathlib import Path
import sys, re

repo = Path(sys.argv[1])
out = Path(sys.argv[2])
p = repo / "Specimen" / "Scoring.lean"
txt = p.read_text()

patterns = [
  ("Scorable class", r"class Scorable"),
  ("DefaultScore instance", r"instance : Scorable DefaultScore"),
  ("WorstLeafScore instance", r"instance : Scorable WorstLeafScore"),
  ("DensityScore instance", r"instance : Scorable DensityScore"),
  ("UniformDensityScore instance", r"instance : Scorable UniformDensityScore"),
]

lines = txt.splitlines()
chunks = []
for title, pat in patterns:
  hit = None
  for i, line in enumerate(lines):
    if re.search(pat, line):
      hit = i
      break
  chunks.append(f"\n\n===== {title} =====")
  if hit is None:
    chunks.append("NOT FOUND")
  else:
    start = max(0, hit-12)
    end = min(len(lines), hit+45)
    for j in range(start, end):
      chunks.append(f"{j+1:04d}: {lines[j]}")

(out / "scoring_context.txt").write_text("\n".join(chunks) + "\n")
print((out / "scoring_context.txt").read_text())
PY

echo
echo "05 patch LawfulScorable class only"
python3 - "$REPO" "$OUT" <<'PY'
from pathlib import Path
import sys, difflib

repo = Path(sys.argv[1])
out = Path(sys.argv[2])
p = repo / "Specimen" / "Scoring.lean"
orig = p.read_text()

insert = r'''
/-- Laws expected from scoring strategies used by branch-and-bound search.

`Scorable` stays executable and lightweight.  `LawfulScorable` packages the
extra invariants required by proof-carrying uses of scoring strategies. -/
class LawfulScorable (S : Type) [Scorable S] : Prop where
  /-- Adding combined work to a score should not strictly improve it. -/
  not_isBetter_combine_left :
    ∀ a b : S, ¬ Scorable.isBetter (S := S) (Scorable.combine (S := S) a b) a

  /-- Strict score comparison should be transitive. -/
  isBetter_trans :
    ∀ a b c : S,
      Scorable.isBetter (S := S) a b →
      Scorable.isBetter (S := S) b c →
      Scorable.isBetter (S := S) a c

  /-- `empty` is a left identity for `combine`. -/
  empty_combine :
    ∀ a : S, Scorable.combine (S := S) (Scorable.empty (S := S)) a = a

  /-- `empty` is a right identity for `combine`. -/
  combine_empty :
    ∀ a : S, Scorable.combine (S := S) a (Scorable.empty (S := S)) = a

  /-- The initial branch-and-bound sentinel should not beat a real candidate. -/
  not_worst_isBetter :
    ∀ a : S, ¬ Scorable.isBetter (S := S) (Scorable.worst (S := S)) a

  /-- Scores that are better according to `isBetter` should not have worse visual badness. -/
  badness_mono :
    ∀ a b : S,
      Scorable.isBetter (S := S) a b →
      Scorable.badness (S := S) a ≤ Scorable.badness (S := S) b
'''

if "class LawfulScorable" in orig:
  patched = orig
else:
  marker = "  badness : S → Float\n"
  if marker not in orig:
    raise SystemExit("Could not find insertion marker after Scorable.badness")
  patched = orig.replace(marker, marker + insert, 1)

p.write_text(patched)
diff = "\n".join(difflib.unified_diff(
  orig.splitlines(),
  patched.splitlines(),
  fromfile="a/Specimen/Scoring.lean",
  tofile="b/Specimen/Scoring.lean",
  lineterm=""
)) + "\n"
(out / "lawful_scorable_class_only.diff").write_text(diff)
print(diff)
PY

echo
echo "06 patched Lean check"
cd "$REPO" || exit 1
{
  lake env lean Specimen/Scoring.lean
  echo "rc=$?"
} > "$OUT/patched_scoring_check.txt" 2>&1
tail -120 "$OUT/patched_scoring_check.txt"

echo
echo "07 patched lake build"
{
  lake build
  echo "rc=$?"
} > "$OUT/patched_lake_build.txt" 2>&1
tail -120 "$OUT/patched_lake_build.txt"

echo
echo "08 decide"
python3 - "$OUT" <<'PY'
from pathlib import Path
import sys, json, re

out = Path(sys.argv[1])
scoring = (out / "patched_scoring_check.txt").read_text(errors="replace")
build = (out / "patched_lake_build.txt").read_text(errors="replace")
diff = (out / "lawful_scorable_class_only.diff").read_text(errors="replace")

scoring_ok = "rc=0" in scoring
build_ok = "rc=0" in build
has_badness = "badness_mono" in diff
has_worst = "not_worst_isBetter" in diff
has_trans = "isBetter_trans" in diff

if scoring_ok and build_ok:
  verdict = "COMPILES__DRAFT_PR_CANDIDATE_BUT_INSTANCES_STILL_NEEDED"
elif scoring_ok:
  verdict = "SCORING_COMPILES__BUILD_FAILS_ELSEWHERE"
else:
  verdict = "PATCH_FAILS__FIX_CLASS_SHAPE"

summary = {
  "verdict": verdict,
  "scoring_check_ok": scoring_ok,
  "lake_build_ok": build_ok,
  "adds_badness_mono": has_badness,
  "adds_worst_law": has_worst,
  "adds_transitivity": has_trans,
}
(out / "decision.json").write_text(json.dumps(summary, indent=2))
print(json.dumps(summary, indent=2))
PY

echo
echo "09 write report"
python3 - "$OUT" <<'PY'
from pathlib import Path
import sys, json

out = Path(sys.argv[1])
d = json.loads((out / "decision.json").read_text())

def read(name, limit=12000):
  p = out / name
  if not p.exists(): return ""
  return p.read_text(errors="replace")[:limit]

lines = []
lines.append("# strata-org/specimen #45 LawfulScorable Probe v3")
lines.append("")
lines.append("## Verdict")
lines.append("")
lines.append(f"`{d['verdict']}`")
lines.append("")
lines.append("## What this patch does")
lines.append("")
lines.append("Adds a proof-carrying `LawfulScorable` class next to the existing executable `Scorable` interface.")
lines.append("")
lines.append("It captures the issue-requested invariants without changing runtime behavior:")
lines.append("")
lines.append("- `combine` should not improve the left score")
lines.append("- `isBetter` should be transitive")
lines.append("- `empty` should be a left and right identity")
lines.append("- `worst` should not beat a real candidate")
lines.append("- `badness` should be monotone with `isBetter`")
lines.append("")
lines.append("## Status")
lines.append("")
lines.append(f"- `Specimen/Scoring.lean` check: `{d['scoring_check_ok']}`")
lines.append(f"- `lake build`: `{d['lake_build_ok']}`")
lines.append("")
lines.append("## MathGraph classification")
lines.append("")
if d["scoring_check_ok"] and d["lake_build_ok"]:
  lines.append("- Residual: scorer invariants are implicit.")
  lines.append("- Portal: separate executable interface from lawful/proof-carrying interface.")
  lines.append("- Certificate: Lean build accepts the interface.")
  lines.append("- Remaining obstruction: proving instances may reveal that `worst := 1000` is only bounded-worst, not globally worst.")
else:
  lines.append("- Residual: scorer invariants remain implicit.")
  lines.append("- Obstruction: current proposed class shape does not yet compile cleanly.")
  lines.append("- Next action: repair the exact typeclass field syntax from Lean error output.")
lines.append("")
lines.append("## Important caveat")
lines.append("")
lines.append("The issue asks for `worst` as a valid branch-and-bound initial bound. Existing score instances use finite sentinels such as `1000`, so a strong law like `∀ a, isBetter a worst` may be false for unbounded scores. This v3 patch uses the weaker law `¬ isBetter worst a`, which is safer but may not fully satisfy the intended invariant. A later PR should either prove bounded laws or introduce a true top sentinel.")
lines.append("")
lines.append("## Diff")
lines.append("")
lines.append("```diff")
lines.append(read("lawful_scorable_class_only.diff", 20000))
lines.append("```")
lines.append("")
lines.append("## Lean check tail")
lines.append("")
lines.append("```text")
lines.append(read("patched_scoring_check.txt", 12000))
lines.append("```")
lines.append("")
lines.append("## Build tail")
lines.append("")
lines.append("```text")
lines.append(read("patched_lake_build.txt", 12000))
lines.append("```")
lines.append("")
(out / "REPORT.md").write_text("\n".join(lines) + "\n")
print((out / "REPORT.md").read_text())
PY

echo
echo "10 restore repo"
cd "$REPO" || exit 1
git reset --hard "origin/$DEFAULT_BRANCH" | tee "$OUT/restore_reset.log"
git clean -fd | tee "$OUT/restore_clean.log"

echo
echo "11 commit artifact"
cd "$ROOT" || exit 1
git add "$OUT" strata_specimen_45_lawful_scorable_probe_v3.sh
git commit -m "Add strata specimen issue45 LawfulScorable probe v3" || true
git push origin local-main || true

echo
echo "12 final status"
git status --short
df -h /
echo
echo "Artifacts:"
echo "$OUT/REPORT.md"
echo "$OUT/decision.json"
echo "$OUT/lawful_scorable_class_only.diff"
echo "$OUT/patched_scoring_check.txt"
echo "$OUT/patched_lake_build.txt"
