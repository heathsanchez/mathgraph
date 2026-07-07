# tinygrad/tinygrad #3039 Reclone Unsparse Recon v3

## Verdict

`PATCH_PROBE_NEXT`

## Issue

```json
{
  "number": 3039,
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

## Signals

- local import works: `True`
- Tensor has cumsum: `True`
- cumsum behavioral probe: `True`
- has `tinygrad/tensor.py`: `True`
- has `test/`: `True`
- candidate files found: `698`

## Top candidate files

```json
[
  {
    "path": "test/backend/test_ops.py",
    "score": 13600,
    "hits": {
      "cumsum": 56,
      "cumprod": 34,
      "cummax": 58,
      "reduce": 45,
      "tensor": 759,
      "kernel": 85,
      "lower": 5,
      "test": 1964
    },
    "lines": 3422,
    "bytes": 200563
  },
  {
    "path": "test/null/test_schedule.py",
    "score": 6048,
    "hits": {
      "cummax": 1,
      "reduce": 74,
      "ops.add": 1,
      "ops.mul": 9,
      "tensor": 505,
      "uop": 103,
      "schedule": 294,
      "kernel": 33,
      "lower": 1,
      "test": 337
    },
    "lines": 2001,
    "bytes": 69904
  },
  {
    "path": "tinygrad/runtime/autogen/mesa.py",
    "score": 5519,
    "hits": {
      "scan": 17,
      "prefix": 2,
      "ssm": 14,
      "reduce": 45,
      "kernel": 23,
      "lower": 855,
      "test": 73
    },
    "lines": 10533,
    "bytes": 857265
  },
  {
    "path": "test/null/test_tensor_uop_mixin.py",
    "score": 3445,
    "hits": {
      "cumsum": 8,
      "cumprod": 2,
      "cummax": 6,
      "reduce": 19,
      "tensor": 140,
      "uop": 269,
      "test": 310
    },
    "lines": 530,
    "bytes": 30614
  },
  {
    "path": "tinygrad/mixin/__init__.py",
    "score": 3230,
    "hits": {
      "cumsum": 21,
      "cumprod": 2,
      "cummax": 7,
      "ssm": 6,
      "reduce": 66,
      "ops.add": 5,
      "ops.mul": 3,
      "ops.max": 4,
      "tensor": 341,
      "uop": 20,
      "kernel": 9,
      "lower": 2,
      "test": 1
    },
    "lines": 1911,
    "bytes": 98275
  },
  {
    "path": "tinygrad/runtime/autogen/nv_570.py",
    "score": 3065,
    "hits": {
      "scan": 18,
      "prefix": 2,
      "ssm": 41,
      "reduce": 62,
      "tensor": 3,
      "schedule": 68,
      "kernel": 42,
      "lower": 149,
      "test": 78
    },
    "lines": 24867,
    "bytes": 1418789
  },
  {
    "path": "tinygrad/runtime/autogen/nv_580.py",
    "score": 2891,
    "hits": {
      "scan": 18,
      "prefix": 2,
      "ssm": 41,
      "reduce": 62,
      "tensor": 3,
      "schedule": 75,
      "kernel": 42,
      "lower": 100,
      "test": 90
    },
    "lines": 26002,
    "bytes": 1497555
  },
  {
    "path": "extra/nv_pma/cupti/cupti.py",
    "score": 2890,
    "hits": {
      "prefix": 2,
      "ssm": 26,
      "tensor": 157,
      "kernel": 348,
      "lower": 1,
      "test": 23
    },
    "lines": 14184,
    "bytes": 888889
  },
  {
    "path": "tinygrad/uop/ops.py",
    "score": 2573,
    "hits": {
      "ssm": 1,
      "reduce": 36,
      "ops.add": 8,
      "ops.mul": 20,
      "ops.max": 3,
      "tensor": 4,
      "uop": 350,
      "schedule": 1,
      "kernel": 9,
      "lower": 4,
      "test": 17
    },
    "lines": 1670,
    "bytes": 92450
  },
  {
    "path": "test/unit/test_indexing.py",
    "score": 2486,
    "hits": {
      "cumsum": 1,
      "prefix": 4,
      "tensor": 298,
      "uop": 6,
      "schedule": 1,
      "kernel": 14,
      "test": 365
    },
    "lines": 1394,
    "bytes": 54795
  },
  {
    "path": "test/null/test_uop_graph.py",
    "score": 2435,
    "hits": {
      "reduce": 13,
      "ops.add": 10,
      "ops.mul": 2,
      "uop": 345,
      "schedule": 4,
      "lower": 1,
      "test": 145
    },
    "lines": 772,
    "bytes": 30490
  },
  {
    "path": "test/null/test_uop_symbolic.py",
    "score": 2411,
    "hits": {
      "reduce": 4,
      "uop": 93,
      "kernel": 1,
      "lower": 1,
      "test": 632
    },
    "lines": 1416,
    "bytes": 66376
  },
  {
    "path": "test/mockgpu/amd/emu.py",
    "score": 2379,
    "hits": {
      "prefix": 7,
      "reduce": 4,
      "ops.add": 5,
      "uop": 426,
      "kernel": 4,
      "lower": 3,
      "test": 4
    },
    "lines": 2280,
    "bytes": 138560
  },
  {
    "path": "tinygrad/nn/onnx.py",
    "score": 2212,
    "hits": {
      "cumsum": 4,
      "ssm": 2,
      "reduce": 23,
      "tensor": 426,
      "uop": 1,
      "kernel": 17,
      "lower": 3,
      "test": 7
    },
    "lines": 1313,
    "bytes": 75723
  },
  {
    "path": "test/unit/test_function.py",
    "score": 2204,
    "hits": {
      "reduce": 1,
      "tensor": 263,
      "uop": 90,
      "kernel": 58,
      "test": 134
    },
    "lines": 654,
    "bytes": 25327
  },
  {
    "path": "test/backend/test_custom_kernel.py",
    "score": 2070,
    "hits": {
      "reduce": 6,
      "tensor": 158,
      "uop": 119,
      "schedule": 8,
      "kernel": 109,
      "test": 66
    },
    "lines": 503,
    "bytes": 20069
  },
  {
    "path": "test/unit/test_assign.py",
    "score": 2035,
    "hits": {
      "reduce": 7,
      "ops.add": 1,
      "tensor": 240,
      "uop": 47,
      "schedule": 2,
      "kernel": 24,
      "test": 210
    },
    "lines": 1071,
    "bytes": 42689
  },
  {
    "path": "tinygrad/renderer/cstyle.py",
    "score": 1883,
    "hits": {
      "prefix": 74,
      "reduce": 1,
      "ops.add": 3,
      "ops.mul": 2,
      "tensor": 4,
      "uop": 85,
      "kernel": 38,
      "lower": 1,
      "test": 1
    },
    "lines": 591,
    "bytes": 37623
  },
  {
    "path": "extra/torch_backend/test.py",
    "score": 1878,
    "hits": {
      "cumsum": 17,
      "tensor": 127,
      "kernel": 1,
      "test": 285
    },
    "lines": 962,
    "bytes": 39072
  },
  {
    "path": "test/backend/test_tensor.py",
    "score": 1734,
    "hits": {
      "reduce": 3,
      "tensor": 238,
      "uop": 24,
      "lower": 1,
      "test": 209
    },
    "lines": 777,
    "bytes": 30515
  },
  {
    "path": "tinygrad/tensor.py",
    "score": 1713,
    "hits": {
      "ssm": 1,
      "reduce": 2,
      "tensor": 228,
      "uop": 144,
      "schedule": 3,
      "kernel": 5,
      "lower": 1
    },
    "lines": 690,
    "bytes": 33263
  },
  {
    "path": "test/backend/test_uops.py",
    "score": 1655,
    "hits": {
      "reduce": 3,
      "ops.add": 3,
      "ops.mul": 10,
      "ops.max": 1,
      "tensor": 17,
      "uop": 186,
      "schedule": 2,
      "kernel": 6,
      "test": 149
    },
    "lines": 352,
    "bytes": 17351
  },
  {
    "path": "test/unit/test_multitensor.py",
    "score": 1626,
    "hits": {
      "reduce": 5,
      "tensor": 144,
      "uop": 30,
      "schedule": 14,
      "kernel": 12,
      "test": 240
    },
    "lines": 962,
    "bytes": 39041
  },
  {
    "path": "test/null/test_graph_rewrite.py",
    "score": 1473,
    "hits": {
      "reduce": 10,
      "ops.add": 10,
      "ops.mul": 1,
      "uop": 192,
      "test": 101
    },
    "lines": 532,
    "bytes": 23067
  },
  {
    "path": "test/null/test_viz.py",
    "score": 1457,
    "hits": {
      "ops.add": 1,
      "tensor": 49,
      "uop": 101,
      "schedule": 5,
      "kernel": 56,
      "test": 147
    },
    "lines": 1121,
    "bytes": 48416
  },
  {
    "path": "test/device/test_hcq.py",
    "score": 1453,
    "hits": {
      "ssm": 1,
      "tensor": 5,
      "uop": 17,
      "schedule": 3,
      "kernel": 3,
      "test": 434
    },
    "lines": 654,
    "bytes": 31045
  },
  {
    "path": "test/null/test_uops.py",
    "score": 1448,
    "hits": {
      "reduce": 1,
      "ops.add": 13,
      "ops.mul": 3,
      "tensor": 5,
      "uop": 188,
      "kernel": 1,
      "lower": 2,
      "test": 101
    },
    "lines": 367,
    "bytes": 17953
  },
  {
    "path": "test/backend/test_schedule.py",
    "score": 1447,
    "hits": {
      "cumsum": 6,
      "reduce": 17,
      "tensor": 101,
      "uop": 23,
      "schedule": 36,
      "kernel": 13,
      "test": 111
    },
    "lines": 492,
    "bytes": 19923
  },
  {
    "path": "test/amd/hw/test_vop3.py",
    "score": 1444,
    "hits": {
      "reduce": 1,
      "uop": 1,
      "kernel": 2,
      "test": 473
    },
    "lines": 3657,
    "bytes": 133578
  },
  {
    "path": "tinygrad/llm/model.py",
    "score": 1344,
    "hits": {
      "prefix": 14,
      "ssm": 44,
      "tensor": 64,
      "uop": 24,
      "kernel": 7,
      "lower": 1
    },
    "lines": 417,
    "bytes": 25031
  },
  {
    "path": "test/backend/test_linearizer.py",
    "score": 1321,
    "hits": {
      "reduce": 9,
      "ops.max": 1,
      "tensor": 78,
      "uop": 112,
      "schedule": 10,
      "kernel": 3,
      "lower": 1,
      "test": 93
    },
    "lines": 460,
    "bytes": 25184
  },
  {
    "path": "test/external/external_test_hcq.py",
    "score": 1321,
    "hits": {
      "ssm": 1,
      "tensor": 2,
      "uop": 34,
      "schedule": 1,
      "test": 374
    },
    "lines": 329,
    "bytes": 16543
  },
  {
    "path": "extra/torch_backend/backend.py",
    "score": 1319,
    "hits": {
      "cumsum": 6,
      "cumprod": 1,
      "cummax": 2,
      "reduce": 6,
      "tensor": 225,
      "uop": 12,
      "kernel": 9,
      "test": 2
    },
    "lines": 810,
    "bytes": 39435
  },
  {
    "path": "test/null/test_uop_vmin_vmax.py",
    "score": 1284,
    "hits": {
      "reduce": 1,
      "uop": 214,
      "test": 68
    },
    "lines": 407,
    "bytes": 14078
  },
  {
    "path": "test/null/test_dtype_spec.py",
    "score": 1263,
    "hits": {
      "cumsum": 20,
      "tensor": 105,
      "test": 81
    },
    "lines": 441,
    "bytes": 24141
  },
  {
    "path": "tinygrad/schedule/rangeify.py",
    "score": 1214,
    "hits": {
      "prefix": 5,
      "reduce": 53,
      "uop": 84,
      "schedule": 4,
      "kernel": 25,
      "lower": 3,
      "test": 8
    },
    "lines": 624,
    "bytes": 32033
  },
  {
    "path": "tinygrad/codegen/opt/postrange.py",
    "score": 1156,
    "hits": {
      "reduce": 69,
      "ops.add": 2,
      "ops.mul": 1,
      "tensor": 27,
      "uop": 38,
      "schedule": 7,
      "kernel": 18,
      "lower": 2,
      "test": 1
    },
    "lines": 355,
    "bytes": 20627
  },
  {
    "path": "tinygrad/renderer/isa/x86.py",
    "score": 1122,
    "hits": {
      "prefix": 3,
      "ssm": 4,
      "reduce": 2,
      "ops.add": 12,
      "ops.mul": 4,
      "uop": 155,
      "schedule": 2,
      "kernel": 1,
      "lower": 8
    },
    "lines": 936,
    "bytes": 69860
  },
  {
    "path": "test/unit/test_disk_tensor.py",
    "score": 1120,
    "hits": {
      "reduce": 1,
      "tensor": 144,
      "test": 178
    },
    "lines": 569,
    "bytes": 25805
  },
  {
    "path": "test/backend/test_dtype.py",
    "score": 1079,
    "hits": {
      "ssm": 13,
      "tensor": 77,
      "uop": 1,
      "test": 186
    },
    "lines": 420,
    "bytes": 20007
  },
  {
    "path": "test/mockgpu/amd/pcode.py",
    "score": 1075,
    "hits": {
      "reduce": 16,
      "ops.mul": 2,
      "ops.max": 2,
      "uop": 159,
      "lower": 16
    },
    "lines": 1360,
    "bytes": 70795
  },
  {
    "path": "test/backend/test_multitensor.py",
    "score": 1061,
    "hits": {
      "reduce": 24,
      "ops.add": 5,
      "ops.mul": 2,
      "ops.max": 2,
      "tensor": 88,
      "uop": 10,
      "schedule": 5,
      "kernel": 5,
      "test": 93
    },
    "lines": 477,
    "bytes": 18941
  },
  {
    "path": "tinygrad/runtime/autogen/hsa.py",
    "score": 1042,
    "hits": {
      "reduce": 2,
      "kernel": 202,
      "test": 4
    },
    "lines": 1108,
    "bytes": 140382
  },
  {
    "path": "tinygrad/runtime/autogen/cuda.py",
    "score": 1018,
    "hits": {
      "ssm": 4,
      "tensor": 104,
      "kernel": 103,
      "lower": 1,
      "test": 6
    },
    "lines": 2156,
    "bytes": 210276
  },
  {
    "path": "extra/gemm/cdna_asm_gemm.py",
    "score": 1014,
    "hits": {
      "reduce": 6,
      "ops.add": 1,
      "tensor": 64,
      "uop": 114,
      "kernel": 23,
      "test": 1
    },
    "lines": 356,
    "bytes": 20679
  },
  {
    "path": "tinygrad/mixin/elementwise.py",
    "score": 1012,
    "hits": {
      "reduce": 2,
      "ops.add": 1,
      "ops.mul": 1,
      "ops.max": 1,
      "tensor": 223,
      "uop": 13,
      "lower": 1
    },
    "lines": 1079,
    "bytes": 37418
  },
  {
    "path": "tinygrad/codegen/__init__.py",
    "score": 981,
    "hits": {
      "scan": 2,
      "reduce": 48,
      "tensor": 3,
      "uop": 82,
      "schedule": 3,
      "kernel": 3,
      "lower": 5
    },
    "lines": 472,
    "bytes": 23132
  },
  {
    "path": "test/backend/test_nn.py",
    "score": 934,
    "hits": {
      "reduce": 1,
      "tensor": 97,
      "uop": 7,
      "kernel": 18,
      "test": 137
    },
    "lines": 625,
    "bytes": 25613
  },
  {
    "path": "tinygrad/codegen/simplify.py",
    "score": 933,
    "hits": {
      "reduce": 58,
      "ops.add": 12,
      "ops.mul": 2,
      "ops.max": 1,
      "tensor": 2,
      "uop": 32,
      "lower": 7
    },
    "lines": 155,
    "bytes": 8526
  },
  {
    "path": "test/testextra/test_tk.py",
    "score": 923,
    "hits": {
      "reduce": 10,
      "tensor": 106,
      "uop": 46,
      "kernel": 17,
      "test": 28
    },
    "lines": 989,
    "bytes": 35085
  },
  {
    "path": "tinygrad/uop/symbolic.py",
    "score": 880,
    "hits": {
      "reduce": 8,
      "ops.add": 9,
      "ops.mul": 5,
      "ops.max": 2,
      "uop": 126,
      "kernel": 1,
      "lower": 1
    },
    "lines": 470,
    "bytes": 31155
  },
  {
    "path": "extra/hcq2/hcq2.py",
    "score": 879,
    "hits": {
      "uop": 152,
      "schedule": 13,
      "kernel": 4,
      "lower": 5,
      "test": 3
    },
    "lines": 553,
    "bytes": 29851
  },
  {
    "path": "test/unit/test_call.py",
    "score": 872,
    "hits": {
      "reduce": 4,
      "tensor": 103,
      "uop": 33,
      "schedule": 3,
      "test": 80
    },
    "lines": 352,
    "bytes": 13686
  },
  {
    "path": "examples/mlperf/model_train.py",
    "score": 863,
    "hits": {
      "cumprod": 13,
      "tensor": 72,
      "uop": 1,
      "schedule": 50,
      "kernel": 1,
      "test": 1
    },
    "lines": 1813,
    "bytes": 83028
  },
  {
    "path": "test/external/external_test_onnx_backend.py",
    "score": 848,
    "hits": {
      "cumsum": 1,
      "scan": 1,
      "ssm": 2,
      "reduce": 1,
      "tensor": 5,
      "test": 248
    },
    "lines": 211,
    "bytes": 9500
  },
  {
    "path": "test/null/test_simplify_valid_idx.py",
    "score": 842,
    "hits": {
      "cumsum": 1,
      "reduce": 4,
      "ops.add": 2,
      "uop": 102,
      "kernel": 6,
      "lower": 1,
      "test": 69
    },
    "lines": 586,
    "bytes": 24167
  },
  {
    "path": "test/backend/test_const_folding.py",
    "score": 755,
    "hits": {
      "reduce": 13,
      "tensor": 72,
      "uop": 8,
      "schedule": 8,
      "kernel": 1,
      "test": 84
    },
    "lines": 212,
    "bytes": 9644
  },
  {
    "path": "tinygrad/nn/__init__.py",
    "score": 746,
    "hits": {
      "reduce": 2,
      "tensor": 114,
      "uop": 27,
      "kernel": 26,
      "lower": 1
    },
    "lines": 421,
    "bytes": 18606
  },
  {
    "path": "test/amd/hw/test_vop1.py",
    "score": 738,
    "hits": {
      "test": 246
    },
    "lines": 1634,
    "bytes": 53809
  },
  {
    "path": "extra/models/mask_rcnn.py",
    "score": 728,
    "hits": {
      "cumsum": 3,
      "reduce": 4,
      "tensor": 139,
      "kernel": 6,
      "test": 4
    },
    "lines": 1215,
    "bytes": 39423
  }
]
```

## Import smoke

```text
tinygrad_file /Users/heath/Documents/mathgraph-lean-work/external/bounty_triage_v1/tinygrad__tinygrad_v3/tinygrad/__init__.py
Tensor <class 'tinygrad.tensor.Tensor'>
cumsum True
cummax True
cumprod True
sum True
where True
cat True
stack True
pad True
permute True
reshape True
contiguous True

