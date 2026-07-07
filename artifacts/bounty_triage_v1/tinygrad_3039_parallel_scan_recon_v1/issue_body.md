It would be great to have a general parallel prefix sum (associative scan) operation in tinygrad, something like [associative_scan](https://jax.readthedocs.io/en/latest/_autosummary/jax.lax.associative_scan.html) in JAX or [scan_associative](https://www.tensorflow.org/probability/api_docs/python/tfp/math/scan_associative) in TensorFlow Probability. This operation is key for the parallelization of some algorithms in CRFs, [filtering/smoothing in state space models](https://github.com/EEA-sensors/sequential-parallelization-examples/blob/main/python/temporal-parallelization-bayes-smoothers/parallel_kalman_jax.ipynb), mamba etc.

Additional Reference

https://arxiv.org/abs/2311.06281
---

Current Bounty: $500
To lock the bounty submit a draft PR with a decent amount of progress made
Make sure to reference this issue in the PR for future tracking

Notice: If the PR goes stale the bounty will be unlocked
