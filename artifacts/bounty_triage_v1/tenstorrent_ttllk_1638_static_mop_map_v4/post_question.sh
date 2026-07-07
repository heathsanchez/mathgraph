#!/usr/bin/env bash
set -u
ROOT="/Users/heath/Documents/mathgraph-lean-work"
OUT="$ROOT/artifacts/bounty_triage_v1/tenstorrent_ttllk_1638_static_mop_map_v4"
COMMENT="$OUT/maintainer_question.md"

if [ "${POST:-0}" = "1" ]; then
  gh issue comment "https://github.com/tenstorrent/tt-llk/issues/1638" --body-file "$COMMENT"
else
  echo "DRY RUN ONLY. To post:"
  echo "POST=1 bash $OUT/post_question.sh"
  echo
  cat "$COMMENT"
fi
