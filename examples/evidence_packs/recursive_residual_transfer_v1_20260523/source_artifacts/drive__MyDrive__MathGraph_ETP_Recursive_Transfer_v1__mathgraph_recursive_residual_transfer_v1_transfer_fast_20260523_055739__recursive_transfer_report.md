# MathGraph / ETP Recursive Residual-Mined Memory Transfer Test v1

## Core question

Does a compact residual-mined atlas trained on one slice transfer to fresh unseen ETP FALSE pairs, across seeds, without TRUE contamination, while beating generic/random/shuffled controls?

## Summary

```json
{
  "advisory_boundary_ok": true,
  "all_gates_pass": true,
  "best_route_mean_recoveries": 11731.0,
  "elapsed_sec": 1487.2542037963867,
  "equations": 4694,
  "false_count": 13855357,
  "gates_passed": 9,
  "gates_total": 9,
  "generic_mean_recoveries": 11405.5,
  "matrix_shape": [
    4694,
    4694
  ],
  "out_dir": "/content/drive/MyDrive/MathGraph_ETP_Recursive_Transfer_v1/mathgraph_recursive_residual_transfer_v1_transfer_fast_20260523_055739",
  "profile": "TRANSFER_FAST",
  "run_name": "mathgraph_recursive_residual_transfer_v1",
  "seeds": [
    1729,
    42,
    137
  ],
  "true_contamination_max": 0,
  "true_count": 8178279
}
```

## Gate results

| gate_id   | gate                                      |      value |   threshold | passed   |
|:----------|:------------------------------------------|-----------:|------------:|:---------|
| T1        | compact_transfer_gain_vs_generic_positive | 234.167    |    1        | True     |
| T2        | compact_beats_random_same_size            | 205        |    0        | True     |
| T3        | compact_beats_shuffled_atlas_same_size    |  86.9583   |    0        | True     |
| T4        | compact_retains_recursive_gain            |   0.989575 |    0.7      | True     |
| T5        | compact_prunes_recursive_memory           |   0.53     |    0.4      | True     |
| T6        | zero_true_contamination                   |   0        |    0        | True     |
| T7        | positive_gain_in_enough_seeds             |   1        |    0.666667 | True     |
| T8        | oracle_gap_captured                       |   0.68992  |    0.2      | True     |
| T9        | advisory_boundary_preserved               |   1        |    1        | True     |

## Best compact route by seed/split

| best_compact_route   | route_kind    |   best_compact_route_size |   false_pairs |   true_pairs |   compact_recoveries |   yield_rate |   compact_residuals |   new_recoveries_vs_generic |   true_contamination_count |   true_contamination_rate | advisory_only   | can_promote_truth   |   seed | split     |   generic_recoveries |   generic_residuals |   recursive_recoveries |   recursive_residuals |   recursive_route_size |   oracle_recoveries |   compact_gain_vs_generic |   recursive_gain_vs_generic |   gain_retention |   pruning_ratio |   oracle_gap_captured |
|:---------------------|:--------------|--------------------------:|--------------:|-------------:|---------------------:|-------------:|--------------------:|----------------------------:|---------------------------:|--------------------------:|:----------------|:--------------------|-------:|:----------|---------------------:|--------------------:|-----------------------:|----------------------:|-----------------------:|--------------------:|--------------------------:|----------------------------:|-----------------:|----------------:|----------------------:|
| compact_top_24       | compact_atlas |                        61 |         12000 |         2000 |                11588 |     0.965667 |                 412 |                         108 |                          0 |                         0 | True            | False               |     42 | heldout_a |                11480 |                 520 |                  11589 |                   411 |                     90 |               11725 |                       108 |                         109 |         0.990826 |            0.58 |              0.440816 |
| compact_top_24       | compact_atlas |                        61 |         12000 |         2000 |                11622 |     0.9685   |                 378 |                         114 |                          0 |                         0 | True            | False               |     42 | heldout_b |                11508 |                 492 |                  11623 |                   377 |                     90 |               11733 |                       114 |                         115 |         0.991304 |            0.58 |              0.506667 |
| compact_top_32       | compact_atlas |                        66 |         12000 |         2000 |                11690 |     0.974167 |                 310 |                         323 |                          0 |                         0 | True            | False               |    137 | heldout_a |                11367 |                 633 |                  11694 |                   306 |                     90 |               11721 |                       323 |                         327 |         0.987768 |            0.48 |              0.912429 |
| compact_top_24       | compact_atlas |                        64 |         12000 |         2000 |                11696 |     0.974667 |                 304 |                         349 |                          0 |                         0 | True            | False               |    137 | heldout_b |                11347 |                 653 |                  11702 |                   298 |                     90 |               11733 |                       349 |                         355 |         0.983099 |            0.52 |              0.904145 |
| compact_top_24       | compact_atlas |                        64 |         12000 |         2000 |                11613 |     0.96775  |                 387 |                         249 |                          0 |                         0 | True            | False               |   1729 | heldout_a |                11364 |                 636 |                  11615 |                   385 |                     90 |               11735 |                       249 |                         251 |         0.992032 |            0.52 |              0.671159 |
| compact_top_32       | compact_atlas |                        65 |         12000 |         2000 |                11629 |     0.969083 |                 371 |                         262 |                          0 |                         0 | True            | False               |   1729 | heldout_b |                11367 |                 633 |                  11631 |                   369 |                     90 |               11739 |                       262 |                         264 |         0.992424 |            0.5  |              0.704301 |

