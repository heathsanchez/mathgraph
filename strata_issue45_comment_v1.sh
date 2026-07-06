#!/usr/bin/env bash
set -u

ROOT="$PWD"
OUT="$ROOT/artifacts/bounty_triage_v1/strata_specimen_issue45_comment_v1"
mkdir -p "$OUT"

COMMENT="$OUT/comment.md"

cat > "$COMMENT" <<'MD'
I started implementing `LawfulScorable` for this and found two design constraints before opening a PR.

A class-only interface compiles cleanly, but some natural global laws appear false over the current raw score types.

First, `worst` is currently a finite sentinel such as `{ checks := 1000 }`, while the raw score types admit larger scores. For example, Lean confirms that for `DefaultScore`, `WorstLeafScore`, and `UniformDensityScore`, a score with `1001` can be worse than the current sentinel, so:

    Scorable.isBetter Scorable.worst largerScore = true

That means a global law like:

    ∀ a, ¬ Scorable.isBetter Scorable.worst a

does not hold over all inhabitants of the score type.

Second, `DensityScore.combine` can strictly improve the left score. `combine` uses:

    forChecker := a.forChecker || b.forChecker

but the ordering reverses density interpretation when `forChecker = true`. I found a small Lean-checked example where:

    Scorable.isBetter (Scorable.combine a b) a = true

So a global monotonicity law like:

    ∀ a b, ¬ Scorable.isBetter (Scorable.combine a b) a

also does not hold for the raw type as currently defined.

The probe compiles with:

    lake env lean Specimen/LawfulScorableObstructionProbe.lean

Question before I continue: should `LawfulScorable` quantify over a validity predicate / scheduler-produced scores, should `worst` become a true top element, or should the intended laws be weaker than the invariants listed above?
MD

echo
echo "Draft comment written to:"
echo "$COMMENT"
echo
cat "$COMMENT"

if [ "${POST:-0}" = "1" ]; then
  echo
  echo "Posting comment to strata-org/specimen#45"
  gh issue comment "https://github.com/strata-org/specimen/issues/45" --body-file "$COMMENT"
else
  echo
  echo "DRY RUN ONLY. To post:"
  echo "POST=1 bash strata_issue45_comment_v1.sh"
fi

git add "$OUT" strata_issue45_comment_v1.sh
git commit -m "Add strata specimen issue45 maintainer comment draft" || true
git push origin local-main || true
