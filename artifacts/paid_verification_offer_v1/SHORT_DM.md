Hey — I’m doing fixed-scope proof-repair / verification sprints for Lean and formal-methods repos.

Recent public traces include CI-green FormalBook/equational-theories proof PRs, generated-spec proof repairs, and a draft Strata PR adding a proof-carrying `LawfulScorable` interface with local `lake build` passing.

The workflow is simple: give me one repo, one issue, and one verifier command. I return a patch/PR if repairable, or a short obstruction report if not.

Best fit is Lean 4 proof gaps, `sorry` removal, generated spec obligations, or small correctness invariants.

Diagnostic sprint: $500. Proof-repair sprint: $1.5k.
