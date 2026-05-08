# Shadow Collapse

Many candidate roots can be aliases or shadows of the same deeper support
pillar. Shadow collapse preserves those candidates while assigning full
load-bearing credit to a stable canonical root.

Candidate roots may be shadows when they share:

- evidence rows or SAT pairs
- table motifs
- witness schemas
- source bursts
- target-demand signatures
- route behavior
- obstruction surfaces
- similar root keys or canonical names

`mathgraph.root_shadow_collapse` computes overlap links, chooses canonical roots
by load-bearing score, SAT support, residual compression, and stable ID order,
and emits `RootAlias`-compatible records.

Shadows are not deleted. They are preserved as aliases and evidence. This keeps
the history auditable while preventing duplicate roots from receiving duplicate
load-bearing credit.

Shadow collapse is advisory and does not change the terminal truth boundary.
