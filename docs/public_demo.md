# Public Demo

```bash
python scripts/run_public_demo.py --ensure-configs
python scripts/run_public_demo.py --out-dir demo_out
python scripts/run_public_demo.py --allow-execution --allow-missing-verifier --accept-verified-entries-in-memory --out-dir demo_out
```

The public demo uses repo-local synthetic fixtures, prints a concise summary, and
writes polished artifacts when `--out-dir` is supplied. Demo success is advisory
unless explicit verifier/importer/finite-validator/chain-audit evidence is present.
