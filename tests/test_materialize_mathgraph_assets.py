import json
import os
import subprocess
import sys
from pathlib import Path

from mathgraph import AssetMaterializationConfig, materialize_mathgraph_assets
from mathgraph.asset_materialization import AssetMaterializationResult
from mathgraph.kernel import Kernel


ROOT = Path(__file__).resolve().parents[1]


def _write_traces(path: Path, source: str = "x = x") -> None:
    trace = Kernel().prove(source, source)
    path.write_text(json.dumps([trace.to_dict()]), encoding="utf-8")


def _write_assets(base: Path, prefix: str = "") -> tuple[Path, Path, Path]:
    base.mkdir(parents=True, exist_ok=True)
    traces = base / f"{prefix}traces.json"
    equations = base / f"{prefix}equations.txt"
    matrix = base / f"{prefix}etp_matrix_full_best_bool.npy"
    _write_traces(traces)
    equations.write_text("x = x\nx = y\n", encoding="utf-8")
    try:
        import numpy as np  # type: ignore

        np.save(matrix, np.array([[True, False], [True, True]], dtype=bool))
    except ImportError:
        matrix.write_bytes(b"fake npy")
    return traces, equations, matrix


def test_explicit_paths_win_over_search_discovered_paths(tmp_path: Path) -> None:
    explicit_dir = tmp_path / "explicit"
    search_dir = tmp_path / "search"
    explicit_traces, explicit_equations, explicit_matrix = _write_assets(explicit_dir)
    search_traces, _, _ = _write_assets(search_dir)
    result = materialize_mathgraph_assets(
        AssetMaterializationConfig(
            out_dir=str(tmp_path / "out"),
            traces_json=str(explicit_traces),
            equations_path=str(explicit_equations),
            matrix_path=str(explicit_matrix),
            mode="manifest-only",
            search_roots=[str(search_dir)],
        )
    )
    assert result.selected_assets["traces_json"]["path"] == str(explicit_traces)
    assert result.selected_assets["traces_json"]["path"] != str(search_traces)


def test_copy_mode_materializes_exact_filenames(tmp_path: Path) -> None:
    traces, equations, matrix = _write_assets(tmp_path / "input")
    result = materialize_mathgraph_assets(
        AssetMaterializationConfig(
            out_dir=str(tmp_path / "out"),
            traces_json=str(traces),
            equations_path=str(equations),
            matrix_path=str(matrix),
            mode="copy",
            search_roots=[],
        )
    )
    assert result.complete
    assert (tmp_path / "out" / "assets" / "traces.json").exists()
    assert (tmp_path / "out" / "assets" / "equations.txt").exists()
    assert (tmp_path / "out" / "assets" / "etp_matrix_full_best_bool.npy").exists()
    assert Path(result.outputs["summary_json"]).exists()
    assert Path(result.outputs["report_md"]).exists()


def test_manifest_only_does_not_create_copied_assets(tmp_path: Path) -> None:
    traces, equations, matrix = _write_assets(tmp_path / "input")
    result = materialize_mathgraph_assets(
        AssetMaterializationConfig(
            out_dir=str(tmp_path / "out"),
            traces_json=str(traces),
            equations_path=str(equations),
            matrix_path=str(matrix),
            mode="manifest-only",
            search_roots=[],
        )
    )
    assert result.complete
    assert not (tmp_path / "out" / "assets" / "traces.json").exists()
    assert result.materialized_assets["traces_json"] is None


def test_missing_assets_summarize_safely(tmp_path: Path) -> None:
    result = materialize_mathgraph_assets(
        AssetMaterializationConfig(
            out_dir=str(tmp_path / "out"),
            traces_json=str(tmp_path / "missing_traces.json"),
            equations_path=str(tmp_path / "missing_equations.txt"),
            matrix_path=str(tmp_path / "missing.npy"),
            search_roots=[],
        )
    )
    assert result.ok
    assert not result.complete
    assert set(result.missing_assets) == {"traces_json", "equations_path", "matrix_path"}
    assert Path(result.outputs["summary_json"]).exists()
    roundtrip = AssetMaterializationResult.from_dict(result.to_dict())
    assert roundtrip.missing_assets == result.missing_assets


def test_routelean_parquet_is_related_not_selected(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    parquet = root / "routelean_results_v19_1.parquet"
    parquet.write_bytes(b"parquet-ish")
    result = materialize_mathgraph_assets(
        AssetMaterializationConfig(
            out_dir=str(tmp_path / "out"),
            mode="manifest-only",
            search_roots=[str(root)],
        )
    )
    assert result.selected_assets["traces_json"] is None
    assert result.related_artifacts
    assert result.related_artifacts[0]["path"] == str(parquet)


def test_symlink_mode_when_supported(tmp_path: Path) -> None:
    if not hasattr(os, "symlink"):
        return
    traces, equations, matrix = _write_assets(tmp_path / "input")
    result = materialize_mathgraph_assets(
        AssetMaterializationConfig(
            out_dir=str(tmp_path / "out"),
            traces_json=str(traces),
            equations_path=str(equations),
            matrix_path=str(matrix),
            mode="symlink",
            search_roots=[],
        )
    )
    target = Path(result.materialized_assets["traces_json"])
    assert target.exists()
    assert target.is_symlink() or target.read_text(encoding="utf-8")


def test_cli_materialize_writes_summary_and_report(tmp_path: Path) -> None:
    traces, equations, matrix = _write_assets(tmp_path / "input")
    out = tmp_path / "out"
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "materialize_mathgraph_assets.py"),
            "--traces-json",
            str(traces),
            "--equations-path",
            str(equations),
            "--matrix-path",
            str(matrix),
            "--out-dir",
            str(out),
            "--mode",
            "copy",
            "--search-root",
            str(tmp_path / "empty"),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["complete"]
    assert (out / "asset_materialization_summary.json").exists()
    assert (out / "asset_materialization_report.md").exists()
