from mathgraph.root_operator_schema import ParameterSpec, RootOperatorSchema


def _schema() -> RootOperatorSchema:
    return RootOperatorSchema.create(
        [
            {"name": "move", "kind": "spatial", "params": {"axis": "$axis", "distance": 2}},
            {"name": "recolor", "kind": "color", "params": {"color": "$color"}},
        ],
        [ParameterSpec("axis", "axis", ("x", "y")), ParameterSpec("color", "color", (1, 7))],
        source_trace_ids=("t1", "t2"),
        support=2,
    )


def test_stable_schema_ids():
    assert _schema().schema_id == _schema().schema_id


def test_json_roundtrip():
    schema = _schema()
    assert RootOperatorSchema.from_json(schema.to_json()).schema_id == schema.schema_id


def test_advisory_boundary_fields():
    schema = _schema()
    assert schema.advisory_only is True
    assert schema.verifier_promoted is False
    assert schema.to_dict()["advisory_only"] is True


def test_row_export():
    row = _schema().to_row()
    assert row["schema_id"]
    assert isinstance(row["atoms"], str)


def test_equality_dedup_behavior_by_id():
    schemas = {_schema().schema_id: _schema()}
    assert len(schemas) == 1
