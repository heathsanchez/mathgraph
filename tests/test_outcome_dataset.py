import json
import subprocess
import sys
from pathlib import Path

from mathgraph import (
    Certificate,
    CertificateLawbook,
    DerivedCertificateGenerator,
    LawbookStore,
    OutcomeDatasetBuilder,
    TerminalForm,
    Trace,
    VerificationStatus,
    extract_outcome_pair_features,
)


ROOT = Path(__file__).resolve().parents[1]


def _trace(source: str, target: str, terminal_form: str, route: str) -> Trace:
    terminal = TerminalForm(terminal_form)
    status = (
        VerificationStatus.VERIFIED
        if terminal == TerminalForm.VERIFIED_PROOF
        else VerificationStatus.REFUTED
    )
    lean_status = "lean_verified" if terminal == TerminalForm.VERIFIED_PROOF else None
    return Trace(
        claim=f"{source}=>{target}",
        source=source,
        target=target,
        routes_tried=[route],
        terminal_form=terminal,
        verification_status=status,
        certificate=Certificate(
            terminal_form=terminal,
            claim=f"{source}=>{target}",
            payload={
                "source_idx": source,
                "target_idx": target,
                "compiled_route": route,
                "claim_hash": f"{source}->{target}",
                "lean_status": lean_status,
            },
        ),
        metadata={
            "source_idx": source,
            "target_idx": target,
            "compiled_route": route,
            "claim_hash": f"{source}->{target}",
            "lean_status": lean_status,
        },
    )


def _store(path: Path, with_derived: bool = True) -> LawbookStore:
    store = LawbookStore(path)
    store.import_lawbook(
        CertificateLawbook.from_traces(
            [
                _trace("A", "B", "VERIFIED_PROOF", "variable_identification"),
                _trace("B", "C", "VERIFIED_PROOF", "skeleton_preserving_relabel"),
                _trace("B", "D", "FINITE_COUNTERMODEL", "finite_countermodel"),
            ]
        ),
        replace=True,
    )
    if with_derived:
        certs, _ = DerivedCertificateGenerator(store).derive_all()
        store.import_derived_certificates(certs, replace=True)
    return store


def test_builds_outcomes_from_primitive_traces(tmp_path: Path) -> None:
    store = _store(tmp_path / "lawbook.sqlite", with_derived=False)
    try:
        outcomes = OutcomeDatasetBuilder(store).build(include_derived=False)
        assert len(outcomes) == 3
        assert {outcome.origin for outcome in outcomes} == {"primitive_trace"}
        assert any(outcome.trust_level == "finite_verified" for outcome in outcomes)
    finally:
        store.close()


def test_builds_outcomes_from_derived_certs(tmp_path: Path) -> None:
    store = _store(tmp_path / "lawbook.sqlite")
    try:
        outcomes = OutcomeDatasetBuilder(store).build(include_primitive=False)
        assert outcomes
        assert {outcome.origin for outcome in outcomes} == {"derived_certificate"}
        assert all(outcome.trust_level == "derived_from_verified_traces" for outcome in outcomes)
    finally:
        store.close()


def test_primitive_and_derived_included_by_default(tmp_path: Path) -> None:
    store = _store(tmp_path / "lawbook.sqlite")
    try:
        outcomes = OutcomeDatasetBuilder(store).build()
        assert {outcome.origin for outcome in outcomes} == {
            "primitive_trace",
            "derived_certificate",
        }
    finally:
        store.close()


def test_unknown_pairs_are_included_correctly(tmp_path: Path) -> None:
    store = _store(tmp_path / "lawbook.sqlite", with_derived=False)
    try:
        outcomes = OutcomeDatasetBuilder(store).build(
            include_primitive=False,
            include_derived=False,
            unknown_pairs=[{"source": "X", "target": "Y", "source_idx": 1}],
        )
        assert outcomes[0].origin == "oracle_unknown"
        assert outcomes[0].terminal_form == "NAMED_OBSTRUCTION"
        assert outcomes[0].trust_level == "unknown"
        assert outcomes[0].labels["is_unknown"]
    finally:
        store.close()


