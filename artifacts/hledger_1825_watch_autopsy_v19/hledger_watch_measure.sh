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