```

## Cumsum probe

```text
Tensor.arange(16).cumsum() OK elapsed 1.119225 shape (16,) val [0, 1, 3, 6, 10, 15, 21, 28, 36, 45, 55, 66, 78, 91, 105, 120]
Tensor.arange(16).reshape(4,4).cumsum(axis=0) OK elapsed 0.078886 shape (4, 4) val [[0, 1, 2, 3], [4, 6, 8, 10], [12, 15, 18, 21], [24, 28, 32, 36]]
Tensor.arange(16).reshape(4,4).cumsum(axis=1) OK elapsed 0.067276 shape (4, 4) val [[0, 1, 3, 6], [4, 9, 15, 22], [8, 17, 27, 38], [12, 25, 39, 54]]
Tensor.ones(32).cumsum() OK elapsed 0.310279 shape (32,) val [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0, 20.0, 21.0, 22.0, 23.0, 24.0, 25.0, 26.0, 27.0, 28.0, 29.0, 30.0, 31.0, 32.0]

```

## Tensor scan source

```text


```

## Candidate context

```text


===== test/backend/test_ops.py score=13600 =====

--- around line 1094 ---
1072:                    low=-400, high=-300)
1073:   def test_quick_gelu(self):
1074:     helper_test_op([(45,65)], lambda x: x * torch.sigmoid(1.702 * x), Tensor.quick_gelu)
1075:     helper_test_op([()], lambda x: x * torch.sigmoid(1.702 * x), Tensor.quick_gelu)
1076:   def test_quick_gelu_extreme(self):
1077:     helper_test_op([(45,65)], lambda x: x * torch.sigmoid(1.702 * x), Tensor.quick_gelu, low=300, high=400)
1078:     helper_test_op([(45,65)], lambda x: x * torch.sigmoid(1.702 * x), Tensor.quick_gelu, low=-400, high=-300)
1079: 
1080:   def test_elu(self):
1081:     helper_test_op([(45,65)], torch.nn.functional.elu, Tensor.elu)
1082:     helper_test_op([(45,65)], lambda x: torch.nn.functional.elu(x, alpha=0.1), lambda x: Tensor.elu(x, alpha=0.1))
1083:     helper_test_op([()], torch.nn.functional.elu, Tensor.elu)
1084:   def test_relu6(self):
1085:     helper_test_op([(45,65)], torch.nn.functional.relu6, Tensor.relu6)
1086:     helper_test_op([()], torch.nn.functional.relu6, Tensor.relu6)
1087:   def test_hardswish(self):
1088:     helper_test_op([(45,65)], torch.nn.functional.hardswish, Tensor.hardswish, grad_atol=1e-6)
1089:     helper_test_op([()], torch.nn.functional.hardswish, Tensor.hardswish, grad_atol=1e-6)
1090:   def test_mish(self):
1091:     helper_test_op([(45,65)], torch.nn.functional.mish, Tensor.mish)
1092:     helper_test_op([()], torch.nn.functional.mish, Tensor.mish)
1093: 
1094:   def test_small_cumsum(self):
1095:     helper_test_op([(10)], lambda x: torch.cumsum(x, dim=0), lambda x: Tensor.cumsum(x, axis=0))
1096:   @slow_test
1097:   def test_simple_cumsum(self):
1098:     helper_test_op([(512)], lambda x: torch.cumsum(x, dim=0), lambda x: Tensor.cumsum(x, axis=0))
1099:     helper_test_op([(1022)], lambda x: torch.cumsum(x, dim=0), lambda x: Tensor.cumsum(x, axis=0))
1100:   @slow_test
1101:   def test_cumsum(self):
1102:     helper_test_op([()], lambda x: torch.cumsum(x, dim=0), lambda x: Tensor.cumsum(x, axis=0))
1103:     self.helper_test_exception([()], lambda x: torch.cumsum(x, dim=1), lambda x: Tensor.cumsum(x, axis=1), expected=IndexError)
1104:     helper_test_op([(20,)], lambda x: torch.cumsum(x, dim=0), lambda x: Tensor.cumsum(x, axis=0))
1105:     self.helper_test_exception([(20,)], lambda x: torch.cumsum(x, dim=1), lambda x: Tensor.cumsum(x, axis=1), expected=IndexError)
1106:     self.helper_test_exception([(20,)], lambda x: torch.cumsum(x, dim=-2), lambda x: Tensor.cumsum(x, axis=-2), expected=IndexError)
1107:     helper_test_op([(20,30)], lambda x: torch.cumsum(x, dim=0), lambda x: Tensor.cumsum(x, axis=0))
1108:     helper_test_op([(20,30)], lambda x: torch.cumsum(x, dim=1), lambda x: Tensor.cumsum(x, axis=1))
1109:     helper_test_op([(20,30,40)], lambda x: torch.cumsum(x, dim=2), lambda x: Tensor.cumsum(x, axis=2))
1110:     helper_test_op([(20,30,40)], lambda x: torch.cumsum(x, dim=-1), lambda x: Tensor.cumsum(x, axis=-1))
1111:   def test_cumsum_zero_axis(self):
1112:     helper_test_op([(2,0,4)], lambda x: torch.cumsum(x, dim=1), lambda x: Tensor.cumsum(x, axis=1))
1113:     helper_test_op([(0,3)], lambda x: torch.cumsum(x, dim=0), lambda x: Tensor.cumsum(x, axis=0))
1114:     helper_test_op([(2,3,0)], lambda x: torch.cumsum(x, dim=2), lambda x: Tensor.cumsum(x, axis=2))
1115: 
1116:   def test_small_cumprod(self):
1117:     helper_test_op([(10)],lambda x: torch.cumprod(x, dim=0),lambda x: Tensor.cumprod(x, axis=0))
1118:   @slow_test
1119:   def test_simple_cumprod(self):
1120:     helper_test_op([(512)],lambda x: torch.cumprod(x, dim=0),lambda x: Tensor.cumprod(x, axis=0))
1121:     helper_test_op([(1022)],lambda x: torch.cumprod(x, dim=0),lambda x: Tensor.cumprod(x, axis=0))
1122:   @slow_test
1123:   def test_cumprod(self):
1124:     helper_test_op([()],lambda x: torch.cumprod(x, dim=0),lambda x: Tensor.cumprod(x, axis=0))
1125:     self.helper_test_exception([()],lambda x: torch.cumprod(x, dim=1),lambda x: Tensor.cumprod(x, axis=1),expected=IndexError)
1126:     helper_test_op([(20,)],lambda x: torch.cumprod(x, dim=0),lambda x: Tensor.cumprod(x, axis=0))
1127:     self.helper_test_exception([(20,)],lambda x: torch.cumprod(x, dim=1),lambda x: Tensor.cumprod(x, axis=1),expected=IndexError)
1128:     self.helper_test_exception([(20,)],lambda x: torch.cumprod(x, dim=-2),lambda x: Tensor.cumprod(x, axis=-2),expected=IndexError)
1129:     helper_test_op([(20, 30)],lambda x: torch.cumprod(x, dim=0),lambda x: Tensor.cumprod(x, axis=0))

