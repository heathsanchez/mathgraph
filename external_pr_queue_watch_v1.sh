#!/usr/bin/env bash
set -u

ROOT="/Users/heath/Documents/mathgraph-lean-work"
OUT="$ROOT/artifacts/external_pr_queue_watch_v1"

mkdir -p "$OUT"
cd "$ROOT" || exit 1

echo "MathGraph External PR Queue Watch v1"
echo

echo "01 status"
{
  date -u +"%Y-%m-%dT%H:%M:%SZ"
  df -h /
  git status --short
} | tee "$OUT/status_start.txt"

echo
echo "02 watch known external PRs"

cat > "$OUT/pr_list.tsv" <<'EOF'
strata-org/specimen	46	Add LawfulScorable scorer laws interface
Beneficial-AI-Foundation/vericoding-benchmark	12	Fill local index-bound proofs in generated specs
mo271/FormalBook	138	Fill two local arithmetic steps in Chapter 03
mo271/FormalBook	137	Fill polynomial evaluation norm step in Chapter 06
digama0/lean4lean	15	Fix constDF case in Stratified induction
digama0/lean4lean	14	Fix constDF case in StratifiedUntyped induction
teorth/equational_theories	1461	Prove Law43 term definability from swapped arguments
EOF

python3 - "$OUT" <<'PY'
from pathlib import Path
import json, sys

out = Path(sys.argv[1])
rows = []
for line in (out / "pr_list.tsv").read_text().splitlines():
  if not line.strip():
    continue
  repo, num, title = line.split("\t", 2)
  rows.append({"repo": repo, "num": num, "title_hint": title})
(out / "pr_list.json").write_text(json.dumps(rows, indent=2))
print(json.dumps(rows, indent=2))
PY

while IFS=$'\t' read -r REPO PR TITLE; do
  SAFE="$(echo "${REPO}_${PR}" | tr '/#' '__')"
  echo
  echo "===== $REPO #$PR — $TITLE ====="

  gh pr view "$PR" --repo "$REPO" \
    --json number,title,state,isDraft,url,author,baseRefName,headRefName,headRefOid,mergeable,reviewDecision,updatedAt,createdAt,comments,reviews,statusCheckRollup,files,commits \
    > "$OUT/${SAFE}_view.json" 2> "$OUT/${SAFE}_view.err" || true

  python3 - "$OUT" "$SAFE" "$REPO" "$PR" <<'PY'
from pathlib import Path
import json, sys

out = Path(sys.argv[1])
safe = sys.argv[2]
repo = sys.argv[3]
pr = sys.argv[4]

p = out / f"{safe}_view.json"
errp = out / f"{safe}_view.err"

if not p.exists() or p.stat().st_size == 0:
  print(json.dumps({
    "repo": repo,
    "pr": pr,
    "view_ok": False,
    "error": errp.read_text(errors="replace") if errp.exists() else "",
  }, indent=2))
  raise SystemExit(0)

j = json.loads(p.read_text())
comments = j.get("comments") or []
reviews = j.get("reviews") or []
checks = j.get("statusCheckRollup") or []

summary = {
  "repo": repo,
  "pr": pr,
  "view_ok": True,
  "url": j.get("url"),
  "title": j.get("title"),
  "state": j.get("state"),
  "isDraft": j.get("isDraft"),
  "mergeable": j.get("mergeable"),
  "reviewDecision": j.get("reviewDecision"),
  "updatedAt": j.get("updatedAt"),
  "headRefOid": j.get("headRefOid"),
  "comments": len(comments),
  "reviews": len(reviews),
  "checks": [
    {
      "name": c.get("name") or c.get("context") or c.get("workflowName"),
      "state": c.get("state") or c.get("status"),
      "conclusion": c.get("conclusion"),
      "url": c.get("detailsUrl") or c.get("targetUrl") or c.get("url"),
    }
    for c in checks
  ],
  "files": [
    {
      "path": f.get("path"),
      "additions": f.get("additions"),
      "deletions": f.get("deletions"),
    }
    for f in j.get("files", [])
  ],
  "latest_comments": [
    {
      "author": (c.get("author") or {}).get("login"),
      "createdAt": c.get("createdAt"),
      "body": (c.get("body") or "")[:1000],
    }
    for c in comments[-5:]
  ],
  "latest_reviews": [
    {
      "author": (r.get("author") or {}).get("login"),
      "state": r.get("state"),
      "body": (r.get("body") or "")[:1000],
    }
    for r in reviews[-5:]
  ],
}

(out / f"{safe}_summary.json").write_text(json.dumps(summary, indent=2))
print(json.dumps(summary, indent=2))
PY

  HEAD_SHA="$(python3 - "$OUT" "$SAFE" <<'PY'
from pathlib import Path
import json, sys
out = Path(sys.argv[1])
safe = sys.argv[2]
p = out / f"{safe}_summary.json"
if not p.exists():
  print("")
  raise SystemExit
j = json.loads(p.read_text())
print(j.get("headRefOid") or "")
PY
)"

  if [ -n "$HEAD_SHA" ]; then
    gh run list --repo "$REPO" --commit "$HEAD_SHA" --limit 20 \
      > "$OUT/${SAFE}_runs.txt" 2> "$OUT/${SAFE}_runs.err" || true
  else
    echo "no head sha" > "$OUT/${SAFE}_runs.err"
  fi
done < "$OUT/pr_list.tsv"

echo
echo "03 classify PR queue"
python3 - "$OUT" <<'PY'
from pathlib import Path
import json, sys

out = Path(sys.argv[1])

summaries = []
for p in sorted(out.glob("*_summary.json")):
  try:
    summaries.append(json.loads(p.read_text()))
  except Exception:
    pass

