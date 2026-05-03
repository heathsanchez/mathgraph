import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from adapters.etp_adapter import load_matrix, sample_false_pairs, summarize_assets


def main() -> None:
    equations_path = os.environ.get("MATHGRAPH_EQUATIONS_PATH")
    matrix_path = os.environ.get("MATHGRAPH_MATRIX_PATH")
    if not equations_path or not matrix_path:
        print("Set MATHGRAPH_EQUATIONS_PATH and MATHGRAPH_MATRIX_PATH to sample local ETP assets.")
        return

    summary = summarize_assets(equations_path, matrix_path)
    matrix = load_matrix(matrix_path)
    print(summary)
    print(sample_false_pairs(matrix, limit=5, seed=0))


if __name__ == "__main__":
    main()
