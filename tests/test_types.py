import pytest

from mathgraph.types import (
    ExtensionalCollapsePolicy,
    HyperintensionalIdentityMode,
    TypeParseError,
    TypedObject,
    canonical_encoded_object_id,
    normalize_type_expr,
    parse_type_expr,
    should_merge_objects,
)


def test_type_expr_parsing_and_roundtrip():
    for expr in ["i", "<>", "<i>", "<i,i>", "<<i>>", "<<i,i>>", " < < i , i > > "]:
        parsed = parse_type_expr(expr)
        assert normalize_type_expr(parsed.normalized) == parsed.normalized

    assert parse_type_expr("i").is_individual
    assert parse_type_expr("<>").is_proposition
    assert parse_type_expr("<i,i>").arity == 2
    with pytest.raises(TypeParseError):
        parse_type_expr("<i,,i>")


def test_typed_object_and_hyperintensional_merge_guard():
    object_id = canonical_encoded_object_id("k", "w", "<i>", {"motif": "projection_left"})
    assert object_id == canonical_encoded_object_id("k", "w", "< i >", {"motif": "projection_left"})
    obj = TypedObject(
        object_id=object_id,
        type_expr="<i>",
        object_kind="RootNode",
        encoded_properties={"coverage": [1, 2]},
        hyperintensional_identity_mode=HyperintensionalIdentityMode.CERTIFICATE_COVERAGE.value,
    )
    other = TypedObject(
        object_id="other",
        type_expr="<i>",
        object_kind="RootNode",
        encoded_properties={"coverage": [1, 2]},
    )
    assert obj.to_dict()["uniqueness_status"] == "UNKNOWN"
    assert not should_merge_objects(obj, other, ExtensionalCollapsePolicy.NEVER_BY_DEFAULT)
    assert not should_merge_objects(obj, other, ExtensionalCollapsePolicy.ADVISORY_ONLY)
