#!/usr/bin/env bash
set -u

ROOT="/Users/heath/Documents/mathgraph-lean-work"
REPO="$ROOT/external/bounty_triage_v1/strata-org__specimen"
OUT="$ROOT/artifacts/bounty_triage_v1/strata_specimen_45_push_pr_fix_v5"
BRANCH="mathgraph-lawful-scorable-issue45"
UPSTREAM="strata-org/specimen"

mkdir -p "$OUT"

echo "MathGraph Strata/specimen #45 v5 — repair fork push and open draft PR"
echo

echo "01 status"
{
  date -u +"%Y-%m-%dT%H:%M:%SZ"
  df -h /
  git -C "$ROOT" status --short
} | tee "$OUT/status_start.txt"

echo
echo "02 enter specimen repo"
cd "$REPO" || {
  echo "Missing repo: $REPO"
  exit 1
}

git status --short | tee "$OUT/specimen_status_start.txt"
git branch --show-current | tee "$OUT/current_branch_start.txt"
git log --oneline -5 | tee "$OUT/log_start.txt"

echo
echo "03 ensure local branch and patch commit exist"
if git show-ref --verify --quiet "refs/heads/$BRANCH"; then
  git checkout "$BRANCH" | tee "$OUT/git_checkout_branch.log"
else
  echo "Branch $BRANCH not found. Recreating from origin/main."
  git fetch origin | tee "$OUT/git_fetch_origin.log"
  git checkout -B "$BRANCH" origin/main | tee "$OUT/git_recreate_branch.log"

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

if "class LawfulScorable" not in orig:
  marker = "  badness : S → Float\n"
  if marker not in orig:
    raise SystemExit("Could not find insertion marker")
  patched = orig.replace(marker, marker + insert, 1)
else:
  patched = orig

p.write_text(patched)
diff = "\n".join(difflib.unified_diff(
  orig.splitlines(),
  patched.splitlines(),
  fromfile="a/Specimen/Scoring.lean",
  tofile="b/Specimen/Scoring.lean",
  lineterm=""
)) + "\n"
(out / "recreated_patch.diff").write_text(diff)
print(diff)
PY

  git add Specimen/Scoring.lean
  git commit -m "Add LawfulScorable scorer laws interface" | tee "$OUT/recreated_commit.log"
fi

git rev-parse HEAD | tee "$OUT/local_branch_head.txt"
git show --stat --oneline HEAD | tee "$OUT/local_branch_stat.txt"

echo
echo "04 verify local build still passes"
{
  echo "lake env lean Specimen/Scoring.lean"
  lake env lean Specimen/Scoring.lean
  echo "scoring_rc=$?"
  echo
  echo "lake build"
  lake build
  echo "build_rc=$?"
} > "$OUT/local_verify.txt" 2>&1

tail -120 "$OUT/local_verify.txt"

if ! grep -q "scoring_rc=0" "$OUT/local_verify.txt"; then
  echo "Scoring check failed; aborting."
  exit 1
fi
if ! grep -q "build_rc=0" "$OUT/local_verify.txt"; then
  echo "Lake build failed; aborting."
  exit 1
fi

echo
echo "05 identify GitHub user"
GH_USER="$(gh api user --jq .login 2>/dev/null || true)"
if [ -z "$GH_USER" ]; then
  echo "Could not determine GitHub user from gh auth."
  exit 1
fi
echo "$GH_USER" | tee "$OUT/gh_user.txt"

FORK="$GH_USER/specimen"
FORK_URL="https://github.com/$FORK.git"

echo
echo "06 ensure fork exists"
if gh repo view "$FORK" --json nameWithOwner,url > "$OUT/fork_view_before.json" 2> "$OUT/fork_view_before.err"; then
  echo "Fork already exists:"
  cat "$OUT/fork_view_before.json"
else
  echo "Fork missing; creating via GitHub API..."
  gh api -X POST "repos/$UPSTREAM/forks" > "$OUT/fork_create.json" 2> "$OUT/fork_create.err" || true
  cat "$OUT/fork_create.json" || true
  cat "$OUT/fork_create.err" || true
fi

echo
echo "07 wait for fork to become readable"
FOUND=0
for i in $(seq 1 30); do
  if gh repo view "$FORK" --json nameWithOwner,url > "$OUT/fork_view_poll_$i.json" 2> "$OUT/fork_view_poll_$i.err"; then
    FOUND=1
    echo "Fork ready on poll $i"
    cat "$OUT/fork_view_poll_$i.json"
    break
  fi
  echo "poll $i: fork not ready yet"
  sleep 3
done

if [ "$FOUND" != "1" ]; then
  echo "Fork still not readable. Check:"
  echo "  gh repo view $FORK"
  echo "  cat $OUT/fork_create.err"
  exit 1
fi

echo
echo "08 set fork remote and push branch"
if git remote get-url fork >/dev/null 2>&1; then
  git remote set-url fork "$FORK_URL"
