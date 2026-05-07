# Logic Combinations

`LogicCombination` records how formal worlds or DomainKernels are intended to
interact: product combination, fibering, shallow HOL combination, shared-domain
combination, translation bridge, or advisory alignment.

The record includes component kernels, component formal worlds, interaction
axioms, conflict policy, faithfulness status, and benchmark status.

Logic combinations are unsafe for truth transfer by default. They become
candidate bridge infrastructure only after interaction semantics, conflict
policy, faithfulness, and benchmarks have been assessed. They do not alter
`KernelOracle` terminal-form behavior.
