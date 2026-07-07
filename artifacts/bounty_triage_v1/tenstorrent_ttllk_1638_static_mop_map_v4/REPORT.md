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
0103:     in0_dimensions = matmul_config.tile_dimensions.in0_dimensions
0104:     in1_dimensions = matmul_config.tile_dimensions.in1_dimensions
0105:     transpose = matmul_config.face_layout_config.unpack_transpose_faces
0106:     num_faces_in0 = matmul_config.face_layout_config.num_faces_in0
0107:     num_faces_in1 = matmul_config.face_layout_config.num_faces_in1
0108:     num_faces = matmul_config.face_layout_config.num_faces
0109: 
0110:     if is_dest_acc_needed(formats) and matmul_config.dest_acc == DestAccumulation.No:
0111:         pytest.skip("Dest accumulation must be enabled for this format")
0112: 


--- around line 97 ---
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
0109: 
0110:     if is_dest_acc_needed(formats) and matmul_config.dest_acc == DestAccumulation.No:
0111:         pytest.skip("Dest accumulation must be enabled for this format")
0112: 
0113:     run_types = [
0114:         PerfRunType.L1_TO_L1,
0115:         PerfRunType.UNPACK_ISOLATE,


--- around line 111 ---
0103:     in0_dimensions = matmul_config.tile_dimensions.in0_dimensions
0104:     in1_dimensions = matmul_config.tile_dimensions.in1_dimensions
0105:     transpose = matmul_config.face_layout_config.unpack_transpose_faces
0106:     num_faces_in0 = matmul_config.face_layout_config.num_faces_in0
0107:     num_faces_in1 = matmul_config.face_layout_config.num_faces_in1
0108:     num_faces = matmul_config.face_layout_config.num_faces
0109: 
0110:     if is_dest_acc_needed(formats) and matmul_config.dest_acc == DestAccumulation.No:
0111:         pytest.skip("Dest accumulation must be enabled for this format")
0112: 
0113:     run_types = [
0114:         PerfRunType.L1_TO_L1,
0115:         PerfRunType.UNPACK_ISOLATE,
0116:         PerfRunType.MATH_ISOLATE,
0117:         PerfRunType.PACK_ISOLATE,
0118:         PerfRunType.L1_CONGESTION,
0119:     ]
0120: 
0121:     variant_tile_count = (
0122:         matmul_config.tile_dimensions.rt_dim
0123:         * matmul_config.tile_dimensions.ct_dim
0124:         * matmul_config.tile_dimensions.kt_dim
0125:     )
0126: 
0127:     configuration = PerfConfig(
0128:         "sources/math_matmul_perf.cpp",
0129:         formats,


--- around line 114 ---
0106:     num_faces_in0 = matmul_config.face_layout_config.num_faces_in0
0107:     num_faces_in1 = matmul_config.face_layout_config.num_faces_in1
0108:     num_faces = matmul_config.face_layout_config.num_faces
0109: 
0110:     if is_dest_acc_needed(formats) and matmul_config.dest_acc == DestAccumulation.No:
0111:         pytest.skip("Dest accumulation must be enabled for this format")
0112: 
0113:     run_types = [
0114:         PerfRunType.L1_TO_L1,
0115:         PerfRunType.UNPACK_ISOLATE,
0116:         PerfRunType.MATH_ISOLATE,
0117:         PerfRunType.PACK_ISOLATE,
0118:         PerfRunType.L1_CONGESTION,
0119:     ]
0120: 
0121:     variant_tile_count = (
0122:         matmul_config.tile_dimensions.rt_dim
0123:         * matmul_config.tile_dimensions.ct_dim
0124:         * matmul_config.tile_dimensions.kt_dim
0125:     )
0126: 
0127:     configuration = PerfConfig(
0128:         "sources/math_matmul_perf.cpp",
0129:         formats,
0130:         run_types,
0131:         templates=[
0132:             MATH_FIDELITY(math_fidelity),


--- around line 115 ---
0107:     num_faces_in1 = matmul_config.face_layout_config.num_faces_in1
0108:     num_faces = matmul_config.face_layout_config.num_faces
0109: 
0110:     if is_dest_acc_needed(formats) and matmul_config.dest_acc == DestAccumulation.No:
0111:         pytest.skip("Dest accumulation must be enabled for this format")
0112: 
0113:     run_types = [
0114:         PerfRunType.L1_TO_L1,
0115:         PerfRunType.UNPACK_ISOLATE,
0116:         PerfRunType.MATH_ISOLATE,
0117:         PerfRunType.PACK_ISOLATE,
0118:         PerfRunType.L1_CONGESTION,
0119:     ]
0120: 
0121:     variant_tile_count = (
0122:         matmul_config.tile_dimensions.rt_dim
0123:         * matmul_config.tile_dimensions.ct_dim
0124:         * matmul_config.tile_dimensions.kt_dim
0125:     )
0126: 
0127:     configuration = PerfConfig(
0128:         "sources/math_matmul_perf.cpp",
0129:         formats,
0130:         run_types,
0131:         templates=[
0132:             MATH_FIDELITY(math_fidelity),
0133:             DEST_SYNC(matmul_config.dest_sync),


--- around line 116 ---
0108:     num_faces = matmul_config.face_layout_config.num_faces
0109: 
0110:     if is_dest_acc_needed(formats) and matmul_config.dest_acc == DestAccumulation.No:
0111:         pytest.skip("Dest accumulation must be enabled for this format")
0112: 
0113:     run_types = [
0114:         PerfRunType.L1_TO_L1,
0115:         PerfRunType.UNPACK_ISOLATE,
0116:         PerfRunType.MATH_ISOLATE,
0117:         PerfRunType.PACK_ISOLATE,
0118:         PerfRunType.L1_CONGESTION,
0119:     ]
0120: 
0121:     variant_tile_count = (
0122:         matmul_config.tile_dimensions.rt_dim
0123:         * matmul_config.tile_dimensions.ct_dim
0124:         * matmul_config.tile_dimensions.kt_dim
0125:     )
0126: 
0127:     configuration = PerfConfig(
0128:         "sources/math_matmul_perf.cpp",
0129:         formats,
0130:         run_types,
0131:         templates=[
0132:             MATH_FIDELITY(math_fidelity),
0133:             DEST_SYNC(matmul_config.dest_sync),
0134:             THROTTLE_LEVEL(throttle),


--- around line 117 ---
0109: 
0110:     if is_dest_acc_needed(formats) and matmul_config.dest_acc == DestAccumulation.No:
0111:         pytest.skip("Dest accumulation must be enabled for this format")
0112: 
0113:     run_types = [
0114:         PerfRunType.L1_TO_L1,
0115:         PerfRunType.UNPACK_ISOLATE,
0116:         PerfRunType.MATH_ISOLATE,
0117:         PerfRunType.PACK_ISOLATE,
0118:         PerfRunType.L1_CONGESTION,
0119:     ]
0120: 
0121:     variant_tile_count = (
0122:         matmul_config.tile_dimensions.rt_dim
0123:         * matmul_config.tile_dimensions.ct_dim
0124:         * matmul_config.tile_dimensions.kt_dim
0125:     )
0126: 
0127:     configuration = PerfConfig(
0128:         "sources/math_matmul_perf.cpp",
0129:         formats,
0130:         run_types,
0131:         templates=[
0132:             MATH_FIDELITY(math_fidelity),
0133:             DEST_SYNC(matmul_config.dest_sync),
0134:             THROTTLE_LEVEL(throttle),
0135:         ],


--- around line 118 ---
0110:     if is_dest_acc_needed(formats) and matmul_config.dest_acc == DestAccumulation.No:
0111:         pytest.skip("Dest accumulation must be enabled for this format")
0112: 
0113:     run_types = [
0114:         PerfRunType.L1_TO_L1,
0115:         PerfRunType.UNPACK_ISOLATE,
0116:         PerfRunType.MATH_ISOLATE,
0117:         PerfRunType.PACK_ISOLATE,
0118:         P
```

## Focused context excerpt

```text


===== tt_llk_wormhole_b0/llk_lib/experimental/llk_math_matmul_custom_no_mop.h =====

--- around line 13 ---
0001: // SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
0002: //
0003: // SPDX-License-Identifier: Apache-2.0
0004: 
0005: #pragma once
0006: 
0007: #include <cstdint>
0008: 
0009: #include "llk_math_matmul.h"
0010: 
0011: using namespace ckernel;
0012: 
0013: inline void matmul_validate_no_mop_contract(
0014:     const std::uint32_t in0_tile_r_dim = TILE_R_DIM,
0015:     const std::uint32_t in0_tile_c_dim = TILE_C_DIM,
0016:     const std::uint32_t in1_tile_r_dim = TILE_R_DIM,
0017:     const std::uint32_t in1_tile_c_dim = TILE_C_DIM,
0018:     const bool partial_face            = false)
0019: {
0020:     LLK_ASSERT(
0021:         in0_tile_r_dim == TILE_R_DIM && in0_tile_c_dim == TILE_C_DIM && in1_tile_r_dim == TILE_R_DIM && in1_tile_c_dim == TILE_C_DIM && !partial_face,
0022:         "Wormhole custom no-mop matmul currently supports only full 32x32 tiles with partial_face disabled");
0023: }
0024: 
0025: inline std::uint32_t matmul_get_replay_buf_len_no_mop(
0026:     [[maybe_unused]] const std::uint32_t in0_tile_r_dim = TILE_R_DIM,
0027:     [[maybe_unused]] const std::uint32_t in0_tile_c_dim = TILE_C_DIM,
0028:     [[maybe_unused]] const std::uint32_t in1_tile_r_dim = TILE_R_DIM,
0029:     [[maybe_unused]] const std::uint32_t in1_tile_c_dim = TILE_C_DIM,
0030:     [[maybe_unused]] const bool partial_face            = false)
0031: {
0032:     // The narrowed WH full-tile path uses a fixed replay image.
0033:     return 16;
0034: }
0035: 
0036: template <MathFidelity math_fidelity, int THROTTLE_LEVEL = 0>
0037: inline void matmul_configure_addrmod_no_mop(
0038:     const bool transpose,
0039:     const std::uint32_t in0_tile_r_dim = TILE_R_DIM,
0040:     const std::uint32_t in0_tile_c_dim = TILE_C_DIM,
0041:     const std::uint32_t in1_tile_r_dim = TILE_R_DIM,
0042:     const std::uint32_t in1_tile_c_dim = TILE_C_DIM,
0043:     const bool partial_face            = false,
0044:     const std::uint32_t ct_dim         = 1,
0045:     const std::uint32_t rt_dim         = 1)

--- around line 62 ---
0046: {
0047:     // The current Wormhole no-mop path is intentionally narrowed to the
0048:     // full-tile use case. Keep the contract explicit so generic LLK harnesses
0049:     // do not silently exercise unsupported tiny-tile or partial-face variants.
0050:     static_assert(THROTTLE_LEVEL == 0, "Wormhole custom no-mop matmul only supports THROTTLE_LEVEL == 0");
0051:     matmul_validate_no_mop_contract(in0_tile_r_dim, in0_tile_c_dim, in1_tile_r_dim, in1_tile_c_dim, partial_face);
0052: 
0053:     // Reuse the regular Wormhole matmul addrmods for the tile traversal itself.
0054:     // The no-mop-specific part below only fixes up the dvalid contract for
0055:     // reentry. Unlike BH, this WH path has to make the A/B reuse policy explicit
0056:     // so repeated replays keep the right source valid across ct/rt shapes.
0057:     matmul_configure_addrmod<math_fidelity, THROTTLE_LEVEL>(transpose, in0_tile_r_dim, in0_tile_c_dim, in1_tile_r_dim, in1_tile_c_dim, partial_face);
0058: 
0059:     const bool reuse_a        = ct_dim >= rt_dim;
0060:     const std::uint32_t t_dim = reuse_a ? rt_dim : ct_dim;
0061: 
0062:     // When the replay reuses one operand across multiple output tiles, keep the
0063:     // opposite source disabled until the replay sequence explicitly clears it.
0064:     if (t_dim > 1)
0065:     {
0066:         if (reuse_a)
0067:         {
0068:             TTI_SETC16(CLR_DVALID_SrcB_Disable_ADDR32, CLR_DVALID_SrcB_Disable_MASK);
0069:         }
0070:         else
0071:         {
0072:             TTI_SETC16(CLR_DVALID_SrcA_Disable_ADDR32, CLR_DVALID_SrcA_Disable_MASK);
0073:         }
0074:     }
0075:     else
0076:     {
0077:         TTI_SETC16(CLR_DVALID_SrcA_Disable_ADDR32, 0);
0078:     }
0079: }
0080: 
0081: template <MathFidelity math_fidelity>
0082: inline void matmul_emit_replay_program_no_mop(
0083:     const std::uint32_t ct_dim,
0084:     const std::uint32_t rt_dim,
0085:     [[maybe_unused]] const std::uint32_t in0_tile_r_dim = TILE_R_DIM,
0086:     [[maybe_unused]] const std::uint32_t in0_tile_c_dim = TILE_C_DIM,
0087:     [[maybe_unused]] const std::uint32_t in1_tile_r_dim = TILE_R_DIM,
0088:     [[maybe_unused]] const std::uint32_t in1_tile_c_dim = TILE_C_DIM,
0089:     [[maybe_unused]] const bool partial_face            = false)
0090: {
0091:     const bool reuse_a        = ct_dim >= rt_dim;
0092:     const std::uint32_t t_dim = reuse_a ? rt_dim : ct_dim;
0093: 
0094:     // This is the fixed full-tile replay image for the current no-mop path.

--- around line 174 ---
0158:         }
0159:         else
0160:         {
0161:             if (t_dim > 1)
0162:             {
0163:                 TTI_MVMUL(p_setrwc::CLR_NONE, 0, ADDR_MOD_1, 0);
0164:             }
0165:             else
0166:             {
0167:                 TTI_MVMUL(p_setrwc::CLR_B, 0, ADDR_MOD_1, 0);
0168:             }
0169:         }
0170:     }
0171: }
0172: 
0173: template <MathFidelity math_fidelity>
0174: inline void matmul_load_replay_no_mop(
0175:     const std::uint32_t ct_dim,
0176:     const std::uint32_t rt_dim,
0177:     const std::uint32_t in0_tile_r_dim = TILE_R_DIM,
0178:     const std::uint32_t in0_tile_c_dim = TILE_C_DIM,
0179:     const std::uint32_t in1_tile_r_dim = TILE_R_DIM,
0180:     const std::uint32_t in1_tile_c_dim = TILE_C_DIM,
0181:     const bool partial_face            = false)
0182: {
0183:     const std::uint32_t replay_buf_len = matmul_get_replay_buf_len_no_mop(in0_tile_r_dim, in0_tile_c_dim, in1_tile_r_dim, in1_tile_c_dim, partial_face);
0184: 
0185:     // WH records the replay image explicitly at init/reinit time rather than
0186:     // assuming it persists like the BH path does.
0187:     lltt::record<lltt::NoExec>(ckernel::math::replay_buf_offset, replay_buf_len);
0188:     matmul_emit_replay_program_no_mop<math_fidelity>(ct_dim, rt_dim, in0_tile_r_dim, in0_tile_c_dim, in1_tile_r_dim, in1_tile_c_dim, partial_face);
0189: }
0190: 
0191: template <MathFidelity math_fidelity>
0192: inline void matmul_execute_replay_no_mop(const std::uint32_t replay_buf_len, const bool reuse_a, const std::uint32_t t_dim)
0193: {
0194:     if constexpr (!is_high_fidelity(math_fidelity))
0195:     {
0196:         lltt::replay(ckernel::math::replay_buf_offset, replay_buf_len);
0197:         return;
0198:     }
0199: 
0200:     // HiFi paths replay the same full-tile program multiple times, then repair
0201:     // the A/B/F counter state to match what the next outer-loop iteration
0202:     // expects.
0203:     constexpr std::uint32_t num_replay = to_underlying(math_fidelity);
0204:     for (std::uint32_t replay = 0; replay < num_replay; replay++)
0205:     {
0206:         lltt::replay(ckernel::math::replay_buf_offset, replay_buf_len);

--- around line 224 ---
0208: 
0209:     if (t_dim > 1)
0210:     {
0211:         TTI_SETRWC(p_setrwc::CLR_NONE, 0, 0, 0, 0, p_setrwc::SET_F);
0212:     }
0213:     else if (reuse_a)
0214:     {
0215:         TTI_SETRWC(p_setrwc::CLR_A, 0, 0, 0, 0, p_setrwc::SET_ABD_F);
0216:     }
0217:     else
0218:     {
0219:         TTI_SETRWC(p_setrwc::CLR_B, 0, 0, 0, 0, p_setrwc::SET_ABD_F);
0220:     }
0221: }
0222: 
0223: template <MathFidelity math_fidelity>
0224: inline void matmul_run_no_mop_tdim1_reuse_a(
0225:     const std::uint32_t dst_index, [[maybe_unused]] const std::uint32_t ct_dim, const std::uint32_t rut_dim, const std::uint32_t replay_buf_len)
0226: {
0227:     for (std::uint32_t rut = 0; (rut + 1) < rut_dim; rut++)
0228:     {
0229:         math::set_dst_write_addr<DstTileShape::Tile32x32, UnpackDestination::SrcRegs>(dst_index + rut);
0230:         matmul_execute_replay_no_mop<math_fidelity>(replay_buf_len, true, 1);
0231:     }
0232: 
0233:     math::set_dst_write_addr<DstTileShape::Tile32x32, UnpackDestination::SrcRegs>(dst_index + rut_dim - 1);
0234:     matmul_execute_replay_no_mop<math_fidelity>(replay_buf_len, true, 1);
0235:     TTI_SETRWC(p_setrwc::CLR_B, 0, 0, 0, 0, p_setrwc::SET_ABD);
0236: }
0237: 
0238: template <MathFidelity math_fidelity>
0239: inline void matmul_run_no_mop_tdim1_reuse_b(
0240:     const std::uint32_t dst_index, const std::uint32_t ct_dim, const std::uint32_t rut_dim, const std::uint32_t replay_buf_len)
0241: {
0242:     for (std::uint32_t rut = 0; (rut + 1) < rut_dim; rut++)
0243:     {
0244:         math::set_dst_write_addr<DstTileShape::Tile32x32, UnpackDestination::SrcRegs>(dst_index + rut * ct_dim);
0245:         matmul_execute_replay_no_mop<math_fidelity>(replay_buf_len, false, 1);
0246:     }
0247: 
0248:     math::set_dst_write_addr<DstTileShape::Tile32x32, UnpackDestination::SrcRegs>(dst_index + (rut_dim - 1) * ct_dim);
0249:     matmul_execute_replay_no_mop<math_fidelity>(replay_buf_len, false, 1);
0250:     TTI_SETRWC(p_setrwc::CLR_A, 0, 0, 0, 0, p_setrwc::SET_ABD);
0251: }
0252: 
0253: template <MathFidelity math_fidelity>
0254: inline void matmul_run_no_mop_tdim_gt1_reuse_a(
0255:     const std::uint32_t dst_index, const std::uint32_t ct_dim, const std::uint32_t t_dim, const std::uint32_t rut_dim, const std::uint32_t replay_buf_len)
0256: {


===== tt_llk_blackhole/llk_lib/experimental/llk_math_matmul_custom_no_mop.h =====

--- around line 27 ---
0011: #include "ckernel_template.h"
0012: #include "cmath_common.h"
0013: #include "llk_assert.h"
0014: #include "llk_math_common.h"
0015: 
0016: using namespace ckernel;
0017: 
0018: // Helper functions for math fidelity
0019: constexpr int get_math_num_fidelity_phases(const MathFidelity math_fidelity)
0020: {
0021:     // LoFi = 0 has 0 fidelity phases
0022:     // HiFi2 = 1 has 1 phase, HiFi3 = 2 has 2 phases, HiFi4 = 3 has 3 phases
0023:     return ckernel::to_underlying(math_fidelity);
0024: }
0025: 
0026: template <MathFidelity math_fidelity, int THROTTLE_LEVEL>
0027: inline void matmul_configure_addrmod_no_mop(
0028:     const bool transpose,
0029:     [[maybe_unused]] const std::uint32_t in0_tile_r_dim = TILE_R_DIM,
0030:     [[maybe_unused]] const std::uint32_t in0_tile_c_dim = TILE_C_DIM,
0031:     [[maybe_unused]] const std::uint32_t in1_tile_r_dim = TILE_R_DIM,
0032:     [[maybe_unused]] const std::uint32_t in1_tile_c_dim = TILE_C_DIM,
0033:     [[maybe_unused]] const bool partial_face            = false)
0034: {
0035:     static_assert(THROTTLE_LEVEL >= 0 && THROTTLE_LEVEL <= 5, "THROTTLE_LEVEL must be in range [0, 5]");
0036:     constexpr bool high_fidelity     = math_fidelity != MathFidelity::LoFi;
0037:     constexpr int fidelity_increment = high_fidelity ? 1 : 0;
0038: 
0039:     // MVMUL does D = B*A
0040: 
0041:     // Inner Loop --> 32/8 = 4 times for the full 32x16 face
0042:     // DEST -- 8 rows are calculated each time
0043:     // SRCB -- 8 rows are needed
0044:     // SRCA -- full 16x16 gets used -- hardware will pair cols of A with rows of B
0045:     // D[8,16] = B[8,16] * A[16,16]
0046:     addr_mod_t {
0047:         .srca = {.incr = 0, .clr = 0, .cr = 0},
0048:         .srcb = {.incr = 8, .clr = 0, .cr = 0},
0049:         .dest = {.incr = 8, .clr = 0, .cr = 0},
0050:     }
0051:         .set(ADDR_MOD_0);
0052: 
0053:     // reset all, increment fidelity if we have more fidelity phases
0054:     addr_mod_t {
0055:         .srca     = {.incr = 0, .clr = 1, .cr = 1},
0056:         .srcb     = {.incr = 0, .clr = 1, .cr = 1},
0057:         .dest     = {.incr = 0, .clr = 1, .cr = 1},
0058:         .fidelity = {.incr = fidelity_increment, .clr = 0},
0059:     }

--- around line 127 ---
0111:     else
0112:     {
0113:         addr_mod_t {
0114:             .srca = {.incr = 32, .clr = 0, .cr = 1},
0115:             //.srca = {.incr = srca_set, .clr = 0, .cr = 1},
0116:             .srcb = {.incr = 48, .clr = 0, .cr = 1}, // cr=32 before, cr+48=16 after wrapping
0117:             .dest = {.incr = 0, .clr = 0, .cr = 1},
0118:             // .bias = {.incr = 1},
0119:         }
0120:             .set(ADDR_MOD_4);
0121:     }
0122: }
0123: 
0124: template <MathFidelity math_fidelity = MathFidelity::LoFi, int THROTTLE_LEVEL = 0>
0125: inline void matmul_configure_addrmod_reinit(const bool transpose = false)
0126: {
0127:     // Reinit must restore the full matmul address-modifier contract used by replay.
0128:     // In particular, transpose affects ADDR_MOD_1/4 and fidelity/throttle use ADDR_MOD_5/6.
0129:     matmul_configure_addrmod_no_mop<math_fidelity, THROTTLE_LEVEL>(transpose);
0130: }
0131: 
0132: template <MathFidelity math_fidelity>
0133: inline void matmul_configure_mop_custom(
0134:     const std::uint32_t ct_dim,
0135:     const std::uint32_t rt_dim,
0136:     [[maybe_unused]] const std::uint32_t in0_tile_r_dim = TILE_R_DIM,
0137:     [[maybe_unused]] const std::uint32_t in0_tile_c_dim = TILE_C_DIM,
0138:     [[maybe_unused]] const std::uint32_t in1_tile_r_dim = TILE_R_DIM,
0139:     [[maybe_unused]] const std::uint32_t in1_tile_c_dim = TILE_C_DIM,
0140:     [[maybe_unused]] const bool partial_face            = false)
0141: {
0142:     // in0 - loaded to SrcB
0143:     // in1 - loaded to SrcA
0144:     // Unpacker will always load faces in f0,f1,f2,f3 order
0145:     // if in1 is transposed then faces 1&2 need to be swapped during read
0146:     // by changing address increment amount via addr_mods
0147:     // Col major layout in dest only impacts destination address increment
0148:     // if col major layout faces are ordered as f0,f2,f1,f3
0149: 
0150:     [[maybe_unused]] constexpr int num_fidelity_phases = get_math_num_fidelity_phases(math_fidelity);
0151:     constexpr bool high_fidelity                       = math_fidelity != MathFidelity::LoFi;
0152: 
0153:     const bool reuse_a                         = ct_dim >= rt_dim;
0154:     [[maybe_unused]] const std::uint32_t t_dim = reuse_a ? rt_dim : ct_dim;
0155: 
0156:     const std::uint32_t replay_buf_len = 16;
0157: 
0158:     load_replay_buf(
0159:         ckernel::math::replay_buf_offset,

--- around line 201 ---
0185:                 // TTI_MVMUL(p_setrwc::CLR_NONE, 0, ADDR_MOD_1, 0); // B3A3 or B3A2 // reset srca/srcb/dest, increment phase (addr_mod_5)
0186:                 TTI_MVMUL(p_setrwc::CLR_NONE, 0, ADDR_MOD_5, 0); // B3A3 or B3A2 // reset srca/srcb/dest, increment phase (addr_mod_5)
0187:             }
0188:             else
0189:             {
0190:                 if (reuse_a)
0191:                 {
0192:                     TTI_MVMUL(p_setrwc::CLR_A, 0, ADDR_MOD_5, 0); // B3A3 or B3A2 // reset srca/srcb/dest, increment phase (addr_mod_5), clear src A
0193:                 }
0194:                 else
0195:                 {
0196:                     TTI_MVMUL(p_setrwc::CLR_B, 0, ADDR_MOD_5, 0); // B3A3 or B2A1 // reset srca/srcb/dest, increment phase (addr_mod_5), clear src A
0197:                 }
0198:             }
0199:         });
0200: 
0201:     // MOP template programming removed - will use direct replay calls
0202: }
0203: 
0204: template <int Level>
0205: void run_throttled_sequence_no_mop();
0206: 
0207: template <>
0208: void run_throttled_sequence_no_mop<1>()
0209: {
0210:     TTI_NOP;
0211:     TTI_MVMUL(p_setrwc::CLR_NONE, 0, ADDR_MOD_0, 0);
0212:     TTI_MVMUL(p_setrwc::CLR_NONE, 0, ADDR_MOD_1, 0);
0213:     TTI_MVMUL(p_setrwc::CLR_NONE, 0, ADDR_MOD_0, 0);
0214:     TTI_NOP;
0215:     TTI_MVMUL(p_setrwc::CLR_NONE, 0, ADDR_MOD_2, 0);
0216:     TTI_MVMUL(p_setrwc::CLR_NONE, 0, ADDR_MOD_0, 0);
0217:     TTI_MVMUL(p_setrwc::CLR_NONE, 0, ADDR_MOD_1, 0);
0218:     TTI_NOP;
0219:     TTI_MVMUL(p_setrwc::CLR_NONE, 0, ADDR_MOD_0, 0);
0220: }
0221: 
0222: template <>
0223: void run_throttled_sequence_no_mop<2>()
0224: {
0225:     TTI_NOP;
0226:     TTI_MVMUL(p_setrwc::CLR_NONE, 0, ADDR_MOD_0, 0);
0227:     TTI_MVMUL(p_setrwc::CLR_NONE, 0, ADDR_MOD_1, 0);
0228:     TTI_NOP;
0229:     TTI_MVMUL(p_setrwc::CLR_NONE, 0, ADDR_MOD_0, 0);
0230:     TTI_MVMUL(p_setrwc::CLR_NONE, 0, ADDR_MOD_2, 0);
0231:     TTI_NOP;
0232:     TTI_MVMUL(p_setrwc::CLR_NONE, 0, ADDR_MOD_0, 0);
0233:     TTI_MVMUL(p_setrwc::CLR_NONE, 0, ADDR_MOD_1, 0);

--- around line 259 ---
0243:     TTI_NOP;
0244:     TTI_MVMUL(p_setrwc::CLR_NONE, 0, ADDR_MOD_1, 0);
0245:     TTI_NOP;
0246:     TTI_MVMUL(p_setrwc::CLR_NONE, 0, ADDR_MOD_0, 0);
0247:     TTI_NOP;
0248:     TTI_MVMUL(p_setrwc::CLR_NONE, 0, ADDR_MOD_2, 0);
0249:     TTI_NOP;
0250:     TTI_MVMUL(p_setrwc::CLR_NONE, 0, ADDR_MOD_0, 0);
0251:     TTI_NOP;
0252:     TTI_MVMUL(p_setrwc::CLR_NONE, 0, ADDR_MOD_1, 0);
0253:     TTI_NOP;
0254:     TTI_MVMUL(p_setrwc::CLR_NONE, 0, ADDR_MOD_0, 0);
0255:     TTI_NOP;
0256: }
0257: 
0258: template <>
0259: void run_throttled_sequence_no_mop<4>()
0260: {
0261:     TTI_NOP;
0262:     TTI_MVMUL(p_setrwc::CLR_NONE, 0, ADDR_MOD_0, 0);
0263:     TTI_NOP;
0264:     TTI_NOP;
0265:     TTI_MVMUL(p_setrwc::CLR_NONE, 0, ADDR_MOD_1, 0);
0266:     TTI_NOP;
0267:     TTI_MVMUL(p_setrwc::CLR_NONE, 0, ADDR_MOD_0, 0);
0268:     TTI_NOP;
0269:     TTI_NOP;
0270: }
0271: 
0272: template <>
0273: void run_throttled_sequence_no_mop<5>()
0274: {
0275:     TTI_NOP;
0276:     TTI_NOP;
0277:     TTI_MVMUL(p_setrwc::CLR_NONE, 0, ADDR_MOD_0, 0);
0278:     TTI_NOP;
0279:     TTI_NOP;
0280:     TTI_MVMUL(p_setrwc::CLR_NONE, 0, ADDR_MOD_1, 0);
0281:     TTI_NOP;
0282:     TTI_NOP;
0283:     TTI_MVMUL(p_setrwc::CLR_NONE, 0, ADDR_MOD_0, 0);
0284:     TTI_NOP;
0285:     TTI_NOP;
0286: }
0287: 
0288: /*
0289:  * Programming of the MOP for the case we limit matmul compute throughput
0290:  * Done by inserting NOP instructions between MVMUL instructions of matmul kernel
0291:  *

--- around line 327 ---
0311:     // in1 - loaded to SrcA
0312:     // Unpacker will always load faces in f0,f1,f2,f3 order
0313:     // if in1 is transposed then faces 1&2 need to be swapped during read
0314:     // by changing address increment amount via addr_mods
0315:     // Col major layout in dest only impacts destination address increment
0316:     // if col major layout faces are ordered as f0,f2,f1,f3
0317: 
0318:     constexpr int num_fidelity_phases = get_math_num_fidelity_phases(math_fidelity);
0319:     constexpr bool high_fidelity      = math_fidelity != MathFidelity::LoFi;
0320:     static_assert((THROTTLE_LEVEL > 0) && (THROTTLE_LEVEL <= 5), "MM throttling only enabled for THROTTLE_LEVEL={1,2,3,4,5}");
0321:     LLK_ASSERT(
0322:         (in0_tile_r_dim == TILE_R_DIM) && (in0_tile_c_dim == TILE_C_DIM) && (in1_tile_r_dim == TILE_R_DIM) && (in1_tile_c_dim == TILE_C_DIM) && !partial_face,
0323:         "MM throttling only enabled for full 32x32 tile size");
0324: 
0325:     const bool reuse_a = ct_dim >= rt_dim;
0326: 
0327:     constexpr std::uint32_t replay_buf_len = (THROTTLE_LEVEL > 3) ? (1 + THROTTLE_LEVEL * 2) : ((THROTTLE_LEVEL > 1) ? (3 + THROTTLE_LEVEL * 4) : 10);
0328: 
0329:     load_replay_buf(
0330:         ckernel::math::replay_buf_offset,
0331:         replay_buf_len,
0332:         // Lambda function to load reply buffer
0333:         [] { run_throttled_sequence_no_mop<THROTTLE_LEVEL>(); });
0334: 
0335:     // MOP template programming removed - will use direct replay calls
0336: }
0337: 
0338: template <MathFidelity math_fidelity, int THROTTLE_LEVEL = 0>
0339: inline void _llk_math_matmul_init_no_mop_(
0340:     const std::uint32_t in0_tile_r_dim = TILE_R_DIM,
0341:     const std::uint32_t in0_tile_c_dim = TILE_C_DIM,
0342:     const std::uint32_t in1_tile_r_dim = TILE_R_DIM,
0343:     const std::uint32_t in1_tile_c_dim = TILE_C_DIM,
0344:     const bool partial_face            = false,
0345:     const std::uint32_t transpose      = 0,
0346:     const std::uint32_t ct_dim         = 1,
0347:     const std::uint32_t rt_dim         = 1)
0348: {
0349:     matmul_configure_addrmod_no_mop<math_fidelity, THROTTLE_LEVEL>(transpose, in0_tile_r_dim, in0_tile_c_dim, in1_tile_r_dim, in1_tile_c_dim, partial_face);
0350:     if constexpr (THROTTLE_LEVEL > 0)
0351:     {
0352:         matmul_configure_mop_throttled_no_mop<math_fidelity, THROTTLE_LEVEL>(
0353:             ct_dim, rt_dim, in0_tile_r_dim, in0_tile_c_dim, in1_tile_r_dim, in1_tile_c_dim, partial_face);
0354:     }
0355:     else
0356:     {
0357:         matmul_configure_mop_custom<math_fidelity>(ct_dim, rt_dim, in0_tile_r_dim, in0_tile_c_dim, in1_tile_r_dim, in1_tile_c_dim, partial_face);
0358:     }
0359:     math::reset_counters(p_setrwc::SET_ABD_F);

--- around line 384 ---
0368: inline void _llk_math_matmul_no_mop_(
0369:     std::uint32_t dst_index,
0370:     const std::uint32_t ct_dim                          = 1,
0371:     const std::uint32_t rt_dim                          = 1,
0372:     [[maybe_unused]] const std::uint32_t in0_tile_r_dim = TILE_R_DIM,
0373:     [[maybe_unused]] const std::uint32_t in0_tile_c_dim = TILE_C_DIM,
0374:     [[maybe_unused]] const std::uint32_t in1_tile_r_dim = TILE_R_DIM,
0375:     [[maybe_unused]] const std::uint32_t in1_tile_c_dim = TILE_C_DIM,
0376:     [[maybe_unused]] const bool partial_face            = false)
0377: {
0378:     const bool reuse_a                = ct_dim >= rt_dim;
0379:     const std::uint32_t t_dim         = reuse_a ? rt_dim : ct_dim;
0380:     const std::uint32_t rut_dim       = reuse_a ? ct_dim : rt_dim; // reuse-dim
0381:     constexpr int num_fidelity_phases = get_math_num_fidelity_phases(math_fidelity);
0382:     constexpr bool high_fidelity      = math_fidelity != MathFidelity::LoFi;
0383: 
0384:     // Compute replay buffer length based on tile dimensions (same logic as in matmul_configure_mop)
0385:     std::uint32_t replay_buf_len;
0386:     if constexpr (THROTTLE_LEVEL > 0)
0387:     {
0388:         replay_buf_len = (THROTTLE_LEVEL > 3) ? (1 + THROTTLE_LEVEL * 2) : ((THROTTLE_LEVEL > 1) ? (3 + THROTTLE_LEVEL * 4) : 10);
0389:     }
0390:     else
0391:     {
0392:         replay_buf_len = 16;
0393:     }
0394: 
0395:     for (std::uint32_t t = 0; t < t_dim; t++)
0396:     {
0397:         for (std::uint32_t rut = 0; rut < rut_dim; rut++)
0398:         {
0399:             math::set_dst_write_addr<DstTileShape::Tile32x32, UnpackDestination::SrcRegs>(dst_index + (reuse_a ? ct_dim * t + rut : t + rut * ct_dim));
0400: 
0401:             if constexpr (THROTTLE_LEVEL > 0)
0402:             {
0403:                 // Throttled execution
0404:                 if constexpr (THROTTLE_LEVEL > 3)
0405:                 {
0406:                     // THROTTLE_LEVEL 4 or 5: outer_loops = 2
0407:                     if constexpr (high_fidelity)
0408:                     {
0409:                         // outer loop for fidelity phases
0410:                         for (std::uint32_t phase = 0; phase < num_fidelity_phases; phase++)
0411:                         {
0412:                             // inner loop (2 iterations for standard tiles)
0413:                             for (std::uint32_t inner = 0; inner < 2; inner++)
0414:                             {
0415:                                 lltt::replay(ckernel::math::replay_buf_offset, replay_buf_len);
0416:                                 if (inner < 1)


===== tt_llk_wormhole_b0/llk_lib/llk_math_matmul.h =====

--- around line 300 ---
0284:         }
0285:         else
0286:         {
0287:             addr_mod_t {
0288:                 .srca = {.incr = 32, .clr = 0, .cr = 1},
0289:                 //.srca = {.incr = srca_set, .clr = 0, .cr = 1},
0290:                 .srcb = {.incr = 48, .clr = 0, .cr = 1}, // cr=32 before, cr+48=16 after wrapping
0291:                 .dest = {.incr = 0, .clr = 0, .cr = 1},
0292:                 .bias = {.incr = 1},
0293:             }
0294:                 .set(ADDR_MOD_4);
0295:         }
0296:     }
0297: }
0298: 
0299: template <MathFidelity math_fidelity>
0300: inline void matmul_configure_mop(
0301:     const std::uint32_t ct_dim,
0302:     const std::uint32_t rt_dim,
0303:     const std::uint32_t in0_tile_r_dim = TILE_R_DIM,
0304:     const std::uint32_t in0_tile_c_dim = TILE_C_DIM,
0305:     const std::uint32_t in1_tile_r_dim = TILE_R_DIM,
03
```

