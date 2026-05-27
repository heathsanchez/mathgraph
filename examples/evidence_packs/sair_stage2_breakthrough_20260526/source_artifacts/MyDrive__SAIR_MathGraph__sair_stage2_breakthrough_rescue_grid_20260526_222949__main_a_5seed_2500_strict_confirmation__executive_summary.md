# Official SAIR Stage 2 Breakthrough Search

- Final classification: `verified_memory_compounding_breakthrough`
- Total gain over baseline: 8.0
- Strict admission passed: True

## Selected Policy
- `baseline`: baseline finite constructor search is always retained
- `lawbook`: non-negative held-out evidence with sufficient support
- `microbasin`: non-negative held-out evidence with sufficient support

## Rejected Components
- `repair`: negative held-out marginal contribution

## Component Diagnostics
| component | episode | yield_count | residual_count | marginal_gain | gain_over_baseline | attempt_cost_per_certificate | support | classification | advisory_only | can_promote_truth | failed_search_promoted_true_count | advisory_promoted_truth_count | true_contamination_count | unsafe_certificate_rejected_count | strict_admission_passed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | 0 | 269.0 | 30.0 | 0.0 | 0.0 | nan | 269 | required | False | False | 0 | 0 | 0 | 0 | True |
| lawbook | 1 | 270.0 | 29.0 | 1.0 | 1.0 | nan | 270 | helpful | True | False | 0 | 0 | 0 | 0 | True |
| microbasin | 2 | 277.0 | 0.0 | 7.0 | 8.0 | nan | 277 | helpful | True | False | 0 | 0 | 0 | 0 | True |
| repair | 3 | 36.0 | 0.0 | -241.0 | -233.0 | 52.27777777777778 | 36 | harmful | True | False | 0 | 0 | 0 | 0 | True |
| combined | 99 | 277.0 | 0.0 | -233.0 | 8.0 | 52.27777777777778 | 277 | helpful | True | False | 0 | 0 | 0 | 0 | True |

Finite-search failure remains residual evidence only. Advisory routes cannot promote truth.