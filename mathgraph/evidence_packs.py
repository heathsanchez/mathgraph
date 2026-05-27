"""Frozen evidence-pack loaders and trust-boundary validation.

Evidence packs preserve empirical MathGraph runs and replay metadata.  They are
not terminal certificates by themselves.  This module intentionally validates
that pack metrics do not cross the MathGraph trust boundary: advisory scores,
route memory, classifier signals, and failed finite searches cannot promote
truth.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping


EVIDENCE_PACK_ROOT = Path(__file__).resolve().parents[1] / "examples" / "evidence_packs"

TRUST_BOUNDARY_ZERO_FIELDS: tuple[str, ...] = (
    "advisory_promoted_truth_count",
    "failed_search_promoted_true_count",
    "true_contamination_count",
    "true_contamination_max",
)

TRUST_BOUNDARY_FALSE_FIELDS: tuple[str, ...] = (
    "can_promote_truth",
    "compact_atlas_can_promote_truth",
    "route_scores_can_promote_truth",
    "root_node_score_can_promote_truth",
    "residual_score_can_promote_truth",
    "failed_finite_search_can_promote_true",
    "failed_search_can_promote_true",
)


class EvidencePackError(ValueError):
    """Raised when an evidence pack is malformed or violates trust boundaries."""


@dataclass(frozen=True)
class EvidenceArtifact:
    filename: str
    role: str = ""
    copied_to_repo: bool = False
    repo_path: str | None = None
    source_path: str | None = None
    size_bytes: int | None = None
    sha256: str | None = None
    required_for_full_replay: bool = False
    reason_not_copied: str | None = None

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "EvidenceArtifact":
        return cls(
            filename=str(data.get("filename", "")),
            role=str(data.get("role", "")),
            copied_to_repo=bool(data.get("copied_to_repo", False)),
            repo_path=str(data["repo_path"]) if data.get("repo_path") else None,
            source_path=str(data["source_path"]) if data.get("source_path") else None,
            size_bytes=_optional_int(data.get("size_bytes")),
            sha256=str(data["sha256"]) if data.get("sha256") else None,
            required_for_full_replay=bool(data.get("required_for_full_replay", False)),
            reason_not_copied=str(data["reason_not_copied"]) if data.get("reason_not_copied") else None,
        )


@dataclass(frozen=True)
class EvidencePack:
    pack_id: str
    directory: Path
    metrics: dict[str, Any]
    manifest: dict[str, Any] = field(default_factory=dict)

    @property
    def artifacts(self) -> tuple[EvidenceArtifact, ...]:
        return tuple(EvidenceArtifact.from_dict(row) for row in self.manifest.get("artifacts", []) or [])

    @property
    def trust_boundary(self) -> dict[str, Any]:
        raw = dict(self.metrics.get("trust_boundary", {}) or {})
        raw.update(dict(self.manifest.get("trust_boundary", {}) or {}))
        return raw

    def require_fields(self, fields: tuple[str, ...] | list[str]) -> None:
        missing = [field for field in fields if field not in self.metrics]
        if missing:
            raise EvidencePackError(f"{self.pack_id} missing required metric fields: {', '.join(missing)}")

    def assert_trust_boundary(self) -> None:
        assert_trust_boundary(self.metrics, self.pack_id)


def resolve_evidence_pack_dir(name_or_path: str | Path) -> Path:
    raw = Path(name_or_path)
    if raw.exists():
        return raw if raw.is_dir() else raw.parent
    return EVIDENCE_PACK_ROOT / str(name_or_path)


def load_evidence_pack(name_or_path: str | Path, *, required_fields: tuple[str, ...] | list[str] = ()) -> EvidencePack:
    directory = resolve_evidence_pack_dir(name_or_path)
    metrics_path = directory / "metrics.json"
    if not metrics_path.exists():
        metrics_path = directory / "summary.json"
    if not metrics_path.exists():
        raise FileNotFoundError(f"evidence metrics not found under {directory}")
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    manifest_path = directory / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    pack = EvidencePack(
        pack_id=str(metrics.get("pack_id") or manifest.get("pack_id") or directory.name),
        directory=directory,
        metrics=dict(metrics),
        manifest=dict(manifest),
    )
    pack.require_fields(tuple(required_fields))
    pack.assert_trust_boundary()
    return pack


def list_evidence_packs(root: str | Path = EVIDENCE_PACK_ROOT) -> tuple[str, ...]:
    path = Path(root)
    if not path.exists():
        return ()
    return tuple(sorted(child.name for child in path.iterdir() if child.is_dir()))


def assert_trust_boundary(metrics: Mapping[str, Any], pack_id: str = "evidence_pack") -> None:
    boundary = dict(metrics.get("trust_boundary", {}) or {})
    combined: dict[str, Any] = dict(metrics)
    combined.update(boundary)

    for field in TRUST_BOUNDARY_ZERO_FIELDS:
        if field in combined and _to_int(combined[field]) != 0:
            raise EvidencePackError(f"{pack_id} violates trust boundary: {field}={combined[field]}")

    for field in TRUST_BOUNDARY_FALSE_FIELDS:
        if field in combined and bool(combined[field]) is not False:
            raise EvidencePackError(f"{pack_id} violates trust boundary: {field}={combined[field]}")

    if bool(combined.get("advisory_boundary_ok", True)) is False:
        raise EvidencePackError(f"{pack_id} violates trust boundary: advisory_boundary_ok is false")
    if bool(combined.get("strict_admission_passed", True)) is False:
        raise EvidencePackError(f"{pack_id} violates trust boundary: strict_admission_passed is false")


def _to_int(value: Any) -> int:
    if value is None or value == "":
        return 0
    if isinstance(value, bool):
        return int(value)
    return int(float(value))


def _optional_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    return _to_int(value)
