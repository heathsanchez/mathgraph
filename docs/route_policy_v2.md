# Route Policy v2

Route Policy v2 converts replay signals into advisory policy cards that can
guide future scheduling and root-constructor lab runs.

```text
trace → replay → route policy → scheduler hint → constructor attempt → verifier → trace
```

Replay is memory. Route policy is learned pressure. H-tilt priority is the
scheduler's taste for lawful continuation. None of these are proof.

## Policy Cards

Each card records a route key, root label, constructor family, replay counts,
certificate yield, near-miss rate, residual rate, and the pressure components
used to compute `htilt_priority`.

## Pressure Components

**Exploitation pressure**
: certificate yield plus promoted-certificate rate.

**Exploration pressure**
: high near-miss routes and positive residual-compression deltas.

**Obstruction pressure**
: repeated structured failures or residual pressure, especially when replay
  recommended conversion to obstruction pressure.

**H-tilt priority**
: a sigmoid over route strength, exploitation pressure, exploration pressure,
  obstruction pressure, and residual penalty.

## Advisory Boundary

Route policy does not verify or refute claims. It does not promote roots,
certificates, or obstructions. The verifier/importer boundary still decides all
terminal certificates.

## Downstream Residual Atlas

Residual Atlas v1 consumes Route Policy v2 cards as pressure signals. The atlas
uses `htilt_priority` to decide which unresolved membranes look ready for
another attempt, which look saturated, and which should become obstruction or
representation-shift pressure.

Frontier Builder v2 then turns those atlas cases into prioritized task proposals
for the next episode.
