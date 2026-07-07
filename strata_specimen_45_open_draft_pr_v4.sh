#!/usr/bin/env bash
set -u

ROOT="/Users/heath/Documents/mathgraph-lean-work"
REPO="$ROOT/external/bounty_triage_v1/strata-org__specimen"
OUT="$ROOT/artifacts/bounty_triage_v1/strata_specimen_45_open_draft_pr_v4"
BRANCH="mathgraph-lawful-scorable-issue45"

mkdir -p "$OUT"

echo "MathGraph Strata/specimen #45 v4 — open draft PR from build-accepted LawfulScorable patch"
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
git checkout "$DEFAULT_BRANCH" | tee "$OUT/git_checkout_default.log"
git pull --ff-only origin "$DEFAULT_BRANCH" | tee "$OUT/git_pull.log"
git reset --hard "origin/$DEFAULT_BRANCH" | tee "$OUT/git_reset.log"
git clean -fd | tee "$OUT/git_clean.log"
git rev-parse HEAD | tee "$OUT/base_head.txt"

echo
echo "03 create branch"
git checkout -B "$BRANCH" | tee "$OUT/git_checkout_branch.log"

echo
echo "04 apply LawfulScorable patch"
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
(out / "pr_patch.diff").write_text(diff)
print(diff)
PY

echo
echo "05 run local verifier"
{
  echo "lean-toolchain:"
  cat lean-toolchain || true
  echo
  echo "lake env lean Specimen/Scoring.lean"
  lake env lean Specimen/Scoring.lean
  echo "scoring_rc=$?"
  echo
  echo "lake build"
  lake build
  echo "build_rc=$?"
} > "$OUT/local_verify.txt" 2>&1
tail -160 "$OUT/local_verify.txt"

if ! grep -q "scoring_rc=0" "$OUT/local_verify.txt"; then
  echo "Scoring.lean check failed; not opening PR."
  exit 1
fi

if ! grep -q "build_rc=0" "$OUT/local_verify.txt"; then
  echo "lake build failed; not opening PR."
  exit 1
fi

echo
echo "06 commit specimen branch"
git status --short | tee "$OUT/specimen_status_before_commit.txt"
git add Specimen/Scoring.lean
git commit -m "Add LawfulScorable scorer laws interface" | tee "$OUT/specimen_commit.log" || true
git rev-parse HEAD | tee "$OUT/branch_head.txt"
git show --stat --oneline HEAD | tee "$OUT/branch_commit_stat.txt"

echo
echo "07 fork remote and push"
GH_USER="$(gh api user --jq .login 2>/dev/null || true)"
if [ -z "$GH_USER" ]; then
  echo "Could not determine gh user."
  exit 1
fi
echo "$GH_USER" | tee "$OUT/gh_user.txt"

gh repo fork strata-org/specimen --clone=false --remote=false > "$OUT/gh_fork.out" 2> "$OUT/gh_fork.err" || true

if git remote get-url fork >/dev/null 2>&1; then
  git remote set-url fork "https://github.com/$GH_USER/specimen.git"
else
  git remote add fork "https://github.com/$GH_USER/specimen.git"
fi

git remote -v | tee "$OUT/remotes.txt"
git push -u fork "$BRANCH" | tee "$OUT/git_push_fork.log"

echo
echo "08 PR body"
cat > "$OUT/pr_body.md" <<'EOF'
Draft progress for #45.

This PR adds a proof-carrying `LawfulScorable` interface next to the existing executable `Scorable` typeclass.

What is included:

- `combine` should not strictly improve the left score
- `isBetter` should be transitive
- `empty` should be a left and right identity for `combine`
- `worst` should not beat a real candidate
- `badness` should be monotone with `isBetter`

Local verification:

- `lake env lean Specimen/Scoring.lean` passes
- `lake build` passes

I kept this as a separate law class rather than modifying `Scorable`, so existing scoring strategies remain executable/lightweight and proof-carrying code can request the stronger interface explicitly.

Important design note: the issue text says `worst` must be worse than any real schedule. The current instances use finite sentinels such as `1000`, so a strong global law like “every score beats worst” may not hold for unbounded scores. This draft therefore uses the safer law “worst does not beat a candidate” while leaving open whether the final fix should use bounded laws or a true top sentinel.

Next step after feedback: add `LawfulScorable` instances or refine the `worst` law to match the intended branch-and-bound invariant.

Refs #45.
EOF

