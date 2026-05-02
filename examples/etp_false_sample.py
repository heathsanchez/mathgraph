import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from adapters.finite_magma_adapter import FiniteMagma
from mathgraph import parse_equation


def main() -> None:
    conclusion = parse_equation("x * x = x")
    magma = FiniteMagma.from_table([[0, 1], [1, 0]], name="xor_magma")
    print(magma.counterexample_to_equation(conclusion))


if __name__ == "__main__":
    main()
