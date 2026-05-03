"""Load and inspect a MathGraph trace corpus exported from SAIR Stage 2."""

from __future__ import annotations

import os

from mathgraph import CertificateCorpus, TerminalForm


def main() -> None:
    path = os.environ.get("MATHGRAPH_TRACES_JSON")
    if not path:
        print("Set MATHGRAPH_TRACES_JSON to a traces.json export path.")
        return

    corpus = CertificateCorpus.from_json(path)
    summary = corpus.summary()
    countermodels = corpus.query(terminal_form=TerminalForm.FINITE_COUNTERMODEL)
    proofs = corpus.query(terminal_form=TerminalForm.VERIFIED_PROOF)

    print(summary)
    print("finite_countermodels:", len(countermodels))
    print("verified_proofs:", len(proofs))

    for trace in corpus.query(limit=5):
        print(
            {
                "terminal_form": trace.terminal_form.value,
                "verification_status": trace.verification_status.value,
                "claim": trace.claim,
            }
        )


if __name__ == "__main__":
    main()
