# tenstorrent/tt-llk #1638 Comment Gate v5

## Verdict

`PARK_UNTIL_MAINTAINER_ANSWERS`

## Why

The static pass found a real MOP/no-MOP matmul wedge, but the bounty is not safely claimable until the maintainer confirms the exact scoring command and canonical RISCV instruction-count metric.

## Gate

```json
{
  "safe_to_post": true,
  "reason": "no similar comment detected",
  "matched_comment_url": null
}
```

## Issue summary

```json
{
  "issue_view_ok": true,
  "already_commented_similar": false,
  "matched_comment_url": null,
  "state": "OPEN",
  "title": "[Bounty $1000] Reduce RISCV instructions used to pass on tensix instructions using AI/Optimizer.",
  "labels": [
    "P2",
    "bounty",
    "bounty_difficulty/medium",
    "LLK"
  ],
  "comment_count": 18
}
```

## Post result

- post rc: `0`
- posted/matched URL: `https://github.com/tenstorrent/tt-llk/issues/1638#issuecomment-4898756583`

## Comment

```text
I did a focused static pass on #1638 and found what looks like a good first wedge: the matmul MOP/no-MOP surface, especially the existing `llk_math_matmul_custom_no_mop.h` experimental headers plus the `perf_math_matmul.py` / `math_matmul_perf.cpp` performance tests.

I also found the hardware counter docs/code that mention thread instruction counts, including the counter IDs in the performance counter path. Before attempting a patch, what exact local command should contributors use as the acceptance metric for this bounty?

Specifically:
1. Should we optimize/measure `tests/python_tests/perf_math_matmul.py` first, or another preferred op?
2. Should the score be taken from `pytest --compile-producer/--compile-consumer -m perf`, a performance counter CSV, profiler output, or CI device perf results?
3. For the objective “minimize RISCV instructions,” which counter/report column should be treated as canonical?
4. Is the existing `llk_math_matmul_custom_no_mop.h` path an acceptable starting point for a small PR, or do you prefer changes in the generic MOP/replay-buffer template code?

I can produce a small before/after patch once the exact scoring command and target op are confirmed.
```

## Next bounty routing

1. If maintainer answers with a runnable metric, return to Tenstorrent and target `perf_math_matmul.py` / `math_matmul_perf.cpp`.
2. If no answer, park Tenstorrent.
3. Next active cash route: inspect `xevrion-v2/agent-playground #2207`.
4. Next prestige route: inspect `tinygrad #3039`.

## Previous static report excerpt

```text
# tenstorrent/tt-llk #1638 Static MOP Map v4

## Verdict

`GOOD_BUT_ASK_FOR_SCORING_COMMAND_BEFORE_PATCH`

## What we found

- Existing MOP/no-MOP wedge: `True`
- Matmul perf test surface: `True`
- Thread instruction counter references: `True`
- Compile producer/consumer command surface: `True`

## Interpretation

This is now a real technical bounty surface, but still not claimable without the exact scoring command.

The likely first patch target is matmul, because the repo already has:

- `tt_llk_wormhole_b0/llk_lib/experimental/llk_math_matmul_custom_no_mop.h`
- `tt_llk_blackhole/llk_lib/experimental/llk_math_matmul_custom_no_mop.h`
- `tests/python_tests/perf_math_matmul.py`
- `tests/sources/math_matmul_perf.cpp`
- perf/counter infrastructure including thread instruction count references

## Next action

Post/ask the maintainer question unless you already have `ttexalens`/device simulator access.

## Maintainer question

```text
I did a focused static pass on #1638 and found what looks like a good first wedge: the matmul MOP/no-MOP surface, especially the existing `llk_math_matmul_custom_no_mop.h` experimental headers plus the `perf_math_matmul.py` / `math_matmul_perf.cpp` performance tests.

I also found the hardware counter docs/code that mention thread instruction counts, including the counter IDs in the performance counter path. Before attempting a patch, what exact local command should contributors use as the acceptance metric for this bounty?

