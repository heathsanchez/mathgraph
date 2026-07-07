#!/usr/bin/env bash
set -euo pipefail

echo "MathGraph hledger #1825 Watch Autopsy v19"
echo "Goal: locate --watch implementation, identify leak surfaces, and produce a minimal repro/fix plan without speculative patching."
echo

ROOT="/Users/heath/Documents/mathgraph-lean-work"
REPO="simonmichael/hledger"
ISSUE="1825"
H_DIR="$ROOT/external/cash_win_legit_recon_v17/simonmichael__hledger_1825"
OUT="$ROOT/artifacts/hledger_1825_watch_autopsy_v19"

mkdir -p "$OUT"
cd "$ROOT"

echo "01 status"
date -u +"%Y-%m-%dT%H:%M:%SZ" | tee "$OUT/status_start.txt"
df -h / | tee "$OUT/df_start.txt"
git status --short | tee "$OUT/mathgraph_status_start.txt" || true
echo

echo "02 issue state after claim"
gh issue view "$ISSUE" -R "$REPO" --comments > "$OUT/issue_1825_after_claim.txt"
grep -nEi "heathsanchez|claim|claimed|bounty|available|watch|cpu|ram|memory|leak|fsnotify|hfsnotify" "$OUT/issue_1825_after_claim.txt" | tee "$OUT/issue_signal_lines.txt" || true
echo

echo "03 ensure hledger repo"
if [ ! -d "$H_DIR/.git" ]; then
  mkdir -p "$(dirname "$H_DIR")"
  gh repo clone "$REPO" "$H_DIR" -- --filter=blob:none
fi

cd "$H_DIR"
git fetch origin
git checkout master 2>/dev/null || git checkout main 2>/dev/null || true
git pull --ff-only origin "$(git branch --show-current)" || true
git rev-parse HEAD | tee "$OUT/hledger_head.txt"
git status --short | tee "$OUT/hledger_status_start.txt"
echo

echo "04 exact watch/fsnotify source map"
{
  echo "===== watch flags/options ====="
  grep -RIn --exclude-dir=.git --exclude-dir=.stack-work --exclude-dir=dist-newstyle -- "watch" hledger hledger-ui hledger-lib 2>/dev/null | head -500 || true
  echo
  echo "===== fsnotify/hfsnotify refs ====="
  grep -RIn --exclude-dir=.git --exclude-dir=.stack-work --exclude-dir=dist-newstyle -- "fsnotify\|hfsnotify\|watchTree\|watchDir\|withManager\|WatchManager\|Event" hledger hledger-ui hledger-lib 2>/dev/null | head -500 || true
  echo
  echo "===== reload/redraw refs ====="
  grep -RIn --exclude-dir=.git --exclude-dir=.stack-work --exclude-dir=dist-newstyle -- "reload\|redraw\|refresh\|invalidate\|vty\|Brick" hledger-ui hledger-lib 2>/dev/null | head -500 || true
  echo
  echo "===== async/thread/channel refs ====="
  grep -RIn --exclude-dir=.git --exclude-dir=.stack-work --exclude-dir=dist-newstyle -- "forkIO\|async\|TChan\|Chan\|MVar\|TVar\|atomically\|threadDelay" hledger-ui hledger-lib 2>/dev/null | head -500 || true
} | tee "$OUT/source_map.txt"
echo

echo "05 list likely files"
python3 - "$OUT/source_map.txt" "$OUT/likely_files.txt" <<'PY'
from pathlib import Path
import re, sys
source = Path(sys.argv[1]).read_text(errors="replace")
files = []
for line in source.splitlines():
    m = re.match(r"([^:]+):(\d+):", line)
    if m:
        f = m.group(1)
        if f not in files:
            files.append(f)
Path(sys.argv[2]).write_text("\n".join(files[:120]) + "\n")
print("\n".join(files[:80]))
PY
echo

echo "06 snapshot likely source files"
mkdir -p "$OUT/source_snaps"
while IFS= read -r f; do
  [ -f "$f" ] || continue
  safe="$(echo "$f" | sed 's#[/ ]#__#g')"
  {
    echo "===== FILE: $f ====="
    sed -n '1,260p' "$f"
  } > "$OUT/source_snaps/$safe.txt"
