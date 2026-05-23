# Module Map

This map is a practical orientation aid. It does not delete or demote legacy
modules.

## Integrity Spine

- `certificates.py`: terminal forms and certificate records
- `invariants.py`: trust-boundary invariant reports
- `evidence_manifest.py`: replayable evidence manifest records
- `evidence_replay.py`: replay and artifact hash checks
- `lawbook.py`: Lawbook entries, review, and audit helpers
- `lawbook_acceptance.py`: acceptance contract around manifests and invariants
- `lawbook_store.py`: SQLite-backed stores and benchmark persistence surfaces

## Verification Boundaries

- `verifier_execution.py`: local verifier execution contract
- `proof_system_integration.py`: proof-system artifacts and boundary contracts
- `proof_verification.py`: proof verification records and traces
- `finite_magma_world.py`: deterministic finite magma checker
- `external_certificates.py`: external verifier certificate envelope
- `promotion_gate.py`: boundary gate for terminal candidates

## Claim And Semantic Boundaries

- `kernel.py`: compact claim acceptance kernel
- `verification.py`: certificate verification helpers
- `domain_claims.py`: domain claim IR and adapters
- `semantic_validation.py`: informal/formal validation boundary
- `semantic_intake.py`: advisory natural-language intake

## Routing And Memory

- `reason_atlas.py`: routing memory and verifier-backed outcome metrics
- `reason_atlas_store.py`: persistent advisory Reason Atlas entries
- `reason_atlas_feedback_loop.py`: advisory feedback orchestration
- `reason_atlas_htilt.py`: H-Tilt scoring over Reason Atlas entries
- `route_learner.py`: route learning
- `route_priors.py`: smoothed route priors
- `route_telemetry.py`: route telemetry
- `spectral_htilt.py`: spectral H-Tilt estimates
- `viability_operators.py`: candidate V operators

## SAIR And Finite Countermodel Workflows

- `sair_task_loader.py`: SAIR equation/matrix loading
- `sair_constructor_bank.py`: finite magma constructor bank
- `sair_breakthrough_runner.py`: SAIR breakthrough loop runner
- `sair_motif_hygiene.py`: clean motif hygiene
- `sair_clean_motif_mining.py`: clean motif mining
- `sair_scheduler_evaluation.py`: held-out scheduler evaluation
- `sair_real_compounding_benchmark.py`: real/fallback compounding benchmark

## Compounding And Artifact Packs

- `compounding_lawbook_engine.py`: fallback compounding engine
- `multi_episode_compounding.py`: multi-episode compounding evaluation
- `real_sair_artifact_pack.py`: real/fallback artifact pack runner
- `lawbook_admission.py`: production admission levels
- `lawbook_promotion.py`: run artifact promotion reports

## Canonical Examples And Checks

- `scripts/run_canonical_finite_countermodel_demo.py`
- `scripts/replay_evidence_manifest.py`
- `scripts/run_reason_atlas_demo.py`
- `scripts/run_trust_boundary_check.py`
- `scripts/run_release_check.py`
- `scripts/run_repo_architecture_audit.py`

## Legacy Surface

The repository includes many experiment and smoke-run modules. Keep them unless
a focused cleanup PR proves they are obsolete and preserves tests. The canonical
spine above is the preferred path for new integrations.
