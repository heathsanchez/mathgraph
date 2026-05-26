# Proposal-Specific Finite Constructor Synthesis v1

Active Residual Discovery names residual constructor pressure. Proposal-specific
synthesis turns that pressure into concrete finite magma tables.

## Distinctions

- A proposal is an advisory family-level route suggestion.
- A synthesized constructor is a concrete finite table generated from a
  proposal.
- A finite-checked recovery is a synthesized table satisfying the source
  equation and violating the target equation.
- A terminal FALSE certificate still requires checker-backed countermodel
  evidence and replayable provenance.

Synthesis metadata is advisory. Failed synthesis is residual evidence, not TRUE.

## Loop

```text
residual -> obstruction pressure -> proposal -> finite constructor
-> finite checker -> exact attribution
```

Residual-conditioned synthesis is the next layer. It does not start from a
family label alone; it uses the residual pair to choose a target witness, force
partial table constraints, complete candidate tables, and then finite-check the
result. See [residual_conditioned_synthesis.md](residual_conditioned_synthesis.md).

## Fallback

```bash
python scripts/run_proposal_constructor_synthesis.py \
  --out-dir /tmp/mathgraph_proposal_synthesis_demo \
  --fallback-demo \
  --seed 1729
```

## Active Discovery With Synthesis

```bash
python scripts/run_active_residual_discovery_benchmark.py \
  --out-dir /tmp/mathgraph_active_discovery_synthesis_demo \
  --fallback-demo \
  --synthesize-constructors \
  --seed 1729
```

## Real ETP

```bash
python scripts/run_active_residual_discovery_benchmark.py \
  --equations /content/equations.txt \
  --matrix /content/etp_matrix_full_best_bool.npy \
  --input-dir /content/drive/MyDrive/SAIR_MathGraph/<previous_heldout_run>/baseline_large \
  --out-dir /content/drive/MyDrive/SAIR_MathGraph/active_residual_discovery_synthesis_v1 \
  --min-support 3 \
  --max-proposals-per-basin 3 \
  --max-pairs-per-proposal 100 \
  --synthesize-constructors \
  --max-tables-per-proposal 32 \
  --max-pairs-per-constructor 100 \
  --max-n 4 \
  --seed 20260524
```
