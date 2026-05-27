import csv
import json

from mathgraph.compounding_lawbook_engine import build_lawbook_view, run_compounding_lawbook_engine


def test_lawbook_view_loads_canonical_evidence_packs() -> None:
    view = build_lawbook_view()
    ids = {entry.evidence_pack_id for entry in view}
    assert ids == {
        "recursive_residual_transfer_v1_20260523",
        "sair_stage2_breakthrough_20260526",
        "residual_obstruction_atlas_v8_4",
        "collatz_primitive_divisor_v12_2",
        "root_node_persistent_filtration_v16_3",
        "cross_world_semantic_residual_invariant",
    }
    assert all(entry.trust_boundary_status == "PASS" for entry in view)
    assert next(entry for entry in view if entry.evidence_pack_id == "sair_stage2_breakthrough_20260526").terminal_form_type == "FINITE_COUNTERMODEL"
    assert next(entry for entry in view if entry.evidence_pack_id == "collatz_primitive_divisor_v12_2").terminal_form_type == "NONE_ADVISORY"
    assert next(entry for entry in view if entry.evidence_pack_id == "cross_world_semantic_residual_invariant").claim_status == "empirical_cross_world_invariant_candidate"


def test_compounding_lawbook_engine_demo_outputs_and_boundaries(tmp_path) -> None:
    report = run_compounding_lawbook_engine(tmp_path / "run", max_tasks=6, fallback_smoke=True)
    assert report.evidence_pack_count == 6
    assert report.lawbook_hit_rate == 1.0
    assert report.lawbook_action_change_rate == 1.0
    assert report.decode_supported_rate > 0.0
    assert report.prohibited_promotion_count == 0
    assert report.advisory_boundary_ok is True
    assert report.advisory_boundary_preserved is True
    assert report.memory_supported_count >= report.baseline_supported_count

    out = tmp_path / "run"
    for name in (
        "compounding_report.json",
        "compounding_report.md",
        "lawbook_attention_trace.csv",
        "decode_to_verify_eval.csv",
    ):
        assert (out / name).exists()

    data = json.loads((out / "compounding_report.json").read_text(encoding="utf-8"))
    assert data["metrics"]["prohibited_promotion_count"] == 0
    assert data["metrics"]["advisory_boundary_ok"] is True
    assert "finite-checked FALSE" in (out / "compounding_report.md").read_text(encoding="utf-8")

    attention = list(csv.DictReader((out / "lawbook_attention_trace.csv").open(encoding="utf-8")))
    decode = list(csv.DictReader((out / "decode_to_verify_eval.csv").open(encoding="utf-8")))
    assert len(attention) == 6
    assert len(decode) == 6
    assert {row["prohibited_promotion"] for row in attention} == {"False"}
    assert {row["advisory_boundary_ok"] for row in decode} == {"True"}
