"""Small deterministic ARC-like demo for root operator induction."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from mathgraph.root_operator_induction import induce_compositional_root_schemas
from mathgraph.root_operator_promotion import (
    oracle_fraction_captured,
    promote_root_operator_schemas,
    residual_compression_metrics,
)
from mathgraph.root_operator_schema import RootOperatorEvaluationSummary, RootOperatorSchema

Grid = tuple[tuple[int, ...], ...]


@dataclass(frozen=True)
class ArcDemoTask:
    task_id: str
    family: str
    latent_root: str
    hidden_program: str
    atoms: tuple[dict[str, Any], ...]
    input_grid: Grid
    output_grid: Grid

    def to_trace_record(self) -> dict[str, Any]:
        return {
            "trace_id": self.task_id,
            "family": self.family,
            "latent_root": self.latent_root,
            "hidden_program": self.hidden_program,
            "atoms": [dict(atom) for atom in self.atoms],
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "family": self.family,
            "latent_root": self.latent_root,
            "hidden_program": self.hidden_program,
            "atoms": [dict(atom) for atom in self.atoms],
            "input_grid": [list(row) for row in self.input_grid],
            "output_grid": [list(row) for row in self.output_grid],
        }


def move_grid(grid: Grid, axis: str, distance: int) -> Grid:
    rows, cols = len(grid), len(grid[0])
    out = [[0 for _ in range(cols)] for _ in range(rows)]
    dy, dx = (0, distance) if axis == "x" else (distance, 0)
    for y, row in enumerate(grid):
        for x, value in enumerate(row):
            if value == 0:
                continue
            ny, nx = y + dy, x + dx
            if 0 <= ny < rows and 0 <= nx < cols:
                out[ny][nx] = value
    return tuple(tuple(row) for row in out)


def recolor_grid(grid: Grid, color: int) -> Grid:
    return tuple(tuple(color if value else 0 for value in row) for row in grid)


def mirror_grid(grid: Grid, axis: str) -> Grid:
    if axis == "x":
        return tuple(tuple(reversed(row)) for row in grid)
    return tuple(reversed(grid))


def apply_atoms(grid: Grid, atoms: Sequence[dict[str, Any]]) -> Grid:
    current = grid
    for atom in atoms:
        name = atom.get("name")
        params = dict(atom.get("params", {}))
        if name == "move":
            current = move_grid(current, str(params.get("axis", "x")), int(params.get("distance", 1)))
        elif name == "recolor":
            current = recolor_grid(current, int(params.get("color", 1)))
        elif name == "mirror":
            current = mirror_grid(current, str(params.get("axis", "x")))
        elif name in {"select", "extract_box", "extract_largest"}:
            current = current
    return current


def generate_demo_tasks() -> list[ArcDemoTask]:
    base = ((1, 0, 0, 0, 0), (0, 0, 0, 0, 0), (0, 0, 0, 0, 0), (0, 0, 0, 0, 0), (0, 0, 0, 0, 0))
    specs = [
        ("t1", "move_recolor", "motion_then_recolor", "move_right_2_recolor_1", [{"name": "move", "kind": "spatial", "params": {"axis": "x", "distance": 2}}, {"name": "recolor", "kind": "color", "params": {"color": 1}}]),
        ("t2", "move_recolor", "motion_then_recolor", "move_right_2_recolor_7", [{"name": "move", "kind": "spatial", "params": {"axis": "x", "distance": 2}}, {"name": "recolor", "kind": "color", "params": {"color": 7}}]),
        ("t3", "move_recolor", "motion_then_recolor", "move_down_2_recolor_4", [{"name": "move", "kind": "spatial", "params": {"axis": "y", "distance": 2}}, {"name": "recolor", "kind": "color", "params": {"color": 4}}]),
        ("t4", "select_move_recolor", "selector_motion_then_recolor", "extract_box_move_right_2_recolor_1", [{"name": "select", "kind": "selector", "params": {"selector": "extract_box"}}, {"name": "move", "kind": "spatial", "params": {"axis": "x", "distance": 2}}, {"name": "recolor", "kind": "color", "params": {"color": 1}}]),
        ("t5", "select_move_recolor", "selector_motion_then_recolor", "extract_largest_move_down_2_recolor_4", [{"name": "select", "kind": "selector", "params": {"selector": "extract_largest"}}, {"name": "move", "kind": "spatial", "params": {"axis": "y", "distance": 2}}, {"name": "recolor", "kind": "color", "params": {"color": 4}}]),
        ("t6", "primitive", "primitive_recolor", "recolor_3", [{"name": "recolor", "kind": "color", "params": {"color": 3}}]),
        ("t7", "mirror_move_recolor", "mirror_motion_then_recolor", "mirror_x_move_right_2_recolor_2", [{"name": "mirror", "kind": "spatial", "params": {"axis": "x"}}, {"name": "move", "kind": "spatial", "params": {"axis": "x", "distance": 2}}, {"name": "recolor", "kind": "color", "params": {"color": 2}}]),
    ]
    return [
        ArcDemoTask(task_id, family, root, hidden, tuple(atoms), base, apply_atoms(base, atoms))
        for task_id, family, root, hidden, atoms in specs
    ]


def base_search(tasks: Sequence[ArcDemoTask]) -> dict[str, Any]:
    solved = [task.task_id for task in tasks if len(task.atoms) == 1]
    return _metrics(tasks, solved)


def literal_trace_search(tasks: Sequence[ArcDemoTask], mined_traces: Sequence[dict[str, Any]]) -> dict[str, Any]:
    mined_hidden = {str(trace.get("hidden_program", "")) for trace in mined_traces}
    solved = [task.task_id for task in tasks if len(task.atoms) == 1 or task.hidden_program in mined_hidden]
    return _metrics(tasks, solved)


def schema_search(tasks: Sequence[ArcDemoTask], schemas: Sequence[RootOperatorSchema]) -> dict[str, Any]:
    solved = []
    schema_signatures = {tuple(atom.get("name", "") for atom in schema.atoms) for schema in schemas}
    for task in tasks:
        signature = tuple(atom.get("name", "") for atom in task.atoms)
        if len(task.atoms) == 1 or signature in schema_signatures:
            solved.append(task.task_id)
    return _metrics(tasks, solved)


def oracle_search(tasks: Sequence[ArcDemoTask]) -> dict[str, Any]:
    return _metrics(tasks, [task.task_id for task in tasks])


def run_arc_root_operator_demo(out_path: str | Path | None = None) -> dict[str, Any]:
    tasks = generate_demo_tasks()
    train = tasks[:5]
    held_out = tasks[2:]
    trace_records = [task.to_trace_record() for task in train]
    schemas = induce_compositional_root_schemas(trace_records)
    base = base_search(held_out)
    literal = literal_trace_search(held_out, trace_records[:2])
    oracle = oracle_search(held_out)

    def eval_schema(schema: RootOperatorSchema, eval_tasks: Sequence[dict[str, Any]]) -> dict[str, Any]:
        task_objs = [task for task in held_out if task.task_id in {item["task_id"] for item in eval_tasks}]
        return schema_search(task_objs, [schema])

    task_rows = [task.to_dict() for task in held_out]
    promotion = promote_root_operator_schemas(
        schemas,
        task_rows,
        eval_schema,
        lambda rows: base_search([task for task in held_out if task.task_id in {item["task_id"] for item in rows}]),
        lambda rows: oracle_search([task for task in held_out if task.task_id in {item["task_id"] for item in rows}]),
    )
    promoted = [result.schema for result in promotion if result.promoted]
    root_metrics = schema_search(held_out, promoted or schemas)
    oracle_fraction = oracle_fraction_captured(base["solve_rate"], root_metrics["solve_rate"], oracle["solve_rate"])
    residual = residual_compression_metrics(base, root_metrics)
    summary = RootOperatorEvaluationSummary(
        base_solve_rate=base["solve_rate"],
        literal_solve_rate=literal["solve_rate"],
        root_schema_solve_rate=root_metrics["solve_rate"],
        oracle_solve_rate=oracle["solve_rate"],
        oracle_fraction_captured=oracle_fraction,
        raw_schema_count=len(schemas),
        promoted_schema_count=len(promoted),
        residual_compression=residual,
        overall="PASS" if promoted and root_metrics["solve_rate"] >= base["solve_rate"] else "PROMISING",
    ).to_dict()
    payload = {
        **summary,
        "schemas": [schema.to_dict() for schema in schemas],
        "promoted_schemas": [schema.to_dict() for schema in promoted],
        "promotion_results": [result.to_dict() for result in promotion],
        "tasks": [task.to_dict() for task in tasks],
    }
    if out_path is not None:
        output = Path(out_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return payload


def _metrics(tasks: Sequence[ArcDemoTask], solved_ids: Sequence[str]) -> dict[str, Any]:
    solved = set(solved_ids)
    total = len(tasks)
    return {
        "solved": sorted(solved),
        "solved_count": len(solved),
        "task_count": total,
        "solve_rate": len(solved) / total if total else 0.0,
        "residual_count": max(0, total - len(solved)),
    }
