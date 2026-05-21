from mathgraph.root_operator_induction import anti_unify_trace_group, induce_root_operator_schemas


def trace(trace_id, atoms, family="f", root="r", hidden="h"):
    return {"trace_id": trace_id, "family": family, "latent_root": root, "hidden_program": hidden, "atoms": atoms}


def move_recolor(axis="x", color=1):
    return [
        {"name": "move", "kind": "spatial", "params": {"axis": axis, "distance": 2}},
        {"name": "recolor", "kind": "color", "params": {"color": color}},
    ]


def select_move_recolor(selector="extract_box", axis="x", color=1):
    return [
        {"name": "select", "kind": "selector", "params": {"selector": selector}},
        *move_recolor(axis, color),
    ]


def test_exact_trace_grouping_induces_schema_with_support():
    schema = anti_unify_trace_group([trace("t1", move_recolor()), trace("t2", move_recolor())])
    assert schema is not None
    assert schema.support == 2


def test_anti_unifies_colors_into_color_parameter():
    schema = anti_unify_trace_group([trace("t1", move_recolor(color=1)), trace("t2", move_recolor(color=7))])
    assert schema is not None
    assert any(param.kind == "color" for param in schema.parameters)


def test_anti_unifies_x_y_movement_into_axis_parameter():
    schema = anti_unify_trace_group([trace("t1", move_recolor(axis="x")), trace("t2", move_recolor(axis="y"))])
    assert schema is not None
    assert any(param.kind == "axis" for param in schema.parameters)


def test_anti_unifies_selector_alternatives():
    schema = anti_unify_trace_group(
        [trace("t1", select_move_recolor("extract_box")), trace("t2", select_move_recolor("extract_largest"))]
    )
    assert schema is not None
    assert any(param.kind == "selector" for param in schema.parameters)


def test_induces_move_axis_distance_recolor_color():
    schemas = induce_root_operator_schemas(
        [trace("t1", move_recolor("x", 1)), trace("t2", move_recolor("y", 7)), trace("t3", move_recolor("x", 4))]
    )
    assert any(schema.compact_name.startswith("move_axis_2__recolor_color") for schema in schemas)


def test_induces_select_move_recolor():
    schemas = induce_root_operator_schemas(
        [
            trace("t1", select_move_recolor("extract_box", "x", 1)),
            trace("t2", select_move_recolor("extract_largest", "y", 4)),
        ]
    )
    assert any("select_selector__move_axis_2__recolor_color" in schema.compact_name for schema in schemas)


def test_rejects_useless_low_support_literal_schema():
    schemas = induce_root_operator_schemas([trace("t1", move_recolor("x", 1))])
    assert schemas == []
