import json
import subprocess
import sys


def test_build_proof_atlas_cli_outputs_json_and_db(tmp_path):
    csv_path = tmp_path / "true_proofs.csv"
    csv_path.write_text(
        "source_idx,target_idx,source,target,proof_route,source_basin,target_basin,verification_status,trust_level,provenance_type,theorem_name\n"
        "1,2,x=x,x=x,variable_identification,same,same,LEAN_VERIFIED,LEAN_VERIFIED,IMPORTED,eq1_implies_eq2\n"
        "3,4,x*y=x,x*(y*z)=x,projection_left,left_projection,collapse,IMPORTED_UNCHECKED,ADVISORY_ROUTE,IMPORTED,candidate_projection\n",
        encoding="utf-8",
    )
    out_dir = tmp_path / "atlas"
    db = tmp_path / "atlas.sqlite"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/build_proof_atlas.py",
            "--input",
            str(csv_path),
            "--out-dir",
            str(out_dir),
            "--out-db",
            str(db),
            "--emit-lean-sketches",
        ],
        check=True,
        text=True,
        capture_output=True,
    )
    assert json.loads(result.stdout)["proof_motif_count"] == 2
    assert (out_dir / "proof_motifs.json").exists()
    assert (out_dir / "lemma_candidates.json").exists()
    assert (out_dir / "lean_artifacts.json").exists()
    query = subprocess.run(
        [sys.executable, "scripts/query_lawbook.py", "--db", str(db), "--proof-motifs"],
        check=True,
        text=True,
        capture_output=True,
    )
    assert len(json.loads(query.stdout)) == 2
