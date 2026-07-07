# strata-org/specimen #45 LawfulScorable Probe v3

## Verdict

`COMPILES__DRAFT_PR_CANDIDATE_BUT_INSTANCES_STILL_NEEDED`

## What this patch does

Adds a proof-carrying `LawfulScorable` class next to the existing executable `Scorable` interface.

It captures the issue-requested invariants without changing runtime behavior:

- `combine` should not improve the left score
- `isBetter` should be transitive
- `empty` should be a left and right identity
- `worst` should not beat a real candidate
- `badness` should be monotone with `isBetter`

## Status

- `Specimen/Scoring.lean` check: `True`
- `lake build`: `True`

## MathGraph classification

- Residual: scorer invariants are implicit.
- Portal: separate executable interface from lawful/proof-carrying interface.
- Certificate: Lean build accepts the interface.
- Remaining obstruction: proving instances may reveal that `worst := 1000` is only bounded-worst, not globally worst.

## Important caveat

The issue asks for `worst` as a valid branch-and-bound initial bound. Existing score instances use finite sentinels such as `1000`, so a strong law like `∀ a, isBetter a worst` may be false for unbounded scores. This v3 patch uses the weaker law `¬ isBetter worst a`, which is safer but may not fully satisfy the intended invariant. A later PR should either prove bounded laws or introduce a true top sentinel.

## Diff

```diff
--- a/Specimen/Scoring.lean
+++ b/Specimen/Scoring.lean
@@ -62,6 +62,40 @@
   /-- Must be worse than any real schedule under `isBetter`. -/
   worst : S
   badness : S → Float
+
+/-- Laws expected from scoring strategies used by branch-and-bound search.
+
+`Scorable` stays executable and lightweight.  `LawfulScorable` packages the
+extra invariants required by proof-carrying uses of scoring strategies. -/
+class LawfulScorable (S : Type) [Scorable S] : Prop where
+  /-- Adding combined work to a score should not strictly improve it. -/
+  not_isBetter_combine_left :
+    ∀ a b : S, ¬ Scorable.isBetter (S := S) (Scorable.combine (S := S) a b) a
+
+  /-- Strict score comparison should be transitive. -/
+  isBetter_trans :
+    ∀ a b c : S,
+      Scorable.isBetter (S := S) a b →
+      Scorable.isBetter (S := S) b c →
+      Scorable.isBetter (S := S) a c
+
+  /-- `empty` is a left identity for `combine`. -/
+  empty_combine :
+    ∀ a : S, Scorable.combine (S := S) (Scorable.empty (S := S)) a = a
+
+  /-- `empty` is a right identity for `combine`. -/
+  combine_empty :
+    ∀ a : S, Scorable.combine (S := S) a (Scorable.empty (S := S)) = a
+
+  /-- The initial branch-and-bound sentinel should not beat a real candidate. -/
+  not_worst_isBetter :
+    ∀ a : S, ¬ Scorable.isBetter (S := S) (Scorable.worst (S := S)) a
+
+  /-- Scores that are better according to `isBetter` should not have worse visual badness. -/
+  badness_mono :
+    ∀ a b : S,
+      Scorable.isBetter (S := S) a b →
+      Scorable.badness (S := S) a ≤ Scorable.badness (S := S) b
 
 ----------------------------------------------
 -- Scorer function types (parameterized by score type)

```

## Lean check tail

```text
rc=0

```

## Build tail

```text
✔ [41/47] Built Specimen.Scoring (1.2s)
✔ [42/47] Built Specimen.PatternCoverage (1.3s)
✔ [43/47] Built Specimen.DeriveSchedules (4.3s)
✔ [44/47] Built Specimen.DeriveConstrainedProducer (12s)
✔ [45/47] Built Specimen.DeriveChecker (3.3s)
✔ [46/47] Built Specimen (800ms)
Build completed successfully (47 jobs).
rc=0

```

