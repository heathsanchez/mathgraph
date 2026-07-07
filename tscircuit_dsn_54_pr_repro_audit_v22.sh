#!/usr/bin/env bash
set -euo pipefail

echo "MathGraph tscircuit/dsn-converter #54 PR/Repro Audit v22"
echo "Goal: determine whether #54 is still live, what prior PRs/comments did, and whether Smoothie Board repro still fails locally."
echo

ROOT="/Users/heath/Documents/mathgraph-lean-work"
REPO="tscircuit/dsn-converter"
ISSUE="54"
DIR="$ROOT/external/cash_win_recon_v21/tscircuit__dsn-converter_54"
OUT="$ROOT/artifacts/tscircuit_dsn_54_pr_repro_audit_v22"

mkdir -p "$OUT"
cd "$ROOT"

echo "01 status"
date -u +"%Y-%m-%dT%H:%M:%SZ" | tee "$OUT/status_start.txt"
df -h / | tee "$OUT/df_start.txt"
git status --short | tee "$OUT/mathgraph_status_start.txt" || true
echo

echo "02 issue full audit"
gh issue view "$ISSUE" -R "$REPO" --comments > "$OUT/issue_54_full.txt"
grep -nEi "bounty|claim|claimed|assigned|available|smoothie|dsn|repro|test|fix|fixed|pr|pull request|merged|closed|heathsanchez" "$OUT/issue_54_full.txt" | tee "$OUT/issue_signal_lines.txt" || true
echo

echo "03 timeline and PR audit"
gh api \
  -H "Accept: application/vnd.github+json" \
  "/repos/$REPO/issues/$ISSUE/timeline?per_page=100" \
  > "$OUT/issue_54_timeline.json" 2> "$OUT/issue_54_timeline.err" || true

gh pr list -R "$REPO" --state all --limit 100 --search "54 OR Smoothie OR smoothie OR dsn" --json number,title,state,isDraft,author,createdAt,updatedAt,mergedAt,url,headRefName,baseRefName > "$OUT/pr_search.json" 2> "$OUT/pr_search.err" || true

python3 - "$OUT" <<'PY'
from pathlib import Path
import json, sys, re

out = Path(sys.argv[1])

timeline = []
if (out / "issue_54_timeline.json").exists():
    try:
        timeline = json.loads((out / "issue_54_timeline.json").read_text())
    except Exception:
        timeline = []

prs = []
if (out / "pr_search.json").exists():
    try:
        prs = json.loads((out / "pr_search.json").read_text())
    except Exception:
        prs = []

events = []
for ev in timeline:
    et = ev.get("event") or ev.get("event_type") or ""
    actor = (ev.get("actor") or {}).get("login")
    created = ev.get("created_at")
    item = {
        "event": et,
        "actor": actor,
        "created_at": created,
    }
    if ev.get("source"):
        item["source"] = ev.get("source")
    if ev.get("commit_id"):
        item["commit_id"] = ev.get("commit_id")
    if ev.get("url"):
        item["url"] = ev.get("url")
    events.append(item)

summary = {
    "timeline_event_count": len(events),
    "timeline_events": events,
    "pr_count": len(prs),
    "prs": prs,
}
(out / "timeline_pr_summary.json").write_text(json.dumps(summary, indent=2) + "\n")

print(json.dumps(summary, indent=2)[:12000])
PY
echo

echo "04 repo update and Smoothie surface"
if [ ! -d "$DIR/.git" ]; then
  mkdir -p "$(dirname "$DIR")"
  gh repo clone "$REPO" "$DIR" -- --filter=blob:none
fi

cd "$DIR"
git fetch origin
git checkout main 2>/dev/null || git checkout master 2>/dev/null || true
git pull --ff-only origin "$(git branch --show-current)" || true
git rev-parse HEAD | tee "$OUT/head.txt"
git status --short | tee "$OUT/repo_status_start.txt"

{
  echo "===== smoothie files ====="
  find . -maxdepth 5 -type f | grep -Ei "smoothie|Issue145|freerouting|repro" | sort
  echo
  echo "===== smoothie test references ====="
  grep -RIn --exclude-dir=.git --exclude-dir=node_modules --exclude-dir=dist -- "smoothie\|Issue145\|freerouting" tests lib src . 2>/dev/null | head -500 || true
  echo
  echo "===== likely parser/converter files ====="
  find lib src -maxdepth 5 -type f 2>/dev/null | sort | head -400 || true
} | tee "$OUT/smoothie_surface.txt"
echo

