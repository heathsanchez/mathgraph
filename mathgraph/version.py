"""Release metadata for MathGraph."""
from __future__ import annotations

__version__ = "0.1.0rc1"
__release_stage__ = "release-candidate"
__release_name__ = "MathGraph v0.1 RC1"
__release_summary__ = "Generative verification kernel with public proof-library demo and strict verifier boundary."
__release_date__ = None


def get_version_info() -> dict[str, str | None]:
    return {
        "version": __version__,
        "release_stage": __release_stage__,
        "release_name": __release_name__,
        "release_summary": __release_summary__,
        "release_date": __release_date__,
    }
