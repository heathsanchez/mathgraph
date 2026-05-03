import importlib.util
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_real_asset_pipeline.py"


def _load_validator():
    spec = importlib.util.spec_from_file_location("validate_real_asset_pipeline", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_no_assets_allowed_no_crash(tmp_path: Path) -> None:
    out = tmp_path / "validate_missing"
    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--repo-root",
            str(ROOT),
            "--out-dir",
            str(out),
            "--skip-install",
            "--allow-missing-assets",
            "--traces-json",
            str(tmp_path / "missing_traces.json"),
            "--equations-path",
            str(tmp_path / "missing_equations.txt"),
            "--max-frontier-pairs",
            "5",
            "--top-k-schedule",
            "5",
            "--max-tasks",
            "5",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr + completed.stdout
    summary = json.loads((out / "validation_summary.json").read_text(encoding="utf-8"))
    assert summary["overall_ok"]
    assert summary["missing_assets"]
    assert summary["real_smoke_ok"]
    assert (out / "validation_report.md").exists()
    assert (out / "logs" / "asset_discovery.stdout.txt").exists()


def test_no_assets_with_synthetic_fallback(tmp_path: Path) -> None:
    out = tmp_path / "validate_fallback"
    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--repo-root",
            str(ROOT),
            "--out-dir",
            str(out),
            "--skip-install",
            "--allow-missing-assets",
            "--allow-synthetic-fallback",
            "--traces-json",
            str(tmp_path / "missing_traces.json"),
            "--equations-path",
            str(tmp_path / "missing_equations.txt"),
            "--max-frontier-pairs",
            "8",
            "--top-k-schedule",
            "8",
            "--max-tasks",
            "8",
            "--max-countermodel-order",
            "2",
            "--random-tables-per-order",
            "0",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr + completed.stdout
    summary = json.loads((out / "validation_summary.json").read_text(encoding="utf-8"))
    assert summary["fallback_smoke_ok"] is True
    assert summary["synthetic_fallback_used"] is True
    assert summary["real_assets_found"] is False
    fallback_report = json.loads(Path(summary["paths"]["fallback_smoke_report"]).read_text(encoding="utf-8"))
    assert fallback_report["summary"]["synthetic_fallback_used"] is True
    assert fallback_report["summary"]["real_asset_mode"] is False


def test_parse_smoke_summary_helper() -> None:
    module = _load_validator()
    real = module.parse_smoke_summary(
        {"summary": {"real_asset_mode": True, "synthetic_fallback_used": False, "missing_assets": []}}
    )
    assert real["real_asset_mode"] is True
    assert real["synthetic_fallback_used"] is False
    missing = module.parse_smoke_summary({"summary": {"missing_assets": ["traces_json"]}})
    assert missing["real_asset_mode"] is False
    assert missing["missing_assets"] == ["traces_json"]
    fallback = module.parse_smoke_summary(
        {"summary": {"synthetic_fallback_used": True, "real_asset_mode": False}}
    )
    assert fallback["synthetic_fallback_used"] is True
