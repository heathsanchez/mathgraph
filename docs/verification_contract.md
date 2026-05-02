# Verification Contract

Every accepted `Certificate` must include:

- a `TerminalForm`
- a non-empty claim string
- payload fields required by that terminal form

Required payload keys:

- `VERIFIED_PROOF`: `proof_id`
- `FINITE_COUNTERMODEL`: `model`
- `NAMED_OBSTRUCTION`: `name`

`Kernel.prove()` returns a trace with `claim`, `routes_tried`,
`terminal_form`, `verification_status`, `certificate` or `obstruction`, and
`verify()`.

Obstructions must never be treated as verified proofs. They record that the
available routes did not produce a proof or finite countermodel.
