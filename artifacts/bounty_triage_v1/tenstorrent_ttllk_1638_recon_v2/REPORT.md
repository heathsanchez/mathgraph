# tenstorrent/tt-llk #1638 Recon v2

## Issue

- Title: [Bounty $1000] Reduce RISCV instructions used to pass on tensix instructions using AI/Optimizer.
- Labels: P2, bounty, bounty_difficulty/medium, LLK
- Comments: 18

## Verdict

`MAYBE_HARDWARE_DOMAIN_RISK`

## Bounty fit

Why it fits MathGraph:

- bounded optimization/search problem
- measurable objective: reduce RISCV instructions
- semantic constraint: preserve tensix instruction sequence
- resource constraint: limited replay buffer usage

Main risk:

- may need Tenstorrent hardware/domain simulator for acceptance
- may not have an obvious local judge
- high codebase-specific knowledge burden

## Issue body excerpt

```text
The number of tensix instructions to do a particular task can be easily optimized with human thinking, as the main task would have an algorithm and the proper instructions and sequence can often be easily chosen. But to pass on the tensix insturctions to the tensix engine, we often use MOPs and Replay buffers to pass them so that the number of RISCV instructions are rerduced. That part has too many ways of accomplishing and is not too easy to find out what is the most optimal way all the time. 

This is where we can use AI to reduce the number of RISV instructions used, by varying the possibilities of writing the MOP and arrangement of the replay buffer. Overall the task is 

Objective : Minimize the number of RISCV instructions to issue instructions to tensix engine 
Constraints : Sequence of tensix instructions passed remains the same
                       Only specified amount of replay buffer is used (for example if Math thread uses whole of the buffer, it may clash with SFPU algorithms when they are run from a separate thread on WH/BH for the buffer being shared. 
                        Take into account two ways of writing mops and their constraints. 

An AI agent may be asked to do it for all the ops we have and then we filter out the good suggestions and apply them. 
```

## Candidate files

