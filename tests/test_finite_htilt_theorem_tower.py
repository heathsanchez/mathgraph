import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = ROOT / "docs" / "finite_htilt_theorem_tower.md"
BOUNDARY_PATH = (
    ROOT
    / "artifacts"
    / "obstruction_atlas"
    / "finite_htilt_remaining_boundaries_v1.json"
)
CONDITIONAL_LAWBOOK_PATH = (
    ROOT / "artifacts" / "lawbook" / "finite_htilt_discrete_doob_stationary_v1.json"
)
PF_LAWBOOK_PATH = (
    ROOT / "artifacts" / "lawbook" / "finite_htilt_pf_discrete_survivor_law_v1.json"
)
PF_LEAN_PATH = (
    ROOT / "examples" / "verifier_fixtures" / "lean" / "htilt_pf_discrete_survivor_law.lean"
)


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_theorem_tower_document_lists_all_layers_and_bridge_obstruction() -> None:
    text = DOC_PATH.read_text(encoding="utf-8")
    for artifact_id in (
        "finite_htilt_survivor_law_v1",
        "finite_htilt_discrete_doob_stationary_v1",
        "finite_htilt_pf_discrete_survivor_law_v1",
    ):
        assert artifact_id in text
    assert "killed_generator_bridge_from_discrete_pf" in text


def test_remaining_boundary_record_blocks_all_out_of_scope_claims() -> None:
    boundary = _read_json(BOUNDARY_PATH)
    assert boundary["status"] == "ACTIVE_BOUNDARY"
    ids = {item["id"] for item in boundary["remaining_obstructions"]}
    assert {
        "killed_generator_bridge_from_discrete_pf",
        "markov_convergence_not_proved",
        "empirical_h_band_not_proved",
        "consciousness_not_proved",
        "scheduler_performance_not_proved",
    } <= ids
    assert all(item["status"] == "OPEN" for item in boundary["remaining_obstructions"])


def test_conditional_discrete_lawbook_is_verified_and_normalized() -> None:
    lawbook = _read_json(CONDITIONAL_LAWBOOK_PATH)
    assert lawbook["status"] == "VERIFIED_PROOF"
    names = set(lawbook["verified_theorems"])
    for name in (
        "HTiltDiscreteDoob.survivorWeight_pos",
        "HTiltDiscreteDoob.survivorNorm_pos",
        "HTiltDiscreteDoob.piStar_pos",
        "HTiltDiscreteDoob.piStar_sum_one",
        "HTiltDiscreteDoob.discreteDoobEntry_nonneg",
        "HTiltDiscreteDoob.piStar_is_stationary_distribution_for_discreteDoob",
    ):
        assert name in names


def test_pf_portal_lawbook_records_exact_pin_and_clean_axiom_graph() -> None:
    lawbook = _read_json(PF_LAWBOOK_PATH)
    assert lawbook["status"] == "VERIFIED_PROOF"
    boundary = lawbook["boundary"]
    assert boundary["lean_version"] == "4.27.0-rc1"
    assert boundary["mathlib_revision"] == "ae0143cded18d09875e12c3056f428090484d9a4"
    assert boundary["external_repo_commit"] == (
        "0bbb8999d1703776516f37f412334e01e07a30a0"
    )
    assert boundary["excluded_axioms"] == ["sorryAx"]
    precision = lawbook["dependency_precision"]
    assert precision["portal_theorem_depends_on_upstream_sorry"] is False
    assert precision["external_subtree_globally_placeholder_free"] is False


def test_claimed_normalized_pf_theorem_occurs_in_lean_source() -> None:
    lawbook = _read_json(PF_LAWBOOK_PATH)
    theorem_name = (
        "HTiltPFDiscreteSurvivor."
        "exists_positive_stationary_distribution_of_irreducible"
    )
    assert theorem_name in lawbook["verified_theorems"]
    assert "theorem exists_positive_stationary_distribution_of_irreducible" in (
        PF_LEAN_PATH.read_text(encoding="utf-8")
    )