def test_advisory_tasks_are_included_correctly(tmp_path: Path) -> None:
    store = _store(tmp_path / "lawbook.sqlite", with_derived=False)
    task = {
        "task_id": "task_1",
        "source": "X",
        "target": "Z",
        "task_kind": "proof_template",
        "route": "variable_identification",
        "status": "planned",
        "warnings": ["advisory only"],
    }
    try:
        outcomes = OutcomeDatasetBuilder(store).build(
            include_primitive=False,
            include_derived=False,
            advisory_tasks=[task],
        )
        assert outcomes[0].origin == "advisory_task"
        assert outcomes[0].trust_level == "advisory_only"
        assert outcomes[0].evidence["task_kind"] == "proof_template"
    finally:
        store.close()


def test_feature_extraction_is_deterministic_and_has_required_keys() -> None:
    one = extract_outcome_pair_features("x * y = x", "x * x = x")
    two = extract_outcome_pair_features("x * y = x", "x * x = x")
    assert one == two
    for key in [
        "source_len",
        "target_len",
        "len_delta",
        "source_op_count",
        "target_op_count",
        "source_var_set",
        "target_var_set",
        "new_target_vars",
        "same_skeleton_rough",
        "paren_delta",
    ]:
        assert key in one


def test_stats_counts_core_dimensions(tmp_path: Path) -> None:
    store = _store(tmp_path / "lawbook.sqlite")
    try:
        builder = OutcomeDatasetBuilder(store)
        outcomes = builder.build(unknown_pairs=[{"source": "X", "target": "Y"}])
        stats = builder.stats(outcomes)
        assert stats.row_count == len(outcomes)
        assert stats.primitive_count == 3
        assert stats.derived_count >= 1
        assert stats.unknown_count == 1
        assert stats.by_origin["primitive_trace"] == 3
        assert stats.by_terminal_form["NAMED_OBSTRUCTION"] == 1
        assert stats.by_route["finite_countermodel"] == 1
    finally:
        store.close()


def test_diagnostics_computes_compounding_metrics(tmp_path: Path) -> None:
    store = _store(tmp_path / "lawbook.sqlite")
    try:
        builder = OutcomeDatasetBuilder(store)
        outcomes = builder.build()
        diagnostics = builder.diagnostics(outcomes, episode_id="episode", equation_count=10)
        assert diagnostics.derived_per_primitive > 0
        assert diagnostics.corpus_density == diagnostics.total_certificate_count / 100
        assert diagnostics.route_yield
        assert diagnostics.derivation_yield
    finally:
        store.close()


def test_diagnostics_warning_for_no_derived_certs(tmp_path: Path) -> None:
    store = _store(tmp_path / "lawbook.sqlite", with_derived=False)
    try:
        builder = OutcomeDatasetBuilder(store)
        diagnostics = builder.diagnostics(builder.build(include_derived=False), episode_id="episode")
        assert "No derived certificates found." in diagnostics.warnings
    finally:
        store.close()


def test_jsonl_json_and_diagnostics_save(tmp_path: Path) -> None:
    store = _store(tmp_path / "lawbook.sqlite")
    jsonl_path = tmp_path / "outcomes.jsonl"
    json_path = tmp_path / "outcomes.json"
    diag_path = tmp_path / "diagnostics.json"
    try:
        builder = OutcomeDatasetBuilder(store)
        outcomes = builder.build()
        diagnostics = builder.diagnostics(outcomes, episode_id="episode")
        builder.save_jsonl(outcomes, jsonl_path)
        builder.save_json(outcomes, json_path)
        builder.save_diagnostics(diagnostics, diag_path)
        assert jsonl_path.read_text(encoding="utf-8").splitlines()
        assert json.loads(json_path.read_text(encoding="utf-8"))
        assert json.loads(diag_path.read_text(encoding="utf-8"))["episode_id"] == "episode"
    finally:
        store.close()


def test_build_outcome_dataset_cli(tmp_path: Path) -> None:
    store = _store(tmp_path / "lawbook.sqlite")
    store.close()
    jsonl_path = tmp_path / "pair_outcomes.jsonl"
    json_path = tmp_path / "pair_outcomes.json"
    diag_path = tmp_path / "diagnostics.json"
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "build_outcome_dataset.py"),
            "--store",
            str(tmp_path / "lawbook.sqlite"),
            "--out-jsonl",
            str(jsonl_path),
            "--out-json",
            str(json_path),
            "--diagnostics",
            str(diag_path),
            "--episode-id",
            "episode",
            "--equation-count",
            "10",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["stats"]["primitive_count"] == 3
    assert jsonl_path.exists()
    assert json_path.exists()
    assert diag_path.exists()