echo "05 snapshot relevant files"
mkdir -p "$OUT/snaps"
for f in \
  tests/assets/repro/smoothieboard-repro.dsn \
  tests/repros/repro13-missing-traces-waterCounter.test.ts \
  tests/dsn-pcb/parse-dsn-json-to-circuit-json.test.ts \
  tests/dsn-pcb/convert-dsn-file-to-circuit-json.test.ts \
  package.json
do
  if [ -f "$f" ]; then
    safe="$(echo "$f" | sed 's#[/ ]#__#g')"
    { echo "===== FILE: $f ====="; sed -n '1,260p' "$f"; } > "$OUT/snaps/$safe.txt"
  fi
done
find "$OUT/snaps" -type f -maxdepth 1 -print | sort
echo

echo "06 tool/install gate"
{
  echo "===== paths ====="
  command -v node || true
  command -v npm || true
  command -v bun || true
  command -v npx || true
  echo
  echo "===== versions ====="
  node --version 2>/dev/null || true
  npm --version 2>/dev/null || true
  bun --version 2>/dev/null || true
  npx --version 2>/dev/null || true
} | tee "$OUT/tool_gate.txt"
echo

echo "07 optional local install and repro"
DO_INSTALL="${DO_INSTALL:-0}"
echo "$DO_INSTALL" | tee "$OUT/do_install.txt"

if [ "$DO_INSTALL" = "1" ]; then
  echo "Installing dependencies with npm install..."
  npm install > "$OUT/npm_install.out" 2> "$OUT/npm_install.err" || true
  cat "$OUT/npm_install.err" | tail -120 || true

  echo "Attempting focused bun repro tests via npx bun..."
  set +e
  npx --yes bun test tests/repros tests/dsn-pcb --timeout 30000 > "$OUT/bun_repro_tests.out" 2> "$OUT/bun_repro_tests.err"
  BUN_RC=$?
  set -e
  echo "$BUN_RC" | tee "$OUT/bun_repro_tests.rc"
  tail -200 "$OUT/bun_repro_tests.out" || true
  tail -200 "$OUT/bun_repro_tests.err" || true
else
  echo "Skipping install. Re-run with DO_INSTALL=1 bash tscircuit_dsn_54_pr_repro_audit_v22.sh after reviewing claim/PR status." | tee "$OUT/install_skipped.txt"
fi
echo

echo "08 classify"
python3 - "$OUT" <<'PY'
from pathlib import Path
import json, re, sys

out = Path(sys.argv[1])

issue = (out / "issue_54_full.txt").read_text(errors="replace") if (out / "issue_54_full.txt").exists() else ""
signals = (out / "issue_signal_lines.txt").read_text(errors="replace") if (out / "issue_signal_lines.txt").exists() else ""
surface = (out / "smoothie_surface.txt").read_text(errors="replace") if (out / "smoothie_surface.txt").exists() else ""
tool = (out / "tool_gate.txt").read_text(errors="replace") if (out / "tool_gate.txt").exists() else ""

timeline_pr = {}
if (out / "timeline_pr_summary.json").exists():
    try:
        timeline_pr = json.loads((out / "timeline_pr_summary.json").read_text())
    except Exception:
        timeline_pr = {}

prs = timeline_pr.get("prs") or []
merged_prs = [p for p in prs if p.get("mergedAt")]
open_prs = [p for p in prs if p.get("state") == "OPEN"]

claim_words = re.findall(r"claim|claimed|assigned|working on|pull request|PR|merged|fixed|submitted", issue, re.I)
claim_risk = bool(claim_words or merged_prs or open_prs)
bounty_visible = bool(re.search(r"/bounty|\$70|bounty", issue, re.I))
smoothie_fixture = "tests/assets/repro/smoothieboard-repro.dsn" in surface
has_node = bool(re.search(r"/node$|^node$", tool, re.M))
has_npm = bool(re.search(r"/npm$|^npm$", tool, re.M))
has_bun = bool(re.search(r"/bun$|^bun$", tool, re.M))

do_install = (out / "do_install.txt").read_text(errors="replace").strip() if (out / "do_install.txt").exists() else "0"
bun_rc = None
if (out / "bun_repro_tests.rc").exists():
    bun_rc = (out / "bun_repro_tests.rc").read_text(errors="replace").strip()

score = 0
reasons = []
if bounty_visible:
    score += 15; reasons.append("bounty visible")
