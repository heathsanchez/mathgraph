# Colab Harness Order

The Stage 2 Colab workflow now uses the official repository as the contract
source:

1. Clone MathGraph.
2. Install MathGraph dev/test dependencies.
3. Clone or update `SAIRcompetition/equational-theories-lean-stage2` with
   `official/clone_stage2_repo.py`.
4. Inspect the official contract with `official/inspect_stage2_contract.py`.
5. Build `competitions/sair_stage2/dist/solver.py`.
6. Run `official/run_official_smoke.py`.
7. Run local ETP validation/distillation if equations and matrix assets are
   present.

The generated `solver.py` remains standalone and must not import MathGraph.