done < "$OUT/likely_files.txt"

echo "snapshots:"
find "$OUT/source_snaps" -type f | sort | head -40
echo

echo "07 build/test tooling reality"
{
  echo "===== tools ====="
  command -v stack || true
  command -v cabal || true
  command -v ghc || true
  command -v make || true
  command -v hledger-ui || true
  command -v hledger || true
  command -v ps || true
  command -v vm_stat || true
  echo
  echo "===== build files ====="
  find . -maxdepth 3 \( -name "stack.yaml" -o -name "cabal.project" -o -name "*.cabal" -o -name "package.yaml" -o -name "Makefile" -o -name "justfile" \) -type f | sort
  echo
  echo "===== package refs ====="
  grep -RIn --exclude-dir=.git --exclude-dir=.stack-work --exclude-dir=dist-newstyle -- "fsnotify\|brick\|vty\|hledger-ui" package.yaml *.cabal hledger-ui/*.cabal hledger-lib/*.cabal stack.yaml cabal.project 2>/dev/null || true
} | tee "$OUT/tooling_reality.txt"
echo

echo "08 create local measurement harness draft"
cat > "$OUT/hledger_watch_measure.sh" <<'MEASURE'
#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   HLEDGER_UI_BIN=hledger-ui HLEDGER_JOURNAL=/path/to/journal.journal bash hledger_watch_measure.sh
#
# This is a diagnostic harness for hledger#1825.
# It starts hledger-ui --watch against a journal, samples CPU/RSS, and appends results to CSV.
# It does not modify hledger source.

BIN="${HLEDGER_UI_BIN:-hledger-ui}"
JOURNAL="${HLEDGER_JOURNAL:-./watch-repro.journal}"
OUT_CSV="${OUT_CSV:-watch_measure.csv}"
SECONDS_TOTAL="${SECONDS_TOTAL:-600}"
INTERVAL="${INTERVAL:-5}"

if ! command -v "$BIN" >/dev/null 2>&1; then
  echo "Missing hledger-ui binary: $BIN" >&2
  exit 1
fi

if [ ! -f "$JOURNAL" ]; then
  cat > "$JOURNAL" <<'EOF'
2026-01-01 opening balances
    assets:bank      $1000
    equity:opening  $-1000

2026-01-02 coffee
    expenses:food       $5
    assets:bank        $-5
EOF
fi

echo "timestamp,pid,pcpu,rss_kb,command" > "$OUT_CSV"

"$BIN" --watch -f "$JOURNAL" >/tmp/hledger-ui-watch-repro.out 2>/tmp/hledger-ui-watch-repro.err &
PID="$!"

cleanup() {
  kill "$PID" >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM

END=$((SECONDS + SECONDS_TOTAL))
while [ "$SECONDS" -lt "$END" ]; do
  if ! kill -0 "$PID" >/dev/null 2>&1; then
    echo "hledger-ui exited early" >&2
    break
  fi
  ps -p "$PID" -o pid= -o pcpu= -o rss= -o command= | awk -v ts="$(date -u +%Y-%m-%dT%H:%M:%SZ)" '{print ts "," $1 "," $2 "," $3 "," substr($0, index($0,$4))}' >> "$OUT_CSV"
  sleep "$INTERVAL"
done

echo "wrote $OUT_CSV"
MEASURE
chmod +x "$OUT/hledger_watch_measure.sh"
echo

echo "09 analyze and write report"
python3 - "$OUT" <<'PY'
from pathlib import Path
import json
import re
import sys

out = Path(sys.argv[1])
source = (out / "source_map.txt").read_text(errors="replace")
issue = (out / "issue_1825_after_claim.txt").read_text(errors="replace")
tools = (out / "tooling_reality.txt").read_text(errors="replace")
files = (out / "likely_files.txt").read_text(errors="replace").splitlines()

signals = {
    "claim_post_visible": "heathsanchez" in issue.lower(),
    "watch_refs": len(re.findall(r"watch", source, re.I)),
    "fsnotify_refs": len(re.findall(r"fsnotify|hfsnotify|watchTree|watchDir|withManager|WatchManager", source, re.I)),
    "async_refs": len(re.findall(r"forkIO|async|TChan|Chan|MVar|TVar|atomically|threadDelay", source, re.I)),
    "reload_refs": len(re.findall(r"reload|redraw|refresh|invalidate", source, re.I)),
    "stack_available": bool(re.search(r"^/.*/stack$|^stack$", tools, re.M)),
    "cabal_available": bool(re.search(r"^/.*/cabal$|^cabal$", tools, re.M)),
    "ghc_available": bool(re.search(r"^/.*/ghc$|^ghc$", tools, re.M)),
    "hledger_ui_available": bool(re.search(r"^/.*/hledger-ui$|^hledger-ui$", tools, re.M)),
}

