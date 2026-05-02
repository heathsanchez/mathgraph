# Colab Archive Manifest

Source zip: `/Users/heath/Downloads/mathgraph_script_backup_v0_3_1777762545_44d35272e7.zip`

Only source-like reference files were extracted. Generated Lean certificates, parquet/sqlite/numpy/csv/archive outputs, run folders, ledgers, and build products were intentionally skipped.

| Original filename/path inside zip | New repo path | Description | Status |
| --- | --- | --- | --- |
| `README_BACKUP_SUMMARY.md`<br>`README_BACKUP_SUMMARY.md` | `docs/archive/mathgraph_script_backup_v0_3_summary.md` | Backup summary with milestone checklist and notes about heavy artifacts intentionally skipped. | active |
| `files/README.md`<br>`/content/drive/MyDrive/MathGraphKernel/README.md` | `docs/archive/colab_mathgraph_kernel_readme.md` | Colab-era MathGraphKernel README describing the Drive workspace. | reference-only |
| `manual_scripts_bucket/README_manual_scripts_bucket.md`<br>`manual_scripts_bucket/README_manual_scripts_bucket.md` | `docs/archive/manual_scripts_bucket_readme.md` | Notes for manually preserving scripts missing from the automated backup. | reference-only |
| `files/manifest.json`<br>`/content/drive/MyDrive/MathGraphKernel/manifest.json` | `scripts/colab_archive/drive_manifest_v0_3.json` | Drive workspace manifest from the Colab-era MathGraph backup. | reference-only |
| `files/kernel_state.json`<br>`/content/drive/MyDrive/MathGraphKernel/kernel_state.json` | `scripts/colab_archive/kernel_state_v0_1.json` | Serialized MathGraph v0.1 kernel state and counters from the prototype. | reference-only |
| `files/latest_run_manifest_v0_1.json`<br>`/content/drive/MyDrive/MathGraphKernel/latest_run_manifest_v0_1.json` | `scripts/colab_archive/latest_run_manifest_v0_1.json` | Latest v0.1 run manifest from the Colab prototype. | reference-only |
| `files/core/core_hashes.json`<br>`/content/drive/MyDrive/MathGraphKernel/core/core_hashes.json` | `scripts/colab_archive/core_hashes.json` | Hashes for core input assets preserved in Drive. | reference-only |
| `files/core/equations.txt`<br>`/content/drive/MyDrive/MathGraphKernel/core/equations.txt` | `scripts/colab_archive/equations_sample_core.txt` | Core ETP/SAIR equation list from the prototype; kept as a text reference, not a generated matrix. | reference-only |

## Skipped Categories

- `copied_files_manifest.csv`: generated backup listing; summarized here instead.
- `backup_manifest.json`: large generated backup listing; selected records were distilled into this manifest.
- `files/artifacts/lean/**`: generated Lean certificate/countermodel artifacts, not source scripts.
- `.parquet`, `.sqlite`, `.npy`, `.npz`, `.csv`, `.gz`, `.zip`, `.lake`, build outputs, run folders, ledgers, and caches.
