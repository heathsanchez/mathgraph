#!/usr/bin/env bash
set -u

echo "MathGraph Bounty Step v5 — tenstorrent/tt-llk #1638 comment gate + park decision"
echo

ROOT="$PWD"
OUT="$ROOT/artifacts/bounty_triage_v1/tenstorrent_ttllk_1638_comment_or_park_v5"
PREV="$ROOT/artifacts/bounty_triage_v1/tenstorrent_ttllk_1638_static_mop_map_v4"
COMMENT_SRC="$PREV/maintainer_question.md"
ISSUE_URL="https://github.com/tenstorrent/tt-llk/issues/1638"

mkdir -p "$OUT"

echo "01 check previous artifact"
if [ ! -f "$COMMENT_SRC" ]; then
  echo "ERROR missing comment source:"
  echo "$COMMENT_SRC"
  exit 1
fi

cp "$COMMENT_SRC" "$OUT/maintainer_question.md"

echo
echo "02 current status"
git status --short > "$OUT/status_start.txt"
df -h / | tee "$OUT/df_start.txt"

echo
echo "03 comment body"
cat "$OUT/maintainer_question.md"

echo
echo "04 check gh auth and existing comments"
if command -v gh >/dev/null 2>&1; then
  gh auth status > "$OUT/gh_auth_status.txt" 2>&1 || true
  cat "$OUT/gh_auth_status.txt"

  gh issue view "$ISSUE_URL" --json comments,title,state,labels,url > "$OUT/issue_view.json" 2>"$OUT/issue_view.err" || true

  python3 - "$OUT" <<'PY'
from pathlib import Path
import json, sys

out = Path(sys.argv[1])
issue_json = out / "issue_view.json"
comment_body = (out / "maintainer_question.md").read_text(errors="replace")

summary = {
    "issue_view_ok": False,
    "already_commented_similar": False,
    "matched_comment_url": None,
    "state": None,
    "title": None,
    "labels": [],
    "comment_count": 0,
}

if issue_json.exists() and issue_json.stat().st_size:
    try:
        data = json.loads(issue_json.read_text(errors="replace"))
        summary["issue_view_ok"] = True
        summary["state"] = data.get("state")
        summary["title"] = data.get("title")
        summary["labels"] = [x.get("name") for x in data.get("labels", []) if isinstance(x, dict)]
        comments = data.get("comments", []) or []
        summary["comment_count"] = len(comments)

        needles = [
            "matmul MOP/no-MOP surface",
            "llk_math_matmul_custom_no_mop.h",
            "perf_math_matmul.py",
            "minimize RISCV instructions",
            "which counter/report column should be treated as canonical",
        ]

        for c in comments:
            body = c.get("body", "") or ""
            hits = sum(1 for n in needles if n in body)
            if hits >= 3:
                summary["already_commented_similar"] = True
                summary["matched_comment_url"] = c.get("url")
                break
    except Exception as e:
        summary["error"] = repr(e)

(out / "comment_gate_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
print(json.dumps(summary, indent=2))
PY

else
  echo "gh not installed" | tee "$OUT/gh_auth_status.txt"
  cat > "$OUT/comment_gate_summary.json" <<'JSON'
{
  "issue_view_ok": false,
  "already_commented_similar": false,
  "error": "gh not installed"
}
JSON
fi

echo
echo "05 post gate"
python3 - "$OUT" <<'PY'
from pathlib import Path
import json, sys
out = Path(sys.argv[1])
summary = json.loads((out / "comment_gate_summary.json").read_text(errors="replace"))
already = bool(summary.get("already_commented_similar"))
gate = {
    "safe_to_post": (not already),
    "reason": "similar comment already exists" if already else "no similar comment detected",
    "matched_comment_url": summary.get("matched_comment_url"),
}
(out / "post_gate.json").write_text(json.dumps(gate, indent=2) + "\n")
print(json.dumps(gate, indent=2))
PY

POST_RC=0
POSTED_URL=""
if [ "${POST:-0}" = "1" ]; then
  SAFE="$(python3 - "$OUT" <<'PY'
from pathlib import Path
import json, sys
out = Path(sys.argv[1])
gate = json.loads((out / "post_gate.json").read_text(errors="replace"))
print("1" if gate.get("safe_to_post") else "0")
PY
)"
  if [ "$SAFE" = "1" ]; then
    echo "Posting comment to $ISSUE_URL"
    gh issue comment "$ISSUE_URL" --body-file "$OUT/maintainer_question.md" > "$OUT/post_comment.out" 2>"$OUT/post_comment.err" || POST_RC=$?
    cat "$OUT/post_comment.out" || true
    cat "$OUT/post_comment.err" || true
    POSTED_URL="$(cat "$OUT/post_comment.out" 2>/dev/null | tail -1 || true)"
  else
    echo "SKIP_POST: similar comment already exists"
    cat "$OUT/post_gate.json"
  fi
