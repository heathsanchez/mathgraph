# Root Node Persistent Filtration v16.3

Canonical evidence pack:
`examples/evidence_packs/root_node_persistent_filtration_v16_3/`

## Metrics

- lawbook rows: `288`
- promoted root nodes: `164`
- watchlist root nodes: `64`
- shadow clusters: `242`
- promoted decisions: `164`
- watchlist decisions: `64`
- shadow duplicates: `46`
- insufficient independent filtration: `14`

## Root Node Meaning

A root node is a persistent, load-bearing continuation root. It is not just a
cluster, a high-support feature, or a path concentrator.

The evidence schema requires:

- `path_concentration_score`
- `load_bearing_score`
- `persistence_score`
- `constructor_yield`
- `obstruction_yield`
- `lawbook_compression_gain`
- `null_lift`
- `shadow_duplicate_discount`
- `effective_filtration_count`

Path concentration is diagnostic. Persistence, null resistance, load-bearing
coverage, and downstream certificate or obstruction pressure are what make a
root node meaningful.

## Trust Boundary

Root nodes prioritize continuation. They do not prove TRUE claims, emit FALSE
certificates, or turn failed searches into terminal forms.
