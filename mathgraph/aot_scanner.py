"""Advisory scanner for AOT-style Isabelle theory repositories."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from mathgraph.hashing import content_id
from mathgraph.semantic_embeddings import ArtifactRisk
from mathgraph.theory_registry import (
    InferenceRule,
    ProofMethod,
    ProofMethodKind,
    TheoryDeclaration,
    TheoryDeclarationKind,
)
from mathgraph.trust import ProvenanceType, TrustLevel


DECL_PATTERNS: tuple[tuple[re.Pattern[str], TheoryDeclarationKind], ...] = (
    (re.compile(r"\btheory\s+([A-Za-z0-9_'.-]+)"), TheoryDeclarationKind.SYNTAX_DECLARATION),
    (re.compile(r"\bAOT_theorem\s+([A-Za-z0-9_'.-]+)"), TheoryDeclarationKind.THEOREM),
    (re.compile(r"\bAOT_act_theorem\s+([A-Za-z0-9_'.-]+)"), TheoryDeclarationKind.THEOREM),
    (re.compile(r"\bAOT_lemma\s+([A-Za-z0-9_'.-]+)"), TheoryDeclarationKind.LEMMA),
    (re.compile(r"\bAOT_axiom\s+([A-Za-z0-9_'.-]+)"), TheoryDeclarationKind.AXIOM),
    (re.compile(r"\bAOT_define\s+([A-Za-z0-9_'.-]+)"), TheoryDeclarationKind.DEFINITION),
    (re.compile(r"\bAOT_world\s+([A-Za-z0-9_'.-]+)"), TheoryDeclarationKind.WORLD_DECLARATION),
)


@dataclass(frozen=True)
class AOTScannedDeclaration:
    name: str
    declaration_kind: TheoryDeclarationKind
    source_file: str
    source_line: int
    raw_text: str
    theory_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "declaration_kind": self.declaration_kind.value,
            "source_file": self.source_file,
            "source_line": self.source_line,
            "raw_text": self.raw_text,
            "theory_id": self.theory_id,
            "trust_level": TrustLevel.ADVISORY_ROUTE.value,
            "provenance_type": ProvenanceType.IMPORTED.value,
        }

    def to_theory_declaration(
        self,
        domain_kernel_id: str = "aot",
        formal_world_id: str = "formal_world_aot_precedent",
    ) -> TheoryDeclaration:
        payload = self.to_dict()
        return TheoryDeclaration(
            declaration_id=content_id("aot_declaration", payload),
            domain_kernel_id=domain_kernel_id,
            formal_world_id=formal_world_id,
            theory_id=self.theory_id or Path(self.source_file).stem,
            declaration_kind=self.declaration_kind,
            name=self.name,
            statement=self.raw_text,
            source_file=self.source_file,
            source_line=self.source_line,
            trust_level=TrustLevel.ADVISORY_ROUTE,
            provenance_type=ProvenanceType.IMPORTED,
            host_logic="Isabelle/HOL",
            object_logic="AOT / second-order modal object theory",
            object_theory_verified=False,
            host_embedding_verified=False,
            artifact_risk=ArtifactRisk.UNKNOWN,
            payload={"scanner": "aot_scanner_v1", "advisory_only": True},
        )


@dataclass(frozen=True)
class AOTScanResult:
    aot_dir: str
    files_scanned: int
    declarations: list[AOTScannedDeclaration] = field(default_factory=list)
    proof_methods: list[ProofMethod] = field(default_factory=list)
    inference_rules: list[InferenceRule] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def summary(self) -> dict[str, Any]:
        counts: dict[str, int] = {}
        for decl in self.declarations:
            counts[decl.declaration_kind.value] = counts.get(decl.declaration_kind.value, 0) + 1
        return {
            "aot_dir": self.aot_dir,
            "files_scanned": self.files_scanned,
            "declaration_count": len(self.declarations),
            "proof_method_count": len(self.proof_methods),
            "inference_rule_count": len(self.inference_rules),
            "by_declaration_kind": counts,
            "warnings": list(self.warnings),
            "truth_boundary": "AOT scanner imports advisory metadata only; it does not run Isabelle.",
        }


def scan_aot_repository(aot_dir: str | Path) -> AOTScanResult:
    root = Path(aot_dir)
    if not root.exists():
        return AOTScanResult(str(root), 0, warnings=[f"AOT directory does not exist: {root}"])
    declarations: list[AOTScannedDeclaration] = []
    proof_methods: list[ProofMethod] = []
    inference_rules: list[InferenceRule] = []
    warnings: list[str] = []
    files = [path for path in sorted(root.rglob("*")) if path.suffix in {".thy", ".ML"}]
    for path in files:
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError as exc:
            warnings.append(f"Could not read {path}: {exc}")
            continue
        current_theory = path.stem
        for line_no, line in enumerate(lines, start=1):
            stripped = line.strip()
            for pattern, kind in DECL_PATTERNS:
                match = pattern.search(stripped)
                if not match:
                    continue
                name = match.group(1)
                if kind is TheoryDeclarationKind.SYNTAX_DECLARATION:
                    current_theory = name
                declarations.append(
                    AOTScannedDeclaration(
                        name=name,
                        declaration_kind=kind,
                        source_file=str(path),
                        source_line=line_no,
                        raw_text=stripped,
                        theory_id=current_theory,
                    )
                )
            if "named_theorems" in stripped:
                proof_methods.append(_proof_method(path, line_no, current_theory, "named_theorems", stripped))
            if path.suffix == ".ML" and ("Outer_Syntax.command" in stripped or "Method.setup" in stripped):
                proof_methods.append(_proof_method(path, line_no, current_theory, "ML_command", stripped))
            if "intro" in stripped or "elim" in stripped or "simp" in stripped:
                if "AOT_" in stripped or "named_theorems" in stripped:
                    inference_rules.append(_inference_rule(path, line_no, current_theory, stripped))
    return AOTScanResult(
        aot_dir=str(root),
        files_scanned=len(files),
        declarations=declarations,
        proof_methods=proof_methods,
        inference_rules=inference_rules,
        warnings=warnings,
    )


def _proof_method(path: Path, line_no: int, theory_id: str, name: str, raw: str) -> ProofMethod:
    return ProofMethod(
        proof_method_id=content_id("aot_proof_method", {"path": str(path), "line": line_no, "raw": raw}),
        domain_kernel_id="aot",
        formal_world_id="formal_world_aot_precedent",
        theory_id=theory_id,
        name=name,
        method_kind=ProofMethodKind.CUSTOM_METHOD,
        source_file=str(path),
        source_line=line_no,
        payload={"raw_text": raw, "advisory_only": True},
    )


def _inference_rule(path: Path, line_no: int, theory_id: str, raw: str) -> InferenceRule:
    return InferenceRule(
        inference_rule_id=content_id("aot_inference_rule", {"path": str(path), "line": line_no, "raw": raw}),
        domain_kernel_id="aot",
        formal_world_id="formal_world_aot_precedent",
        theory_id=theory_id,
        name="AOT advisory rule",
        rule_kind=ProofMethodKind.UNKNOWN,
        statement=raw,
        source_file=str(path),
        source_line=line_no,
        payload={"scanner": "aot_scanner_v1", "advisory_only": True},
    )
