#!/usr/bin/env bash
set -u

ROOT="/Users/heath/Documents/mathgraph-lean-work"
REPO="$ROOT/external/bounty_triage_v1/strata-org__specimen"
OUT="$ROOT/artifacts/bounty_triage_v1/strata_specimen_46_pr_watch_v6"
UPSTREAM="strata-org/specimen"
PR_NUM="46"

mkdir -p "$OUT"

echo "MathGraph Strata/specimen PR #46 v6 — watch CI/review and prepare next patch"
echo

echo "01 status"
{
  date -u +"%Y-%m-%dT%H:%M:%SZ"
  df -h /
  git -C "$ROOT" status --short
} | tee "$OUT/status_start.txt"

echo
echo "02 fetch PR metadata"
gh pr view "$PR_NUM" --repo "$UPSTREAM" \
  --json number,title,state,isDraft,url,author,baseRefName,headRefName,headRepositoryOwner,headRepository,commits,files,labels,body,reviews,comments,checks,mergeable,reviewDecision,updatedAt,createdAt \
  > "$OUT/pr_view.json" 2> "$OUT/pr_view.err" || true

python3 - "$OUT" <<'PY'
from pathlib import Path
import json
import sys

out = Path(sys.argv[1])
p = out / "pr_view.json"

if not p.exists() or p.stat().st_size == 0:
  print("PR view failed")
  err = out / "pr_view.err"
  if err.exists():
    print(err.read_text(errors="replace"))
  raise SystemExit(1)

j = json.loads(p.read_text())

summary = {
  "number": j.get("number"),
  "title": j.get("title"),
  "state": j.get("state"),
  "isDraft": j.get("isDraft"),
  "url": j.get("url"),
  "author": (j.get("author") or {}).get("login"),
  "baseRefName": j.get("baseRefName"),
  "headRefName": j.get("headRefName"),
  "headRepositoryOwner": (j.get("headRepositoryOwner") or {}).get("login"),
  "mergeable": j.get("mergeable"),
  "reviewDecision": j.get("reviewDecision"),
  "updatedAt": j.get("updatedAt"),
  "createdAt": j.get("createdAt"),
  "files": [
    {
      "path": f.get("path"),
      "additions": f.get("additions"),
      "deletions": f.get("deletions"),
    }
    for f in j.get("files", [])
  ],
  "commits": [
    {
      "oid": c.get("oid"),
      "messageHeadline": c.get("messageHeadline"),
    }
    for c in j.get("commits", [])
  ],
  "checks": [
    {
      "name": c.get("name"),
      "state": c.get("state"),
      "conclusion": c.get("conclusion"),
      "link": c.get("link"),
    }
    for c in j.get("checks", [])
  ],
  "reviews": [
    {
      "author": (r.get("author") or {}).get("login"),
      "state": r.get("state"),
      "body": r.get("body"),
    }
    for r in j.get("reviews", [])
  ],
  "comment_count": len(j.get("comments", [])),
}

(out / "pr_summary.json").write_text(json.dumps(summary, indent=2))
(out / "pr_body.md").write_text(j.get("body") or "")

comments = []
for c in j.get("comments", []):
  comments.append(
    "## " + str((c.get("author") or {}).get("login")) + " — " + str(c.get("createdAt")) + "\n\n" + str(c.get("body") or "") + "\n"
  )
(out / "pr_comments.md").write_text("\n---\n".join(comments))

reviews = []
for r in j.get("reviews", []):
  reviews.append(
    "## " + str((r.get("author") or {}).get("login")) + " — " + str(r.get("state")) + "\n\n" + str(r.get("body") or "") + "\n"
  )
(out / "pr_reviews.md").write_text("\n---\n".join(reviews))

print(json.dumps(summary, indent=2))
PY

echo
echo "03 inspect checks/runs"
cd "$REPO" || exit 1

git fetch origin > "$OUT/git_fetch_origin.log" 2>&1 || true
git fetch fork > "$OUT/git_fetch_fork.log" 2>&1 || true

HEAD_SHA="$(python3 - "$OUT" <<'PY'
from pathlib import Path
import json
import sys

out = Path(sys.argv[1])
j = json.loads((out / "pr_summary.json").read_text())
commits = j.get("commits") or []
if commits:
  print((commits[-1] or {}).get("oid", ""))
else:
  print("")
PY
)"

echo "$HEAD_SHA" | tee "$OUT/pr_head_sha.txt"

if [ -n "$HEAD_SHA" ]; then
  gh run list --repo "$UPSTREAM" --commit "$HEAD_SHA" --limit 20 \
    > "$OUT/gh_run_list.txt" 2> "$OUT/gh_run_list.err" || true
  cat "$OUT/gh_run_list.txt" || true
  cat "$OUT/gh_run_list.err" || true
fi

