import json
import subprocess
import sys
from pathlib import Path

from mathgraph import (
    EpisodeLearningConfig,
    learn_from_assimilation_episodes,
)
from mathgraph.episode_learning import (
    ConstructorYieldStats,
    ResidualBasinStats,
    RouteYieldStats,
)


ROOT = Path(__file__).resolve().parents[1]


def _write_episode(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    task_rows = [
        {
            "task_id": "imported",
            "source": "x = x",
            "target": "x = y",
            "source_idx": 0,
            "target_idx": 1,
            "route": "finite_countermodel",
            "task_kind": "finite_countermodel_search",
            "terminal_goal": "FINITE_COUNTERMODEL",
            "execution_status": "finite_countermodel_found",
            "verification_status": "FINITE_VERIFIED",
            "import_status": "imported",
            "duplicate_status": "not_duplicate",
            "certificate_id": "cert_new",
            "countermodel_order": 2,
            "witness": {"assignment": {"x": 0, "y": 1}},
            "elapsed_sec": 0.2,
        },
        {
            "task_id": "duplicate",
            "source": "x = x",
            "target": "x = z",
            "source_idx": 0,
            "target_idx": 2,
            "route": "finite_countermodel",
            "task_kind": "finite_countermodel_search",
            "terminal_goal": "FINITE_COUNTERMODEL",
            "execution_status": "finite_countermodel_found",
            "verification_status": "FINITE_VERIFIED",
            "import_status": "skipped_duplicate",
            "duplicate_status": "duplicate",
            "certificate_id": "cert_dup",
            "countermodel_order": 2,
            "witness": {"assignment": {"x": 0, "z": 1}},
            "elapsed_sec": 0.4,
            "reason": "exact primitive pair already exists",
        },
        {
            "task_id": "residual",
            "source": "x = x",
            "target": "x = x",
            "source_idx": 0,
            "target_idx": 0,
            "route": "finite_countermodel",
            "task_kind": "finite_countermodel_search",
            "terminal_goal": "FINITE_COUNTERMODEL",
            "execution_status": "no_countermodel_found",
            "verification_status": "NOT_VERIFIED",
            "import_status": "not_attempted",
            "duplicate_status": "not_duplicate",
            "elapsed_sec": 0.6,
            "reason": "no checked table satisfied source and violated target",
        },
    ]
    _write_jsonl(path / "task_outcome_ledger.jsonl", task_rows)
    _write_jsonl(path / "new_certificates.jsonl", [task_rows[0]])
    _write_jsonl(path / "duplicate_certificates.jsonl", [task_rows[1]])
    _write_jsonl(path / "residual_obstruction_candidates.jsonl", [task_rows[2]])
    summary = {
        "task_count": 3,
        "finite_executor_verified_count": 2,
        "imported_count": 1,
        "duplicate_count": 1,
        "residual_count": 1,
        "not_found_count": 1,
        "revalidation_failed_count": 0,
    }
    _write_json(path / "certificate_assimilation_summary.json", summary)
    _write_json(path / "assimilation_episode_diagnostics.json", {"summary": summary})


def test_dataclass_roundtrips() -> None:
    route = RouteYieldStats("r", 1, 1, 1, 0, 0, 0, 1.0, 1.0, 0.0, 0.0)
    assert RouteYieldStats.from_dict(route.to_dict()) == route
    constructor = ConstructorYieldStats("k", "FINITE_COUNTERMODEL", 1, 1, 1, 0, 0, 0.1, 0.1)
    assert ConstructorYieldStats.from_dict(constructor.to_dict()) == constructor
    residual = ResidualBasinStats("r", "k", 1, 2, "x", "y", "reason", "no", "NOT_VERIFIED", "not", "goal", "obs", {})
    assert ResidualBasinStats.from_dict(residual.to_dict()) == residual


def test_learns_from_synthetic_episode(tmp_path: Path) -> None:
    episode = tmp_path / "episode"
    out = tmp_path / "learning"
    _write_episode(episode)
    result = learn_from_assimilation_episodes(EpisodeLearningConfig([str(episode)], str(out)))
    assert result.summary["task_count"] == 3
    assert result.summary["imported_count"] == 1
    assert result.summary["duplicate_count"] == 1
    assert result.summary["residual_count"] == 1
    route = result.route_yield_stats[0]
    assert route["route"] == "finite_countermodel"
    assert route["verified_count"] == 2
    assert route["imported_count"] == 1
    assert route["duplicate_count"] == 1
    constructor = result.constructor_yield_stats[0]
    assert constructor["task_kind"] == "finite_countermodel_search"
    assert constructor["verified_count"] == 2
    assert result.residual_basin_stats[0]["candidate_obstruction_name"].startswith("residual_")


def test_recommendations_for_duplicate_and_scale_up(tmp_path: Path) -> None:
    episode = tmp_path / "episode"
    out = tmp_path / "learning"
    _write_episode(episode)
    result = learn_from_assimilation_episodes(EpisodeLearningConfig([str(episode)], str(out)))
    text = json.dumps(result.next_run_recommendations)
    assert "Duplicate rate is high" in text
    assert "Unique import rate is high" in text
    assert "finite search misses are not proof" in text.lower()


def test_cli_writes_expected_files(tmp_path: Path) -> None:
    episode = tmp_path / "episode"
    out = tmp_path / "learning"
    _write_episode(episode)
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "learn_from_assimilation_episode.py"),
            "--episode-dir",
            str(episode),
            "--out-dir",
            str(out),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    expected = [
        "episode_learning_summary.json",
        "route_yield_stats.json",
        "constructor_yield_stats.json",
        "residual_basin_stats.jsonl",
        "duplicate_motif_stats.json",
        "new_certificate_stats.json",
        "next_run_recommendations.json",
        "episode_learning_report.md",
    ]
    for name in expected:
        assert (out / name).exists()
    assert json.loads(completed.stdout)["task_count"] == 3


def test_public_exports_episode_learning() -> None:
    from mathgraph import EpisodeLearningConfig as PublicConfig
    from mathgraph import learn_from_assimilation_episodes as public_learn

    assert PublicConfig.__name__ == "EpisodeLearningConfig"
    assert callable(public_learn)


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
