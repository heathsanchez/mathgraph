"""Lightweight notebook-equivalent public demo runner.

Demo success is not proof. Only explicit verifier/importer/finite-validator/
chain-audit evidence promotes truth.
"""
from pathlib import Path
import subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"tmp_public_demo_outputs"
subprocess.run([sys.executable,"scripts/run_public_demo.py","--out-dir",str(OUT),"--allow-execution","--allow-missing-verifier","--accept-verified-entries-in-memory"],cwd=ROOT,check=True)
print(OUT/"public_demo_report.md")
