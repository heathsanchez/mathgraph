"""MathGraph: a lightweight kernel for verifiable mathematical claims."""

from mathgraph.certificates import Certificate, TerminalForm, VerificationStatus
from mathgraph.corpus import CertificateCorpus
from mathgraph.equations import Equation, parse_equation
from mathgraph.hashing import (
    canonical_json,
    content_id,
    hash_certificate,
    hash_file,
    hash_trace,
    sha256_hex,
    sha256_json,
    sha256_text,
)
from mathgraph.kernel import Kernel
from mathgraph.lawbook import CertificateLawbook
from mathgraph.ledger import JsonlLedger
from mathgraph.pair_advisor import PairAdvice, advise_many, advise_pair, extract_pair_features
from mathgraph.route_instructor import (
    RouteInstruction,
    build_all_route_instructions,
    build_route_instruction,
    route_instruction_report,
)
from mathgraph.task_planner import (
    CertificateTask,
    plan_certificate_task,
    plan_many_certificate_tasks,
)
from mathgraph.terms import Term, parse_term
from mathgraph.trace import Trace

__all__ = [
    "Certificate",
    "CertificateCorpus",
    "CertificateLawbook",
    "CertificateTask",
    "Equation",
    "Kernel",
    "JsonlLedger",
    "PairAdvice",
    "canonical_json",
    "RouteInstruction",
    "build_all_route_instructions",
    "build_route_instruction",
    "advise_many",
    "advise_pair",
    "content_id",
    "extract_pair_features",
    "hash_certificate",
    "hash_file",
    "hash_trace",
    "sha256_hex",
    "sha256_json",
    "sha256_text",
    "Term",
    "TerminalForm",
    "parse_equation",
    "parse_term",
    "plan_certificate_task",
    "plan_many_certificate_tasks",
    "route_instruction_report",
    "Trace",
    "VerificationStatus",
]