- `./tt_llk_wormhole_b0/instructions/assembly.yaml`
- `./tt_llk_wormhole_b0/common/inc/ckernel_instr_params.h`
- `./tt_llk_wormhole_b0/common/inc/ckernel.h`
- `./tt_llk_wormhole_b0/common/inc/ckernel_structs.h`
- `./tt_llk_wormhole_b0/common/inc/ckernel_debug.h`
- `./tt_llk_wormhole_b0/common/inc/cpack_common.h`
- `./tt_llk_wormhole_b0/common/inc/ckernel_xmov.h`
- `./tt_llk_wormhole_b0/llk_lib/experimental/llk_unpack_AB_sub_bcast_col_custom.h`
- `./tt_llk_wormhole_b0/llk_lib/experimental/llk_unpack_AB_reduce_custom_runtime.h`
- `./tt_llk_wormhole_b0/llk_lib/experimental/llk_unpack_AB_reduce_custom.h`
- `./tt_llk_wormhole_b0/llk_lib/llk_unpack_untilize.h`
- `./tt_llk_wormhole_b0/llk_lib/llk_unpack_common.h`
- `./tt_llk_wormhole_b0/llk_lib/llk_memory_checks.h`
- `./tt_llk_wormhole_b0/llk_lib/llk_unpack_reduce.h`
- `./tt_llk_wormhole_b0/llk_lib/llk_unpack_AB_matmul.h`
- `./tt_llk_wormhole_b0/llk_lib/llk_unpack_A.h`
- `./tt_llk_wormhole_b0/llk_lib/llk_math_common.h`
- `./tt_llk_wormhole_b0/llk_lib/llk_unpack_tilize.h`
- `./tt_llk_wormhole_b0/llk_lib/llk_unpack_AB.h`
- `./tt_llk_wormhole_b0/llk_lib/llk_unpack_AB_reduce.h`
- `./tt_llk_quasar/instructions/assembly.yaml`
- `./tt_llk_quasar/common/inc/ckernel_dest.h`
- `./tt_llk_quasar/common/inc/ckernel_riscv_debug.h`
- `./tt_llk_quasar/common/inc/ckernel_instr_params.h`
- `./tt_llk_quasar/common/inc/ckernel_trisc_common.h`
- `./tt_llk_quasar/common/inc/cmath_common.h`
- `./tt_llk_quasar/common/inc/ckernel.h`
- `./tt_llk_quasar/common/inc/cunpack_common.h`
- `./tt_llk_quasar/common/inc/ckernel_ops.h`
- `./tt_llk_quasar/common/inc/ckernel_vector.h`
- `./tt_llk_quasar/common/inc/ckernel_addrmod.h`
- `./tt_llk_quasar/common/inc/cpack_common.h`
- `./tt_llk_quasar/common/inc/ckernel_proj_params.h`
- `./tt_llk_quasar/llk_lib/llk_math_eltwise_unary_sfpu_common.h`
- `./tt_llk_quasar/llk_lib/llk_memory_checks.h`
- `./tt_llk_quasar/llk_lib/llk_pack_common.h`
- `./tt_llk_quasar/llk_lib/llk_math_common.h`
- `./tests/hw_specific/quasar/inc/tensix_types.h`
- `./tests/hw_specific/quasar/inc/tensix.h`
- `./.cursor/agents/sage-quasar.md`
- `./.cursor/agents/sage-blackhole.md`
- `./.cursor/agents/sage-wormhole.md`
- `./.cursor/rules/sage-of-the-codex.mdc`
- `./.cursor/Reports/tt_llk_quasar.md`
- `./tt_llk_wormhole_b0/common/inc/cunpack_common.h`
- `./tt_llk_wormhole_b0/common/inc/ckernel_template.h`
- `./tt_llk_wormhole_b0/common/inc/sfpu/ckernel_sfpu_exp.h`
- `./tt_llk_wormhole_b0/common/inc/ckernel_include.h`
- `./tt_llk_wormhole_b0/common/inc/ckernel_defs.h`
- `./tt_llk_wormhole_b0/llk_lib/experimental/llk_math_reduce_custom.h`
- `./tt_llk_wormhole_b0/llk_lib/experimental/llk_math_reduce_runtime_custom.h`
- `./tt_llk_wormhole_b0/llk_lib/llk_pack_rows.h`
- `./tt_llk_wormhole_b0/llk_lib/llk_math_eltwise_unary_datacopy.h`
- `./tt_llk_wormhole_b0/llk_lib/llk_pack_common.h`
- `./tt_llk_wormhole_b0/llk_lib/llk_defs.h`
- `./tt_llk_wormhole_b0/llk_lib/llk_pack.h`
- `./tt_llk_wormhole_b0/llk_lib/llk_math_reduce.h`
- `./tt_llk_wormhole_b0/llk_lib/llk_math_transpose_dest.h`
- `./.pre-commit-config.yaml`
- `./tt_llk_quasar/common/inc/ckernel_template.h`
- `./tt_llk_quasar/common/inc/ckernel_defs.h`
- `./tests/hw_specific/quasar/inc/t6_debug_map.h`
- `./tests/hw_specific/quasar/inc/cfg_defines.h`
- `./tests/python_tests/ai_gen/reduce_sfpu_unary.py`
- `./tests/python_tests/conftest.py`
- `./tests/python_tests/test_profiler_primitives.py`
- `./tests/python_tests/streams/test_stream_integration.py`
- `./tests/python_tests/test_zzz_pack.py`
- `./tests/python_tests/z_state/reconfig/test_math_reconfig.py`
- `./tests/python_tests/test_fast_tilize_tiny_tiles.py`
- `./tests/python_tests/fuser/fused_generator.py`
- `./tests/python_tests/fuser/fuser_config.py`
- `./tests/python_tests/test_profiler_overhead.py`
- `./tests/python_tests/test_boot_modes.py`
- `./tests/python_tests/helpers/counters.py`
- `./tests/python_tests/helpers/perf.py`
- `./tests/python_tests/helpers/device.py`
- `./tests/python_tests/helpers/stream.py`
- `./tests/python_tests/helpers/golden_generators.py`
- `./tests/python_tests/helpers/test_config.py`
- `./tests/python_tests/helpers/tensix.py`
- `./tests/python_tests/test_pack_dest_bank.py`
- `./tests/python_tests/test_sdpa_reinits.py`
- `./tests/setup_testing_env.sh`
- `./tests/sources/sdpa_reinits_test.cpp`
- `./tests/sources/math_transpose_perf.cpp`
- `./tests/helpers/include/params.h`
- `./tests/helpers/include/boot.h`
- `./tests/helpers/include/dev_mem_map.h`
- `./tests/helpers/include/ckernel_helper.h`
- `./tests/helpers/include/perf.h`
- `./tests/helpers/include/profiler.h`
- `./tests/helpers/src/trisc.cpp`
- `./docs/performance_counters/performance_counters.md`
- `./docs/llk/l2/top_level_overview.md`
- `./docs/llk/l1/intro.md`
- `./docs/tests/debugging_guide.md`
- `./docs/tests/infra_architecture.md`
- `./docs/tests/getting_started.md`
- `./README.md`
- `./tt_llk_blackhole/instructions/assembly.yaml`
- `./tt_llk_wormhole_b0/common/inc/cmath_common.h`
- `./tt_llk_wormhole_b0/common/inc/ckernel_ops.h`
- `./tt_llk_wormhole_b0/common/inc/ckernel_globals.h`
- `./tt_llk_wormhole_b0/common/inc/sfpu/ckernel_sfpu_reduce.h`
- `./tt_llk_wormhole_b0/common/inc/sfpu/ckernel_sfpu_cumsum.h`
- `./tt_llk_wormhole_b0/common/inc/sfpu/ckernel_sfpu_topk.h`
- `./tt_llk_wormhole_b0/common/inc/sfpu/ckernel_sfpu_add_top_row.h`
- `./tt_llk_wormhole_b0/common/inc/sfpu/ckernel_sfpu_welfords.h`
- `./tt_llk_wormhole_b0/common/inc/sfpu/ckernel_sfpu_where.h`
- `./tt_llk_wormhole_b0/common/inc/sfpu/ckernel_sfpu_reduce_custom.h`
- `./tt_llk_wormhole_b0/common/inc/sfpu/ckernel_sfpu_max_pool_indices.h`
- `./tt_llk_wormhole_b0/common/inc/ckernel_gpr_map.h`
- `./tt_llk_wormhole_b0/llk_lib/llk_math_eltwise_unary_sfpu.h`
- `./tt_llk_wormhole_b0/llk_lib/llk_math_matmul.h`
- `./tt_llk_wormhole_b0/llk_lib/experimental/llk_math_matmul_custom_no_mop.h`
- `./tt_llk_wormhole_b0/llk_lib/llk_math_eltwise_binary_sfpu.h`
- `./tt_llk_wormhole_b0/llk_lib/llk_math_welfords_sfpu.h`
- `./tt_llk_wormhole_b0/llk_lib/llk_math_eltwise_binary.h`
- `./CODE_OF_CONDUCT.md`

