"""Small serializable certificate records for official Stage 2 validation."""

from __future__ import annotations

import json


class FiniteMagmaCertificate:
    def __init__(
        self,
        eq1_id=None,
        eq2_id=None,
        equation1="",
        equation2="",
        n=0,
        table=None,
        witness=None,
        source_holds_verified_python=False,
        target_fails_verified_python=False,
        family="unknown",
        method="finite_table_search",
        certificate_hash=None,
    ):
        self.eq1_id = eq1_id
        self.eq2_id = eq2_id
        self.equation1 = equation1
        self.equation2 = equation2
        self.n = int(n)
        self.table = [list(row) for row in (table or [])]
        self.witness = dict(witness or {})
        self.source_holds_verified_python = bool(source_holds_verified_python)
        self.target_fails_verified_python = bool(target_fails_verified_python)
        self.family = family or "unknown"
        self.method = method or "finite_table_search"
        self.certificate_hash = certificate_hash or stable_certificate_hash(self.to_dict(include_hash=False))

    def to_dict(self, include_hash=True):
        out = {
            "eq1_id": self.eq1_id,
            "eq2_id": self.eq2_id,
            "equation1": self.equation1,
            "equation2": self.equation2,
            "n": self.n,
            "table": self.table,
            "witness": self.witness,
            "source_holds_verified_python": self.source_holds_verified_python,
            "target_fails_verified_python": self.target_fails_verified_python,
            "family": self.family,
            "method": self.method,
        }
        if include_hash:
            out["certificate_hash"] = self.certificate_hash
        return out

    @classmethod
    def from_dict(cls, data):
        data = dict(data or {})
        if "n" not in data and "carrier_size" in data:
            data["n"] = data.get("carrier_size")
        if "witness" not in data and "violating_assignment" in data:
            data["witness"] = data.get("violating_assignment")
        allowed = {
            "eq1_id",
            "eq2_id",
            "equation1",
            "equation2",
            "n",
            "table",
            "witness",
            "source_holds_verified_python",
            "target_fails_verified_python",
            "family",
            "method",
            "certificate_hash",
        }
        return cls(**{k: v for k, v in data.items() if k in allowed})


class LeanJudgeResult:
    def __init__(
        self,
        eq1_id=None,
        eq2_id=None,
        verdict="false",
        status="unknown",
        stdout="",
        stderr="",
        code_hash="",
        elapsed_s=0.0,
    ):
        self.eq1_id = eq1_id
        self.eq2_id = eq2_id
        self.verdict = verdict
        self.status = status
        self.stdout = stdout
        self.stderr = stderr
        self.code_hash = code_hash
        self.elapsed_s = float(elapsed_s or 0.0)

    def to_dict(self):
        return {
            "eq1_id": self.eq1_id,
            "eq2_id": self.eq2_id,
            "verdict": self.verdict,
            "status": self.status,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "code_hash": self.code_hash,
            "elapsed_s": self.elapsed_s,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(**dict(data or {}))


def stable_certificate_hash(payload):
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    h = 2166136261
    for ch in text:
        h ^= ord(ch)
        h = (h * 16777619) & 0xFFFFFFFF
    return "%08x" % h
