# Artifact Conventions

Public demo artifacts use the canonical layout:

```text
demo_out/
  public_demo_report.json
  public_demo_report.md
  proof_library_demo_report.json
  proof_library_demo_report.md
  dependency_graph.json
  release_checks.jsonl
  api_response.json
  logs/
  raw/
```

Release-check artifacts use:

```text
release_out/
  release_check_report.json
  release_check_report.md
  release_checks.jsonl
  command_summary.json
  artifacts_manifest.json
```

Generated artifacts are useful records. They are advisory unless they carry
already-created explicit verifier, trusted-importer, finite-validator, or
chain-audit evidence.