--- around line 1110 ---
1088:     helper_test_op([(45,65)], torch.nn.functional.hardswish, Tensor.hardswish, grad_atol=1e-6)
1089:     helper_test_op([()], torch.nn.functional.hardswish, Tensor.hardswish, grad_atol=1e-6)
1090:   def test_mish(self):
1091:     helper_test_op([(45,65)], torch.nn.functional.mish, Tensor.mish)
1092:     helper_test_op([()], torch.nn.functional.mish, Tensor.mish)
1093: 
1094:   def test_small_cumsum(self):
1095:     helper_test_op([(10)], lambda x: torch.cumsum(x, dim=0), lambda x: Tensor.cumsum(x, axis=0))
1096:   @slow_test
1097:   def test_simple_cumsum(self):
1098:     helper_test_op([(512)], lambda x: torch.cumsum(x, dim=0), lambda x: Tensor.cumsum(x, axis=0))
1099:     helper_test_op([(1022)], lambda x: torch.cumsum(x, dim=0), lambda x: Tensor.cumsum(x, axis=0))
1100:   @slow_test
1101:   def test_cumsum(self):
1102:     helper_test_op([()], lambda x: torch.cumsum(x, dim=0), lambda x: Tensor.cumsum(x, axis=0))
1103:     self.helper_test_exception([()], lambda x: torch.cumsum(x, dim=1), lambda x: Tensor.cumsum(x, axis=1), expected=IndexError)
1104:     helper_test_op([(20,)], lambda x: torch.cumsum(x, dim=0), lambda x: Tensor.cumsum(x, axis=0))
1105:     self.helper_test_exception([(20,)], lambda x: torch.cumsum(x, dim=1), lambda x: Tensor.cumsum(x, axis=1), expected=IndexError)
1106:     self.helper_test_exception([(20,)], lambda x: torch.cumsum(x, dim=-2), lambda x: Tensor.cumsum(x, axis=-2), expected=IndexError)
1107:     helper_test_op([(20,30)], lambda x: torch.cumsum(x, dim=0), lambda x: Tensor.cumsum(x, axis=0))
1108:     helper_test_op([(20,30)], lambda x: torch.cumsum(x, dim=1), lambda x: Tensor.cumsum(x, axis=1))
1109:     helper_test_op([(20,30,40)], lambda x: torch.cumsum(x, dim=2), lambda x: Tensor.cumsum(x, axis=2))
1110:     helper_test_op([(20,30,40)], lambda x: torch.cumsum(x, dim=-1), lambda x: Tensor.cumsum(x, axis=-1))
1111:   def test_cumsum_zero_axis(self):
1112:     helper_test_op([(2,0,4)], lambda x: torch.cumsum(x, dim=1), lambda x: Tensor.cumsum(x, axis=1))
1113:     helper_test_op([(0,3)], lambda x: torch.cumsum(x, dim=0), lambda x: Tensor.cumsum(x, axis=0))
1114:     helper_test_op([(2,3,0)], lambda x: torch.cumsum(x, dim=2), lambda x: Tensor.cumsum(x, axis=2))
1115: 
1116:   def test_small_cumprod(self):
1117:     helper_test_op([(10)],lambda x: torch.cumprod(x, dim=0),lambda x: Tensor.cumprod(x, axis=0))
1118:   @slow_test
1119:   def test_simple_cumprod(self):
1120:     helper_test_op([(512)],lambda x: torch.cumprod(x, dim=0),lambda x: Tensor.cumprod(x, axis=0))
1121:     helper_test_op([(1022)],lambda x: torch.cumprod(x, dim=0),lambda x: Tensor.cumprod(x, axis=0))
1122:   @slow_test
1123:   def test_cumprod(self):
1124:     helper_test_op([()],lambda x: torch.cumprod(x, dim=0),lambda x: Tensor.cumprod(x, axis=0))
1125:     self.helper_test_exception([()],lambda x: torch.cumprod(x, dim=1),lambda x: Tensor.cumprod(x, axis=1),expected=IndexError)
1126:     helper_test_op([(20,)],lambda x: torch.cumprod(x, dim=0),lambda x: Tensor.cumprod(x, axis=0))
1127:     self.helper_test_exception([(20,)],lambda x: torch.cumprod(x, dim=1),lambda x: Tensor.cumprod(x, axis=1),expected=IndexError)
1128:     self.helper_test_exception([(20,)],lambda x: torch.cumprod(x, dim=-2),lambda x: Tensor.cumprod(x, axis=-2),expected=IndexError)
1129:     helper_test_op([(20, 30)],lambda x: torch.cumprod(x, dim=0),lambda x: Tensor.cumprod(x, axis=0))
1130:     helper_test_op([(20, 30)],lambda x: torch.cumprod(x, dim=1),lambda x: Tensor.cumprod(x, axis=1))
1131:     helper_test_op([(20, 30, 40)],lambda x: torch.cumprod(x, dim=2),lambda x: Tensor.cumprod(x, axis=2))
1132:     helper_test_op([(20, 30, 40)],lambda x: torch.cumprod(x, dim=-1),lambda x: Tensor.cumprod(x, axis=-1))
1133:   def test_cumprod_zero_axis(self):
1134:     helper_test_op([(2, 0, 4)],lambda x: torch.cumprod(x, dim=1),lambda x: Tensor.cumprod(x, axis=1))
1135:     helper_test_op([(0, 3)],lambda x: torch.cumprod(x, dim=0),lambda x: Tensor.cumprod(x, axis=0))
1136:     helper_test_op([(2, 3, 0)],lambda x: torch.cumprod(x, dim=2),lambda x: Tensor.cumprod(x, axis=2))
1137: 
1138:   def test_small_cummax(self):
1139:     helper_test_op([(10)], lambda x: torch.cummax(x, dim=0).values, lambda x: Tensor.cummax(x, axis=0)[0])
1140:     helper_test_op([(10)], lambda x: torch.cummax(x, dim=0).indices.int(), lambda x: Tensor.cummax(x, axis=0)[1], forward_only=True)
1141:   @slow_test
1142:   def test_simple_cummax(self):
1143:     helper_test_op([(512)], lambda x: torch.cummax(x, dim=0).values, lambda x: Tensor.cummax(x, axis=0)[0])
1144:     helper_test_op([(512)], lambda x: torch.cummax(x, dim=0).indices.int(), lambda x: Tensor.cummax(x, axis=0)[1], forward_only=True)
1145:     helper_test_op([(1022)], lambda x: torch.cummax(x, dim=0).values, lambda x: Tensor.cummax(x, axis=0)[0])


