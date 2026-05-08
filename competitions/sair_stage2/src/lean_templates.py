"""Lean templates for official Stage 2 finite countermodel certificates."""

from __future__ import annotations

import json

try:
    from .certificate_models import FiniteMagmaCertificate
except ImportError:  # standalone build
    pass


def render_false_countermodel_lean(cert, contract=None):
    """Render official-harness Lean code for a finite countermodel.

    The official Stage 2 judge provides ``JudgeProblem`` with the concrete
    implication goal. For FALSE certificates the accepted pattern is to provide
    a finite magma witness and let ``decideFin!`` discharge the finite check.

    Important: the official proof policy rejects extra top-level declarations.
    Therefore the candidate magma must be introduced as a local ``let`` inside
    ``submission`` rather than as ``def mg_false_*``.
    """

    if isinstance(cert, dict):
        cert = FiniteMagmaCertificate.from_dict(cert)
    if cert is None:
        return ""

    n = int(cert.n)
    if n < 2:
        return ""
    if len(cert.table) != n or any(len(row) != n for row in cert.table):
        return ""
    if any(int(x) < 0 or int(x) >= n for row in cert.table for x in row):
        return ""

    table = [[int(x) for x in row] for row in cert.table]
    table_s = json.dumps(table, separators=(",", ":"))

    return (
        "import JudgeProblem\n"
        "import JudgeDecide.DecideBang\n"
        "import JudgeFinOp.MemoFinOp\n"
        "open MemoFinOp\n\n"
        "def submission : Goal := by\n"
        f"  let candidateMagma : Magma (Fin {n}) := {{\n"
        f"    op := finOpTable \"{table_s}\"\n"
        "  }\n"
        f"  refine ⟨Fin {n}, candidateMagma, ?_⟩\n"
        "  decideFin!\n"
    )
