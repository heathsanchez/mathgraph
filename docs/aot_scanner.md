# AOT Scanner

`scripts/scan_aot_theory.py` scans a local AOT-style repository for `.thy` and
`.ML` declarations such as `theory`, `AOT_theorem`, `AOT_lemma`, `AOT_axiom`,
`AOT_define`, `AOT_world`, and lightweight proof-method markers.

The scanner does not run Isabelle. It does not verify AOT theorems. It imports
advisory metadata into the LawbookStore theory registry so future importers can
connect host proof artifacts to object-theory claims deliberately.

Example:

```bash
python scripts/scan_aot_theory.py \
  --aot-dir /external/path/AOT \
  --db /tmp/mathgraph_aot_scan.sqlite
```

Every scanned declaration uses advisory trust/provenance until a verifier-backed
artifact is imported.