===== test/null/test_schedule.py score=6048 =====

--- around line 142 ---
0120:     a = Tensor.empty(4)
0121:     b = a.reshape((1, 1, 4)).shrink(((0, 1), (0, 1), (0, 3))).contiguous()
0122:     check_schedule(b, 0)  # contiguous shrink of a realized buffer is a zero-copy SLICE
0123: 
0124:   def test_double_contiguous_realizes_once(self):
0125:     a = Tensor.empty(4, 1)
0126:     b = a.expand((4, 4)).contiguous().contiguous()
0127:     check_schedule(b, 1)
0128: 
0129:   def test_view_does_not_realize(self):
0130:     a = Tensor.empty(4)
0131:     b = a.expand((4, 4))
0132:     check_schedule(b, 0)
0133:     self.assertEqual(b.uop.base.buffer.size, 4)
0134: 
0135:   def test_contiguous_view_realizes(self):
0136:     a = Tensor.empty(4)
0137:     b = a.expand((4, 4)).contiguous()
0138:     check_schedule(b, 1)
0139:     self.assertEqual(b.uop.base.buffer.size, 16)
0140: 
0141: class TestSimpleSchedule(unittest.TestCase):
0142:   def test_reduce_doesnt_split(self):
0143:     a = Tensor.empty(16,16).sum(axis=1)
0144:     a1 = a.reshape(4,4)
0145:     a2 = a.reshape(16,1,1)
0146:     self.assertEqual(len(Tensor.schedule_linear(a1, a2).src), 1)
0147: 
0148: class TestSchedule(unittest.TestCase):
0149:   def setUp(self):
0150:     self.ctx = Context(SPLIT_REDUCEOP=0)
0151:     self.ctx.__enter__()
0152:   def tearDown(self):
0153:     self.ctx.__exit__(None, None, None)
0154: 
0155:   def test_arange_avgpool2d(self, kcount=1):
0156:     x = Tensor.arange(25).reshape(1,1,5,5).cast(dtypes.float32)
0157:     t = x.avg_pool2d(padding=1).clone()
0158:     linear, var_vals = t.linear_with_vars()
0159:     self.assertEqual(len(linear.src), kcount)
0160: 
0161:   def test_arange_avgpool2d_fused_noopt(self):
0162:     with Context(NOOPT=1): self.test_arange_avgpool2d(kcount=1)
0163: 
0164:   # when we're fusing a reduce, all ReduceOps must have the same N in the dimensions
0165:   # all permutes, reshapes, expands and shrinks push through the reduce
0166:   def test_arange_sum(self):
0167:     a = Tensor.arange(6).reshape(3, 2).sum(axis=1).clone()
0168:     check_schedule(a, 1)
0169: 
0170:   def test_arange_sum_alt(self):
0171:     a = (Tensor.arange(5).reshape(1,5).expand(6,5)*Tensor(2)).reshape(1,6,5).sum(axis=2).clone()
0172:     check_schedule(a, 1)
0173: 
0174:   def test_permute_arange(self):
0175:     a = Tensor.arange(6).reshape(6, 1, 1).permute(2, 0, 1).sum(axis=1).clone()
0176:     check_schedule(a, 1)
0177: 

--- around line 164 ---
0142:   def test_reduce_doesnt_split(self):
0143:     a = Tensor.empty(16,16).sum(axis=1)
0144:     a1 = a.reshape(4,4)
0145:     a2 = a.reshape(16,1,1)
0146:     self.assertEqual(len(Tensor.schedule_linear(a1, a2).src), 1)
0147: 
0148: class TestSchedule(unittest.TestCase):
0149:   def setUp(self):
0150:     self.ctx = Context(SPLIT_REDUCEOP=0)
0151:     self.ctx.__enter__()
0152:   def tearDown(self):
0153:     self.ctx.__exit__(None, None, None)
0154: 
0155:   def test_arange_avgpool2d(self, kcount=1):
0156:     x = Tensor.arange(25).reshape(1,1,5,5).cast(dtypes.float32)
0157:     t = x.avg_pool2d(padding=1).clone()
0158:     linear, var_vals = t.linear_with_vars()
0159:     self.assertEqual(len(linear.src), kcount)
0160: 
0161:   def test_arange_avgpool2d_fused_noopt(self):
0162:     with Context(NOOPT=1): self.test_arange_avgpool2d(kcount=1)
0163: 
0164:   # when we're fusing a reduce, all ReduceOps must have the same N in the dimensions
0165:   # all permutes, reshapes, expands and shrinks push through the reduce
0166:   def test_arange_sum(self):
0167:     a = Tensor.arange(6).reshape(3, 2).sum(axis=1).clone()
0168:     check_schedule(a, 1)
0169: 
0170:   def test_arange_sum_alt(self):
0171:     a = (Tensor.arange(5).reshape(1,5).expand(6,5)*Tensor(2)).reshape(1,6,5).sum(axis=2).clone()
0172:     check_schedule(a, 1)
0173: 
0174:   def test_permute_arange(self):
0175:     a = Tensor.arange(6).reshape(6, 1, 1).permute(2, 0, 1).sum(axis=1).clone()
0176:     check_schedule(a, 1)
0177: 
0178:   def test_expand_buffer_before_cast(self):
0179:     a = Tensor.zeros(4, 2, 1).realize().permute((1, 0, 2))
0180:     b = a.cast(dtypes.half).expand((2, 4, 4))+2
0181:     check_schedule(b, 1)
0182: 
0183:   def test_indexing_scalars(self):
0184:     # cover each shape at all index corners
0185:     for x, y in [(2,2), (2,3), (3,2), (3,3)]:
0186:       for a, b in [(0,0), (0,y-1), (x-1,0), (x-1,y-1)]:
0187:         X = Tensor.zeros(x, y).realize()
0188:         xt = X[Tensor(a)][Tensor(b)]
0189:         check_schedule(xt, 1)
0190: 
0191:   def test_push_pads_elementwise(self):
0192:     x = Tensor.full((4,4), 2.).contiguous().realize()
0193:     y = Tensor.full((4,4), 4.).contiguous().realize()
0194:     z = (x.reciprocal()*y).pad((None, (0,1),)).sum()
0195:     check_schedule(z, 1)
0196: 
0197:   def test_push_pads_contiguous(self):
0198:     x = Tensor.full((4,1), 2.).contiguous()
0199:     y = Tensor.full((4,4), 4.).contiguous()

--- around line 264 ---
0242:     src = Tensor.ones(4).contiguous().realize()
0243:     a = src.clone()
0244:     b = src.clone()
0245:     sched = check_schedule([a, b], 2, filter_sink=False)
0246:     run_linear(*sched)
0247:     # a and b are assigned to the same device Buffer
0248:     self.assertIsNot(a.uop.base.realized, b.uop.base.realized)
0249: 
0250:   def test_zero_size_assign(self):
0251:     f = Tensor.full((2,), 0.).contiguous().realize()
0252:     a = f.shrink_to((0,))
0253:     a.assign(Tensor.ones_like(a))
0254:     check_schedule(a, 0)
0255:     self.assertEqual(a.tolist(), [])
0256: 
0257:   def test_zero_size_children(self):
0258:     r = Tensor.ones(1,2).contiguous().realize().sum(axis=(1,), keepdim=True)
0259:     ax = r.reshape(1)*2
0260:     ay = r.reshape(1).shrink(((1,1),))*2
0261:     out = ax+ay.pad(((1, 0),))
0262:     check_schedule(out, 1)
0263: 
0264:   def test_preserve_multistage_reduce(self):
0265:     big_enough = getenv("REDUCEOP_SPLIT_THRESHOLD", 32768)
0266:     x = Tensor.empty(big_enough).realize()
0267:     with Context(SPLIT_REDUCEOP=1):
0268:       out = (x - x.max(keepdim=True)).max()
0269:       check_schedule(out, 3)
0270: 
0271:   def test_example_matmul_contig(self):
0272:     x = Tensor.eye(64).clone().realize()
0273:     y = Tensor.eye(64).clone().realize()
0274:     z = y.matmul(x).sum()
0275:     z.backward()
0276:     out = x.grad.contiguous()
0277:     check_schedule(out, 1)
0278: 
0279:   def test_multireduce_shrink(self):
0280:     a = Tensor.empty(32, 32).realize()
0281:     b = Tensor.empty(32, 32).realize()
0282:     c = Tensor.empty(16).realize()
0283:     a_out = a.sum(1)
0284:     a_out = a_out[:16]
0285:     b_out = b.sum(1)
0286:     b_out = b_out[:16]
0287:     out = a_out + b_out + c
0288:     check_schedule(out, 1)
0289: 
0290:   def test_reduce_same_size(self):
0291:     a = Tensor.empty(4, 4).realize()
0292:     out0 = a.sum() + 2
0293:     out1 = a.sum() + 4
0294:     out2 = out0 * out1
0295:     check_schedule([out0, out1, out2], 3) # TODO: 1?
0296: 
0297:   def test_reduce_multiple_paths(self):
0298:     a = Tensor.empty(4, 4).realize()
0299:     out0 = a.sum().exp2()

--- around line 290 ---
0268:       out = (x - x.max(keepdim=True)).max()
0269:       check_schedule(out, 3)
0270: 
0271:   def test_example_matmul_contig(self):
0272:     x = Tensor.eye(64).clone().realize()
0273:     y = Tensor.eye(64).clone().realize()
0274:     z = y.matmul(x).sum()
0275:     z.backward()
0276:     out = x.grad.contiguous()
0277:     check_schedule(out, 1)
0278: 
0279:   def test_multireduce_shrink(self):
0280:     a = Tensor.empty(32, 32).realize()
0281:     b = Tensor.empty(32, 32).realize()
0282:     c = Tensor.empty(16).realize()
0283:     a_out = a.sum(1)
0284:     a_out = a_out[:16]
0285:     b_out = b.sum(1)
0286:     b_out = b_out[:16]
0287:     out = a_out + b_out + c
0288:     check_schedule(out, 1)
0289: 
0290:   def test_reduce_same_size(self):
0291:     a = Tensor.empty(4, 4).realize()
0292:     out0 = a.sum() + 2
0293:     out1 = a.sum() + 4
0294:     out2 = out0 * out1
0295:     check_schedule([out0, out1, out2], 3) # TODO: 1?
0296: 
0297:   def test_reduce_multiple_paths(self):
0298:     a = Tensor.empty(4, 4).realize()
0299:     out0 = a.sum().exp2()
0300:     # out1 has two paths to a.sum()
0301:     out1 = a.sum() + out0
0302:     check_schedule([out0, out1], 2) # TODO: 1?
0303: 
0304:   def test_multireduce_reduce_multiple_paths(self):
0305:     a = Tensor.empty(4, 4).realize()
0306:     out0 = a.sum().exp2()
0307:     out1 = a.sum() + out0
0308:     b = (a + out0 + out1)
0309:     out2 = b.sum().exp2()
0310:     out3 = b.sum() + out2
0311:     # check_schedule([out0, out1, out2, out3], 1)
0312:     check_schedule([out0, out1, out2, out3], 4)
0313: 
0314:   def test_reduce_ext_reduce_child(self):
0315:     a = Tensor.empty(4, 4).realize()
0316:     b = Tensor.empty(4, 4).realize()
0317:     # b.sum() is not a descendant of the fused nodes
0318:     out0 = a.sum() + b.sum() + 2
0319:     out1 = a.sum() + b.sum() + 4
0320:     # check_schedule([out0, out1], 1)
0321:     check_schedule([out0, out1], 2)
0322: 
0323:   def test_reduce_multiple_paths_midreduce(self):
0324:     a = Tensor.empty(4, 4).realize()
0325:     r = a.sum()

