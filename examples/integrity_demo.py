import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from adapters.finite_magma_adapter import FiniteMagma
from mathgraph import Kernel
from mathgraph.ledger import JsonlLedger
from mathgraph.replay import replay_ledger


def main() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        ledger = JsonlLedger(Path(tmpdir) / "integrity_demo.jsonl")
        kernel = Kernel(ledger=ledger)

        kernel.prove("x = x", "x * x = x")
        kernel.prove("x * y = y * x", "a * b = b * a")

        obstruction_kernel = Kernel(
            finite_magmas=[FiniteMagma.from_table([[0]], name="trivial_magma")],
            ledger=ledger,
        )
        obstruction_kernel.prove("(x * y) * z = x * (y * z)", "x * y = y * x")

        summary = replay_ledger(ledger.path)
        print([trace.terminal_form.value for trace in ledger.load_all()])
        print(summary["trace_hashes"])
        print(summary["merkle_root"])
        print(summary["passed"])


if __name__ == "__main__":
    main()