## Runnable detection

```json
{
  "suggested_commands": [
    "python3 -m pytest",
    "python3 -m pytest tests"
  ],
  "notes": [
    "pyproject.toml present",
    "tests directory present",
    "GitHub Actions workflows present"
  ],
  "workflow_notes": [
    ".github/workflows/build-quasar.yml: contains pytest",
    ".github/workflows/build-quasar.yml: contains python",
    ".github/workflows/collect-test-durations.yml: contains pytest",
    ".github/workflows/collect-test-durations.yml: contains python",
    ".github/workflows/nightly.yml: contains pytest",
    ".github/workflows/on-pr.yml: contains pytest",
    ".github/workflows/on-pr.yml: contains python",
    ".github/workflows/pre-commit.yml: contains python",
    ".github/workflows/run-perf-tests.yml: contains pytest",
    ".github/workflows/setup-and-test.yml: contains pytest",
    ".github/workflows/setup-and-test.yml: contains python"
  ]
}

```

## Light probe results

```json
{
  "pytest_collect_tests": {
    "rc": 2,
    "cmd": [
      "python3",
      "-m",
      "pytest",
      "--collect-only",
      "-q",
      "tests"
    ]
  }
}
```

## Candidate context excerpt

```text


===== ./tt_llk_wormhole_b0/instructions/assembly.yaml =====

--- around line 6 ---
0001: # SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC
0002: #
0003: # SPDX-License-Identifier: Apache-2.0
0004: 
0005: # Instruction types:
0006: #   This field only matters for verilog generation, it signifies which hierarchical decoder "owns" instruction
0007: #   LOCAL_CREGS  -
0008: #   PC_MODIFYING -
0009: #   COMPUTE      -
0010: #   COMMON_CREGS -
0011: #
0012: #
0013: # Functional Coverage:
0014: # --------------------------------------
0015: #
0016: # Auto-generated instruction-level FCOV is specified with the following three tags as commented in the example below.
0017: #
0018: #
0019: # SOME_INSTR:
0020: #   instrn_type: LOCAL_CREGS
0021: #   ex_resource: SYNC
0022: #   op_binary: 0xa0

--- around line 55 ---
0047: #           bins: [ {name: "dst_0", slice: "1",  interval: ["0x0","0x0"]},
0048: #                   {name: "dst_1", slice: "15", interval: ["0x1","0x10"]}]
0049: #
0050: #       - name: some_bool_field
0051: #         fcov_point_bool:                                   # This creates a coverage item for 'some_bool_field' as a boolean.
0052: #
0053: 
0054: ATGETM:
0055:     instrn_type: LOCAL_CREGS
0056:     ex_resource: SYNC
0057:     op_binary: 0xa0
0058:     fcov:
0059:     arguments:
0060:         - name: mutex_index
0061:           start_bit: 0
0062:           field_type: HEX
0063:           description: &mutex_index >
0064:               Mutex index
0065:                 0 - math
0066:                 2 - unpack0
0067:                 3 - unpack1
0068:                 4 - pack0
0069:                 5 - pack1
0070:                 6 - pack2
0071:                 7 - pack3

--- around line 83 ---
0075:                     {name: "unpack1",  value: "0x3"},
0076:                     {name: "pack0",    value: "0x4"},
0077:                     {name: "pack1",    value: "0x5"},
0078:                     {name: "pack2",  value: "0x6"},
0079:                     {name: "pack3",  value: "0x7"}]
0080:     description: >
0081:         Acquires mutex with index `mutex_index' for the issuing
0082:         thread. At most one thread can hold the mutex at any time.
0083:         Returns immediately if, when the instruction starts, mutex is
0084:         not held by any thread, or is held by the issuing thread.
0085:         Otherwise, stalls issuing thread until mutex is acquired. When
0086:         instruction completes, issuing thread holds the mutex, and it
0087:         must be released using instruction ATRELM.
0088: 
0089: ATRELM:
0090:     instrn_type: LOCAL_CREGS
0091:     ex_resource: SYNC
0092:     op_binary: 0xa1
0093:     arguments:
0094:         - name: mutex_index
0095:           start_bit: 0
0096:           field_type: HEX
0097:           description: *mutex_index
0098:     description: >
0099:         Releases mutex with index `mutex_index' if it is held by


===== ./tt_llk_wormhole_b0/common/inc/ckernel_instr_params.h =====

--- around line 10 ---
0002: //
0003: // SPDX-License-Identifier: Apache-2.0
0004: 
0005: #pragma once
0006: 
0007: // MT: This should be dissolved and moved to the appropriate place
0008: #include <cstdint>
0009: 
0010: #include "tensix.h"
0011: 
0012: // Hand-coded parameter encoding for various common instructions
0013: namespace ckernel
0014: {
0015: 
0016: struct p_setrwc
0017: {
0018:     constexpr static std::uint32_t CLR_A    = 0x1;
0019:     constexpr static std::uint32_t CLR_B    = 0x2;
0020:     constexpr static std::uint32_t CLR_AB   = 0x3;
0021:     constexpr static std::uint32_t CLR_NONE = 0x0;
0022: 
0023:     constexpr static std::uint32_t SET_A     = 0x1;
0024:     constexpr static std::uint32_t SET_B     = 0x2;
0025:     constexpr static std::uint32_t SET_AB    = 0x3;
0026:     constexpr static std::uint32_t SET_D     = 0x4;

--- around line 229 ---
0221:     // constexpr static uint SEM_ZERO    = 0x20;
0222:     // constexpr static uint SEM_MAX     = 0x40;
0223:     constexpr static std::uint32_t SRCA_CLR       = 0x100;
0224:     constexpr static std::uint32_t SRCB_CLR       = 0x200;
0225:     constexpr static std::uint32_t SRCA_VLD       = 0x400;
0226:     constexpr static std::uint32_t SRCB_VLD       = 0x800;
0227:     constexpr static std::uint32_t XMOV           = 0x1000;
0228:     constexpr static std::uint32_t TRISC_CFG      = 0x2000;
0229:     constexpr static std::uint32_t SFPU1          = 0x4000;
0230:     constexpr static std::uint32_t WAIT_SFPU      = 0x4000;
0231:     constexpr static std::uint32_t ALL_THREAD_RES = THCON | UNPACK | PACK | MATH | XMOV;
0232: 
0233:     // What to stall
0234:     constexpr static std::uint32_t STALL_TDMA   = 0x1;
0235:     constexpr static std::uint32_t STALL_SYNC   = 0x2;
0236:     constexpr static std::uint32_t STALL_PACK   = 0x4;
0237:     constexpr static std::uint32_t STALL_UNPACK = 0x8;
0238:     //    constexpr static uint STALL_XSEARCH = 0x10;
0239:     constexpr static std::uint32_t STALL_XMOV   = 0x10;
0240:     constexpr static std::uint32_t STALL_THCON  = 0x20;
0241:     constexpr static std::uint32_t STALL_MATH   = 0x40;
0242:     constexpr static std::uint32_t STALL_CFG    = 0x80;
0243:     constexpr static std::uint32_t STALL_SFPU   = 0x100;
0244:     constexpr static std::uint32_t STALL_THREAD = 0x1ff;
0245: 

--- around line 325 ---
0317:     constexpr static std::uint32_t SRCB_BCAST_ROW = 0x2;
0318:     constexpr static std::uint32_t SRCB_BCAST_ALL = 0x3;
0319: 
0320:     constexpr static std::uint32_t CLR_A  = 0x1;
0321:     constexpr static std::uint32_t CLR_B  = 0x2;
0322:     constexpr static std::uint32_t CLR_AB = 0x3;
0323: };
0324: 
0325: struct p_sfpu
0326: {
0327:     // SFPU registers
0328:     constexpr static std::uint32_t LREG0 = 0;
0329:     constexpr static std::uint32_t LREG1 = 1;
0330:     constexpr static std::uint32_t LREG2 = 2;
0331:     constexpr static std::uint32_t LREG3 = 3;
0332:     constexpr static std::uint32_t LREG4 = 4;
0333:     constexpr static std::uint32_t LREG5 = 5;
0334:     constexpr static std::uint32_t LREG6 = 6;
0335:     constexpr static std::uint32_t LREG7 = 7;
0336: 
0337:     // HW provided constants
0338:     constexpr static std::uint32_t LCONST_0_8373 = 8;
0339:     constexpr static std::uint32_t LCONST_0      = 9;
0340:     constexpr static std::uint32_t LCONST_1      = 10;
0341: 

--- around line 360 ---
0352:     constexpr static std::uint32_t kCONST_1_FP16A  = 0x3C00;
0353:     constexpr static std::uint32_t kCONST_0        = 0x0000;
0354:     constexpr static std::uint32_t kCONST_Exp_8Bit = 0;
0355:     constexpr static std::uint32_t kCONST_Exp_5Bit = 1;
0356: };
0357: 
0358: struct p_sfpswap
0359: {
0360:     // SFPSWAP instruction modes
0361:     constexpr static std::uint32_t UNCONDITIONALLY = 0;
0362:     constexpr static std::uint32_t ALL_ROWS_MAX    = 1;
0363:     constexpr static std::uint32_t ROWS_01_MAX     = 2;
0364:     constexpr static std::uint32_t ROWS_02_MAX     = 3;
0365:     constexpr static std::uint32_t ROWS_03_MAX     = 4;
0366:     constexpr static std::uint32_t ROW_0_MAX       = 5;
0367:     constexpr static std::uint32_t ROW_1_MAX       = 6;
0368:     constexpr static std::uint32_t ROW_2_MAX       = 5;
0369:     constexpr static std::uint32_t ROW_3_MAX       = 6;
0370: };
0371: 
0372: struct p_exp
0373: {
0374:     constexpr static std::uint32_t FRAC_BITS = 3;
0375:     constexpr static std::uint32_t C23_73    = 0x4340; // Based on FRAC_BITS
0376:     // ADJ_EXP = -0x4300 + 0x003F

--- around line 396 ---
0388:     constexpr static std::uint32_t PAYLOAD_32BIT       = 1;
0389:     constexpr static std::uint32_t PAYLOAD_128BIT      = 2;
0390:     constexpr static std::uint32_t PAYLOAD_TILE_HEADER = 3;
0391: 
0392:     constexpr static std::uint32_t MODE_IMMEDIATE = 0;
0393:     constexpr static std::uint32_t MODE_SIGNAL    = 1;
0394: };
0395: 
0396: struct p_mop
0397: {
0398:     constexpr static std::uint32_t MASK_LOOP   = 0;
0399:     constexpr static std::uint32_t DOUBLE_LOOP = 1;
0400: };
0401: 
0402: struct p_adddmareg
0403: {
0404:     constexpr static std::uint32_t REG_PLUS_REG = 0;
0405:     constexpr static std::uint32_t REG_PLUS_IMM = 1;
0406: };
0407: 
0408: constexpr static std::uint32_t REG2FLOP_FLOP_INDEX(std::uint32_t addr)
0409: {
0410:     return addr - THCON_CFGREG_BASE_ADDR32;
0411: }
0412: 


===== ./tt_llk_wormhole_b0/common/inc/ckernel.h =====

--- around line 11 ---
0003: // SPDX-License-Identifier: Apache-2.0
0004: 
0005: #pragma once
0006: 
0007: #include <cstring>
0008: #include <type_traits>
0009: #include <utility>
0010: 
0011: #include "ckernel_common_ops.h"
0012: #include "ckernel_instr_params.h"
0013: #include "ckernel_ops.h"
0014: #include "internal/risc_attribs.h"
0015: #include "llk_assert.h"
0016: #include "llk_defs.h"
0017: 
0018: // MT: This should be dissolved and moved to the appropriate place
0019: #include "tensix.h"
0020: 
0021: // compiler hints
0022: #define LIKELY(condition)   __builtin_expect(static_cast<bool>(condition), 1)
0023: #define UNLIKELY(condition) __builtin_expect(static_cast<bool>(condition), 0)
0024: #define UNREACHABLE()       __builtin_unreachable()
0025: 
0026: #define UNROLL_LOOP(factor) GCC unroll factor
0027: 

--- around line 48 ---
0040: #ifndef GPR_DEBUG_REGFILE
0041: #define GPR_DEBUG_REGFILE 0
0042: #endif
0043: 
0044: #define TT_ALWAYS_INLINE inline __attribute__((always_inline))
0045: 
0046: #include <cstdint>
0047: 
0048: #include "ckernel_include.h"
0049: 
0050: namespace ckernel
0051: {
0052: 
0053: constexpr std::uint32_t PACK_FLUSH_COUNTERS = // counters flush
0054:     (1 << PACK_COUNTERS_SEC2_pack_per_xy_plane_SHAMT) | (1 << PACK_COUNTERS_SEC2_pack_reads_per_xy_plane_SHAMT) |
0055:     (1 << PACK_COUNTERS_SEC2_pack_xys_per_tile_SHAMT);
0056: 
0057: constexpr std::uint32_t RESET_VAL          = 0;
0058: constexpr std::uint32_t KERNEL_IN_PROGRESS = 15;
0059: constexpr std::uint32_t KERNEL_COMPLETE    = 0xFF;
0060: 
0061: extern volatile std::uint32_t tt_reg_ptr *reg_base;
0062: extern volatile std::uint32_t tt_reg_ptr *pc_buf_base;
0063: extern volatile std::uint32_t tt_reg_ptr *regfile;
0064: } // namespace ckernel


===== ./tt_llk_wormhole_b0/common/inc/ckernel_structs.h =====

--- around line 9 ---
0001: // SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC
0002: //
0003: // SPDX-License-Identifier: Apache-2.0
0004: 
0005: #pragma once
0006: 
0007: #include <cstdint>
0008: 
0009: namespace ckernel
0010: {
0011: 
0012: // Semaphores mapping and trisc space -> tensix space conversion
0013: struct semaphore
0014: {
0015:     constexpr static std::uint32_t FPU_SFPU            = 0; // fpu <-> sfpu sync
0016:     constexpr static std::uint32_t MATH_PACK           = 1; // math <-> pack sync on dest register
0017:     constexpr static std::uint32_t UNPACK_TO_DEST      = 2; // unpack <-> math sync on unpack to dest
0018:     constexpr static std::uint32_t UNPACK_OPERAND_SYNC = 3; // unpack <-> pack, math sync on operand get/release
0019:     constexpr static std::uint32_t PACK_DONE           = 4; // Wait for beginning and end of each pack-iteration. For recording perf events and inserting delay.
0020:     constexpr static std::uint32_t UNPACK_SYNC         = 5; // trisc <-> unpack sync on hw kernel
0021:     // Wait for beginning and end of each unpack or math iteration. For recording perf events and inserting delay.
0022:     // This semaphore should only be used for either unpack or math. Not both at the same time.
0023:     constexpr static std::uint32_t UNPACK_MATH_DONE   = 6;
0024:     constexpr static std::uint32_t MATH_DONE          = 7; // wait for math to finish when unpacking to dest
0025:     constexpr static std::uint8_t NUM_SEMAPHORES      = 8; // number of semaphores, not a semaphore index

--- around line 38 ---
0030:     {
0031:         return (1 << sem_index);
0032:     }
0033: };
0034: 
0035: struct mutex
0036: {
0037:     constexpr static std::uint32_t REG_RMW = 0; // used for atomic register read-modify-write from different threads
0038:     constexpr static std::uint32_t SFPU    = 4; // used for atomic access to SFPU since it's instructions can be issued from both TRISC1 and TRISC2
0039: };
0040: 
0041: constexpr std::uint8_t PC_BUF_SEMAPHORE_BASE = 8;  // base address for semaphores in PC buffer

```

## Next decision

Proceed only if the next step identifies all four:

1. exact MOP/replay-buffer source files
2. exact baseline RISCV instruction-count metric
3. local simulator/test/benchmark for before/after
4. one small op/kernel where a safe patch can be attempted

If not, park this bounty and move to `xevrion-v2/agent-playground #2207` for easy cash or `tinygrad #3039` for prestige.

