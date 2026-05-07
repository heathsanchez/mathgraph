import json
import subprocess
import sys

from mathgraph.artifact_importers import load_v167_root_nodes


def test_load_v167_root_nodes_from_json(tmp_path):
    path = tmp_path / "roots.json"
    path.write_text(
        json.dumps([{"root_node_id": "r1", "canonical_name": "left_projection_n2"}]),
        encoding="utf-8",
    )
    roots = load_v167_root_nodes(path)
    assert roots[0].root_node_id == "r1"


def test_consolidate_root_atlas_cli_tiny_fixture(tmp_path):
    roots_path = tmp_path / "roots.json"
    roots_path.write_text(
        json.dumps(
            [
                {
                    "root_node_id": "r1",
                    "canonical_name": "left_projection_n2",
                    "table_motif": "projection_left",
                    "rows": 2,
                }
            ]
        ),
        encoding="utf-8",
    )
    out_dir = tmp_path / "out"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/consolidate_root_atlas.py",
            "--roots-json",
            str(roots_path),
            "--out-dir",
            str(out_dir),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    summary = json.loads(result.stdout)
    assert summary["canonical_root_count"] == 1
    assert (out_dir / "canonical_root_nodes.json").exists()