--- around line 314 ---
0292:     out0 = a.sum() + 2
0293:     out1 = a.sum() + 4
0294:     out2 = out0 * out1
0295:     check_schedule([out0, out1, out2], 3) # TODO: 1?
0296: 
0297:   def test_reduce_multiple_paths(self):
0298:     a = Tensor.empty(4, 4).realize()
0299:     out0 = a.sum().exp2()
0300:     # out1 has two paths to a.sum()
0301:     out1 = a.sum() + out0
0302:     check_schedule([out0, out1], 2) # TODO: 1?
0303: 
0304:   def test_multireduce_reduce_multiple_paths(self):
0305:     a = Tensor.empty(4, 4).realize()
0306:     out0 = a.sum().exp2()
0307:     out1 = a.sum() + out0
0308:     b = (a + out0 + out1)
0309:     out2 = b.sum().exp2()
0310:     out3 = b.sum() + out2
0311:     # check_schedule([out0, out1, out2, out3], 1)
0312:     check_schedule([out0, out1, out2, out3], 4)
0313: 
0314:   def test_reduce_ext_reduce_child(self):
0315:     a = Tensor.empty(4, 4).realize()
0316:     b = Tensor.empty(4, 4).realize()
0317:     # b.sum() is not a descendant of the fused nodes
0318:     out0 = a.sum() + b.sum() + 2
0319:     out1 = a.sum() + b.sum() + 4
0320:     # check_schedule([out0, out1], 1)
0321:     check_schedule([out0, out1], 2)
0322: 
0323:   def test_reduce_multiple_paths_midreduce(self):
0324:     a = Tensor.empty(4, 4).realize()
0325:     r = a.sum()
0326:     out0 = r.exp2()
0327:     # reduce node in the indirect path from r to out2
0328:     out1 = (a - out0).max()
0329:     out2 = r + out1
0330:     # check_schedule([r, out0, out1, out2], 1)
0331:     check_schedule([r, out0, out1, out2], 4)
0332: 
0333:   def test_reduce_multiple_paths_midreduce_fused(self):
0334:     a = Tensor.empty(4, 4).realize()
0335:     b = Tensor.empty(4, 4).realize()
0336:     out0 = a.sum() + 4
0337:     out1 = b.max() + out0*2
0338:     out2 = a.sum() + out1
0339:     # check_schedule([out0, out1, out2], 1)
0340:     check_schedule([out0, out1, out2], 3)
0341: 
0342:   def test_reduce_multiple_paths_midexpand(self):
0343:     a = Tensor.empty(4, 4).realize()
0344:     b = Tensor.empty(4, 4, 4).realize()
0345:     r = a.sum()
0346:     out0 = r.exp2()
0347:     # e1 is in the indirect path from a.sum() to out1
0348:     e = b + out0
0349:     out1 = r + e[0][0][0]

--- around line 333 ---
0311:     # check_schedule([out0, out1, out2, out3], 1)
0312:     check_schedule([out0, out1, out2, out3], 4)
0313: 
0314:   def test_reduce_ext_reduce_child(self):
0315:     a = Tensor.empty(4, 4).realize()
0316:     b = Tensor.empty(4, 4).realize()
0317:     # b.sum() is not a descendant of the fused nodes
0318:     out0 = a.sum() + b.sum() + 2
0319:     out1 = a.sum() + b.sum() + 4
0320:     # check_schedule([out0, out1], 1)
0321:     check_schedule([out0, out1], 2)
0322: 
0323:   def test_reduce_multiple_paths_midreduce(self):
0324:     a = Tensor.empty(4, 4).realize()
0325:     r = a.sum()
0326:     out0 = r.exp2()
0327:     # reduce node in the indirect path from r to out2
0328:     out1 = (a - out0).max()
0329:     out2 = r + out1
0330:     # check_schedule([r, out0, out1, out2], 1)
0331:     check_schedule([r, out0, out1, out2], 4)
0332: 
0333:   def test_reduce_multiple_paths_midreduce_fused(self):
0334:     a = Tensor.empty(4, 4).realize()
0335:     b = Tensor.empty(4, 4).realize()
0336:     out0 = a.sum() + 4
0337:     out1 = b.max() + out0*2
0338:     out2 = a.sum() + out1
0339:     # check_schedule([out0, out1, out2], 1)
0340:     check_schedule([out0, out1, out2], 3)
0341: 
0342:   def test_reduce_multiple_paths_midexpand(self):
0343:     a = Tensor.empty(4, 4).realize()
0344:     b = Tensor.empty(4, 4, 4).realize()
0345:     r = a.sum()
0346:     out0 = r.exp2()
0347:     # e1 is in the indirect path from a.sum() to out1
0348:     e = b + out0
0349:     out1 = r + e[0][0][0]
0350:     # check_schedule([r, out0, out1, e], 3) # 1 or 2 or 3? should be 1 (one reduce) but the different outputs might make it 3
0351:     check_schedule([r, out0, out1, e], 4)
0352: 
0353:   def test_reduce_expand_child(self):
0354:     a = Tensor.empty((32, 32, 32)).realize()
0355:     b = Tensor.empty((1, 16)).realize()
0356:     out0 = a.sum() + 2
0357:     out1 = a.sum() + b
0358:     check_schedule([out0, out1], 2)
0359: 
0360:   def test_scaled_dot_product_attention_multireduce_fusion(self):
0361:     q = Tensor.empty(32,8,16,8).realize()
0362:     k = Tensor.empty(32,8,16,8).realize()
0363:     v = Tensor.empty(32,8,16,8).realize()
0364:     out = Tensor.scaled_dot_product_attention(q,k,v)
0365:     run_linear(*check_schedule(out, 4))
0366:     out = Tensor.scaled_dot_product_attention(q,k,v)
0367:     check_schedule(out, 4) # TODO: should be 1?
0368: 


===== tinygrad/runtime/autogen/mesa.py score=5519 =====

--- around line 588 ---
0566:   lower_pack_64_4x16: bool
0567:   lower_pack_32_2x16: bool
0568:   lower_pack_64_2x32_split: bool
0569:   lower_pack_32_2x16_split: bool
0570:   lower_unpack_half_2x16: bool
0571:   lower_unpack_unorm_2x16: bool
0572:   lower_unpack_snorm_2x16: bool
0573:   lower_unpack_unorm_4x8: bool
0574:   lower_unpack_snorm_4x8: bool
0575:   lower_unpack_64_2x32_split: bool
0576:   lower_unpack_32_2x16_split: bool
0577:   lower_pack_split: bool
0578:   lower_extract_byte: bool
0579:   lower_extract_word: bool
0580:   lower_insert_byte: bool
0581:   lower_insert_word: bool
0582:   vertex_id_zero_based: bool
0583:   lower_base_vertex: bool
0584:   instance_id_includes_base_index: bool
0585:   lower_helper_invocation: bool
0586:   optimize_sample_mask_in: bool
0587:   optimize_load_front_face_fsign: bool
0588:   optimize_quad_vote_to_reduce: bool
0589:   lower_cs_local_index_to_id: bool
0590:   lower_cs_local_id_to_index: bool
0591:   has_cs_global_id: bool
0592:   lower_device_index_to_zero: bool
0593:   lower_wpos_pntc: bool
0594:   lower_hadd: bool
0595:   lower_hadd64: bool
0596:   lower_uadd_sat: bool
0597:   lower_usub_sat: bool
0598:   lower_iadd_sat: bool
0599:   lower_mul_32x16: bool
0600:   lower_bfloat16_conversions: bool
0601:   vectorize_tess_levels: bool
0602:   lower_to_scalar: bool
0603:   lower_to_scalar_filter: c.CFUNCTYPE[ctypes.c_bool, [c.POINTER[struct_nir_instr], ctypes.c_void_p]]
0604:   vectorize_vec2_16bit: bool
0605:   unify_interfaces: bool
0606:   lower_interpolate_at: bool
0607:   lower_mul_2x32_64: bool
0608:   has_rotate8: bool
0609:   has_rotate16: bool
0610:   has_rotate32: bool
0611:   has_shfr32: bool
0612:   has_iadd3: bool
0613:   has_amul: bool
0614:   has_imul24: bool
0615:   has_umul24: bool
0616:   has_mul24_relaxed: bool
0617:   has_imad32: bool
0618:   has_umad24: bool
0619:   has_fused_comp_and_csel: bool
0620:   has_icsel_eqz64: bool
0621:   has_icsel_eqz32: bool
0622:   has_icsel_eqz16: bool
0623:   has_fneo_fcmpu: bool

