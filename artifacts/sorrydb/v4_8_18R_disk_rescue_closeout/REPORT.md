# MathGraph SorryDB v4.8.18R — Disk Rescue Closeout

## Incident

A fresh FormalBook clone/cache cycle exhausted disk during mathlib cache unpack.

Observed errors:

    No space left on device (os error 28)

## Cause

Repeated temporary FormalBook clones and mathlib cache unpacking consumed local disk.

Measured before rescue:

- free disk: ~2.2Gi
- `/tmp/formalbook_ch03_arith_v4_8_18`: ~7.0Gi
- `/tmp/formalbook_ch03_arith_v4_8_18b`: ~4.0Gi
- `~/.cache/mathlib`: partial cache

## Rescue

Removed temporary clones, partial mathlib cache, and incomplete v4.8.18 artifacts.

Measured after rescue:

- free disk: ~29Gi
- `~/.cache/mathlib`: empty
- `/tmp/formalbook_*`: removed
- `artifacts/sorrydb`: ~26Mi

## New disk law

No more fresh Lean project clone/cache loops while free disk is below 25Gi.

A proof-repair run must use disk-safe mode:

1. reuse one persistent clone when possible;
2. do not run `lake exe cache get` unless `df -h /` shows at least 25Gi free;
3. store only build tails and summaries, not full huge logs;
4. clean `/tmp` immediately after each run;
5. certification still requires:
   - build success;
   - no new `sorry` or `admit`;
   - sorry/admit count decreases.

## Status

v4.8.18 exact-needle run was incomplete and removed.

The next attempt should be a disk-safe Chapter03 regex probe using one persistent clone and capped logs.
