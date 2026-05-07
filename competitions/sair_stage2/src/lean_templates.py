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
    implication goal. For false certificates the accepted pattern is to provide
    a finite magma witness and let ``decideFin!`` discharge the finite check.
    """

    if isinstance(cert, dict):
        cert = FiniteMagmaCertificate.from_dict(cert)
    n = int(cert.n)
    table_s = json.dumps(cert.table, separators=(",", ":"))
    local_name = "mg_false_" + str(cert.eq1_id) + "_" + str(cert.eq2_id) + "_" + cert.certificate_hash[:8]
    return (
        "import JudgeProblem\n"
        "import JudgeDecide.DecideBang\n"
        "import JudgeFinOp.MemoFinOp\n"
        "open MemoFinOp\n\n"
        f"def {local_name} : Magma (Fin {n}) := {{\n"
        f"  op := finOpTable \"{table_s}\"\n"
        "}\n\n"
        "def submission : Goal := by\n"
        f"  refine ⟨Fin {n}, {local_name}, ?_⟩\n"
        "  decideFin!\n"
    )