decision = {
    "verdict": "REPRO_HARNESS_FIRST",
    "issue": "https://github.com/simonmichael/hledger/issues/1825",
    "claim_comment": "https://github.com/simonmichael/hledger/issues/1825#issuecomment-4901262602",
    "signals": signals,
    "likely_files_top20": files[:20],
    "next_patch_shape": [
        "Do not speculate a source fix before reproducing.",
        "Use hledger_watch_measure.sh against installed or locally built hledger-ui.",
        "If CPU/RSS rises without file events, inspect watch thread/event loop lifecycle.",
        "If CPU/RSS rises only after synthetic file changes, inspect event coalescing/reload/redraw scheduling.",
        "First PR should include either a reproducible diagnostic script/doc or a narrow lifecycle fix with measured before/after.",
    ],
}
(out / "decision.json").write_text(json.dumps(decision, indent=2) + "\n")

md = []
md.append("# hledger #1825 Watch Autopsy v19")
md.append("")
md.append("## Verdict")
md.append("")
md.append("`REPRO_HARNESS_FIRST`")
md.append("")
md.append("## Claim")
md.append("")
md.append("- Claim comment: https://github.com/simonmichael/hledger/issues/1825#issuecomment-4901262602")
md.append("")
md.append("## Signals")
md.append("")
for k, v in signals.items():
    md.append(f"- {k}: `{v}`")
md.append("")
md.append("## Likely files")
md.append("")
for f in files[:30]:
    md.append(f"- `{f}`")
md.append("")
md.append("## Next move")
md.append("")
md.append("Do not patch blindly. First create a measurable reproduction. The local machine currently has only `make` visible from the Haskell toolchain scan, so either use an installed `hledger-ui` binary if present, or defer local build until stack/cabal/ghc are available.")
md.append("")
md.append("Diagnostic harness written:")
md.append("")
md.append(f"- `{out / 'hledger_watch_measure.sh'}`")
md.append("")
md.append("## Patch target if reproduction confirms leak")
md.append("")
md.append("Focus on the watch manager/event loop/reload scheduling path, not unrelated UI code.")
md.append("")
(out / "AUTOPSY_REPORT.md").write_text("\n".join(md) + "\n")
print((out / "AUTOPSY_REPORT.md").read_text())
PY
echo

echo "10 optional issue update draft"
cat > "$OUT/issue_update_draft.md" <<'MD'
Quick update: I’ve started by mapping the `--watch` implementation path and preparing a small diagnostic harness to measure idle CPU/RSS over time. I’ll avoid submitting a speculative fix until I can show a reproducible before/after or a clearly isolated event-loop/watch-lifecycle cause.
MD
cat "$OUT/issue_update_draft.md"
echo

echo "11 commit artifact"
cd "$ROOT"
git add "$OUT" hledger_1825_watch_autopsy_v19.sh
git commit -m "Autopsy hledger watch bounty v19" || true
git push origin local-main || true
echo

echo "12 final"
git status --short
df -h /
echo
echo "Artifacts:"
echo "$OUT/AUTOPSY_REPORT.md"
echo "$OUT/decision.json"
echo "$OUT/source_map.txt"
echo "$OUT/likely_files.txt"
echo "$OUT/tooling_reality.txt"
echo "$OUT/hledger_watch_measure.sh"
echo "$OUT/issue_update_draft.md"
