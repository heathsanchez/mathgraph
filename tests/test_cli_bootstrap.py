import importlib.util,os,subprocess,sys
from pathlib import Path
from scripts._bootstrap import ensure_repo_root_on_path,repo_root_from_file
ROOT=Path(__file__).resolve().parents[1]
def _env():
 env=dict(os.environ); env.pop("PYTHONPATH",None); return env
def test_bootstrap_helpers(tmp_path):
 script=ROOT/"scripts"/"run_hardening.py"; assert repo_root_from_file(script)==ROOT
 before=list(sys.path); 
 try:
  sys.path[:]=[x for x in sys.path if x!=str(ROOT)]
  assert ensure_repo_root_on_path(script)==ROOT and sys.path[0]==str(ROOT)
  ensure_repo_root_on_path(script); assert sys.path.count(str(ROOT))==1
 finally: sys.path[:]=before
def test_bootstrap_does_not_import_mathgraph(monkeypatch):
 monkeypatch.delitem(sys.modules,"mathgraph",raising=False); spec=importlib.util.spec_from_file_location("bootstrap_probe",ROOT/"scripts"/"_bootstrap.py"); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
 assert "mathgraph" not in sys.modules
def test_representative_scripts_clean_env_help():
 for script in ("run_verifier_fixtures.py","run_verified_corpus.py","run_lean_project_subset.py","run_mathlib_micro_subset.py","run_mathlib_local_allowlist.py","run_mathlib_declaration_discovery.py","run_mathlib_module_verification.py","run_mathlib_digest_accumulator.py","run_constructor_distiller.py","run_reason_atlas_export.py","run_lawbook_summary.py","run_proof_library_demo.py","run_real_mathlib_demo.py","run_public_demo.py","run_release_check.py","run_e2e_testdrive.py","run_hardening.py","run_roadmap_alignment.py","run_colab_testdrive.py"):
  subprocess.run([sys.executable,f"scripts/{script}","--help"],cwd=ROOT,env=_env(),check=True,capture_output=True,text=True)
def test_representative_scripts_clean_env_dry_run(tmp_path):
 cmds=(
  ["scripts/run_verifier_fixtures.py","--ensure-fixtures"],
  ["scripts/run_verified_corpus.py","--ensure-micro-corpus"],
  ["scripts/run_lean_project_subset.py","--ensure-micro-project"],
  ["scripts/run_mathlib_micro_subset.py","--ensure-synthetic-subset"],
  ["scripts/run_e2e_testdrive.py","--out-report-json",str(tmp_path/"e2e.json")],
  ["scripts/run_hardening.py","--out-report-json",str(tmp_path/"hardening.json")],
  ["scripts/run_roadmap_alignment.py","--fail-on-critical"],
 )
 for argv in cmds: subprocess.run([sys.executable,*argv],cwd=ROOT,env=_env(),check=True,capture_output=True,text=True)
def test_colab_quick_smoke(tmp_path):
 subprocess.run([sys.executable,"scripts/run_colab_testdrive.py","--use-current-checkout","--quick-smoke","--out-dir",str(tmp_path)],cwd=ROOT,env=_env(),check=True,capture_output=True,text=True)
 assert (tmp_path/"colab_testdrive_report.json").exists()