echo
echo "04 verify local branch still builds"
BRANCH="mathgraph-lawful-scorable-issue45"

if git show-ref --verify --quiet "refs/heads/$BRANCH"; then
  git checkout "$BRANCH" > "$OUT/git_checkout_branch.log" 2>&1 || true
else
  git checkout -B "$BRANCH" "fork/$BRANCH" > "$OUT/git_checkout_branch.log" 2>&1 || true
fi

{
  echo "branch:"
  git branch --show-current
  echo
  echo "head:"
  git rev-parse HEAD
  echo
  echo "status:"
  git status --short
  echo
  echo "lake env lean Specimen/Scoring.lean"
  lake env lean Specimen/Scoring.lean
  echo "scoring_rc=$?"
  echo
  echo "lake build"
  lake build
  echo "build_rc=$?"
} > "$OUT/local_verify_again.txt" 2>&1

tail -120 "$OUT/local_verify_again.txt"

echo
echo "05 classify next action"
python3 - "$OUT" <<'PY'
from pathlib import Path
import json
import sys

out = Path(sys.argv[1])
summary = json.loads((out / "pr_summary.json").read_text())

comments = ""
reviews = ""
verify = ""
runs = ""

if (out / "pr_comments.md").exists():
  comments = (out / "pr_comments.md").read_text(errors="replace")
if (out / "pr_reviews.md").exists():
  reviews = (out / "pr_reviews.md").read_text(errors="replace")
if (out / "local_verify_again.txt").exists():
  verify = (out / "local_verify_again.txt").read_text(errors="replace")
if (out / "gh_run_list.txt").exists():
  runs = (out / "gh_run_list.txt").read_text(errors="replace")

text = "\n".join([comments, reviews, runs]).lower()

checks = summary.get("checks") or []

failed_checks = []
pending_checks = []
passed_checks = []

for c in checks:
  state = str(c.get("state")).lower()
  conclusion = str(c.get("conclusion")).lower()
  if conclusion in {"failure", "cancelled", "timed_out", "action_required"} or state in {"failure"}:
    failed_checks.append(c)
  elif state in {"pending", "queued", "in_progress", "waiting", "requested"} or conclusion in {"", "null", "none"}:
    pending_checks.append(c)
  elif conclusion in {"success", "skipped", "neutral"} or state in {"success"}:
    passed_checks.append(c)

needs_instances = any(s in text for s in [
  "instance",
  "instances",
  "prove",
  "proof",
  "lawfulscorable defaultscore",
  "defaultscore",
  "worstleafscore",
  "densityscore",
  "uniformdensityscore",
])

needs_worst = any(s in text for s in [
  "worst",
  "sentinel",
  "1000",
  "bounded",
  "top",
])

needs_changes = any(s in text for s in [
  "changes requested",
  "request changes",
  "please change",
  "could you",
  "can you",
  "fail",
  "failing",
  "broken",
  "doesn't",
  "does not",
])

approved = summary.get("reviewDecision") == "APPROVED" or "approved" in text
local_ok = "scoring_rc=0" in verify and "build_rc=0" in verify

if failed_checks:
  verdict = "CI_FAILED__INSPECT_LOGS"
elif needs_instances or needs_worst or needs_changes:
  verdict = "REVIEW_ACTION_NEEDED__PREPARE_PATCH"
elif pending_checks:
  verdict = "WAIT_FOR_CI"
elif approved:
  verdict = "APPROVED_OR_POSITIVE__WAIT_OR_MARK_READY"
elif local_ok and not checks:
  verdict = "NO_CI_YET__WAIT_FOR_REVIEW"
elif local_ok:
  verdict = "LOCAL_OK__WAIT"
else:
  verdict = "LOCAL_VERIFY_FAILED__FIX_FIRST"

decision = {
  "verdict": verdict,
  "pr_url": summary.get("url"),
  "isDraft": summary.get("isDraft"),
  "state": summary.get("state"),
  "reviewDecision": summary.get("reviewDecision"),
  "local_verify_ok": local_ok,
  "check_count": len(checks),
  "failed_checks": failed_checks,
  "pending_checks": pending_checks,
  "passed_checks": passed_checks,
  "needs_instances": needs_instances,
  "needs_worst": needs_worst,
  "needs_changes": needs_changes,
  "approved": approved,
}

(out / "decision.json").write_text(json.dumps(decision, indent=2))
print(json.dumps(decision, indent=2))
PY

echo
echo "06 prepare optional v7 patch plan"
cat > "$OUT/v7_patch_plan.md" <<'MD'
# v7 Patch Plan if Review Requests More Substance

Current PR #46 only adds the proof-carrying `LawfulScorable` interface.

If maintainers ask for concrete instances, do not blindly prove all current laws. First split the laws by what is actually true.

Likely safe next steps:

