# MathGraph SorryDB v4.8.30 - Baseline Verifier Triage for Remaining Ready Candidates

## Purpose

Before proof probes, check which remaining ready candidates have a working local verifier.

No proof patches were attempted.

## Exclusions

- Verified-zkEVM/ArkLib: parked_baseline_timeout_v4_8_28
- ATOMSLab/LFSE2024: parked_project_environment_obstruction_v4_8_29

## Counts

- target files tested: 6
- baseline ready: 4
- baseline obstructed/skipped: 2

## Baseline-ready targets

### 1. Beneficial-AI-Foundation/vericoding-benchmark specs/LA0521_specs.lean
- status: baseline_ready
- score: 97
- command: `lean specs/LA0521_specs.lean`
- rc: 0
- candidate line: 37
- current: `have h_valid : ValidQuery k n a b := by sorry`

### 2. Beneficial-AI-Foundation/vericoding-benchmark specs/LT0032_specs.lean
- status: baseline_ready
- score: 87
- command: `lean specs/LT0032_specs.lean`
- rc: 0
- candidate line: 26
- current: `have hi : i < rows := by sorry`

### 3. Beneficial-AI-Foundation/vericoding-benchmark specs/LT0479_specs.lean
- status: baseline_ready
- score: 75
- command: `lean specs/LT0479_specs.lean`
- rc: 0
- candidate line: 45
- current: `have h_idx : idx < (xdeg + 1) * (ydeg + 1) := by sorry`

### 4. Beneficial-AI-Foundation/vericoding-benchmark specs/LT0480_specs.lean
- status: baseline_ready
- score: 75
- command: `lean specs/LT0480_specs.lean`
- rc: 0
- candidate line: 46
- current: `have h_idx : idx < (xdeg + 1) * (ydeg + 1) * (zdeg + 1) := by sorry`

## Obstructed/skipped targets

### O1. Brkhu/lean P6011/not_used/P6011_old.lean
- status: baseline_obstructed
- score: 85
- command: `lean P6011/not_used/P6011_old.lean`
- rc: 1
- tail file: artifacts/sorrydb/v4_8_30_baseline_verifier_triage_remaining_ready/Brkhu__lean__P6011__not_used__P6011_old.lean__lean_P6011_not_used_P6011_old.lean.tail

Tail excerpt:

    P6011/not_used/P6011_old.lean:1:0: error: unknown module prefix 'Mathlib'
    
    No directory 'Mathlib' or file 'Mathlib.olean' in the search path entries:
    /Users/heath/.elan/toolchains/leanprover--lean4---v4.28.0/lib/lean

### O2. Brkhu/lean P6011/not_used/P6011_old_check.lean
- status: baseline_obstructed
- score: 75
- command: `lean P6011/not_used/P6011_old_check.lean`
- rc: 1
- tail file: artifacts/sorrydb/v4_8_30_baseline_verifier_triage_remaining_ready/Brkhu__lean__P6011__not_used__P6011_old_check.lean__lean_P6011_not_used_P6011_old_check.lean.tail

Tail excerpt:

    P6011/not_used/P6011_old_check.lean:1:0: error: unknown module prefix 'Mathlib'
    
    No directory 'Mathlib' or file 'Mathlib.olean' in the search path entries:
    /Users/heath/.elan/toolchains/leanprover--lean4---v4.28.0/lib/lean