else
  echo "DRY RUN ONLY. To post:"
  echo "POST=1 bash tenstorrent_ttllk_1638_comment_or_park_v5.sh"
fi

echo "$POST_RC" > "$OUT/post_comment.returncode.txt"
echo "$POSTED_URL" > "$OUT/posted_url.txt"

echo
echo "06 write decision report"
python3 - "$OUT" "$PREV" <<'PY'
from pathlib import Path
import json, sys

out = Path(sys.argv[1])
prev = Path(sys.argv[2])

gate = json.loads((out / "post_gate.json").read_text(errors="replace"))
summary = json.loads((out / "comment_gate_summary.json").read_text(errors="replace"))
post_rc = (out / "post_comment.returncode.txt").read_text(errors="replace").strip() if (out / "post_comment.returncode.txt").exists() else ""
posted_url = (out / "posted_url.txt").read_text(errors="replace").strip() if (out / "posted_url.txt").exists() else ""
comment = (out / "maintainer_question.md").read_text(errors="replace")
prev_report = (prev / "REPORT.md").read_text(errors="replace") if (prev / "REPORT.md").exists() else ""

posted = posted_url or summary.get("matched_comment_url")
if posted:
    verdict = "PARK_UNTIL_MAINTAINER_ANSWERS"
elif gate.get("safe_to_post"):
    verdict = "READY_TO_POST_THEN_PARK"
else:
    verdict = "PARK_ALREADY_COMMENTED"

lines = []
lines.append("# tenstorrent/tt-llk #1638 Comment Gate v5")
lines.append("")
lines.append("## Verdict")
lines.append("")
lines.append(f"`{verdict}`")
lines.append("")
lines.append("## Why")
lines.append("")
lines.append("The static pass found a real MOP/no-MOP matmul wedge, but the bounty is not safely claimable until the maintainer confirms the exact scoring command and canonical RISCV instruction-count metric.")
lines.append("")
lines.append("## Gate")
lines.append("")
lines.append("```json")
lines.append(json.dumps(gate, indent=2))
lines.append("```")
lines.append("")
lines.append("## Issue summary")
lines.append("")
lines.append("```json")
lines.append(json.dumps(summary, indent=2))
lines.append("```")
lines.append("")
lines.append("## Post result")
lines.append("")
lines.append(f"- post rc: `{post_rc}`")
lines.append(f"- posted/matched URL: `{posted or ''}`")
lines.append("")
lines.append("## Comment")
lines.append("")
lines.append("```text")
lines.append(comment.strip())
lines.append("```")
lines.append("")
lines.append("## Next bounty routing")
lines.append("")
lines.append("1. If maintainer answers with a runnable metric, return to Tenstorrent and target `perf_math_matmul.py` / `math_matmul_perf.cpp`.")
lines.append("2. If no answer, park Tenstorrent.")
lines.append("3. Next active cash route: inspect `xevrion-v2/agent-playground #2207`.")
lines.append("4. Next prestige route: inspect `tinygrad #3039`.")
lines.append("")
lines.append("## Previous static report excerpt")
lines.append("")
lines.append("```text")
lines.append(prev_report[:12000])
lines.append("```")
lines.append("")
(out / "REPORT.md").write_text("\n".join(lines) + "\n")
print((out / "REPORT.md").read_text())
PY

echo
echo "07 commit artifact"
cd "$ROOT"
git add "$OUT" tenstorrent_ttllk_1638_comment_or_park_v5.sh
git commit -m "Add tenstorrent tt-llk issue1638 comment gate v5" || true
git push origin local-main || true

echo
echo "08 final status"
git status --short
df -h /
echo
echo "Artifacts:"
echo "$OUT/REPORT.md"
echo "$OUT/maintainer_question.md"
echo "$OUT/post_gate.json"
echo "$OUT/comment_gate_summary.json"
