import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from adapters.finite_magma_adapter import FiniteMagma
from mathgraph import Kernel
from mathgraph.ledger import JsonlLedger


def main() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        ledger = JsonlLedger(Path(tmpdir) / "mathgraph_demo.jsonl")
        kernel = Kernel(ledger=ledger)

        kernel.prove("x = x", "x * x = x")
        kernel.prove("x * y = y * x", "a * b = b * a")

        obstruction_kernel = Kernel(
            finite_magmas=[FiniteMagma.from_table([[0]], name="trivial_magma")],
            ledger=ledger,
        )
        obstruction_kernel.prove("(x * y) * z = x * (y * z)", "x * y = y * x")

        for trace in ledger.load_all():
            print(trace.terminal_form.value)


if __name__ == "__main__":
    main()
