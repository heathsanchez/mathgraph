# Production Lawbook Admission v0

The durable Lawbook is verifier-grade memory, not a dump of run logs.  A run may
produce route traces, motifs, decode candidates, fallback smoke artifacts,
finite-countermodel candidates, proof templates, and obstruction hypotheses.
Only artifacts with adequate provenance, replay/audit metadata, and verifier
boundary evidence may become durable Lawbook entries.

## Levels

- `rejected`
- `advisory_only`
- `candidate`
- `bounded_verified`
- `finite_verified`
- `lean_verified`
- `durable_lawbook`

## Boundary

The admission gate preserves MathGraph's authority boundary:

- no TRUE from finite-search failure
- no durable promotion from fallback smoke alone
- no durable promotion from decode success alone
- no durable promotion without provenance
- no durable promotion without replay/audit metadata
- no durable promotion of heuristic motifs unless they are linked to verified
  artifacts or named obstructions

PromotionGate decides whether a verifier artifact may cross the verifier
boundary.  Lawbook admission decides whether that artifact is clean enough to
become durable memory.

## Durable Cases

Finite countermodels may become durable only when the artifact includes:

- verifier passed
- source equation satisfied globally
- target equation violated
- concrete witness
- carrier size
- replayability
- provenance
- non-fallback source

Lean proofs may become durable only when the artifact includes Lean verification,
a proof artifact, replayability, provenance, and a non-fallback source.

Named obstructions may become durable only with a name, failure trace, scope,
supporting failed route or verifier-backed negative result, and replay/audit or
explicit bounded scope.

## Reports

```bash
python scripts/run_lawbook_promotion.py \
  --run-dir /path/to/run \
  --lawbook-path /path/to/lawbook.sqlite \
  --output-dir /path/to/promotion_report \
  --strict
```

The promotion workflow writes:

- `lawbook_admission_decisions.csv`
- `lawbook_admission_summary.json`
- `lawbook_promoted_artifacts.jsonl`
- `lawbook_rejected_artifacts.jsonl`
- `lawbook_advisory_artifacts.jsonl`
- `lawbook_promotion_report.md`

The summary reports promoted durable artifacts, advisory artifacts, rejected
artifacts, fallback blocks, boundary blocks, missing provenance blocks, and
failed-search TRUE blocks.

## Relation To Compounding

The Compounding Lawbook Engine and Real SAIR Benchmark can store advisory
experience and verifier-backed terminal candidates.  Production Lawbook
Admission is the fixation step: memory compounds only if memory is clean.

