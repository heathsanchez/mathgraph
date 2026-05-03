"""Deterministic hashing helpers for MathGraph audit records."""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from enum import Enum
from hashlib import sha256
from pathlib import Path
from typing import Any


def _json_safe(obj: Any) -> Any:
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    if isinstance(obj, Enum):
        return obj.value
    if is_dataclass(obj):
        return asdict(obj)
    if isinstance(obj, dict):
        return {str(key): _json_safe(value) for key, value in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_json_safe(value) for value in obj]
    return obj


def canonical_json(obj: Any) -> str:
    """Serialize an object into deterministic, compact JSON."""

    return json.dumps(_json_safe(obj), sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_hex(data: Any) -> str:
    if isinstance(data, bytes):
        payload = data
    elif isinstance(data, str):
        payload = data.encode("utf-8")
    else:
        payload = canonical_json(data).encode("utf-8")
    return sha256(payload).hexdigest()


def short_hash(data: Any, n: int = 16) -> str:
    if n <= 0:
        raise ValueError("n must be positive")
    return sha256_hex(data)[:n]


def content_id(prefix: str, payload: Any, n: int = 24) -> str:
    return f"{prefix}_{short_hash(payload, n=n)}"


def hash_file(path: str | Path) -> str:
    digest = sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def hash_trace(trace_or_dict: Any) -> str:
    data = trace_or_dict.to_dict() if hasattr(trace_or_dict, "to_dict") else trace_or_dict
    return sha256_hex(data)


def hash_certificate(certificate_or_dict: Any) -> str:
    data = (
        certificate_or_dict.to_dict()
        if hasattr(certificate_or_dict, "to_dict")
        else certificate_or_dict
    )
    return sha256_hex(data)


# Backward-compatible aliases used by early v0.1 tests and examples.
stable_json_dumps = canonical_json
sha256_text = sha256_hex
sha256_json = sha256_hex
