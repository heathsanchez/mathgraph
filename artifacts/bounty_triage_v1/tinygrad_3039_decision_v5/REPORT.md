# tinygrad/tinygrad #3039 Decision v5

## Verdict

`DO_NOT_PR_THIS_PATCH__NEGATIVE_RESULT_CERTIFIED`

## Meaning

The Hillis-Steele/tree-style cumsum probe is correct, but it is not a bounty-grade patch because the existing `Tensor.cumsum` is faster in the local warm benchmark.

This is still useful: it converts the tinygrad route from vague hope into a certified negative result. The simple Tensor-level tree scan is not the portal.

## Benchmark ratio

| n | builtin median s | probe median s | probe/builtin |
|---:|---:|---:|---:|
| 16 | 0.00137004 | 0.00137167 | 1.001x |
| 32 | 0.00146688 | 0.00158971 | 1.084x |
| 64 | 0.00136467 | 0.00193479 | 1.418x |
| 128 | 0.00135825 | 0.00251558 | 1.852x |
| 256 | 0.00139925 | 0.00369704 | 2.642x |
| 512 | 0.00144646 | 0.00588925 | 4.071x |
| 1024 | 0.00275858 | 0.0102191 | 3.704x |


## Decision

- Do not open a PR with this patch.
- Do not claim or lock the bounty from this result.
- Keep the artifact as a Lawbook/Obstruction entry: naive Tensor-level Hillis-Steele cumsum is correct but too slow.
- Tinygrad remains possible only with a lower-level codegen/scheduler primitive, not with repeated `pad + shrink + add` at Tensor level.

## MathGraph classification

- Residual: fast general associative scan for tinygrad.
- Portal tried: Tensor-level Hillis-Steele scan via shifted adds.
- Certificate: correctness passes against `Tensor.cumsum`.
- Obstruction: performance loses to existing implementation; graph construction and repeated materialization overhead dominate.
- Next route: park tinygrad unless we inspect codegen/UOp-level scan lowering.

## Next routing

1. Return to Tenstorrent if the maintainer answers with a concrete scoring command.
2. Return to Strata/specimen if we want a MathGraph-native formal verification PR.
3. Only continue tinygrad if we are willing to work below Tensor-level APIs in scheduler/UOps/codegen.

## Raw decision JSON

```json
{
  "verdict": "DO_NOT_PR_THIS_PATCH__NEGATIVE_RESULT_CERTIFIED",
  "correctness_passed": true,
  "benchmark_rows": 7,
  "probe_slower_count": 6,
  "probe_faster_count": 0,
  "summary_rows": [
    {
      "n": 16,
      "builtin_median_s": 0.0013700410490855575,
      "probe_median_s": 0.0013716670218855143,
      "probe_over_builtin_ratio": 1.0011868058997517,
      "builtin_min_s": 0.0013504159869626164,
      "probe_min_s": 0.001336582936346531
    },
    {
      "n": 32,
      "builtin_median_s": 0.0014668750809505582,
      "probe_median_s": 0.0015897079138085246,
      "probe_over_builtin_ratio": 1.0837377595768882,
      "builtin_min_s": 0.0013072500005364418,
      "probe_min_s": 0.0015148749807849526
    },
    {
      "n": 64,
      "builtin_median_s": 0.0013646669685840607,
      "probe_median_s": 0.0019347920315340161,
      "probe_over_builtin_ratio": 1.4177759673786938,
      "builtin_min_s": 0.001304208068177104,
      "probe_min_s": 0.0018433330114930868
    },
    {
      "n": 128,
      "builtin_median_s": 0.0013582500396296382,
      "probe_median_s": 0.0025155829498544335,
      "probe_over_builtin_ratio": 1.852076478157418,
      "builtin_min_s": 0.0013207080774009228,
      "probe_min_s": 0.0024371249601244926
    },
    {
      "n": 256,
      "builtin_median_s": 0.0013992500025779009,
      "probe_median_s": 0.0036970420042052865,
      "probe_over_builtin_ratio": 2.6421597265635595,
      "builtin_min_s": 0.001285000005736947,
      "probe_min_s": 0.003566875006072223
    },
    {
      "n": 512,
      "builtin_median_s": 0.0014464579289779067,
      "probe_median_s": 0.005889249965548515,
      "probe_over_builtin_ratio": 4.071497585629722,
      "builtin_min_s": 0.00138579192571342,
      "probe_min_s": 0.005851124995388091
    },
    {
      "n": 1024,
      "builtin_median_s": 0.002758583053946495,
      "probe_median_s": 0.010219083982519805,
      "probe_over_builtin_ratio": 3.7044684835209654,
      "builtin_min_s": 0.00249054201412946,
      "probe_min_s": 0.010192458052188158
    }
  ],
  "complexity_proxy": {
    "builtin_cumsum": {
      "chars": 0,
      "lines": 0,
      "pad": 0,
      "shrink": 0,
      "sum": 0,
      "cat": 0,
      "where": 0,
      "while": 0,
      "for": 0,
      "add_ops": 0,
      "pool": 0,
      "cum": 0
    },
    "probe_hillis_steele": {
      "chars": 734,
      "lines": 26,
      "pad": 1,
      "shrink": 1,
      "sum": 0,
      "cat": 0,
      "where": 0,
      "while": 1,
      "for": 1,
      "add_ops": 2,
      "pool": 0,
      "cum": 1
    }
  }
}
```

