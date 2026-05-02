import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mathgraph import Kernel


def main() -> None:
    kernel = Kernel()
    kernel.add_equation("assoc", "(x * y) * z = x * (y * z)")
    print(kernel.store.list_nodes("equation"))


if __name__ == "__main__":
    main()