--- around line 688 ---
0666:   support_indirect_inputs: int
0667:   support_indirect_outputs: int
0668:   lower_image_offset_to_range_base: bool
0669:   lower_atomic_offset_to_range_base: bool
0670:   preserve_mediump: bool
0671:   lower_fquantize2f16: bool
0672:   force_f2f16_rtz: bool
0673:   lower_layer_fs_input_to_sysval: bool
0674:   compact_arrays: bool
0675:   discard_is_demote: bool
0676:   has_ddx_intrinsics: bool
0677:   scalarize_ddx: bool
0678:   per_view_unique_driver_locations: bool
0679:   compact_view_index: bool
0680:   io_options: int
0681:   skip_lower_packing_ops: int
0682:   lower_mediump_io: c.CFUNCTYPE[None, [c.POINTER[struct_nir_shader]]]
0683:   varying_expression_max_cost: c.CFUNCTYPE[ctypes.c_uint32, [c.POINTER[struct_nir_shader], c.POINTER[struct_nir_shader]]]
0684:   varying_estimate_instr_cost: c.CFUNCTYPE[ctypes.c_uint32, [c.POINTER[struct_nir_instr]]]
0685:   max_varying_expression_cost: int
0686: nir_shader_compiler_options: TypeAlias = struct_nir_shader_compiler_options
0687: nir_instr_filter_cb: TypeAlias = c.CFUNCTYPE[ctypes.c_bool, [c.POINTER[struct_nir_instr], ctypes.c_void_p]]
0688: nir_lower_int64_options: dict[int, str] = {(nir_lower_imul64:=1): 'nir_lower_imul64', (nir_lower_isign64:=2): 'nir_lower_isign64', (nir_lower_divmod64:=4): 'nir_lower_divmod64', (nir_lower_imul_high64:=8): 'nir_lower_imul_high64', (nir_lower_bcsel64:=16): 'nir_lower_bcsel64', (nir_lower_icmp64:=32): 'nir_lower_icmp64', (nir_lower_iadd64:=64): 'nir_lower_iadd64', (nir_lower_iabs64:=128): 'nir_lower_iabs64', (nir_lower_ineg64:=256): 'nir_lower_ineg64', (nir_lower_logic64:=512): 'nir_lower_logic64', (nir_lower_minmax64:=1024): 'nir_lower_minmax64', (nir_lower_shift64:=2048): 'nir_lower_shift64', (nir_lower_imul_2x32_64:=4096): 'nir_lower_imul_2x32_64', (nir_lower_extract64:=8192): 'nir_lower_extract64', (nir_lower_ufind_msb64:=16384): 'nir_lower_ufind_msb64', (nir_lower_bit_count64:=32768): 'nir_lower_bit_count64', (nir_lower_subgroup_shuffle64:=65536): 'nir_lower_subgroup_shuffle64', (nir_lower_scan_reduce_bitwise64:=131072): 'nir_lower_scan_reduce_bitwise64', (nir_lower_scan_reduce_iadd64:=262144): 'nir_lower_scan_reduce_iadd64', (nir_lower_vote_ieq64:=524288): 'nir_lower_vote_ieq64', (nir_lower_usub_sat64:=1048576): 'nir_lower_usub_sat64', (nir_lower_iadd_sat64:=2097152): 'nir_lower_iadd_sat64', (nir_lower_find_lsb64:=4194304): 'nir_lower_find_lsb64', (nir_lower_conv64:=8388608): 'nir_lower_conv64', (nir_lower_uadd_sat64:=16777216): 'nir_lower_uadd_sat64', (nir_lower_iadd3_64:=33554432): 'nir_lower_iadd3_64', (nir_lower_bitfield_reverse64:=67108864): 'nir_lower_bitfield_reverse64', (nir_lower_bitfield_extract64:=134217728): 'nir_lower_bitfield_extract64'}
0689: nir_lower_doubles_options: dict[int, str] = {(nir_lower_drcp:=1): 'nir_lower_drcp', (nir_lower_dsqrt:=2): 'nir_lower_dsqrt', (nir_lower_drsq:=4): 'nir_lower_drsq', (nir_lower_dtrunc:=8): 'nir_lower_dtrunc', (nir_lower_dfloor:=16): 'nir_lower_dfloor', (nir_lower_dceil:=32): 'nir_lower_dceil', (nir_lower_dfract:=64): 'nir_lower_dfract', (nir_lower_dround_even:=128): 'nir_lower_dround_even', (nir_lower_dmod:=256): 'nir_lower_dmod', (nir_lower_dsub:=512): 'nir_lower_dsub', (nir_lower_ddiv:=1024): 'nir_lower_ddiv', (nir_lower_dsign:=2048): 'nir_lower_dsign', (nir_lower_dminmax:=4096): 'nir_lower_dminmax', (nir_lower_dsat:=8192): 'nir_lower_dsat', (nir_lower_fp64_full_software:=16384): 'nir_lower_fp64_full_software'}
0690: nir_divergence_options: dict[int, str] = {(nir_divergence_single_prim_per_subgroup:=1): 'nir_divergence_single_prim_per_subgroup', (nir_divergence_single_patch_per_tcs_subgroup:=2): 'nir_divergence_single_patch_per_tcs_subgroup', (nir_divergence_single_patch_per_tes_subgroup:=4): 'nir_divergence_single_patch_per_tes_subgroup', (nir_divergence_view_index_uniform:=8): 'nir_divergence_view_index_uniform', (nir_divergence_single_frag_shading_rate_per_subgroup:=16): 'nir_divergence_single_frag_shading_rate_per_subgroup', (nir_divergence_multiple_workgroup_per_compute_subgroup:=32): 'nir_divergence_multiple_workgroup_per_compute_subgroup', (nir_divergence_shader_record_ptr_uniform:=64): 'nir_divergence_shader_record_ptr_uniform', (nir_divergence_uniform_load_tears:=128): 'nir_divergence_uniform_load_tears', (nir_divergence_ignore_undef_if_phi_srcs:=256): 'nir_divergence_ignore_undef_if_phi_srcs'}
0691: nir_io_options: dict[int, str] = {(nir_io_has_flexible_input_interpolation_except_flat:=1): 'nir_io_has_flexible_input_interpolation_except_flat', (nir_io_dont_use_pos_for_non_fs_varyings:=2): 'nir_io_dont_use_pos_for_non_fs_varyings', (nir_io_16bit_input_output_support:=4): 'nir_io_16bit_input_output_support', (nir_io_mediump_is_32bit:=8): 'nir_io_mediump_is_32bit', (nir_io_prefer_scalar_fs_inputs:=16): 'nir_io_prefer_scalar_fs_inputs', (nir_io_mix_convergent_flat_with_interpolated:=32): 'nir_io_mix_convergent_flat_with_interpolated', (nir_io_vectorizer_ignores_types:=64): 'nir_io_vectorizer_ignores_types', (nir_io_always_interpolate_convergent_fs_inputs:=128): 'nir_io_always_interpolate_convergent_fs_inputs', (nir_io_compaction_rotates_color_channels:=256): 'nir_io_compaction_rotates_color_channels', (nir_io_compaction_groups_tes_inputs_into_pos_and_var_groups:=512): 'nir_io_compaction_groups_tes_inputs_into_pos_and_var_groups', (nir_io_radv_intrinsic_component_workaround:=1024): 'nir_io_radv_intrinsic_component_workaround', (nir_io_has_intrinsics:=65536): 'nir_io_has_intrinsics', (nir_io_separate_clip_cull_distance_arrays:=131072): 'nir_io_separate_clip_cull_distance_arrays'}
0692: struct_nir_shader_compiler_options.register_fields([('lower_fdiv', ctypes.c_bool, 0), ('lower_ffma16', ctypes.c_bool, 1), ('lower_ffma32', ctypes.c_bool, 2), ('lower_ffma64', ctypes.c_bool, 3), ('fuse_ffma16', ctypes.c_bool, 4), ('fuse_ffma32', ctypes.c_bool, 5), ('fuse_ffma64', ctypes.c_bool, 6), ('lower_flrp16', ctypes.c_bool, 7), ('lower_flrp32', ctypes.c_bool, 8), ('lower_flrp64', ctypes.c_bool, 9), ('lower_fpow', ctypes.c_bool, 10), ('lower_fsat', ctypes.c_bool, 11), ('lower_fsqrt', ctypes.c_bool, 12), ('lower_sincos', ctypes.c_bool, 13), ('lower_fmod', ctypes.c_bool, 14), ('lower_bitfield_extract8', ctypes.c_bool, 15), ('lower_bitfield_extract16', ctypes.c_bool, 16), ('lower_bitfield_extract', ctypes.c_bool, 17), ('lower_bitfield_insert', ctypes.c_bool, 18), ('lower_bitfield_reverse', ctypes.c_bool, 19), ('lower_bit_count', ctypes.c_bool, 20), ('lower_ifind_msb', ctypes.c_bool, 21), ('lower_ufind_msb', ctypes.c_bool, 22), ('lower_find_lsb', ctypes.c_bool, 23), ('lower_uadd_carry', ctypes.c_bool, 24), ('lower_usub_borrow', ctypes.c_bool, 25), ('lower_mul_high', ctypes.c_bool, 26), ('lower_mul_high16', ctypes.c_bool, 27), ('lower_fneg', ctypes.c_bool, 28), ('lower_ineg', ctypes.c_bool, 29), ('lower_fisnormal', ctypes.c_bool, 30), ('lower_scmp', ctypes.c_bool, 31), ('lower_vector_cmp', ctypes.c_bool, 32), ('lower_bitops', ctypes.c_bool, 33), ('lower_isign', ctypes.c_bool, 34), ('lower_fsign', ctypes.c_bool, 35), ('lower_iabs', ctypes.c_bool, 36), ('lower_umax', ctypes.c_bool, 37), ('lower_umin', ctypes.c_bool, 38), ('lower_fminmax_signed_zero', ctypes.c_bool, 39), ('lower_fdph', ctypes.c_bool, 40), ('fdot_replicates', ctypes.c_bool, 41), ('lower_ffloor', ctypes.c_bool, 42), ('lower_ffract', ctypes.c_bool, 43), ('lower_fceil', ctypes.c_bool, 44), ('lower_ftrunc', ctypes.c_bool, 45), ('lower_fround_even', ctypes.c_bool, 46), ('lower_ldexp', ctypes.c_bool, 47), ('lower_pack_half_2x16', ctypes.c_bool, 48), ('lower_pack_unorm_2x16', ctypes.c_bool, 49), ('lower_pack_snorm_2x16', ctypes.c_bool, 50), ('lower_pack_unorm_4x8', ctypes.c_bool, 51), ('lower_pack_snorm_4x8', ctypes.c_bool, 52), ('lower_pack_64_2x32', ctypes.c_bool, 53), ('lower_pack_64_4x16', ctypes.c_bool, 54), ('lower_pack_32_2x16', ctypes.c_bool, 55), ('lower_pack_64_2x32_split', ctypes.c_bool, 56), ('lower_pack_32_2x16_split', ctypes.c_bool, 57), ('lower_unpack_half_2x16', ctypes.c_bool, 58), ('lower_unpack_unorm_2x16', ctypes.c_bool, 59), ('lower_unpack_snorm_2x16', ctypes.c_bool, 60), ('lower_unpack_unorm_4x8', ctypes.c_bool, 61), ('lower_unpack_snorm_4x8', ctypes.c_bool, 62), ('lower_unpack_64_2x32_split', ctypes.c_bool, 63), ('lower_unpack_32_2x16_split', ctypes.c_bool, 64), ('lower_pack_split', ctypes.c_bool, 65), ('lower_extract_byte', ctypes.c_bool, 66), ('lower_extract_word', ctypes.c_bool, 67), ('lower_insert_byte', ctypes.c_bool, 68), ('lower_insert_word', ctypes.c_bool, 69), ('vertex_id_zero_based', ctypes.c_bool, 70), ('lower_base_vertex', ctypes.c_bool, 71), ('instance_id_includes_base_index', ctypes.c_bool, 72), ('lower_helper_invocation', ctypes.c_bool, 73), ('optimize_sample_mask_in', ctypes.c_bool, 74), ('optimize_load_front_face_fsign', ctypes.c_bool, 75), ('optimize_quad_vote_to_reduce', ctypes.c_bool, 76), ('lower_cs_local_index_to_id', ctypes.c_bool, 77), ('lower_cs_local_id_to_index', ctypes.c_bool, 78), ('has_cs_global_id', ctypes.c_bool, 79), ('lower_device_index_to_zero', ctypes.c_bool, 80), ('lower_wpos_pntc', ctypes.c_bool, 81), ('lower_hadd', ctypes.c_bool, 82), ('lower_hadd64', ctypes.c_bool, 83), ('lower_uadd_sat', ctypes.c_bool, 84), ('lower_usub_sat', ctypes.c_bool, 85), ('lower_iadd_sat', ctypes.c_bool, 86), ('lower_mul_32x16', ctypes.c_bool, 87), ('lower_bfloat16_conversions', ctypes.c_bool, 88), ('vectorize_tess_levels', ctypes.c_bool, 89), ('lower_to_scalar', ctypes.c_bool, 90), ('lower_to_scalar_filter', nir_instr_filter_cb, 96), ('vectorize_vec2_16bit', ctypes.c_bool, 104), ('unify_interfaces', ctypes.c_bool, 105), ('lower_interpolate_at', ctypes.c_bool, 106), ('lower_mul_2x32_64', ctypes.c_bool, 107), ('has_rotate8', ctypes.c_bool, 108), ('has_rotate16', ctypes.c_bool, 109), ('has_rotate32', ctypes.c_bool, 110), ('has_shfr32', ctypes.c_bool, 111), ('has_iadd3', ctypes.c_bool, 112), ('has_amul', ctypes.c_bool, 113), ('has_imul24', ctypes.c_bool, 114), ('has_umul24', ctypes.c_bool, 115), ('has_mul24_relaxed', ctypes.c_bool, 116), ('has_imad32', ctypes.c_bool, 117), ('has_umad24', ctypes.c_bool, 118), ('has_fused_comp_and_csel', ctypes.c_bool, 119), ('has_icsel_eqz64', ctypes.c_bool, 120), ('has_icsel_eqz32', ctypes.c_bool, 121), ('has_icsel_eqz16', ctypes.c_bool, 122), ('has_fneo_fcmpu', ctypes.c_bool, 123), ('has_ford_funord', ctypes.c_bool, 124), ('has_fsub', ctypes.c_bool, 125), ('has_isub', ctypes.c_bool, 126), ('has_pack_32_4x8', ctypes.c_bool, 127), ('has_texture_scaling', ctypes.c_bool, 128), ('has_sdot_4x8', ctypes.c_bool, 129), ('has_udot_4x8', ctypes.c_bool, 130), ('has_sudot_4x8', ctypes.c_bool, 131), ('has_sdot_4x8_sat', ctypes.c_bool, 132), ('has_udot_4x8_sat', ctypes.c_bool, 133), ('has_sudot_4x8_sat', ctypes.c_bool, 134), ('has_dot_2x16', ctypes.c_bool, 135), ('has_bfdot2_bfadd', ctypes.c_bool, 136), ('has_fmulz', ctypes.c_bool, 137), ('has_fmulz_no_denorms', ctypes.c_bool, 138), ('has_find_msb_rev', ctypes.c_bool, 139), ('has_pack_half_2x16_rtz', ctypes.c_bool, 140), ('has_bit_test', ctypes.c_bool, 141), ('has_bfe', ctypes.c_bool, 142), ('has_bfm', ctypes.c_bool, 143), ('has_bfi', ctypes.c_bool, 144), ('has_bitfield_select', ctypes.c_bool, 145), ('has_uclz', ctypes.c_bool, 146), ('has_msad', ctypes.c_bool, 147), ('has_f2e4m3fn_satfn', ctypes.c_bool, 148), ('has_load_global_bounded', ctypes.c_bool, 149), ('intel_vec4', ctypes.c_bool, 150), ('avoid_ternary_with_two_constants', ctypes.c_bool, 151), ('support_8bit_alu', ctypes.c_bool, 152), ('support_16bit_alu', ctypes.c_bool, 153), ('max_unroll_iterations', ctypes.c_uint32, 156), ('max_unroll_iterations_aggressive', ctypes.c_uint32, 160), ('max_unroll_iterations_fp64', ctypes.c_uint32, 164), ('lower_uniforms_to_ubo', ctypes.c_bool, 168), ('force_indirect_unrolling_sampler', ctypes.c_bool, 169), ('no_integers', ctypes.c_bool, 170), ('force_indirect_unrolling', ctypes.c_uint32, 172), ('driver_functions', ctypes.c_bool, 176), ('late_lower_int64', ctypes.c_bool, 177), ('lower_int64_options', ctypes.c_uint32, 180), ('lower_doubles_options', ctypes.c_uint32, 184), ('divergence_analysis_options', ctypes.c_uint32, 188), ('support_indirect_inputs', uint8_t, 192), ('support_indirect_outputs', uint8_t, 193), ('lower_image_offset_to_range_base', ctypes.c_bool, 194), ('lower_atomic_offset_to_range_base', ctypes.c_bool, 195), ('preserve_mediump', ctypes.c_bool, 196), ('lower_fquantize2f16', ctypes.c_bool, 197), ('force_f2f16_rtz', ctypes.c_bool, 198), ('lower_layer_fs_input_to_sysval', ctypes.c_bool, 199), ('compact_arrays', ctypes.c_bool, 200), ('discard_is_demote', ctypes.c_bool, 201), ('has_ddx_intrinsics', ctypes.c_bool, 202), ('scalarize_ddx', ctypes.c_bool, 203), ('per_view_unique_driver_locations', ctypes.c_bool, 204), ('compact_view_index', ctypes.c_bool, 205), ('io_options', ctypes.c_uint32, 208), ('skip_lower_packing_ops', ctypes.c_uint32, 212), ('lower_mediump_io', c.CFUNCTYPE[None, [c.POINTER[struct_nir_shader]]], 216), ('varying_expression_max_cost', c.CFUNCTYPE[ctypes.c_uint32, [c.POINTER[struct_nir_shader], c.POINTER[struct_nir_shader]]], 224), ('varying_estimate_instr_cost', c.CFUNCTYPE[ctypes.c_uint32, [c.POINTER[struct_nir_instr]]], 232), ('max_varying_expression_cost', ctypes.c_uint32, 240)])
0693: @c.record
0694: class struct_shader_info(c.Struct):
0695:   SIZE = 368
0696:   name: c.POINTER[ctypes.c_char]
0697:   label: c.POINTER[ctypes.c_char]
0698:   internal: bool
0699:   source_blake3: c.Array[ctypes.c_ubyte, Literal[32]]
0700:   stage: int
0701:   prev_stage: int
0702:   next_stage: int
0703:   prev_stage_has_xfb: bool
0704:   num_textures: int
0705:   num_ubos: int
0706:   num_abos: int
0707:   num_ssbos: int
0708:   num_images: int
0709:   inputs_read: int
0710:   dual_slot_inputs: int
0711:   outputs_written: int
0712:   outputs_read: int
0713:   system_values_read: c.Array[ctypes.c_uint32, Literal[4]]
0714:   per_primitive_inputs: int
0715:   per_primitive_outputs: int
0716:   per_view_outputs: int
0717:   view_mask: int
0718:   inputs_read_16bit: int
0719:   outputs_written_16bit: int
0720:   outputs_read_16bit: int
0721:   inputs_read_indirectly_16bit: int
0722:   outputs_read_indirectly_16bit: int
0723:   outputs_written_indirectly_16bit: int

