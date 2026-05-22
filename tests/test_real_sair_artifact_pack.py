import json
from pathlib import Path

import pytest

from mathgraph.real_sair_artifact_pack import RealSairArtifactPackConfig, RealSairArtifactPackRunner


def test_missing_real_files_fail_when_fallback_not_allowed(tmp_path):
    with pytest.raises(FileNotFoundError):
        RealSairArtifactPackRunner(
            RealSairArtifactPackConfig(
                equations_path=tmp_path / "missing_eqs.txt",
                matrix_path=tmp_path / "missing_matrix.npy",
                output_dir=tmp_path / "pack",
                allow_fallback=False,
            )
        ).run()


def test_fallback_smoke_pack_outputs_and_archive(tmp_path):
    result = RealSairArtifactPackRunner(
        RealSairArtifactPackConfig(
            equations_path=tmp_path / "missing_eqs.txt",
            matrix_path=tmp_path / "missing_matrix.npy",
            output_dir=tmp_path / "pack",
            num_episodes=2,
            episode_size=12,
            allow_fallback=True,
            create_archive=True,
        )
    ).run()
    assert result.real_sair_used is False
    assert result.fallback_mode is True
    assert result.advisory_boundary_preserved is True
    assert Path(result.archive_path).exists()
    assert Path(result.manifest_path).exists()
    assert Path(result.summary_json_path).exists()
    assert Path(result.report_md_path).exists()
    assert result.durable_artifact_count == 0
    assert result.promoted_artifact_count == 0
    assert result.warnings


def test_manifest_and_summary_required_fields(tmp_path):
    result = RealSairArtifactPackRunner(
        RealSairArtifactPackConfig(
            equations_path=tmp_path / "missing_eqs.txt",
            matrix_path=tmp_path / "missing_matrix.npy",
            output_dir=tmp_path / "pack",
            num_episodes=2,
            episode_size=12,
            allow_fallback=True,
            create_archive=True,
            run_label="unit-test",
        )
    ).run()
    manifest = json.loads(Path(result.manifest_path).read_text(encoding="utf-8"))
    summary = json.loads(Path(result.summary_json_path).read_text(encoding="utf-8"))
    for key in (
        "run_id",
        "run_label",
        "timestamp_utc",
        "git_commit",
        "git_branch",
        "repo_dirty",
        "python_version",
        "platform",
        "real_sair_used",
        "fallback_mode",
        "generated_files",
        "generated_directories",
        "warnings",
    ):
        assert key in manifest
    assert manifest["run_label"] == "unit-test"
    assert summary["fallback_mode"] is True
    assert "multi_episode" in summary


def test_markdown_report_interpretation_is_honest(tmp_path):
    result = RealSairArtifactPackRunner(
        RealSairArtifactPackConfig(
            equations_path=tmp_path / "missing_eqs.txt",
            matrix_path=tmp_path / "missing_matrix.npy",
            output_dir=tmp_path / "pack",
            num_episodes=2,
            episode_size=12,
            allow_fallback=True,
            create_archive=False,
        )
    ).run()
    text = Path(result.report_md_path).read_text(encoding="utf-8")
    assert "fallback smoke artifact pack" in text
    assert "not real SAIR compounding" in text