if smoothie_fixture:
    score += 20; reasons.append("Smoothie fixture already in repo")
if has_node and has_npm:
    score += 15; reasons.append("Node/npm available")
if has_bun:
    score += 10; reasons.append("bun available")
if bun_rc is not None:
    score += 20 if bun_rc != "0" else 5
    reasons.append(f"local bun repro rc={bun_rc}")
if merged_prs:
    score -= 35; reasons.append("merged related PR risk")
if open_prs:
    score -= 25; reasons.append("open related PR risk")
if len(claim_words) > 0:
    score -= 20; reasons.append("claim/PR words in issue")

if score >= 50 and not open_prs and not merged_prs:
    verdict = "CLAIM_OR_ASK_AVAILABLE"
elif score >= 30 and do_install != "1":
    verdict = "INSTALL_REPRO_BEFORE_CLAIM"
elif claim_risk:
    verdict = "ASK_AVAILABILITY_ONLY_OR_PARK"
else:
    verdict = "PARK"

decision = {
    "verdict": verdict,
    "score": score,
    "reasons": reasons,
    "issue": "https://github.com/tscircuit/dsn-converter/issues/54",
    "bounty_visible": bounty_visible,
    "claim_risk": claim_risk,
    "claim_words_count": len(claim_words),
    "smoothie_fixture": smoothie_fixture,
    "has_node": has_node,
    "has_npm": has_npm,
    "has_bun": has_bun,
    "do_install": do_install,
    "bun_repro_rc": bun_rc,
    "open_related_prs": open_prs,
    "merged_related_prs": merged_prs,
}
(out / "decision.json").write_text(json.dumps(decision, indent=2) + "\n")

md = []
md.append("# tscircuit/dsn-converter #54 PR/Repro Audit v22")
md.append("")
md.append("## Verdict")
md.append("")
md.append(f"`{verdict}`")
md.append("")
md.append("## Score")
md.append("")
md.append(f"- Score: `{score}`")
md.append(f"- Reasons: {', '.join(reasons)}")
md.append("")
md.append("## Gates")
md.append("")
for k in ["bounty_visible", "claim_risk", "claim_words_count", "smoothie_fixture", "has_node", "has_npm", "has_bun", "do_install", "bun_repro_rc"]:
    md.append(f"- {k}: `{decision[k]}`")
md.append("")
md.append("## Related PRs")
md.append("")
for p in prs[:20]:
    md.append(f"- #{p.get('number')} `{p.get('state')}` merged={bool(p.get('mergedAt'))}: {p.get('title')} - {p.get('url')}")
md.append("")
md.append("## Next")
md.append("")
if verdict == "INSTALL_REPRO_BEFORE_CLAIM":
    md.append("Re-run this script with `DO_INSTALL=1` to establish a local failing/passing signal before claiming.")
elif verdict == "ASK_AVAILABILITY_ONLY_OR_PARK":
    md.append("Do not claim directly. Ask whether the bounty is still available given prior claim/PR signals, or park.")
else:
    md.append("If still available, claim a narrow first slice and proceed with focused repro/fix.")
md.append("")
(out / "AUDIT_REPORT.md").write_text("\n".join(md) + "\n")
print((out / "AUDIT_REPORT.md").read_text())
PY
echo

echo "09 availability comment draft"
cat > "$OUT/availability_comment_draft.md" <<'MD'
Hi, is this bounty still available?

I see the repo already has a Smoothie Board repro fixture, so before making noise or duplicating prior work I want to confirm whether a focused small PR is still useful here. My intended first slice would be to run the existing Smoothie fixture locally, isolate the current failing conversion step, and submit either a regression test plus parser/converter fix or a narrower failing fixture if maintainer guidance is needed.
MD
cat "$OUT/availability_comment_draft.md"
echo

echo "10 commit artifact"
cd "$ROOT"
git add "$OUT" tscircuit_dsn_54_pr_repro_audit_v22.sh
git commit -m "Audit tscircuit dsn converter PR and repro v22" || true
git push origin local-main || true
echo

echo "11 final"
git status --short
df -h /
echo
echo "Artifacts:"
echo "$OUT/AUDIT_REPORT.md"
echo "$OUT/decision.json"
echo "$OUT/timeline_pr_summary.json"
echo "$OUT/pr_search.json"
echo "$OUT/smoothie_surface.txt"
echo "$OUT/tool_gate.txt"
echo "$OUT/availability_comment_draft.md"