--- around line 934 ---
0912:   ssa_alloc: int
0913:   num_blocks: int
0914:   structured: bool
0915:   valid_metadata: int
0916:   loop_analysis_indirect_mask: int
0917:   loop_analysis_force_unroll_sampler_indirect: bool
0918: nir_function_impl: TypeAlias = struct_nir_function_impl
0919: nir_metadata: dict[int, str] = {(nir_metadata_none:=0): 'nir_metadata_none', (nir_metadata_block_index:=1): 'nir_metadata_block_index', (nir_metadata_dominance:=2): 'nir_metadata_dominance', (nir_metadata_live_defs:=4): 'nir_metadata_live_defs', (nir_metadata_not_properly_reset:=8): 'nir_metadata_not_properly_reset', (nir_metadata_loop_analysis:=16): 'nir_metadata_loop_analysis', (nir_metadata_instr_index:=32): 'nir_metadata_instr_index', (nir_metadata_divergence:=64): 'nir_metadata_divergence', (nir_metadata_control_flow:=3): 'nir_metadata_control_flow', (nir_metadata_all:=-9): 'nir_metadata_all'}
0920: struct_nir_function_impl.register_fields([('cf_node', nir_cf_node, 0), ('function', c.POINTER[nir_function], 32), ('preamble', c.POINTER[nir_function], 40), ('body', struct_exec_list, 48), ('end_block', c.POINTER[nir_block], 80), ('locals', struct_exec_list, 88), ('ssa_alloc', ctypes.c_uint32, 120), ('num_blocks', ctypes.c_uint32, 124), ('structured', ctypes.c_bool, 128), ('valid_metadata', ctypes.c_int32, 132), ('loop_analysis_indirect_mask', ctypes.c_uint32, 136), ('loop_analysis_force_unroll_sampler_indirect', ctypes.c_bool, 140)])
0921: struct_nir_function.register_fields([('node', struct_exec_node, 0), ('name', c.POINTER[ctypes.c_char], 16), ('shader', c.POINTER[nir_shader], 24), ('num_params', ctypes.c_uint32, 32), ('params', c.POINTER[nir_parameter], 40), ('impl', c.POINTER[nir_function_impl], 48), ('driver_attributes', uint32_t, 56), ('is_entrypoint', ctypes.c_bool, 60), ('is_exported', ctypes.c_bool, 61), ('is_preamble', ctypes.c_bool, 62), ('should_inline', ctypes.c_bool, 63), ('dont_inline', ctypes.c_bool, 64), ('workgroup_size', c.Array[ctypes.c_uint32, Literal[3]], 68), ('is_subroutine', ctypes.c_bool, 80), ('is_tmp_globals_wrapper', ctypes.c_bool, 81), ('num_subroutine_types', ctypes.c_int32, 84), ('subroutine_types', c.POINTER[c.POINTER[struct_glsl_type]], 88), ('subroutine_index', ctypes.c_int32, 96), ('pass_flags', uint32_t, 100)])
0922: struct_nir_call_instr.register_fields([('instr', nir_instr, 0), ('callee', c.POINTER[nir_function], 32), ('indirect_callee', nir_src, 40), ('num_params', ctypes.c_uint32, 72), ('params', c.Array[nir_src, Literal[0]], 80)])
0923: nir_call_instr: TypeAlias = struct_nir_call_instr
0924: @c.record
0925: class struct_nir_intrinsic_instr(c.Struct):
0926:   SIZE = 120
0927:   instr: struct_nir_instr
0928:   intrinsic: int
0929:   _def: struct_nir_def
0930:   num_components: int
0931:   const_index: c.Array[ctypes.c_int32, Literal[8]]
0932:   name: c.POINTER[ctypes.c_char]
0933:   src: c.Array[struct_nir_src, Literal[0]]
0934: nir_intrinsic_op: dict[int, str] = {(nir_intrinsic_accept_ray_intersection:=0): 'nir_intrinsic_accept_ray_intersection', (nir_intrinsic_addr_mode_is:=1): 'nir_intrinsic_addr_mode_is', (nir_intrinsic_al2p_nv:=2): 'nir_intrinsic_al2p_nv', (nir_intrinsic_ald_nv:=3): 'nir_intrinsic_ald_nv', (nir_intrinsic_alpha_to_coverage:=4): 'nir_intrinsic_alpha_to_coverage', (nir_intrinsic_as_uniform:=5): 'nir_intrinsic_as_uniform', (nir_intrinsic_ast_nv:=6): 'nir_intrinsic_ast_nv', (nir_intrinsic_atomic_add_gen_prim_count_amd:=7): 'nir_intrinsic_atomic_add_gen_prim_count_amd', (nir_intrinsic_atomic_add_gs_emit_prim_count_amd:=8): 'nir_intrinsic_atomic_add_gs_emit_prim_count_amd', (nir_intrinsic_atomic_add_shader_invocation_count_amd:=9): 'nir_intrinsic_atomic_add_shader_invocation_count_amd', (nir_intrinsic_atomic_add_xfb_prim_count_amd:=10): 'nir_intrinsic_atomic_add_xfb_prim_count_amd', (nir_intrinsic_atomic_counter_add:=11): 'nir_intrinsic_atomic_counter_add', (nir_intrinsic_atomic_counter_add_deref:=12): 'nir_intrinsic_atomic_counter_add_deref', (nir_intrinsic_atomic_counter_and:=13): 'nir_intrinsic_atomic_counter_and', (nir_intrinsic_atomic_counter_and_deref:=14): 'nir_intrinsic_atomic_counter_and_deref', (nir_intrinsic_atomic_counter_comp_swap:=15): 'nir_intrinsic_atomic_counter_comp_swap', (nir_intrinsic_atomic_counter_comp_swap_deref:=16): 'nir_intrinsic_atomic_counter_comp_swap_deref', (nir_intrinsic_atomic_counter_exchange:=17): 'nir_intrinsic_atomic_counter_exchange', (nir_intrinsic_atomic_counter_exchange_deref:=18): 'nir_intrinsic_atomic_counter_exchange_deref', (nir_intrinsic_atomic_counter_inc:=19): 'nir_intrinsic_atomic_counter_inc', (nir_intrinsic_atomic_counter_inc_deref:=20): 'nir_intrinsic_atomic_counter_inc_deref', (nir_intrinsic_atomic_counter_max:=21): 'nir_intrinsic_atomic_counter_max', (nir_intrinsic_atomic_counter_max_deref:=22): 'nir_intrinsic_atomic_counter_max_deref', (nir_intrinsic_atomic_counter_min:=23): 'nir_intrinsic_atomic_counter_min', (nir_intrinsic_atomic_counter_min_deref:=24): 'nir_intrinsic_atomic_counter_min_deref', (nir_intrinsic_atomic_counter_or:=25): 'nir_intrinsic_atomic_counter_or', (nir_intrinsic_atomic_counter_or_deref:=26): 'nir_intrinsic_atomic_counter_or_deref', (nir_intrinsic_atomic_counter_post_dec:=27): 'nir_intrinsic_atomic_counter_post_dec', (nir_intrinsic_atomic_counter_post_dec_deref:=28): 'nir_intrinsic_atomic_counter_post_dec_deref', (nir_intrinsic_atomic_counter_pre_dec:=29): 'nir_intrinsic_atomic_counter_pre_dec', (nir_intrinsic_atomic_counter_pre_dec_deref:=30): 'nir_intrinsic_atomic_counter_pre_dec_deref', (nir_intrinsic_atomic_counter_read:=31): 'nir_intrinsic_atomic_counter_read', (nir_intrinsic_atomic_counter_read_deref:=32): 'nir_intrinsic_atomic_counter_read_deref', (nir_intrinsic_atomic_counter_xor:=33): 'nir_intrinsic_atomic_counter_xor', (nir_intrinsic_atomic_counter_xor_deref:=34): 'nir_intrinsic_atomic_counter_xor_deref', (nir_intrinsic_ballot:=35): 'nir_intrinsic_ballot', (nir_intrinsic_ballot_bit_count_exclusive:=36): 'nir_intrinsic_ballot_bit_count_exclusive', (nir_intrinsic_ballot_bit_count_inclusive:=37): 'nir_intrinsic_ballot_bit_count_inclusive', (nir_intrinsic_ballot_bit_count_reduce:=38): 'nir_intrinsic_ballot_bit_count_reduce', (nir_intrinsic_ballot_bitfield_extract:=39): 'nir_intrinsic_ballot_bitfield_extract', (nir_intrinsic_ballot_find_lsb:=40): 'nir_intrinsic_ballot_find_lsb', (nir_intrinsic_ballot_find_msb:=41): 'nir_intrinsic_ballot_find_msb', (nir_intrinsic_ballot_relaxed:=42): 'nir_intrinsic_ballot_relaxed', (nir_intrinsic_bar_break_nv:=43): 'nir_intrinsic_bar_break_nv', (nir_intrinsic_bar_set_nv:=44): 'nir_intrinsic_bar_set_nv', (nir_intrinsic_bar_sync_nv:=45): 'nir_intrinsic_bar_sync_nv', (nir_intrinsic_barrier:=46): 'nir_intrinsic_barrier', (nir_intrinsic_begin_invocation_interlock:=47): 'nir_intrinsic_begin_invocation_interlock', (nir_intrinsic_bindgen_return:=48): 'nir_intrinsic_bindgen_return', (nir_intrinsic_bindless_image_agx:=49): 'nir_intrinsic_bindless_image_agx', (nir_intrinsic_bindless_image_atomic:=50): 'nir_intrinsic_bindless_image_atomic', (nir_intrinsic_bindless_image_atomic_swap:=51): 'nir_intrinsic_bindless_image_atomic_swap', (nir_intrinsic_bindless_image_descriptor_amd:=52): 'nir_intrinsic_bindless_image_descriptor_amd', (nir_intrinsic_bindless_image_format:=53): 'nir_intrinsic_bindless_image_format', (nir_intrinsic_bindless_image_fragment_mask_load_amd:=54): 'nir_intrinsic_bindless_image_fragment_mask_load_amd', (nir_intrinsic_bindless_image_levels:=55): 'nir_intrinsic_bindless_image_levels', (nir_intrinsic_bindless_image_load:=56): 'nir_intrinsic_bindless_image_load', (nir_intrinsic_bindless_image_load_raw_intel:=57): 'nir_intrinsic_bindless_image_load_raw_intel', (nir_intrinsic_bindless_image_order:=58): 'nir_intrinsic_bindless_image_order', (nir_intrinsic_bindless_image_samples:=59): 'nir_intrinsic_bindless_image_samples', (nir_intrinsic_bindless_image_samples_identical:=60): 'nir_intrinsic_bindless_image_samples_identical', (nir_intrinsic_bindless_image_size:=61): 'nir_intrinsic_bindless_image_size', (nir_intrinsic_bindless_image_sparse_load:=62): 'nir_intrinsic_bindless_image_sparse_load', (nir_intrinsic_bindless_image_store:=63): 'nir_intrinsic_bindless_image_store', (nir_intrinsic_bindless_image_store_block_agx:=64): 'nir_intrinsic_bindless_image_store_block_agx', (nir_intrinsic_bindless_image_store_raw_intel:=65): 'nir_intrinsic_bindless_image_store_raw_intel', (nir_intrinsic_bindless_image_texel_address:=66): 'nir_intrinsic_bindless_image_texel_address', (nir_intrinsic_bindless_resource_ir3:=67): 'nir_intrinsic_bindless_resource_ir3', (nir_intrinsic_brcst_active_ir3:=68): 'nir_intrinsic_brcst_active_ir3', (nir_intrinsic_btd_retire_intel:=69): 'nir_intrinsic_btd_retire_intel', (nir_intrinsic_btd_spawn_intel:=70): 'nir_intrinsic_btd_spawn_intel', (nir_intrinsic_btd_stack_push_intel:=71): 'nir_intrinsic_btd_stack_push_intel', (nir_intrinsic_bvh64_intersect_ray_amd:=72): 'nir_intrinsic_bvh64_intersect_ray_amd', (nir_intrinsic_bvh8_intersect_ray_amd:=73): 'nir_intrinsic_bvh8_intersect_ray_amd', (nir_intrinsic_bvh_stack_rtn_amd:=74): 'nir_intrinsic_bvh_stack_rtn_amd', (nir_intrinsic_cmat_binary_op:=75): 'nir_intrinsic_cmat_binary_op', (nir_intrinsic_cmat_bitcast:=76): 'nir_intrinsic_cmat_bitcast', (nir_intrinsic_cmat_construct:=77): 'nir_intrinsic_cmat_construct', (nir_intrinsic_cmat_convert:=78): 'nir_intrinsic_cmat_convert', (nir_intrinsic_cmat_copy:=79): 'nir_intrinsic_cmat_copy', (nir_intrinsic_cmat_extract:=80): 'nir_intrinsic_cmat_extract', (nir_intrinsic_cmat_insert:=81): 'nir_intrinsic_cmat_insert', (nir_intrinsic_cmat_length:=82): 'nir_intrinsic_cmat_length', (nir_intrinsic_cmat_load:=83): 'nir_intrinsic_cmat_load', (nir_intrinsic_cmat_muladd:=84): 'nir_intrinsic_cmat_muladd', (nir_intrinsic_cmat_muladd_amd:=85): 'nir_intrinsic_cmat_muladd_amd', (nir_intrinsic_cmat_muladd_nv:=86): 'nir_intrinsic_cmat_muladd_nv', (nir_intrinsic_cmat_scalar_op:=87): 'nir_intrinsic_cmat_scalar_op', (nir_intrinsic_cmat_store:=88): 'nir_intrinsic_cmat_store', (nir_intrinsic_cmat_transpose:=89): 'nir_intrinsic_cmat_transpose', (nir_intrinsic_cmat_unary_op:=90): 'nir_intrinsic_cmat_unary_op', (nir_intrinsic_convert_alu_types:=91): 'nir_intrinsic_convert_alu_types', (nir_intrinsic_convert_cmat_intel:=92): 'nir_intrinsic_convert_cmat_intel', (nir_intrinsic_copy_deref:=93): 'nir_intrinsic_copy_deref', (nir_intrinsic_copy_fs_outputs_nv:=94): 'nir_intrinsic_copy_fs_outputs_nv', (nir_intrinsic_copy_global_to_uniform_ir3:=95): 'nir_intrinsic_copy_global_to_uniform_ir3', (n
```

## Next action

Build a tiny before/after metric harness around existing `Tensor.cumsum`, then attempt the smallest associative/tree-scan improvement or draft PR if progress is meaningful.

