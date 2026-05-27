# MathGraph CrossWorld v2 — Semantic Residual Independence Rank

## Read these numbers first

| Metric | Value |
| --- | ---: |
| semantic_root_all_world_auc_false | 0.9933195438173603 |
| residual_rank_all_world_auc_false | 0.9969114909460145 |
| leave_one_world_out_mean_auc_false | 0.9837976420735745 |
| etp_semantic_root_auc_false | 0.97914248 |
| top_shared_feature | near_force_score |
| root_level_candidate | False |
| breakthrough_shaped | False |

## Interpretation guide

- All-world AUC > 0.70: strong shared signal.
- Leave-one-world-out AUC > 0.75: serious generalisation signal.
- ETP semantic AUC > 0.70: ETP semantic closure is beginning to work.
- If target_complexity remains top, the representation is still too shallow.