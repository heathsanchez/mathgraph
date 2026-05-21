from types import SimpleNamespace

from mathgraph.reason_atlas_adapters import (
    entry_from_contact_promotion,
    entry_from_dict,
    entry_from_root_operator_instance,
    entry_from_root_operator_schema,
)
from mathgraph.reason_atlas_store import ReasonAtlasEntryKind


def test_adapter_from_dict():
    entry = entry_from_dict({"law_id": "l1", "law_kind": "PROMOTED_ROUTE_LAW", "shape": "s", "repair_strategy": "r"})
    assert entry.kind == ReasonAtlasEntryKind.PROMOTED_ROUTE_LAW
    assert entry.advisory_only is True


def test_adapter_from_duck_root_operator_schema():
    obj = SimpleNamespace(schema_id="s1", compact_name="move_axis", atoms=[{"name": "move", "params": {"axis": "$axis"}}], support=2, promoted=True)
    entry = entry_from_root_operator_schema(obj)
    assert entry.kind == ReasonAtlasEntryKind.ROOT_OPERATOR_SCHEMA
    assert "move" in entry.atoms


def test_adapter_from_duck_root_operator_instance():
    obj = SimpleNamespace(instance_id="i1", schema_id="s1", atoms=[{"name": "recolor", "params": {"color": 1}}])
    entry = entry_from_root_operator_instance(obj)
    assert entry.kind == ReasonAtlasEntryKind.ROOT_OPERATOR_INSTANCE


def test_adapter_from_contact_object_and_no_truth_forms():
    obj = SimpleNamespace(to_dict=lambda: {"seed_id": "seed", "kind": "STRICT_CONTACT_SEED", "decl_name": "Nat.x", "shape": "s"})
    entry = entry_from_contact_promotion(obj)
    assert entry.kind == ReasonAtlasEntryKind.STRICT_CONTACT_SEED
    assert "VERIFIED_PROOF" not in str(entry.to_dict())
    assert "REFUTATION_CERTIFICATE" not in str(entry.to_dict())
