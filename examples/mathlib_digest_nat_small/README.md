# Nat Small Mathlib Digest Pack

This is a tiny focused Mathlib digest configuration for the persistent digest
Lawbook workflow. It targets five Nat-focused reason basins and fourteen
explicit declarations from `Mathlib.Data.Nat.Basic`.

Dry run, no Lean required:

```bash
python scripts/run_mathlib_digest_accumulator.py \
  --lawbook /tmp/mathgraph_lawbook_test.sqlite \
  --pack-config examples/mathlib_digest_nat_small/config.json \
  --out-base /tmp/mathgraph_lawbook_runs
```

Live local Mathlib run, only when the project already exists:

```bash
python scripts/run_mathlib_digest_accumulator.py \
  --mathlib-root /content/mathlib4 \
  --lawbook /content/drive/MyDrive/MathGraph_Lawbook/lawbook.sqlite \
  --pack-config examples/mathlib_digest_nat_small/config.json \
  --out-base /content/drive/MyDrive/MathGraph_Lawbook/runs \
  --allow-live-lean \
  --verify-constructors
```

Discovery output, `#print` references, generated constructor files, failed
constructor tests, stdout, and return code remain advisory unless Lean accepts
the generated check/constructor file.
