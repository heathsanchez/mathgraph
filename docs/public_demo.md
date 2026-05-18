# Public Demo

```bash
python scripts/run_public_demo.py --ensure-configs
python scripts/run_public_demo.py
python scripts/run_public_demo.py --allow-execution --allow-missing-verifier --accept-verified-entries-in-memory
```

The public demo uses repo-local synthetic fixtures and writes polished artifacts when `--out-dir` is supplied. Demo success is advisory unless explicit verifier/importer/finite-validator/chain-audit evidence is present.
