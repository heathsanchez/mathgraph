# tinygrad/tinygrad #3039 Parallel Scan Recon v1

## Verdict

`ASK_OR_PARK`

## Issue

```json
{
  "title": "Bounty: Fast parallel scan (Mamba, etc). ",
  "state": "OPEN",
  "url": "https://github.com/tinygrad/tinygrad/issues/3039",
  "labels": [
    "bounty"
  ],
  "comment_count": 17,
  "updatedAt": "2026-07-06T19:16:55Z"
}
```

## Static findings

- issue concrete for scan/mamba: `True`
- scan/cumsum candidate surface: `False`
- local tinygrad import smoke has Tensor.cumsum: `False`
- candidate files: `5`

## Top candidate files

```json
[
  {
    "path": "README.md",
    "score": 120,
    "hits": {
      "kernel": 5,
      "lower": 2,
      "tensor": 18,
      "test": 28
    },
    "lines": 202,
    "bytes": 9417
  },
  {
    "path": ".pre-commit-config.yaml",
    "score": 74,
    "hits": {
      "schedule": 2,
      "uop": 1,
      "tensor": 1,
      "test": 30
    },
    "lines": 35,
    "bytes": 1230
  },
  {
    "path": "pyproject.toml",
    "score": 68,
    "hits": {
      "schedule": 2,
      "uop": 2,
      "tensor": 2,
      "test": 24
    },
    "lines": 264,
    "bytes": 6430
  },
  {
    "path": "mkdocs.yml",
    "score": 26,
    "hits": {
      "uop": 2,
      "lower": 1,
      "tensor": 7
    },
    "lines": 150,
    "bytes": 3666
  },
  {
    "path": "sz.py",
    "score": 4,
    "hits": {
      "uop": 1
    },
    "lines": 96,
    "bytes": 4545
  }
]
```

## Local import smoke

```text

Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
ModuleNotFoundError: No module named 'tinygrad'

```

## Candidate context excerpt

```text


```

## Issue body excerpt

```text
It would be great to have a general parallel prefix sum (associative scan) operation in tinygrad, something like [associative_scan](https://jax.readthedocs.io/en/latest/_autosummary/jax.lax.associative_scan.html) in JAX or [scan_associative](https://www.tensorflow.org/probability/api_docs/python/tfp/math/scan_associative) in TensorFlow Probability. This operation is key for the parallelization of some algorithms in CRFs, [filtering/smoothing in state space models](https://github.com/EEA-sensors/sequential-parallelization-examples/blob/main/python/temporal-parallelization-bayes-smoothers/parallel_kalman_jax.ipynb), mamba etc.

Additional Reference

https://arxiv.org/abs/2311.06281
---

Current Bounty: $500
To lock the bounty submit a draft PR with a decent amount of progress made
Make sure to reference this issue in the PR for future tracking

Notice: If the PR goes stale the bounty will be unlocked

```

## Next action

Park if issue is stale or lacks local metric.

