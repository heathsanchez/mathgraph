# Root Operator Induction

Root Operator Induction is the layer that lifts verified trace survivals into
typed, parameterized constructor candidates.

Literal trace macros are useful, but they are surface survivals. The deeper
object is a root operator schema: a reusable continuation kernel such as:

```text
move(axis, distance=2) ; recolor(color)
select(selector) ; move(axis, distance=2) ; recolor(color)
```

## Why Literal Macros Are Insufficient

Literal traces such as `move_right_2|recolor_1` and
`move_down_2|recolor_4` solve only the examples they exactly match. A root
operator schema anti-unifies those traces into parameters: axis, distance,
color, selector, and operator alternatives.

## Anti-Unification

`mathgraph.root_operator_induction` accepts generic trace records:

```json
{
  "trace_id": "t1",
  "family": "move_recolor",
  "latent_root": "motion_then_recolor",
  "hidden_program": "move_right_2_recolor_7",
  "atoms": [
    {"name": "move", "kind": "spatial", "params": {"axis": "x", "distance": 2}},
    {"name": "recolor", "kind": "color", "params": {"color": 7}}
  ]
}
```

The anti-unifier groups compatible traces, lifts varying values into typed
parameters, scores compression, and emits advisory `RootOperatorSchema` records.

## Promotion

`mathgraph.root_operator_promotion` promotes schemas as constructor hints only
when they improve held-out task performance, capture oracle gap, or compress
residuals. Promotion does not create a proof, countermodel, truth value, or
terminal certificate.

## Offline v1 Result

The motivating offline ARC/program-synthesis experiment reported:

- base_only solve rate: `0.323810`
- base_plus_random_macros solve rate: `0.561905`
- base_plus_literal_mined solve rate: `0.628571`
- base_plus_root_operator_schemas solve rate: `0.723810`
- base_plus_literal_and_root_schemas solve rate: `0.723810`
- base_plus_oracle solve rate: `0.980952`
- oracle gap: `0.657143`
- oracle fraction captured: `0.608696`
- residual count compressed: `71 → 29`
- residual family count compressed: `11 → 6`
- residual latent root count compressed: `6 → 5`
- residual hidden program count compressed: `55 → 23`
- promoted schema count: `22`

## Verifier Boundary

Root operator schemas are advisory constructor candidates. They can guide proof
search, countermodel search, program synthesis, route scheduling, residual
splitting, and Reason Atlas updates. They cannot produce `VERIFIED_PROOF`,
`REFUTATION_CERTIFICATE`, `TRUE`, or `FALSE` without an independent verifier,
trusted importer, finite checker, or chain audit.

## Connections

Root operators connect:

- Reason Atlas contact promotion
- Root Node Atlas construction
- constructor discovery
- residual compression
- abstraction formation law
- MathGraph as a generative verification kernel

The intended learning loop is:

```text
verified traces
→ anti-unified typed schemas
→ reusable root operators
→ residual compression
→ oracle-gap closure
```

## Smoke Run

```bash
python scripts/run_root_operator_induction_smoke.py
```

The script writes:

```text
/tmp/mathgraph_root_operator_induction_smoke/root_operator_induction_smoke.json
```

## Future Work

- second-order root operators
- schema composition algebra
- proof-constructor root induction
- finite countermodel root induction
- Lawbook persistence of promoted schemas
- H-tilt scheduling over schema families
- learned schema proposal models
- Lean/Coq/Isabelle trace anti-unification
