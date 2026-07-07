# qojulia #407 Patch Gate v7

## Verdict

`PATCHABLE_AFTER_READING_EXACT_BENCHMARK_REQUEST`

## Decision JSON

```json
{
  "verdict": "PATCHABLE_AFTER_READING_EXACT_BENCHMARK_REQUEST",
  "has_bounty": true,
  "has_benchmark_surface": true,
  "has_ci": true,
  "julia_installed": false,
  "assigned": false,
  "mentions_claimed_or_pr": false,
  "url": "https://github.com/qojulia/QuantumOptics.jl/issues/407",
  "title": "Update the benchmark suite and bring it into the CI runner [$400]"
}
```

## What to do next

Proceed to v8 focused patch design, but do not open PR until the exact benchmark expectation is extracted from `ISSUE_PACKET.md`.

Likely patch shape:

1. Add or update benchmark project/files.
2. Add benchmark CI job that is lightweight enough for PRs.
3. Add docs explaining local benchmark command.
4. Run formatting/tests if Julia is available; otherwise create a maintainer question asking for expected command/output.

## Suggested maintainer question

> I’m looking at the $400 benchmark-suite bounty. Before patching, can you confirm the expected local command and CI behavior? For example, should this add a lightweight benchmark smoke job to GitHub Actions, a full PkgBenchmark suite, or both? I can keep the first PR narrow: benchmark project + reproducible command + CI smoke gate.

## Files to read

- `ISSUE_PACKET.md`
- `inventory.txt`
- `grep.txt`
- `julia_probe.txt`
