I did a focused static pass on #1638 and found what looks like a good first wedge: the matmul MOP/no-MOP surface, especially the existing `llk_math_matmul_custom_no_mop.h` experimental headers plus the `perf_math_matmul.py` / `math_matmul_perf.cpp` performance tests.

I also found the hardware counter docs/code that mention thread instruction counts, including the counter IDs in the performance counter path. Before attempting a patch, what exact local command should contributors use as the acceptance metric for this bounty?

Specifically:
1. Should we optimize/measure `tests/python_tests/perf_math_matmul.py` first, or another preferred op?
2. Should the score be taken from `pytest --compile-producer/--compile-consumer -m perf`, a performance counter CSV, profiler output, or CI device perf results?
3. For the objective “minimize RISCV instructions,” which counter/report column should be treated as canonical?
4. Is the existing `llk_math_matmul_custom_no_mop.h` path an acceptable starting point for a small PR, or do you prefer changes in the generic MOP/replay-buffer template code?

I can produce a small before/after patch once the exact scoring command and target op are confirmed.