else
  git remote add fork "$FORK_URL"
fi

git remote -v | tee "$OUT/remotes.txt"

git push -u fork "$BRANCH" --force-with-lease > "$OUT/git_push_fork.out" 2> "$OUT/git_push_fork.err" || {
  echo "Push failed:"
  cat "$OUT/git_push_fork.out"
  cat "$OUT/git_push_fork.err"
  exit 1
}

cat "$OUT/git_push_fork.out"
cat "$OUT/git_push_fork.err"

echo
echo "09 verify pushed branch exists"
gh api "repos/$FORK/branches/$BRANCH" > "$OUT/fork_branch_view.json" 2> "$OUT/fork_branch_view.err" || {
  echo "Pushed branch not visible:"
  cat "$OUT/fork_branch_view.err"
  exit 1
}
cat "$OUT/fork_branch_view.json" | head -80

echo
echo "10 PR body"
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
echo "11 create or reuse draft PR"
EXISTING_PR="$(gh pr list --repo "$UPSTREAM" --head "$GH_USER:$BRANCH" --json url --jq '.[0].url' 2>/dev/null || true)"
if [ -n "$EXISTING_PR" ] && [ "$EXISTING_PR" != "null" ]; then
  echo "$EXISTING_PR" | tee "$OUT/pr_url.txt"
  echo "Existing PR found; not creating duplicate."
else
  gh pr create \
    --repo "$UPSTREAM" \
    --head "$GH_USER:$BRANCH" \
    --base main \
    --draft \
    --title "Add LawfulScorable scorer laws interface" \
    --body-file "$OUT/pr_body.md" \
    > "$OUT/pr_create.out" 2> "$OUT/pr_create.err" || true

  cat "$OUT/pr_create.out" | tee "$OUT/pr_url.txt"
  if [ ! -s "$OUT/pr_url.txt" ]; then
    echo "PR creation stderr:"
    cat "$OUT/pr_create.err"
    exit 1
  fi
fi

echo
echo "12 write report"
python3 - "$OUT" "$GH_USER" "$BRANCH" "$FORK" <<'PY'
from pathlib import Path
import sys, json

out = Path(sys.argv[1])
gh_user = sys.argv[2]
branch = sys.argv[3]
fork = sys.argv[4]

def read(name, limit=20000):
  p = out / name
  if not p.exists(): return ""
  return p.read_text(errors="replace")[:limit]

pr_url = read("pr_url.txt").strip()
verify = read("local_verify.txt", 12000)
push_err = read("git_push_fork.err", 12000)
push_out = read("git_push_fork.out", 12000)
body = read("pr_body.md", 12000)

summary = {
  "verdict": "DRAFT_PR_OPENED_OR_REUSED" if pr_url.startswith("https://") else "PR_NOT_CONFIRMED",
  "pr_url": pr_url,
  "github_user": gh_user,
  "fork": fork,
  "branch": branch,
  "local_scoring_ok": "scoring_rc=0" in verify,
  "local_build_ok": "build_rc=0" in verify,
}
(out / "summary.json").write_text(json.dumps(summary, indent=2))

lines = []
lines.append("# strata-org/specimen #45 PR Push Fix v5")
lines.append("")
lines.append("## Verdict")
lines.append("")
lines.append(f"`{summary['verdict']}`")
lines.append("")
lines.append("## PR")
lines.append("")
lines.append(pr_url or "No PR URL confirmed.")
lines.append("")
lines.append("## Fork/branch")
lines.append("")
lines.append(f"- fork: `{fork}`")
lines.append(f"- branch: `{branch}`")
lines.append("")
lines.append("## Local verifier")
lines.append("")
lines.append(f"- `Specimen/Scoring.lean`: `{summary['local_scoring_ok']}`")
lines.append(f"- `lake build`: `{summary['local_build_ok']}`")
lines.append("")
lines.append("## Meaning")
lines.append("")
lines.append("The earlier v4 attempt produced a valid local Lean patch but failed because the fork remote did not exist. v5 force-created/polled the fork, pushed the branch, and created/reused the draft PR.")
lines.append("")
lines.append("## PR body")
lines.append("")
lines.append("```text")
lines.append(body)
lines.append("```")
lines.append("")
lines.append("## Push output")
lines.append("")
lines.append("```text")
lines.append(push_out)
lines.append(push_err)
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
echo "13 commit MathGraph artifact"
cd "$ROOT" || exit 1
git add "$OUT" strata_specimen_45_push_pr_fix_v5.sh
git commit -m "Fix strata specimen issue45 draft PR fork push" || true
git push origin local-main || true

echo
echo "14 final status"
git status --short
df -h /
echo
echo "Artifacts:"
echo "$OUT/REPORT.md"
echo "$OUT/summary.json"
echo "$OUT/pr_url.txt"
echo "$OUT/local_verify.txt"
echo "$OUT/git_push_fork.err"
