# Release Checklist

```bash
python scripts/run_release_check.py --quick
python scripts/run_release_check.py --include-public-demo --allow-live-verifier --allow-missing-verifier
```

The release check covers imports, public terms, key CLI availability, docs/examples presence, and roadmap alignment. Passing it is a release signal, not proof.
