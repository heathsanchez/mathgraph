# Persistent Filtration

Persistent filtration asks whether a root candidate survives many genuinely
different cuts of the telemetry universe.

Supported filtrations include:

- source-shape filtration
- target-demand filtration
- skeleton filtration
- route filtration
- carrier-order filtration
- table-motif filtration
- witness-schema filtration
- obstruction-surface filtration
- residual-basin filtration
- SAT/UNSAT boundary filtration

A root candidate becomes stronger when it remains explanatory across these
cuts. A candidate that only survives one table motif, one source burst, or one
witness schema may still be useful, but it receives less effective filtration
credit.

The implementation in `mathgraph.persistent_filtration` computes filtration
evidence and a persistence summary. The summary rewards effective filtration
count, contrast, boundary clarity, and residual compression. It penalizes
duplicated evidence and extreme single-channel dominance.

This is advisory scoring only. It does not verify claims or promote
certificates.
