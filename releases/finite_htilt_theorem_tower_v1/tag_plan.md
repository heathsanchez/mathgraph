# Tag Plan

Suggested tag:

```text
finite-htilt-theorem-tower-v1
```

Alternative:

```text
v0.1.0-finite-htilt-tower
```

## Preconditions

- Full pytest passes.
- Main Lean files replay.
- The external PF file replays in the exact-pin environment.
- The axiom audit records no `sorryAx`.
- The release manifest has `ready_for_tag: true`.
- Git status and the staged file allowlist are reviewed.

## Commands

```bash
git status --short
git add <explicit release allowlist>
git commit -m "Package finite H-Tilt verified theorem tower v1"
git tag -a finite-htilt-theorem-tower-v1 \
  -m "Finite H-Tilt Survivor Law verified theorem tower v1"
git push origin HEAD
git push origin finite-htilt-theorem-tower-v1
```

## Do not tag if

- any Lean proof fails;
- pytest fails;
- the axiom audit shows `sorryAx`;
- the release bundle claims a killed-generator bridge or convergence result.