## Prior correctness probe excerpt

```text
1d_1 axis 0 ok True expected [0] got [0]
1d_2 axis 0 ok True expected [0, 1] got [0, 1]
1d_3 axis 0 ok True expected [0, 1, 3] got [0, 1, 3]
1d_4 axis 0 ok True expected [0, 1, 3, 6] got [0, 1, 3, 6]
1d_7 axis 0 ok True expected [0, 1, 3, 6, 10, 15, 21] got [0, 1, 3, 6, 10, 15, 21]
1d_16 axis 0 ok True expected [0, 1, 3, 6, 10, 15, 21, 28, 36, 45, 55, 66, 78, 91, 105, 120] got [0, 1, 3, 6, 10, 15, 21, 28, 36, 45, 55, 66, 78, 91, 105, 120]
2d_axis0 axis 0 ok True expected [[0, 1, 2, 3], [4, 6, 8, 10], [12, 15, 18, 21]] got [[0, 1, 2, 3], [4, 6, 8, 10], [12, 15, 18, 21]]
2d_axis1 axis 1 ok True expected [[0, 1, 3, 6], [4, 9, 15, 22], [8, 17, 27, 38]] got [[0, 1, 3, 6], [4, 9, 15, 22], [8, 17, 27, 38]]
2d_axis_neg1 axis -1 ok True expected [[0, 1, 3, 6], [4, 9, 15, 22], [8, 17, 27, 38]] got [[0, 1, 3, 6], [4, 9, 15, 22], [8, 17, 27, 38]]
ALL_OK True

```

## Prior benchmark excerpt