Specifically:
1. Should we optimize/measure `tests/python_tests/perf_math_matmul.py` first, or another preferred op?
2. Should the score be taken from `pytest --compile-producer/--compile-consumer -m perf`, a performance counter CSV, profiler output, or CI device perf results?
3. For the objective “minimize RISCV instructions,” which counter/report column should be treated as canonical?
4. Is the existing `llk_math_matmul_custom_no_mop.h` path an acceptable starting point for a small PR, or do you prefer changes in the generic MOP/replay-buffer template code?

I can produce a small before/after patch once the exact scoring command and target op are confirmed.
```

## Static proxy counts

```text
file	lines	bytes	TTI_calls	MOP	LOADMACRO	replay	for_loops	if_constexpr	inline_funcs	perf_markers
tt_llk_wormhole_b0/llk_lib/experimental/llk_math_matmul_custom_no_mop.h	421	17532	38	9	0	68	7	2	13	0
tt_llk_blackhole/llk_lib/experimental/llk_math_matmul_custom_no_mop.h	555	22587	93	3	0	39	10	9	7	0
tt_llk_wormhole_b0/llk_lib/llk_math_matmul.h	875	34463	135	1	0	30	5	17	6	0
tt_llk_blackhole/llk_lib/llk_math_matmul.h	677	26879	100	1	0	16	3	8	6	0
tests/helpers/include/perf.h	242	7869	7	0	0	0	12	0	6	2
tests/sources/math_matmul_perf.cpp	276	9478	0	0	0	0	10	7	0	19
tests/sources/matmul_perf.cpp	277	9437	0	0	0	0	10	7	0	19

```

## Candidate presence

```text
FOUND tt_llk_wormhole_b0/llk_lib/experimental/llk_math_matmul_custom_no_mop.h
FOUND tt_llk_blackhole/llk_lib/experimental/llk_math_matmul_custom_no_mop.h
FOUND tt_llk_wormhole_b0/llk_lib/llk_math_matmul.h
FOUND tt_llk_blackhole/llk_lib/llk_math_matmul.h
FOUND tt_llk_wormhole_b0/common/inc/ckernel_template.h
FOUND tt_llk_wormhole_b0/common/inc/ckernel_ops.h
FOUND tt_llk_wormhole_b0/common/inc/ckernel_instr_params.h
FOUND tests/python_tests/perf_math_matmul.py
FOUND tests/sources/math_matmul_perf.cpp
FOUND tests/sources/matmul_perf.cpp
FOUND tests/helpers/include/perf.h
FOUND tests/python_tests/helpers/perf.py
FOUND tests/python_tests/helpers/counters.py
FOUND docs/performance_counters/performance_counters.md

```

## Perf command surface excerpt

```text

===== tests/python_tests/perf_math_matmul.py =====

