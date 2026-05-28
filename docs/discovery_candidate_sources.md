# DiscoveryScheduler v1: Evidence-Derived Candidate Sources

Discovery Candidate Sources turns existing MathGraph evidence into scheduler-ready continuation candidates. It is a source adapter for the DiscoveryScheduler / Taste Policy Ledger, not a new theorem prover or discovery engine.

## Purpose

The module reads canonical evidence packs and optional Lean digest outputs, then emits advisory candidates that descend into concrete test actions such as finite countermodel attempts, projection tests, replay validation, obstruction naming, Lean digest repair, trust audits, or Reason Atlas route tests.

Every generated candidate is `advisory_only=true` and `can_promote_truth=false`.

## Evidence Sources

Canonical evidence packs are read from `examples/evidence_packs` by default:

- `sair_stage2_breakthrough_20260526`
- `recursive_residual_transfer_v1_20260523`
- `cross_world_semantic_residual_invariant`
- `residual_obstruction_atlas_v8_4`
- `root_node_persistent_filtration_v16_3`
- `collatz_primitive_divisor_v12_2`

Optional Lean sources may be supplied:

- Lean Project Digest outputs
- Lean Digest Lawbook Ingestion outputs
- Lean Lawbook Attention outputs

Missing or malformed source files are recorded as rejected/audit rows rather than silently ignored.

## Candidate Types

Examples include:

- `sair_countermodel_frontier_candidate`
- `recursive_transfer_replay_candidate`
- `crossworld_projection_test_candidate`
- `residual_obstruction_split_candidate`
- `root_node_projection_candidate`
- `collatz_obstruction_naming_candidate`
- `lean_sorry_repair_candidate`
- `lean_axiom_boundary_candidate`
- `lean_unsafe_audit_candidate`
- `lean_import_dependency_route_candidate`
- `lean_theorem_cluster_route_candidate`

Each candidate carries source provenance, a mode hint, expected value fields, risk fields, trust status, and a descension target.

## Trust Boundary

The source adapter is advisory only. It cannot promote TRUE/FALSE, cannot produce `VERIFIED_PROOF`, cannot turn failed finite search into TRUE, and cannot turn route scores into certificates.

CrossWorld candidates remain empirical invariant candidates, not formal theorems. Collatz v12.2 candidates preserve `not_a_proof` semantics and only become obstruction/proof-template obligations. Textual Lean candidates cannot become `VERIFIED_PROOF` without a real Lean verification boundary.

Rejected candidates are retained in audit output but excluded from attention allocation.

## CLI

```bash
python scripts/run_discovery_scheduler_from_evidence.py \
  --evidence-root examples/evidence_packs \
  --out-dir /tmp/mathgraph_discovery_from_evidence
```

With optional Lean-derived memory:

```bash
python scripts/run_discovery_scheduler_from_evidence.py \
  --evidence-root examples/evidence_packs \
  --lean-digest-dir /tmp/mathgraph_lean_project_digest_demo \
  --lean-lawbook-dir /tmp/mathgraph_lean_digest_lawbook_ingestion_demo \
  --lean-attention-dir /tmp/mathgraph_lean_lawbook_attention_demo \
  --mode frontier \
  --top-k 10 \
  --beta 1.5 \
  --out-dir /tmp/mathgraph_discovery_from_evidence_full
```

## Outputs

- `evidence_candidate_inventory.csv`
- `valid_candidates.csv`
- `rejected_candidates.csv`
- `taste_policy_ledger.csv`
- `attention_allocation.csv`
- `discovery_from_evidence_summary.json`
- `discovery_from_evidence_report.md`

## What This Proves

This proves the repository can derive scheduler candidates from real repo-native evidence sources while preserving descension targets and trust-boundary metadata.

## What This Does Not Prove

It does not prove new mathematics, run H-tilt, synthesize proofs, certify claims, or promote any advisory evidence to terminal truth.
