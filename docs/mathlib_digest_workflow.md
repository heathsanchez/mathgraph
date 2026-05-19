# Mathlib Digest Workflow

MathGraph does not ingest Mathlib merely as data. The digest workflow turns a
small explicit target pack into persistent MathGraph memory:

```text
target pack -> Lean autopsy -> root hints -> reason basin -> constructor tests
-> verified constructor or obstruction -> persistent Lawbook -> atlas exports
```

Lean is the verifier boundary. MathGraph records, routes, and compounds. `#check`
confirms imported declaration availability; `#print` references are hints, not
complete proof dependencies. Constructor templates become trusted constructor
evidence only when Lean accepts the generated constructor test file.

Dry run:

```bash
python scripts/run_mathlib_digest_accumulator.py \
  --lawbook /tmp/mathgraph_lawbook_test.sqlite \
  --pack-config examples/mathlib_digest_nat_small/config.json \
  --out-base /tmp/mathgraph_lawbook_runs
```

Live run with an existing local Mathlib checkout:

```bash
python scripts/run_mathlib_digest_accumulator.py \
  --mathlib-root /content/mathlib4 \
  --lawbook /content/drive/MyDrive/MathGraph_Lawbook/lawbook.sqlite \
  --pack-config examples/mathlib_digest_nat_small/config.json \
  --out-base /content/drive/MyDrive/MathGraph_Lawbook/runs \
  --allow-live-lean \
  --verify-constructors
```

Exports:

```bash
python scripts/run_constructor_distiller.py --lawbook /path/to/lawbook.sqlite --out-dir /path/to/exports
python scripts/run_reason_atlas_export.py --lawbook /path/to/lawbook.sqlite --out-dir /path/to/exports
python scripts/run_lawbook_summary.py --lawbook /path/to/lawbook.sqlite --out-dir /path/to/exports
```

Future work remains: full Lean proof-term dependency extraction, robust
declaration-level dependency graphs, real induction/leRecOn constructor
synthesis, API endpoints, model-trained route ranking, and a Lawbook browser UI.
