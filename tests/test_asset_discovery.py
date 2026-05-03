import json
import subprocess
import sys
from pathlib import Path

from mathgraph import AssetDiscoveryConfig, discover_mathgraph_assets
from mathgraph.asset_discovery import (
    AssetCandidate,
    AssetDiscoveryResult,
    materialize_assets,
    validate_equations_file,
    validate_matrix_file,
    validate_traces_json,
)
from mathgraph.kernel import Kernel


ROOT = Path(__file__).resolve().parents[1]


def _write_assets(tmp_path: Path) -> tuple[Path, Path]:
    traces = tmp_path / "traces.json"
    trace = Kernel().prove("x = x", "x = x")
    traces.write_text(json.dumps([trace.to_dict()]), encoding="utf-8")
    equations = tmp_path / "equations.txt"
    equations.write_text("x = x\nx = y\n", encoding="utf-8")
    return traces, equations


def test_dataclass_roundtrip_and_validation(tmp_path: Path) -> None:
    traces, equations = _write_assets(tmp_path)
    trace_validation = validate_traces_json(traces)
    assert trace_validation["trace_count"] == 1
    assert trace_validation["valid"]
    equation_validation = validate_equations_file(equations)
    assert equation_validation["equation_count"] == 2
    candidate = AssetCandidate("equations", str(equations), "test", True, True, equation_validation, 1.0)
    assert AssetCandidate.from_dict(candidate.to_dict()) == candidate


def test_asset_discovery_finds_exact_configured_candidates(tmp_path: Path) -> None:
    traces, equations = _write_assets(tmp_path)
    config = AssetDiscoveryConfig(
        traces_candidates=[str(traces)],
        equations_candidates=[str(equations)],
        matrix_candidates=[str(tmp_path / "missing.npy")],
        search_roots=[],
    )
    result = discover_mathgraph_assets(config)
    assert result.summary["traces_json_found"]
    assert result.summary["equations_found"]
    assert result.selected["traces_json"]["path"] == str(traces)
    assert result.selected["equations"]["path"] == str(equations)
    assert AssetDiscoveryResult.from_dict(result.to_dict()).summary == result.summary


def test_materialize_assets_returns_paths_or_copies(tmp_path: Path) -> None:
    traces, equations = _write_assets(tmp_path)
    result = discover_mathgraph_assets(
        AssetDiscoveryConfig(
            traces_candidates=[str(traces)],
            equations_candidates=[str(equations)],
            matrix_candidates=[],
            search_roots=[],
        )
    )
    refs = materialize_assets(result, tmp_path / "out")
    assert refs["traces_json"] == str(traces)
    copied = materialize_assets(result, tmp_path / "copied", copy=True)
    assert Path(copied["traces_json"]).exists()
    assert Path(copied["equations"]).exists()


def test_matrix_validation_without_required_numpy(tmp_path: Path) -> None:
    matrix = tmp_path / "etp_matrix_full_best_bool.npy"
    matrix.write_bytes(b"not a real npy")
    validation = validate_matrix_file(matrix)
    assert validation["matrix_exists"]
    assert validation["matrix_validation_status"] in {"error", "numpy_unavailable", "ok"}


def test_discovery_cli_writes_reports(tmp_path: Path) -> None:
    out = tmp_path / "reports"
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "discover_mathgraph_assets.py"),
            "--out-dir",
            str(out),
            "--max-files",
            "5",
            "--json-only",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    assert (out / "asset_discovery_report.json").exists()
    assert (out / "asset_discovery_report.md").exists()
