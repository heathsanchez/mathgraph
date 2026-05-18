import json,os,subprocess,sys
from pathlib import Path
import mathgraph
from mathgraph.demo_release import *
from mathgraph.version import __version__,get_version_info

ROOT=Path(__file__).resolve().parents[1]
def _env(): env=dict(os.environ); env.pop("PYTHONPATH",None); return env
def test_version_and_release_docs():
 info=get_version_info(); assert __version__=="0.1.0rc1" and mathgraph.__version__==__version__ and {"version","release_stage","release_name","release_summary","release_date"}<=set(info)
 assert "0.1.0rc1" in (ROOT/"CHANGELOG.md").read_text()
 assert "verifier" in (ROOT/"RELEASE_NOTES.md").read_text().lower()
 assert "run_release_check.py --quick" in (ROOT/"docs"/"quickstart.md").read_text()
 assert "public_demo_report.md" in (ROOT/"docs"/"artifact_conventions.md").read_text()
 assert "python -m pytest" in (ROOT/"docs"/"release_process.md").read_text()
 assert "run_release_check.py --quick" in (ROOT/"README.md").read_text()
 assert (ROOT/"docs"/"curated_real_mathlib_demo.md").exists()
 assert (ROOT/"examples"/"real_mathlib_demo"/"curated_real_mathlib_demo_config.example.json").exists()
def test_cli_artifacts_and_stdout(tmp_path):
 pub=tmp_path/"pub"; p=subprocess.run([sys.executable,"scripts/run_public_demo.py","--out-dir",str(pub)],cwd=ROOT,env=_env(),check=True,capture_output=True,text=True)
 assert len(p.stdout)<1000 and "MathGraph Public Demo" in p.stdout and (pub/"public_demo_report.json").exists() and (pub/"public_demo_report.md").exists() and (pub/"api_response.json").exists()
 pj=subprocess.run([sys.executable,"scripts/run_public_demo.py","--print-json"],cwd=ROOT,env=_env(),check=True,capture_output=True,text=True); assert json.loads(pj.stdout)["advisory"]
 rel=tmp_path/"release"; q=subprocess.run([sys.executable,"scripts/run_release_check.py","--quick","--out-dir",str(rel)],cwd=ROOT,env=_env(),check=True,capture_output=True,text=True)
 assert len(q.stdout)<1000 and "0.1.0rc1" in q.stdout and (rel/"release_check_report.json").exists() and (rel/"release_checks.jsonl").exists() and (rel/"artifacts_manifest.json").exists()
 data=json.loads((rel/"release_check_report.json").read_text()); assert data["summary"]["critical_total"]==0
def test_boundary_and_notebook():
 dry=run_public_demo(); live=run_public_demo(allow_execution=True,allow_missing_verifier=True); replay=run_public_demo(allow_execution=True,allow_missing_verifier=True,accept_verified_entries_in_memory=True)
 assert dry.boundary_evidence_count()==0 and live.summary["verified_total"] in {0,10} and replay.known_skip_count() in {0,10}
 assert all(live.proof_library_demo_report.summary[k]==0 for k in ("unsafe_verified_total","expected_missing_verified_total","import_failure_verified_total"))
 assert (ROOT/"notebooks"/"mathgraph_public_demo.py").exists()