```text
{
  "n": 16,
  "builtin": {
    "label": "builtin_cumsum",
    "ok": true,
    "err": null,
    "runs": [
      0.15265474992338568,
      0.0013700410490855575,
      0.0013504159869626164
    ],
    "median": 0.0013700410490855575,
    "min": 0.0013504159869626164
  },
  "probe": {
    "label": "hillis_steele_probe",
    "ok": true,
    "err": null,
    "runs": [
      0.060380500042811036,
      0.001336582936346531,
      0.0013716670218855143
    ],
    "median": 0.0013716670218855143,
    "min": 0.001336582936346531
  }
}
{
  "n": 32,
  "builtin": {
    "label": "builtin_cumsum",
    "ok": true,
    "err": null,
    "runs": [
      0.09469141706358641,
      0.0014668750809505582,
      0.0013072500005364418
    ],
    "median": 0.0014668750809505582,
    "min": 0.0013072500005364418
  },
  "probe": {
    "label": "hillis_steele_probe",
    "ok": true,
    "err": null,
    "runs": [
      0.13098129106219858,
      0.0015897079138085246,
      0.0015148749807849526
    ],
    "median": 0.0015897079138085246,
    "min": 0.0015148749807849526
  }
}
{
  "n": 64,
  "builtin": {
    "label": "builtin_cumsum",
    "ok": true,
    "err": null,
    "runs": [
      0.05367266701068729,
      0.0013646669685840607,
      0.001304208068177104
    ],
    "median": 0.0013646669685840607,
    "min": 0.001304208068177104
  },
  "probe": {
    "label": "hillis_steele_probe",
    "ok": true,
    "err": null,
    "runs": [
      0.23627074994146824,
      0.0019347920315340161,
      0.0018433330114930868
    ],
    "median": 0.0019347920315340161,
    "min": 0.0018433330114930868
  }
}
{
  "n": 128,
  "builtin": {
    "label": "builtin_cumsum",
    "ok": true,
    "err": null,
    "runs": [
      0.052047417033463717,
      0.0013582500396296382,
      0.0013207080774009228
    ],
    "median": 0.0013582500396296382,
    "min": 0.0013207080774009228
  },
  "probe": {
    "label": "hillis_steele_probe",
    "ok": true,
    "err": null,
    "runs": [
      0.42658633401151747,
      0.0025155829498544335,
      0.0024371249601244926
    ],
    "median": 0.0025155829498544335,
    "min": 0.0024371249601244926
  }
}
{
  "n": 256,
  "builtin": {
    "label": "builtin_cumsum",
    "ok": true,
    "err": null,
    "runs": [
      0.04973558394704014,
      0.0013992500025779009,
      0.001285000005736947
    ],
    "median": 0.0013992500025779009,
    "min": 0.001285000005736947
  },
  "probe": {
    "label": "hillis_steele_probe",
    "ok": true,
    "err": null,
    "runs": [
      0.8311468340689316,
      0.0036970420042052865,
      0.003566875006072223
    ],
    "median": 0.0036970420042052865,
    "min": 0.003566875006072223
  }
}
{
  "n": 512,
  "builtin": {
    "label": "builtin_cumsum",
    "ok": true,
    "err": null,
    "runs": [
      0.052772291004657745,
      0.0014464579289779067,
      0.00138579192571342
    ],
    "median": 0.0014464579289779067,
    "min": 0.00138579192571342
  },
  "probe": {
    "label": "hillis_steele_probe",
    "ok": true,
    "err": null,
    "runs": [
      1.72652470797766,
      0.005889249965548515,
      0.005851124995388091
    ],
    "median": 0.005889249965548515,
    "min": 0.005851124995388091
  }
}
{
  "n": 1024,
  "builtin": {
    "label": "builtin_cumsum",
    "ok": true,
    "err": null,
    "runs": [
      0.10794650006573647,
      0.002758583053946495,
      0.00249054201412946
    ],
    "median": 0.002758583053946495,
    "min": 0.00249054201412946
  },
  "probe": {
    "label": "hillis_steele_probe",
    "ok": true,
    "err": null,
    "runs": [
      3.859786416986026,
      0.010219083982519805,
      0.010192458052188158
    ],
    "median": 0.010219083982519805,
    "min": 0.010192458052188158
  }
}
JSON_RESULT_START
[
  {
    "n": 16,
    "builtin": {
      "label": "builtin_cumsum",
      "ok": true,
      "err": null,
      "runs": [
        0.15265474992338568,
        0.0013700410490855575,
        0.0013504159869626164
      ],
      "median": 0.0013700410490855575,
      "min": 0.0013504159869626164
    },
    "probe": {
      "label": "hillis_steele_probe",
      "ok": true,
      "err": null,
      "runs": [
        0.060380500042811036,
        0.001336582936346531,
        0.0013716670218855143
      ],
      "median": 0.0013716670218855143,
      "min": 0.001336582936346531
    }
  },
  {
    "n": 32,
    "builtin": {
      "label": "builtin_cumsum",
      "ok": true,
      "err": null,
      "runs": [
        0.09469141706358641,
        0.0014668750809505582,
        0.0013072500005364418
      ],
      "median": 0.0014668750809505582,
      "min": 0.0013072500005364418
    },
    "probe": {
      "label": "hillis_steele_probe",
      "ok": true,
      "err": null,
      "runs": [
        0.13098129106219858,
        0.0015897079138085246,
        0.0015148749807849526
      ],
      "median": 0.0015897079138085246,
      "min": 0.0015148749807849526
    }
  },
  {
    "n": 64,
    "builtin": {
      "label": "builtin_cumsum",
      "ok": true,
      "err": null,
      "runs": [
        0.05367266701068729,
        0.0013646669685840607,
        0.001304208068177104
      ],
      "median": 0.0013646669685840607,
      "min": 0.001304208068177104
    },
    "probe": {
      "label": "hillis_steele_probe",
      "ok": true,
      "err": null,
      "runs": [
        0.23627074994146824,
        0.0019347920315340161,
        0.0018433330114930868
      ],
      "median": 0.0019347920315340161,
      "min": 0.0018433330114930868
    }
  },
  {
    "n": 128,
    "builtin": {
      "label": "builtin_cumsum",
      "ok": true,
      "err": null,
      "runs": [
        0.052047417033463717,
        0.0013582500396296382,
        0.0013207080774009228
      ],
      "median": 0.0013582500396296382,
      "min": 0.0013207080774009228
    },
    "probe": {
      "label": "hillis_steele_probe",
      "ok": true,
      "err": null,
      "runs": [
        0.42658633401151747,
        0.0025155829498544335,
        0.0024371249601244926
      ],
      "median": 0.0025155829498544335,
      "min": 0.0024371249601244926
    }
  },
  {
    "n": 256,
    "builtin": {
      "label": "builtin_cumsum",
      "ok": true,
      "err": null,
      "runs": [
        0.04973558394704014,
        0.0013992500025779009,
        0.001285000005736947
      ],
      "median": 0.0013992500025779009,
      "min": 0.001285000005736947
    },
    "probe": {
      "label": "hillis_steele_probe",
      "ok": true,
      "err": null,
      "runs": [
        0.8311468340689316,
        0.0036970420042052865,
        0.003566875006072223
      ],
      "median": 0.0036970420042052865,
      "min": 0.003566875006072223
    }
  },
  {
    "n": 512,
    "builtin": {
      "label": "builtin_cumsum",
      "ok": true,
      "err": null,
      "runs": [
        0.052772291004657745,
        0.0014464579289779067,
        0.00138579192571342
      ],
      "median": 0.0014464579289779067,
      "min": 0.00138579192571342
    },
    "probe": {
      "label": "hillis_steele_probe",
      "ok": true,
      "err": null,
      "runs": [
        1.72652470797766,
        0.005889249965548515,
        0.005851124995388091
      ],
      "median": 0.005889249965548515,
      "min": 0.005851124995388091
    }
  },
  {
    "n": 1024,
    "builtin": {
      "label": "builtin_cumsum",
      "ok": true,
      "err": null,
      "runs": [
        0.10794650006573647,
        0.002758583053946495,
        0.00249054201412946
      ],
      "median": 0.002758583053946495,
      "min": 0.00249054201412946
    },
    "probe": {
      "label": "hillis_steele_probe",
      "ok": true,
      "err": null,
      "runs": [
        3.859786416986026,
        0.010219083982519805,
        0.010192458052188158
      ],
      "median": 0.010219083982519805,
      "min": 0.010192458052188158
    }
  }
]
JSON_RESULT_END

```

