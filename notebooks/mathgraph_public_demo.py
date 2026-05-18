"""Lightweight notebook-equivalent public demo runner.

Demo success is not proof. Only explicit verifier/importer/finite-validator/
chain-audit evidence promotes truth.
"""
from pathlib import Path
import shutil,subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"tmp_public_demo_outputs"
print("MathGraph public demo")
print("Demo success is not proof; only explicit verifier/importer/finite-validator/chain-audit evidence promotes truth.")
argv=[sys.executable,"scripts/run_public_demo.py","--out-dir",str(OUT)]
if shutil.which("lean"):
 argv+=["--allow-execution","--allow-missing-verifier","--accept-verified-entries-in-memory"]
subprocess.run(argv,cwd=ROOT,check=True)
print(f"Markdown report: {OUT/'public_demo_report.md'}")
