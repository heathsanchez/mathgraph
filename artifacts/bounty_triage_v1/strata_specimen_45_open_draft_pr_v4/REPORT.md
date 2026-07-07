# strata-org/specimen #45 Draft PR v4

## Verdict

`PR_NOT_CONFIRMED`

## PR

No PR URL confirmed.

## Local verifier

- `Specimen/Scoring.lean`: `True`
- `lake build`: `True`

## Meaning

This converts the local build-accepted LawfulScorable patch into a visible external-verifier trace.

The PR is intentionally draft because it defines the proof-carrying law interface but does not yet prove the concrete score instances.

## Lawbook entry

- Residual: scorer invariants were implicit in executable `Scorable`.
- Portal: add separate proof-carrying `LawfulScorable` interface.
- Certificate: local Lean checker and full lake build accept the interface.
- Remaining obstruction: finite `worst := 1000` sentinels may not support a strong global worst law.

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

## Verify log

```text
lean-toolchain:
leanprover/lean4:v4.30.0-rc1
lake env lean Specimen/Scoring.lean
scoring_rc=0

lake build
Build completed successfully (47 jobs).
build_rc=0

```

