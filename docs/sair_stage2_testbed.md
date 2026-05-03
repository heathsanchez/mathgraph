# SAIR Stage 2 Testbed

The first practical testbed is equational implication over magmas.

This repository is still a general MathGraph kernel. SAIR Stage 2 is represented
as one adapter-backed route:

1. Parse premise and conclusion equations over a binary operation `*`.
2. Evaluate them in a supplied finite magma.
3. Emit `FINITE_COUNTERMODEL` when the premises hold and the conclusion fails.
4. Emit a named obstruction when the supplied finite magma does not refute the
   implication.

Finite-search failure is not proof. A bounded finite magma route can produce an
explicit countermodel, or it can fail to find one. The latter is represented as
an obstruction unless another verified route proves the claim.

## Importing External SAIR Stage 2 Certificate Artifacts

Colab and Drive runs may produce route/certificate result tables such as CSV,
CSV.GZ, or Parquet files. These generated artifacts should stay outside GitHub.
MathGraph can import them from caller-supplied local paths:

```python
from adapters.sair_stage2_adapter import import_traces, load_results_table, summarize_results

records = load_results_table("/external/path/routelean_results_v19_1.parquet")
print(summarize_results(records))
traces = import_traces("/external/path/routelean_results_v19_1.parquet", limit=10)
```

The importer is conservative. Verified-false rows become
`FINITE_COUNTERMODEL`. Explicit verified-true rows become `VERIFIED_PROOF`.
Rows without explicit true/false verification become `NAMED_OBSTRUCTION`.
Missing verification, failed finite search, or failed Lean execution is never
promoted to proof.
