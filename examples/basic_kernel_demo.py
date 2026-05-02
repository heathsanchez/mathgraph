import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from adapters.finite_magma_adapter import FiniteMagma
from mathgraph import Kernel


def main() -> None:
    kernel = Kernel()

    countermodel = kernel.prove("x = x", "x * x = x")
    print("finite countermodel")
    print(countermodel.terminal_form.value)
    print(countermodel.certificate.payload["model"]["assignment"])

    structural_proof = kernel.prove("x * y = y * x", "a * b = b * a")
    print("structural proof")
    print(structural_proof.terminal_form.value)
    print(structural_proof.certificate.payload)

    obstruction_kernel = Kernel(finite_magmas=[FiniteMagma.from_table([[0]], name="trivial_magma")])
    obstruction = obstruction_kernel.prove("(x * y) * z = x * (y * z)", "x * y = y * x")
    print("named obstruction")
    print(obstruction.terminal_form.value)
    print(obstruction.obstruction.payload)


if __name__ == "__main__":
    main()
