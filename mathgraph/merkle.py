"""Small Merkle tree helpers for trace integrity checks."""

from __future__ import annotations

from typing import Any

from mathgraph.hashing import sha256_hex


def _combine(left: str, right: str) -> str:
    return sha256_hex(f"{left}{right}")


def _leaf_hash(item: Any) -> str:
    return item if isinstance(item, str) and len(item) == 64 else sha256_hex(item)


def _leaf_hashes(items: list[Any]) -> list[str]:
    return [_leaf_hash(item) for item in items]


def merkle_root(items: list[Any]) -> str:
    """Return a deterministic Merkle root.

    The empty tree root is the SHA-256 hash of the canonical empty list.
    """

    if not items:
        return sha256_hex([])

    level = _leaf_hashes(items)
    while len(level) > 1:
        next_level: list[str] = []
        for i in range(0, len(level), 2):
            left = level[i]
            right = level[i + 1] if i + 1 < len(level) else left
            next_level.append(_combine(left, right))
        level = next_level
    return level[0]


def merkle_proof(items: list[Any], index: int) -> list[dict[str, str]]:
    if index < 0 or index >= len(items):
        raise IndexError("merkle proof index out of range")

    proof: list[dict[str, str]] = []
    level = _leaf_hashes(items)
    current = index
    while len(level) > 1:
        sibling_index = current + 1 if current % 2 == 0 else current - 1
        if sibling_index >= len(level):
            sibling_index = current
        side = "right" if current % 2 == 0 else "left"
        proof.append({"side": side, "hash": level[sibling_index]})

        next_level: list[str] = []
        for i in range(0, len(level), 2):
            left = level[i]
            right = level[i + 1] if i + 1 < len(level) else left
            next_level.append(_combine(left, right))
        current //= 2
        level = next_level
    return proof


def verify_merkle_proof(leaf: Any, proof: list[dict[str, str]], root: str | None) -> bool:
    if root is None:
        return False

    current = _leaf_hash(leaf)
    for step in proof:
        sibling = step["hash"]
        if step["side"] == "left":
            current = _combine(sibling, current)
        elif step["side"] == "right":
            current = _combine(current, sibling)
        else:
            return False
    return current == root
