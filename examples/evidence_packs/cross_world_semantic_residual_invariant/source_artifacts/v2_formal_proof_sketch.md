# CrossWorld v2 — Formal Proof Sketch

## Candidate invariant

Let a world W have a finite semantic universe U of test models, assignments, graphs, strings, tables, or states.

For a source statement A and target statement B, define:

- S(A) = {u in U : u satisfies A}
- S(B) = {u in U : u satisfies B}
- R(A,B) = S(A) \ S(B)

The semantic residual is the source-model region that violates the target.

## Exact finite-world fact

For any finite universe U with exact satisfaction relation:

A implies B over U iff R(A,B) is empty.
A fails to imply B over U iff R(A,B) is nonempty.

## Why this is stronger than closure-gap

Syntactic closure-gap asks whether B appears to demand more than A gives.
Semantic residual rank asks whether, after closing A over the actual model semantics, there is still a witness satisfying A and violating B.

## Trust boundary

For ETP the finite magma bank is only a sample. A found witness can be directly validated as a finite countermodel; absence of a witness is not proof of TRUE.

## Current run summary

```json
{
  "all_features_csv": "/content/crossworld_semantic_residual_rank_v2/crossworld_v2_all_claim_features.csv",
  "best_abstract_root_signature": "residual_escape|gap_extreme|rank_very_high|source_large|absorption_low",
  "best_root_score": 49.32726794109356,
  "best_root_world_count": 2,
  "breakthrough_shaped": false,
  "combined_claim_rows": 16156,
  "combined_false_rate": 0.7314929437979698,
  "combined_false_rows": 11818,
  "combined_true_rows": 4338,
  "compression_summary_csv": "/content/crossworld_semantic_residual_rank_v2/v2_residual_compression_summary.csv",
  "etp_semantic_root_auc_false": 0.97914248,
  "feature_importance_csv": "/content/crossworld_semantic_residual_rank_v2/v2_feature_importance.csv",
  "lawbook_update_csv": "/content/crossworld_semantic_residual_rank_v2/v2_lawbook_update.csv",
  "leave_one_world_out_mean_auc_false": 0.9837976420735745,
  "out_dir": "/content/crossworld_semantic_residual_rank_v2",
  "proof_ledger_csv": "/content/crossworld_semantic_residual_rank_v2/v2_proof_ledger.csv",
  "proof_ledger_summary_csv": "/content/crossworld_semantic_residual_rank_v2/v2_proof_ledger_summary.csv",
  "proof_status_summary": "{\"explained_false\": 11745, \"explained_true\": 4338, \"false_underexplained\": 73}",
  "random_seed": 1729,
  "residual_rank_all_world_auc_false": 0.9969114909460145,
  "root_level_candidate": false,
  "root_nodes_csv": "/content/crossworld_semantic_residual_rank_v2/v2_root_node_candidates.csv",
  "run_name": "crossworld_semantic_residual_rank_v2",
  "runtime_min": 13.338376192251841,
  "runtime_sec": 800.3025715351105,
  "semantic_root_all_world_auc_false": 0.9933195438173603,
  "simple_eval_csv": "/content/crossworld_semantic_residual_rank_v2/v2_simple_score_eval.csv",
  "top_shared_feature": "near_force_score",
  "top_shared_feature_importance": 1.4279646993093744,
  "transfer_eval_csv": "/content/crossworld_semantic_residual_rank_v2/v2_transfer_eval.csv",
  "world_count": 4,
  "world_summary_csv": "/content/crossworld_semantic_residual_rank_v2/v2_world_summary.csv",
  "worlds": "BOOLEAN,ETP,GRAPH,REWRITE"
}
```