#!/usr/bin/env bash
set -euo pipefail

gh release create finite-htilt-theorem-tower-v1 \
  --repo metalogiclabs/mathgraph \
  --title "Finite H-Tilt Survivor Law: Verified Theorem Tower v1" \
  --notes-file releases/finite_htilt_theorem_tower_v1/GITHUB_RELEASE_BODY.md