--- around line 6 ---
0001: # SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC
0002: # SPDX-License-Identifier: Apache-2.0
0003: 
0004: from itertools import chain, product
0005: 
0006: import pytest
0007: from helpers.format_config import DataFormat, is_dest_acc_needed
0008: from helpers.llk_params import (
0009:     DestAccumulation,
0010:     DestSync,
0011:     MathFidelity,
0012:     PerfRunType,
0013:     StochasticRounding,
0014: )
0015: from helpers.matmul_sweep import sweep_matmul, sweep_tiny_tiles_matmul
0016: from helpers.param_config import input_output_formats
0017: from helpers.perf import PerfConfig
0018: from helpers.stimuli_config import StimuliConfig
0019: from helpers.test_variant_parameters import (
0020:     CRK_TILE_DIMM,
0021:     DEST_INDEX,
0022:     DEST_SYNC,
0023:     IN_TILE_DIMS,
0024:     LOOP_FACTOR,


--- around line 12 ---
0004: from itertools import chain, product
0005: 
0006: import pytest
0007: from helpers.format_config import DataFormat, is_dest_acc_needed
0008: from helpers.llk_params import (
0009:     DestAccumulation,
0010:     DestSync,
0011:     MathFidelity,
0012:     PerfRunType,
0013:     StochasticRounding,
0014: )
0015: from helpers.matmul_sweep import sweep_matmul, sweep_tiny_tiles_matmul
0016: from helpers.param_config import input_output_formats
0017: from helpers.perf import PerfConfig
0018: from helpers.stimuli_config import StimuliConfig
0019: from helpers.test_variant_parameters import (
0020:     CRK_TILE_DIMM,
0021:     DEST_INDEX,
0022:     DEST_SYNC,
0023:     IN_TILE_DIMS,
0024:     LOOP_FACTOR,
0025:     MATH_FIDELITY,
0026:     NUM_FACES,
0027:     PARTIAL_FACE,
0028:     THROTTLE_LEVEL,
0029:     TILE_COUNT,
0030:     UNPACK_TRANS_FACES,


--- around line 17 ---
0009:     DestAccumulation,
0010:     DestSync,
0011:     MathFidelity,
0012:     PerfRunType,
0013:     StochasticRounding,
0014: )
0015: from helpers.matmul_sweep import sweep_matmul, sweep_tiny_tiles_matmul
0016: from helpers.param_config import input_output_formats
0017: from helpers.perf import PerfConfig
0018: from helpers.stimuli_config import StimuliConfig
0019: from helpers.test_variant_parameters import (
0020:     CRK_TILE_DIMM,
0021:     DEST_INDEX,
0022:     DEST_SYNC,
0023:     IN_TILE_DIMS,
0024:     LOOP_FACTOR,
0025:     MATH_FIDELITY,
0026:     NUM_FACES,
0027:     PARTIAL_FACE,
0028:     THROTTLE_LEVEL,
0029:     TILE_COUNT,
0030:     UNPACK_TRANS_FACES,
0031:     UNPACK_TRANS_WITHIN_FACE,
0032: )
0033: 
0034: MATMUL_FORMATS = input_output_formats(
0035:     [


--- around line 57 ---
0049:     MathFidelity.HiFi4,
0050: ]
0051: 
0052: MATMUL_COMBINATIONS = sweep_matmul(
0053:     MATMUL_FORMATS,
0054:     DEST_ACC_MODES,
0055:     STOCHASTIC_ROUNDING_MODES,
0056:     DEST_SYNC_MODES,
0057:     math_matmul=True,
0058: )
0059: 
0060: TINY_TILES_MATMUL_COMBINATIONS = sweep_tiny_tiles_matmul(
0061:     MATMUL_FORMATS,
0062:     DEST_ACC_MODES,
0063:     STOCHASTIC_ROUNDING_MODES,
0064:     DEST_SYNC_MODES,
0065:     math_matmul=True,
0066: )
0067: 
0068: ALL_TEST_PARAMS = list(
0069:     chain(
0070:         # Regular matmul combinations with all throttle levels
0071:         # ( Commented to reduce number of tests since CI fails with no free space left on device
0072:         #     (fidelity, combinations, throttle)
0073:         #     for fidelity, combinations, throttle in product(
0074:         #         MATH_FIDELITIES, MATMUL_COMBINATIONS, [1, 2, 3, 4, 5]
0075:         #     )


--- around line 65 ---
0057:     math_matmul=True,
0058: )
0059: 
0060: TINY_TILES_MATMUL_COMBINATIONS = sweep_tiny_tiles_matmul(
0061:     MATMUL_FORMATS,
0062:     DEST_ACC_MODES,
0063:     STOCHASTIC_ROUNDING_MODES,
0064:     DEST_SYNC_MODES,
0065:     math_matmul=True,
0066: )
0067: 
0068: ALL_TEST_PARAMS = list(
0069:     chain(
0070:         # Regular matmul combinations with all throttle levels
0071:         # ( Commented to reduce number of tests since CI fails with no free space left on device
0072:         #     (fidelity, combinations, throttle)
0073:         #     for fidelity, combinations, throttle in product(
0074:         #         MATH_FIDELITIES, MATMUL_COMBINATIONS, [1, 2, 3, 4, 5]
0075:         #     )
0076:         # ),
0077:         # Tiny tiles matmul combinations with throttle level 1 only
0078:         (
0079:             (fidelity, combinations, 0)
0080:             for fidelity, combinations in product(
0081:                 MATH_FIDELITIES, TINY_TILES_MATMUL_COMBINATIONS
0082:             )
0083:         ),


--- around line 88 ---
0080:             for fidelity, combinations in product(
0081:                 MATH_FIDELITIES, TINY_TILES_MATMUL_COMBINATIONS
0082:             )
0083:         ),
0084:     )
0085: )
0086: 
0087: 
0088: @pytest.mark.perf
0089: @pytest.mark.parametrize("math_fidelity,matmul_config,throttle", ALL_TEST_PARAMS)
0090: def test_perf_math_matmul(
0091:     math_fidelity,
0092:     matmul_config,
0093:     throttle,
0094:     perf_report,
0095: ):
0096:     """
0097:     Performance test for matmul operations.
0098: 
0099:     Includes both regular matmul (full 32x32 tiles) and tiny tiles matmul
0100:     (input 0 with rows: 1, 2, 4, 8, 16 and columns: 32, input 1 always 32x32).
0101:     """
0102:     formats = matmul_config.formats
0103:     in0_dimensions = matmul_config.tile_dimensions.in0_dimensions
0104:     in1_dimensions = matmul_config.tile_dimensions.in1_dimensions
0105:     transpose = matmul_config.face_layout_config.unpack_transpose_faces
0106:     num_faces_in0 = matmul_config.face_layout_config.num_faces_in0


--- around line 89 ---
0081:                 MATH_FIDELITIES, TINY_TILES_MATMUL_COMBINATIONS
0082:             )
0083:         ),
0084:     )
0085: )
0086: 
0087: 
0088: @pytest.mark.perf
0089: @pytest.mark.parametrize("math_fidelity,matmul_config,throttle", ALL_TEST_PARAMS)
0090: def test_perf_math_matmul(
0091:     math_fidelity,
0092:     matmul_config,
0093:     throttle,
0094:     perf_report,
0095: ):
0096:     """
0097:     Performance test for matmul operations.
0098: 
0099:     Includes both regular matmul (full 32x32 tiles) and tiny tiles matmul
0100:     (input 0 with rows: 1, 2, 4, 8, 16 and columns: 32, input 1 always 32x32).
0101:     """
0102:     formats = matmul_config.formats
0103:     in0_dimensions = matmul_config.tile_dimensions.in0_dimensions
0104:     in1_dimensions = matmul_config.tile_dimensions.in1_dimensions
0105:     transpose = matmul_config.face_layout_config.unpack_transpose_faces
0106:     num_faces_in0 = matmul_config.face_layout_config.num_faces_in0
0107:     num_faces_in1 = matmul_config.face_layout_config.num_faces_in1