1. Add weaker executable helper lemmas, not global instances, for the current score shapes.
2. Replace the too-strong global `worst` wording with a bounded version if maintainers care about `worst := 1000`.
3. Consider removing `badness_mono`: `badness : S → Float` is visual/UI-facing and proving Float monotonicity may be noisy and not central to branch-and-bound correctness.

Candidate bounded law shape:

    class BoundedWorstScorable (S : Type) [Scorable S] : Prop where
      withinBound : S -> Prop
      worst_loses_to_bounded :
        forall a : S, withinBound a -> Scorable.isBetter (S := S) a (Scorable.worst (S := S))

Most likely maintainer-good v7:

- keep `LawfulScorable` as interface
- remove or postpone `badness_mono`
- add comment explaining finite sentinels
- ask whether to model `worst` with `WithTop` or bounded law
MD

cat "$OUT/v7_patch_plan.md"

echo
echo "07 write report"
python3 - "$OUT" <<'PY'
from pathlib import Path
import json
import sys

out = Path(sys.argv[1])
decision = json.loads((out / "decision.json").read_text())
summary = json.loads((out / "pr_summary.json").read_text())

def read(name, limit=20000):
  p = out / name
  if not p.exists():
    return ""
  return p.read_text(errors="replace")[:limit]

lines = []

lines.append("# strata-org/specimen PR #46 Watch v6")
lines.append("")
lines.append("## Verdict")
lines.append("")
lines.append("`" + decision["verdict"] + "`")
lines.append("")
lines.append("## PR")
lines.append("")
lines.append(summary.get("url") or "")
lines.append("")
lines.append("## Current state")
lines.append("")
lines.append("- state: `" + str(summary.get("state")) + "`")
lines.append("- draft: `" + str(summary.get("isDraft")) + "`")
lines.append("- review decision: `" + str(summary.get("reviewDecision")) + "`")
lines.append("- local verify: `" + str(decision.get("local_verify_ok")) + "`")
lines.append("- check count: `" + str(decision.get("check_count")) + "`")
lines.append("- failed checks: `" + str(len(decision.get("failed_checks") or [])) + "`")
lines.append("- pending checks: `" + str(len(decision.get("pending_checks") or [])) + "`")
lines.append("")
lines.append("## Next action")
lines.append("")

verdict = decision["verdict"]
if verdict == "WAIT_FOR_CI":
  lines.append("Do nothing yet. Wait for CI to finish.")
elif verdict == "NO_CI_YET__WAIT_FOR_REVIEW":
  lines.append("Do nothing yet. The PR is public and locally verified; wait for maintainer review or CI.")
elif verdict == "REVIEW_ACTION_NEEDED__PREPARE_PATCH":
  lines.append("Prepare v7 patch according to maintainer comments. Likely topics: concrete instances, `worst` law strength, or removing `badness_mono`.")
elif verdict == "CI_FAILED__INSPECT_LOGS":
  lines.append("Inspect failing CI logs before editing.")
elif verdict == "LOCAL_VERIFY_FAILED__FIX_FIRST":
  lines.append("Repair local Lean build before any PR update.")
else:
  lines.append("Monitor; no immediate patch required.")

lines.append("")
lines.append("## Decision JSON")
lines.append("")
lines.append("JSON:")
lines.append(json.dumps(decision, indent=2))
lines.append("")
lines.append("## PR summary")
lines.append("")
lines.append("JSON:")
lines.append(json.dumps(summary, indent=2))
lines.append("")
lines.append("## Comments")
lines.append("")
lines.append(read("pr_comments.md", 20000))
lines.append("")
lines.append("## Reviews")
lines.append("")
lines.append(read("pr_reviews.md", 20000))
lines.append("")
lines.append("## Checks / runs")
lines.append("")
lines.append(read("gh_run_list.txt", 12000))
lines.append(read("gh_run_list.err", 12000))
lines.append("")
lines.append("## Local verify")
lines.append("")
lines.append(read("local_verify_again.txt", 12000))
lines.append("")
lines.append("## v7 patch plan")
lines.append("")
lines.append(read("v7_patch_plan.md", 16000))
lines.append("")

(out / "REPORT.md").write_text("\n".join(lines) + "\n")
print((out / "REPORT.md").read_text())
PY

echo
echo "08 commit MathGraph artifact"
cd "$ROOT" || exit 1
git add "$OUT" strata_specimen_46_pr_watch_v6.sh
git commit -m "Watch strata specimen PR46 and prepare v7 patch plan" || true
git push origin local-main || true

echo
echo "09 final status"
git status --short
df -h /
echo
echo "Artifacts:"
echo "$OUT/REPORT.md"
echo "$OUT/decision.json"
echo "$OUT/pr_summary.json"
echo "$OUT/v7_patch_plan.md"
