# Storage Policy

The repository stores code, schema, docs, tests, and small fixtures.

Do not commit growing Mathlib digest artifacts:

- Lawbook SQLite files
- generated run directories
- generated Lean files
- stdout/stderr captures
- large CSV/JSON exports
- archives or cache/build outputs

Recommended Colab layout:

```text
/content/drive/MyDrive/MathGraph_Lawbook/lawbook.sqlite
/content/drive/MyDrive/MathGraph_Lawbook/runs/
/content/drive/MyDrive/MathGraph_Lawbook/exports/
```

The small Nat example pack in `examples/mathlib_digest_nat_small/` is committed
as a fixture. Generated Lawbook state belongs outside git.
