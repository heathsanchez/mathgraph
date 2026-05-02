# MathGraph Script Backup v0.3

Created: 2026-05-02T23:11:27.148611+00:00

This backup is intentionally script/document focused. It preserves the code, query helpers, Lean files,
roadmaps, reports, and manifests needed to reconstruct the work without copying every heavy generated artifact.

## Counts

- Selected files: 5,000
- Copied files: 5,000
- Failed copies: 0
- Manual bucket files: 1

## Important milestone checklist

```json
[
  {
    "label": "v19.1 routelean results",
    "kind": "heavy_artifact",
    "path": "/content/drive/MyDrive/MathGraphKernel/lean_kernel_v19_1/latest/routelean_results_v19_1.parquet",
    "exists": true,
    "size_mb": 0.792,
    "included_by_default": false
  },
  {
    "label": "v19.1 verified certificates",
    "kind": "heavy_artifact",
    "path": "/content/drive/MyDrive/MathGraphKernel/lean_kernel_v19_1/latest/verified_certificates_v19_1.parquet",
    "exists": true,
    "size_mb": 0.792,
    "included_by_default": false
  },
  {
    "label": "v19.1 query helper",
    "kind": "script",
    "path": "/content/drive/MyDrive/MathGraphKernel/graph/query/mathgraph_routelean_query_v19_1.py",
    "exists": true,
    "size_mb": 0.001,
    "included_by_default": true
  },
  {
    "label": "v19.1 report",
    "kind": "report",
    "path": "/content/drive/MyDrive/MathGraphKernel/lean_kernel_v19_1/latest/latest_routelean_execution_report_v19_1.md",
    "exists": true,
    "size_mb": 0.001,
    "included_by_default": true
  },
  {
    "label": "v19.1 sqlite index",
    "kind": "heavy_artifact",
    "path": "/content/drive/MyDrive/MathGraphKernel/lean_kernel_v19_1/latest/routelean_index_v19_1.sqlite",
    "exists": true,
    "size_mb": 12.105,
    "included_by_default": false
  },
  {
    "label": "v19.0 routelean results",
    "kind": "heavy_artifact",
    "path": "/content/drive/MyDrive/MathGraphKernel/lean_kernel_v19_0/latest/latest_routelean_results_v19_0.parquet",
    "exists": true,
    "size_mb": 0.577,
    "included_by_default": false
  },
  {
    "label": "MathGraph v0.1 store",
    "kind": "heavy_artifact",
    "path": "/content/drive/MyDrive/MathGraphKernel/mathgraph_store_v0_1.sqlite",
    "exists": true,
    "size_mb": 0.609,
    "included_by_default": false
  },
  {
    "label": "MathGraph v0.1 query helper",
    "kind": "script",
    "path": "/content/drive/MyDrive/MathGraphKernel/graph/query/mathgraph_query_v0_1.py",
    "exists": true,
    "size_mb": 0.002,
    "included_by_default": true
  },
  {
    "label": "ETP equations",
    "kind": "core_asset",
    "path": "/content/drive/MyDrive/MathGraphKernel/core/equations.txt",
    "exists": true,
    "size_mb": 0.155,
    "included_by_default": true
  },
  {
    "label": "ETP matrix",
    "kind": "heavy_core_asset",
    "path": "/content/drive/MyDrive/MathGraphKernel/core/etp_matrix_full_best_bool.npy",
    "exists": true,
    "size_mb": 21.013,
    "included_by_default": false
  }
]
```

## Notes

Heavy artifacts such as `.parquet`, `.sqlite`, `.npy`, logs, and package caches are skipped by default.
Set `INCLUDE_HEAVY_ARTIFACTS=True` near the top of the script if you want a larger archival copy.

Most important local files to preserve manually if not found in this zip:

1. v19.1 Lean execution + sanitizer script
2. MathGraph v0.1 lightweight generative kernel script
3. v19.1 query helper
4. v0.1 query helper
5. MathGraph roadmap markdown
6. v19.0 route-specific Lean generation script
7. SAIR Stage 2 constructor/router scripts
8. H-tilt / discovery / invariant-mining scripts