--- around line 90 ---
0082:             )
0083:         ),
0084:     )
0085: )
0086: 
0087: 
0088: @pytest.mark.perf
0089: @pytest.mark.parametrize("math_fidelity,matmul_config,throttle", ALL_TEST_PARAMS)
0090: def test_perf_math_matmul(
0091:     math_fidelity,
0092:     matmul_config,
0093:     throttle,
0094:     perf_report,
0095: ):
0096:     """
0097:     Performance test for matmul operations.
0098: 
0099:     Includes both regular matmul (full 32x32 tiles) and tiny tiles matmul
0100:     (input 0 with rows: 1, 2, 4, 8, 16 and columns: 32, input 1 always 32x32).
0101:     """
0102:     formats = matmul_config.formats
0103:     in0_dimensions = matmul_config.tile_dimensions.in0_dimensions
0104:     in1_dimensions = matmul_config.tile_dimensions.in1_dimensions
0105:     transpose = matmul_config.face_layout_config.unpack_transpose_faces
0106:     num_faces_in0 = matmul_config.face_layout_config.num_faces_in0
0107:     num_faces_in1 = matmul_config.face_layout_config.num_faces_in1
0108:     num_faces = matmul_config.face_layout_config.num_faces


--- around line 94 ---
0086: 
0087: 
0088: @pytest.mark.perf
0089: @pytest.mark.parametrize("math_fidelity,matmul_config,throttle", ALL_TEST_PARAMS)
0090: def test_perf_math_matmul(
0091:     math_fidelity,
0092:     matmul_config,
0093:     throttle,
0094:     perf_report,
0095: ):
0096:     """
0097:     Performance test for matmul operations.
0098: 
0099:     Includes both regular matmul (full 32x32 tiles) and tiny tiles matmul
0100:     (input 0 with rows: 1, 2, 4, 8, 16 and columns: 32, input 1 always 32x32).
0101:     """
0102:     formats = matmul_config.formats
0103:     in0_dimensions = matmul_
```