## Route policy summary

| route                      | route_kind            |   recoveries_mean |   residuals_mean |   new_vs_generic_mean |   true_contamination_max |   route_size_mean |
|:---------------------------|:----------------------|------------------:|-----------------:|----------------------:|-------------------------:|------------------:|
| oracle_reference           | oracle_reference      |           11731   |          269     |             325.5     |                        0 |           144.333 |
| recursive_full_memory      | recursive_full_memory |           11642.3 |          357.667 |             236.833   |                        0 |            90     |
| compact_load_bearing_only  | compact_atlas         |           11639.7 |          360.333 |             234.167   |                        0 |            64     |
| compact_top_32             | compact_atlas         |           11639.7 |          360.333 |             234.167   |                        0 |            64     |
| compact_top_40             | compact_atlas         |           11639.7 |          360.333 |             234.167   |                        0 |            64     |
| compact_top_50             | compact_atlas         |           11639.7 |          360.333 |             234.167   |                        0 |            64     |
| compact_top_24             | compact_atlas         |           11639.3 |          360.667 |             233.833   |                        0 |            63     |
| compact_top_16             | compact_atlas         |           11630.8 |          369.167 |             225.333   |                        0 |            56     |
| compact_top_12             | compact_atlas         |           11616.8 |          383.167 |             211.333   |                        0 |            52     |
| compact_top_8              | compact_atlas         |           11591   |          409     |             185.5     |                        0 |            48     |
| shuffled_atlas_same_size_4 | shuffled_control      |           11572.5 |          427.5   |             167       |                        0 |            56     |
| shuffled_atlas_same_size_7 | shuffled_control      |           11560.5 |          439.5   |             155       |                        0 |            56     |
| shuffled_atlas_same_size_3 | shuffled_control      |           11556.7 |          443.333 |             151.167   |                        0 |            56     |
| shuffled_atlas_same_size_6 | shuffled_control      |           11554.2 |          445.833 |             148.667   |                        0 |            56     |
| compact_top_4              | compact_atlas         |           11552   |          448     |             146.5     |                        0 |            44     |
| shuffled_atlas_same_size_5 | shuffled_control      |           11549.7 |          450.333 |             144.167   |                        0 |            56     |
| shuffled_atlas_same_size_2 | shuffled_control      |           11548.2 |          451.833 |             142.667   |                        0 |            56     |
| shuffled_atlas_same_size_8 | shuffled_control      |           11543   |          457     |             137.5     |                        0 |            56     |
| shuffled_atlas_same_size_1 | shuffled_control      |           11537   |          463     |             131.5     |                        0 |            56     |
| random_same_size_5         | random_control        |           11456.7 |          543.333 |              51.1667  |                        0 |            56     |
| random_same_size_1         | random_control        |           11450.8 |          549.167 |              45.3333  |                        0 |            56     |
| random_same_size_4         | random_control        |           11438.8 |          561.167 |              33.3333  |                        0 |            56     |
| random_same_size_3         | random_control        |           11435.5 |          564.5   |              30       |                        0 |            56     |
| random_same_size_8         | random_control        |           11433   |          567     |              27.5     |                        0 |            56     |
| random_same_size_2         | random_control        |           11427.2 |          572.833 |              21.6667  |                        0 |            56     |
| random_same_size_7         | random_control        |           11421.7 |          578.333 |              16.1667  |                        0 |            56     |
| random_same_size_6         | random_control        |           11413.7 |          586.333 |               8.16667 |                        0 |            56     |
| generic                    | generic               |           11405.5 |          594.5   |               0       |                        0 |            40     |

## Trust boundary

- All atlas routes, residual-mined constructors, and attribution scores are advisory only.
- They cannot promote TRUE/FALSE or terminal forms.
- A FALSE certificate would still require a finite magma satisfying source and violating target.
- TRUE contamination is explicitly checked against sampled TRUE pairs.

## Interpretation

A strong pass means the recursive residual memory is not merely fitting the discovery frontier. It transfers to held-out ETP FALSE pairs, retains most of the recursive gain after pruning, beats same-size random and shuffled controls, and preserves zero TRUE contamination.