cat "$OUT/pr_body.md"

echo
echo "09 create or reuse draft PR"
EXISTING_PR="$(gh pr list --repo strata-org/specimen --head "$GH_USER:$BRANCH" --json url --jq '.[0].url' 2>/dev/null || true)"
if [ -n "$EXISTING_PR" ] && [ "$EXISTING_PR" != "null" ]; then
  echo "$EXISTING_PR" | tee "$OUT/pr_url.txt"
  echo "Existing PR found; not creating duplicate."
else
  gh pr create \
    --repo strata-org/specimen \
    --head "$GH_USER:$BRANCH" \
    --base "$DEFAULT_BRANCH" \
    --draft \
    --title "Add LawfulScorable scorer laws interface" \
    --body-file "$OUT/pr_body.md" \
    > "$OUT/pr_create.out" 2> "$OUT/pr_create.err" || true

  cat "$OUT/pr_create.out" | tee "$OUT/pr_url.txt"
  if [ ! -s "$OUT/pr_url.txt" ]; then
    echo "PR creation stderr:"
    cat "$OUT/pr_create.err"
  fi
fi

echo
echo "10 write report"
python3 - "$OUT" "$GH_USER" "$BRANCH" <<'PY'
from pathlib import Path
import sys, json

out = Path(sys.argv[1])
gh_user = sys.argv[2]
branch = sys.argv[3]

def read(name, limit=20000):
  p = out / name
  if not p.exists():
    return ""
  return p.read_text(errors="replace")[:limit]

pr_url = read("pr_url.txt").strip()
verify = read("local_verify.txt", 12000)
diff = read("pr_patch.diff", 20000)

ok = "scoring_rc=0" in verify and "build_rc=0" in verify and pr_url.startswith("https://")

summary = {
  "verdict": "DRAFT_PR_OPENED_OR_REUSED" if ok else "PR_NOT_CONFIRMED",
  "pr_url": pr_url,
  "branch": branch,
  "github_user": gh_user,
  "local_scoring_ok": "scoring_rc=0" in verify,
  "local_build_ok": "build_rc=0" in verify,
}
(out / "summary.json").write_text(json.dumps(summary, indent=2))

lines = []
lines.append("# strata-org/specimen #45 Draft PR v4")
lines.append("")
lines.append("## Verdict")
lines.append("")
lines.append(f"`{summary['verdict']}`")
lines.append("")
lines.append("## PR")
lines.append("")
lines.append(pr_url or "No PR URL confirmed.")
lines.append("")
lines.append("## Local verifier")
lines.append("")
lines.append(f"- `Specimen/Scoring.lean`: `{summary['local_scoring_ok']}`")
lines.append(f"- `lake build`: `{summary['local_build_ok']}`")
lines.append("")
lines.append("## Meaning")
lines.append("")
lines.append("This converts the local build-accepted LawfulScorable patch into a visible external-verifier trace.")
lines.append("")
lines.append("The PR is intentionally draft because it defines the proof-carrying law interface but does not yet prove the concrete score instances.")
lines.append("")
lines.append("## Lawbook entry")
lines.append("")
lines.append("- Residual: scorer invariants were implicit in executable `Scorable`.")
lines.append("- Portal: add separate proof-carrying `LawfulScorable` interface.")
lines.append("- Certificate: local Lean checker and full lake build accept the interface.")
lines.append("- Remaining obstruction: finite `worst := 1000` sentinels may not support a strong global worst law.")
lines.append("")
lines.append("## Diff")
lines.append("")
lines.append("```diff")
lines.append(diff)
lines.append("```")
lines.append("")
lines.append("## Verify log")
lines.append("")
lines.append("```text")
lines.append(verify)
lines.append("```")
lines.append("")
(out / "REPORT.md").write_text("\n".join(lines) + "\n")
print((out / "REPORT.md").read_text())
PY

echo
echo "11 commit MathGraph artifact"
cd "$ROOT" || exit 1
git add "$OUT" strata_specimen_45_open_draft_pr_v4.sh
git commit -m "Open strata specimen issue45 LawfulScorable draft PR" || true
git push origin local-main || true

echo
echo "12 final status"
git status --short
df -h /
echo
echo "Artifacts:"
echo "$OUT/REPORT.md"
echo "$OUT/summary.json"
echo "$OUT/pr_url.txt"
echo "$OUT/pr_patch.diff"
echo "$OUT/local_verify.txt"