def read_runs(repo, pr):
  safe = f"{repo}_{pr}".replace("/", "_").replace("#", "_")
  s = ""
  for name in [f"{safe}_runs.txt", f"{safe}_runs.err"]:
    p = out / name
    if p.exists():
      s += p.read_text(errors="replace") + "\n"
  return s

classified = []
for s in summaries:
  repo = s["repo"]
  pr = s["pr"]
  text = json.dumps(s).lower() + "\n" + read_runs(repo, pr).lower()

  checks = s.get("checks") or []
  failed = []
  pending = []
  passed = []

  for c in checks:
    state = str(c.get("state")).lower()
    conclusion = str(c.get("conclusion")).lower()
    if conclusion in {"failure", "cancelled", "timed_out", "action_required"} or state in {"failure", "error"}:
      failed.append(c)
    elif state in {"pending", "queued", "in_progress", "waiting", "requested", "expected"} or conclusion in {"", "null", "none"}:
      pending.append(c)
    elif conclusion in {"success", "skipped", "neutral"} or state in {"success", "completed"}:
      passed.append(c)

  action_required_run = "action_required" in text
  changes_requested = "changes_requested" in text or "changes requested" in text
  approved = s.get("reviewDecision") == "APPROVED" or '"state": "approved"' in text or "approved" in text
  merged = s.get("state") == "MERGED" or s.get("state") == "CLOSED" and "merged" in text

  if merged:
    verdict = "MERGED_OR_CLOSED__ARCHIVE"
  elif changes_requested:
    verdict = "REVIEW_CHANGES_REQUESTED__PATCH_NEXT"
  elif failed:
    verdict = "CI_FAILED__PATCH_OR_LOGS_NEXT"
  elif action_required_run:
    verdict = "CI_ACTION_REQUIRED__WAIT_FOR_MAINTAINER_APPROVAL"
  elif pending:
    verdict = "CI_PENDING__WAIT"
  elif approved:
    verdict = "APPROVED__READY_OR_WAIT_MERGE"
  elif s.get("isDraft"):
    verdict = "DRAFT__WAIT_OR_MARK_READY_WHEN_COMPLETE"
  elif s.get("reviewDecision") in {"REVIEW_REQUIRED", None}:
    verdict = "AWAITING_REVIEW"
  else:
    verdict = "WATCH"

  classified.append({
    **s,
    "verdict": verdict,
    "failed_check_count": len(failed),
    "pending_check_count": len(pending),
    "passed_check_count": len(passed),
    "action_required_run": action_required_run,
    "changes_requested": changes_requested,
    "approved_detected": approved,
  })

priority_order = {
  "REVIEW_CHANGES_REQUESTED__PATCH_NEXT": 0,
  "CI_FAILED__PATCH_OR_LOGS_NEXT": 1,
  "APPROVED__READY_OR_WAIT_MERGE": 2,
  "DRAFT__WAIT_OR_MARK_READY_WHEN_COMPLETE": 3,
  "CI_ACTION_REQUIRED__WAIT_FOR_MAINTAINER_APPROVAL": 4,
  "CI_PENDING__WAIT": 5,
  "AWAITING_REVIEW": 6,
  "WATCH": 7,
  "MERGED_OR_CLOSED__ARCHIVE": 8,
}
classified.sort(key=lambda x: (priority_order.get(x["verdict"], 99), x["repo"], int(x["pr"])))

(out / "queue_decision.json").write_text(json.dumps(classified, indent=2))

md = []
md.append("# External PR Queue Watch v1")
md.append("")
md.append("## Queue verdict")
md.append("")
md.append("| priority | verdict | PR | draft | review | checks | updated | title |")
md.append("|---:|---|---|---:|---|---|---|---|")
for i, r in enumerate(classified, 1):
  checks = f"{r.get('passed_check_count',0)} pass / {r.get('pending_check_count',0)} pending / {r.get('failed_check_count',0)} fail"
  md.append(
    f"| {i} | `{r['verdict']}` | [{r['repo']}#{r['pr']}]({r['url']}) | {r.get('isDraft')} | {r.get('reviewDecision')} | {checks} | {r.get('updatedAt')} | {r.get('title')} |"
  )

md.append("")
md.append("## Immediate next action")
md.append("")
if classified:
  top = classified[0]
  if top["verdict"] in {"REVIEW_CHANGES_REQUESTED__PATCH_NEXT", "CI_FAILED__PATCH_OR_LOGS_NEXT"}:
    md.append(f"Patch next: `{top['repo']}#{top['pr']}` — {top['url']}")
  elif top["verdict"] == "DRAFT__WAIT_OR_MARK_READY_WHEN_COMPLETE":
    md.append(f"Review draft completeness: `{top['repo']}#{top['pr']}` — {top['url']}")
  else:
    md.append("No patch action required. Queue is mostly waiting on maintainers/CI approvals.")
else:
  md.append("No PRs read.")

md.append("")
md.append("## Lawbook state")
md.append("")
md.append("- Public PRs exist across Lean/FormalBook/vericoding/specimen.")
md.append("- Current obstruction is not local capability; it is maintainer review/CI approval latency.")
md.append("- Best move is to avoid random new work unless a PR returns a concrete failure/review request.")
md.append("")
(out / "REPORT.md").write_text("\n".join(md) + "\n")

print((out / "REPORT.md").read_text())
PY

echo
echo "04 commit artifact"
cd "$ROOT" || exit 1
git add "$OUT" external_pr_queue_watch_v1.sh
git commit -m "Add external PR queue watch v1" || true
git push origin local-main || true

echo
echo "05 final status"
git status --short
df -h /
echo
echo "Artifacts:"
echo "$OUT/REPORT.md"
echo "$OUT/queue_decision.json"
