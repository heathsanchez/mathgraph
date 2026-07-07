# Gold Recon Report

## Verdict

`PROMOTE_PAID_RECON`

## Decision

```json
{
  "repo": "qojulia/QuantumOptics.jl",
  "num": 407,
  "url": "https://github.com/qojulia/QuantumOptics.jl/issues/407",
  "title": "Update the benchmark suite and bring it into the CI runner [$400]",
  "state": "OPEN",
  "updatedAt": "2026-05-01T20:11:21Z",
  "reason": "$400 benchmark suite + CI runner, likely real judged route",
  "amount_estimate": 400.0,
  "money": true,
  "local_judge": true,
  "benchmark_or_metric": true,
  "has_surface": true,
  "prompt_risk": false,
  "hardware_risk": false,
  "web3_risk": false,
  "verdict": "PROMOTE_PAID_RECON"
}
```

## Issue body excerpt

<details>
<summary><strong>Bug bounty logistic details</strong> (click to expand)</summary>

To claim exclusive time to work on this bounty either post a comment here or message [skrastanov@umass.edu](mailto:skrastanov@umass.edu) with:

- your name
- github username
- **(optional)** a brief list of previous pertinent projects you have engaged in

Currently the project is claimed by `no one` until `...`.

If you want to, you can work on this project without making a claim, however claims are encouraged to give you and other contributors peace of mind. Whoever has made a claim takes precedence when solutions are considered.

You can always propose your own funded project, if you would like to contribute something of value that is not yet covered by an official bounty.
</details>

# Update the benchmark suite and bring it into the CI runner [$400]

QuantumOptics.jl has an in-depth benchmarking suite that has bitrotted in the last few years. To claim this bounty:

- Set up a benchmark-on-CI infrastructure (e.g. similar to the one in QuantumClifford.jl) that runs QuantumOptics-specific benchmarks on each pull request
- Include all old benchmarks in that infrastructure (reusing the existing benchmark suite as much as possible) and make it easy to add new micro-benchmarks as new features get developed.

The above are for the sake of the developers of this package. However, this bounty also requires the following to be done for the sake of users:

- Fix up the capability to run benchmarks in comparison to popular python packages (qutip) and add comparative Julia packages (QuantumToolbox.jl)
- Create a makefile that let's a developer to easily update the webpage presenting these comparative benchmarks to the user.

**Required skills**: Understanding of Julia's and Python's benchmarking infrastructure.

**Reviewer**: Stefan Krastanov and/or @david-pl 

**Duration**: 2 months

#### Payout procedure:

The Funding for these bounties comes from the National Science Foundation and from the NSF Center for Quantum Networks. The payouts are managed by the NumFOCUS foundation and processed in bulk once every two months. If you live in a country in which NumFOCUS can make payments, you can participate in this bounty program.

[Click here for more details about the bug bounty program.](https://github.com/QuantumSavory/.github/blob/main/BUG_BOUNTIES.md)

## Cheap commands

```text
pwd=/Users/heath/Documents/mathgraph-lean-work/external/money_gold_recon_v6/qojulia__QuantumOptics.jl_407

Julia Project.toml found.

julia not installed locally; cannot run Pkg.test without setup.

workflows:
.github/workflows/benchmark.yml
.github/workflows/ci.yml
.github/workflows/downgrade.yml
.github/workflows/TagBot.yml

```

## Inventory excerpt

```text
.buildkite/pipeline.yml
.git/config
.git/description
.git/HEAD
.git/hooks/applypatch-msg.sample
.git/hooks/commit-msg.sample
.git/hooks/fsmonitor-watchman.sample
.git/hooks/post-update.sample
.git/hooks/pre-applypatch.sample
.git/hooks/pre-commit.sample
.git/hooks/pre-merge-commit.sample
.git/hooks/pre-push.sample
.git/hooks/pre-rebase.sample
.git/hooks/pre-receive.sample
.git/hooks/prepare-commit-msg.sample
.git/hooks/push-to-checkout.sample
.git/hooks/update.sample
.git/index
.git/info/exclude
.git/logs/HEAD
.git/objects/pack/pack-ab4deda9db20d003d21bc2e869e52dd23a58feed.idx
.git/objects/pack/pack-ab4deda9db20d003d21bc2e869e52dd23a58feed.pack
.git/objects/pack/pack-ab4deda9db20d003d21bc2e869e52dd23a58feed.promisor
.git/objects/pack/pack-c0ec39c6edbcbaa6c04cebda9815ae2686fa546a.idx
.git/objects/pack/pack-c0ec39c6edbcbaa6c04cebda9815ae2686fa546a.pack
.git/objects/pack/pack-c0ec39c6edbcbaa6c04cebda9815ae2686fa546a.promisor
.git/packed-refs
.git/refs/heads/master
.git/shallow
.github/dependabot.yml
.github/workflows/benchmark.yml
.github/workflows/ci.yml
.github/workflows/downgrade.yml
.github/workflows/TagBot.yml
.gitignore
benchmark/benchmarks.jl
benchmark/Project.toml
CITATION.bib
CLAUDE.md
docs/examples/.gitignore
docs/examples/make.jl
docs/examples/markdown_template.tpl
docs/examples/notebooks/atom-dephasing.ipynb
docs/examples/notebooks/cavity-cooling.ipynb
docs/examples/notebooks/correlation-spectrum.ipynb
docs/examples/notebooks/doppler-cooling.ipynb
docs/examples/notebooks/jaynes-cummings.ipynb
docs/examples/notebooks/lasing-and-cooling.ipynb
docs/examples/notebooks/manybody-fourlevel-system.ipynb
docs/examples/notebooks/nparticles-in-double-well.ipynb
docs/examples/notebooks/optomech-cooling.ipynb
docs/examples/notebooks/particle-in-harmonic-trap.ipynb
docs/examples/notebooks/particle-into-barrier.ipynb
docs/examples/notebooks/pumped-cavity.ipynb
docs/examples/notebooks/quantum-kicked-top.ipynb
docs/examples/notebooks/quantum-zeno-effect.ipynb
docs/examples/notebooks/raman.ipynb
docs/examples/notebooks/ramsey.ipynb
docs/examples/notebooks/spin-orbit-coupled-BEC1D.ipynb
docs/examples/notebooks/superradiant-laser.ipynb
docs/examples/notebooks/three-level-maser.ipynb
docs/examples/notebooks/two-qubit-entanglement.ipynb
docs/examples/notebooks/vortex.ipynb
docs/examples/notebooks/wavepacket2D.ipynb
docs/examples/Project.toml
docs/examples/README.md
docs/make.jl
docs/Project.toml
docs/src/api.md
docs/src/assets/favicon.png
docs/src/assets/logo.png
docs/src/index.md
docs/src/installation.md
docs/src/metrics.md
docs/src/quantumobjects/bases.md
docs/src/quantumobjects/operators.md
docs/src/quantumobjects/quantumobjects.md
docs/src/quantumobjects/states.md
docs/src/quantumobjects/superoperators.md
docs/src/quantumsystems/charge.md
docs/src/quantumsystems/fock.md
docs/src/quantumsystems/manybody.md
docs/src/quantumsystems/nlevel.md
docs/src/quantumsystems/particle.md
docs/src/quantumsystems/quantumsystems.md
docs/src/quantumsystems/spin.md
docs/src/quantumsystems/subspace.md
docs/src/semiclassical.md
docs/src/steadystate.md
docs/src/stochastic/master.md
docs/src/stochastic/schroedinger.md
docs/src/stochastic/semiclassical.md
docs/src/stochastic/stochastic.md
docs/src/timecorrelations.md
docs/src/timeevolution/master.md
docs/src/timeevolution/mcwf.md
docs/src/timeevolution/schroedinger.md
docs/src/timeevolution/timedependent-problems.md
docs/src/timeevolution/timeevolution.md
docs/src/tutorial.md
LICENSE.md
Project.toml
README.md
src/bloch_redfield_master.jl
src/debug.jl
src/master.jl
src/mcwf.jl
src/phasespace.jl
src/QuantumOptics.jl
src/schroedinger.jl
src/semiclassical.jl
src/spectralanalysis.jl
src/steadystate_iterative.jl
src/steadystate.jl
src/stochastic_base.jl
src/stochastic_definitions.jl
src/stochastic_master.jl
src/stochastic_schroedinger.jl
src/stochastic_semiclassical.jl
src/time_dependent_operators.jl
src/timecorrelations.jl
src/timeevolution_base.jl
test/ForwardDiff_long_test.jl
test/gpu/implementation/definitions.jl
test/gpu/implementation/imports.jl
test/gpu/implementation/test_platform.jl
test/gpu/implementation/test_schroedinger_gpu.jl
test/gpu/implementation/utilities.jl
test/gpu/test_platform_AMDGPU.jl
test/gpu/test_platform_CUDA.jl
test/gpu/test_platform_Metal.jl
test/gpu/test_platform_OpenCL.jl
test/Project.toml
test/runtests.jl
test/test_aqua.jl
test/test_ForwardDiff.jl
test/test_jet.jl
test/test_phasespace.jl
test/test_sciml_broadcast_interfaces.jl
test/test_semiclassical.jl
test/test_spectralanalysis.jl
test/test_steadystate.jl
test/test_stochastic_definitions.jl
test/test_stochastic_master.jl
test/test_stochastic_schroedinger.jl
test/test_stochastic_semiclassical.jl
test/test_timecorrelations.jl
test/test_timeevolution_abstractdata.jl
test/test_timeevolution_bloch_redfield.jl
test/test_timeevolution_master.jl
test/test_timeevolution_mcwf.jl
test/test_timeevolution_pumpedcavity.jl
test/test_timeevolution_schroedinger.jl
test/test_timeevolution_tdops.jl
test/test_timeevolution_twolevel
```

## Grep excerpt

```text
===== money / judge / benchmark / test hits =====
./benchmark/benchmarks.jl:101:        # benchmark solving ODE problems on data of QO types
./benchmark/benchmarks.jl:102:        SUITE[name]["base array types"][string(dim)] = @benchmarkable solve(prob, DP5(); save_everystep=false) setup=(prob=eval($bench)($dim; pure=true))
./benchmark/benchmarks.jl:103:        # benchmark solving ODE problems on custom QO types
./benchmark/benchmarks.jl:104:        SUITE[name]["qo types"][string(dim)] = @benchmarkable solve(prob, DP5(); save_everystep=false) setup=(prob=eval($bench)($dim; pure=false))
./benchmark/benchmarks.jl:108:        # benchmark solving ODE problems on data of QO types
./benchmark/benchmarks.jl:109:        SUITE[name]["base array types"][string(dim)] = @benchmarkable solve(prob, EM(), dt=1/100; save_everystep=false) setup=(prob=eval($bench)($dim; pure=true))
./benchmark/benchmarks.jl:110:        # benchmark solving ODE problems on custom QO types
./benchmark/benchmarks.jl:111:        SUITE[name]["qo types"][string(dim)] = @benchmarkable solve(prob, EM(), dt=1/100; save_everystep=false) setup=(prob=eval($bench)($dim; pure=false))
./test/test_timeevolution_bloch_redfield.jl:1:@testitem "test_timeevolution_bloch_redfield.jl" begin
./test/test_timeevolution_bloch_redfield.jl:6:@testset "bloch-redfield" begin
./test/test_timeevolution_bloch_redfield.jl:28:@test isapprox(dense(R).data, known_result, atol=1e-5)
./test/test_timeevolution_bloch_redfield.jl:34:@test isapprox(ρt[end].data, rho_end, atol=1e-5)
./test/test_timeevolution_bloch_redfield.jl:35:@test ρt[end] != ρt[end-1]
./test/test_timeevolution_bloch_redfield.jl:36:@test isa(ρt, Vector{<:DenseOpType})
./test/test_timeevolution_bloch_redfield.jl:41:@test all(ρt .== ρt2)
./test/test_timeevolution_bloch_redfield.jl:45:@test length(z) == length(ρt)
./test/test_timeevolution_bloch_redfield.jl:46:@test isa(first(z), ComplexF64)
./test/test_timeevolution_bloch_redfield.jl:48:end # testset
./test/gpu/test_platform_AMDGPU.jl:1:@testitem "AMDGPU" tags = [:amdgpu] begin
./test/gpu/test_platform_AMDGPU.jl:3:    include("implementation/test_platform.jl")
./test/gpu/test_platform_AMDGPU.jl:10:    @testset "Device availability" begin
./test/gpu/test_platform_AMDGPU.jl:11:        @test can_run
./test/gpu/test_platform_AMDGPU.jl:16:        test_platform(AT, synchronize)
./test/gpu/test_platform_AMDGPU.jl:18:        @info "Skipping AMDGPU tests - no devices available"
./test/gpu/test_platform_CUDA.jl:1:@testitem "CUDA" tags = [:cuda] begin
./test/gpu/test_platform_CUDA.jl:3:    include("implementation/test_platform.jl")
./test/gpu/test_platform_CUDA.jl:10:    @testset "Device availability" begin
./test/gpu/test_platform_CUDA.jl:11:        @test can_run
./test/gpu/test_platform_CUDA.jl:16:        test_platform(AT, synchronize)
./test/gpu/test_platform_CUDA.jl:18:        @info "Skipping CUDA tests - no devices available"
./test/gpu/implementation/utilities.jl:1:# Utility functions for GPU time evolution testing
./test/gpu/implementation/utilities.jl:3:function create_test_system(n, AT; storage_eltype=ComplexF64)
./test/gpu/implementation/utilities.jl:4:    """Create a test quantum system and adapt it to the specified array type."""
./test/gpu/implementation/test_platform.jl:1:# Platform-agnostic GPU test runner
./test/gpu/implementation/test_platform.jl:5:include("test_schroedinger_gpu.jl")
./test/gpu/implementation/test_platform.jl:7:function test_platform(AT, synchronize; kwargs...)
./test/gpu/implementation/test_platform.jl:8:    """Run all GPU tests for the specified array type."""
./test/gpu/implementation/test_platform.jl:10:    @testset "QuantumOptics GPU Tests - $(AT)" begin
./test/gpu/implementation/test_platform.jl:12:        test_schroedinger_gpu(AT, synchronize; kwargs...)
./test/gpu/implementation/test_schroedinger_gpu.jl:1:function test_schroedinger_gpu(AT, synchronize; time_eltype=Float64, solver_kwargs=(;), kwargs...)
./test/gpu/implementation/test_schroedinger_gpu.jl:4:    @testset "Schrödinger Time Evolution GPU Tests" begin
./test/gpu/implementation/test_schroedinger_gpu.jl:8:        @testset "Single Oscillator" begin
./test/gpu/implementation/test_schroedinger_gpu.jl:9:            for n in test_sizes
./test/gpu/implementation/test_schroedinger_gpu.jl:10:                H, gpu_H, psi0, gpu_psi0 = create_test_system(n, AT; kwargs...)
./test/gpu/implementation/test_schroedinger_gpu.jl:12:                @test typeof(gpu_H.data) <: AT
./test/gpu/implementation/test_schroedinger_gpu.jl:13:                @test typeof(gpu_psi0.data) <: AT
./test/gpu/implementation/test_schroedinger_gpu.jl:21:                @test verify_timeevolution_result((t_cpu, psi_cpu), (t_gpu, psi_gpu))
./test/gpu/implementation/imports.jl:1:# Required imports for GPU testing
./test/gpu/implementation/definitions.jl:1:# Test parameters for GPU time evolution tests
./test/gpu/implementation/definitions.jl:2:const test_sizes = [2, 4, 8]
./test/gpu/test_platform_OpenCL.jl:1:@testitem "OpenCL" tags = [:opencl] begin
./test/gpu/test_platform_OpenCL.jl:3:    include("implementation/test_platform.jl")
./test/gpu/test_platform_OpenCL.jl:17:    @testset "Device availability" begin
./test/gpu/test_platform_OpenCL.jl:18:        @test can_run
./test/gpu/test_platform_OpenCL.jl:23:        test_platform(AT, synchronize)
./test/gpu/test_platform_OpenCL.jl:25:        @info "Skipping OpenCL tests - no devices available"
./test/gpu/test_platform_Metal.jl:1:@testitem "Metal" tags = [:metal] begin
./test/gpu/test_platform_Metal.jl:3:    include("implementation/test_platform.jl")
./test/gpu/test_platform_Metal.jl:10:    @testset "Device availability" begin
./test/gpu/test_platform_Metal.jl:11:        @test can_run
./test/gpu/test_platform_Metal.jl:16:        test_platform(AT, synchronize;
./test/gpu/test_platform_Metal.jl:22:        @info "Skipping Metal tests - no devices available"
./test/runtests.jl:1:# GPU test flags
./test/runtests.jl:5:    @info "Skipping GPU tests -- only executed on *NIX platforms."
./test/runtests.jl:13:        @info "Skipping GPU tests -- must be explicitly enabled."
./test/runtests.jl:16:        @info "Running with $(GPU_TEST) tests."
./test/runtests.jl:37:# filter for the test
./test/runtests.jl:38:testfilter = ti -> begin
./test/runtests.jl:78:println("Starting tests with $(Threads.nthreads()) threads out of `Sys.CPU_THREADS = $(Sys.CPU_THREADS)`...")
./test/runtests.jl:80:@run_package_tests filter=testfilter
./test/test_timeevolution_abstractdata.jl:1:@testitem "test_timeevolution_abstractdata" begin
./test/test_timeevolution_abstractdata.jl:19:@testset "abstract-data" begin
./test/test_timeevolution_abstractdata.jl:73:    @test psi1==psi2
./test/test_timeevolution_abstractdata.jl:79:    @test psi1.data≈psi2.data
./test/test_timeevolution_abstractdata.jl:138:@test tracedistance(L*ρ₀, ρ) < 1e-10
./test/test_timeevolution_abstractdata.jl:143:@test isa(ρ.data, TestData)
./test/test_timeevolution_abstractdata.jl:144:@test tracedistance(dense(exp(dense(L)*T[end])*ρ₀), dense(ρ)) < 1e-6
./test/test_timeevolution_abstractdata.jl:146:@test isa(ρ₀.data, TestData) && isa(H.data,TestData) && all(isa(j.data,TestData) for j=J)
./test/test_timeevolution_abstractdata.jl:148:@test isa(ρt[end].data, TestData)
./test/test_timeevolution_abstractdata.jl:149:@test tracedistance(dense(ρt[end]), dense(ρ)) < 1e-5
./test/test_timeevolution_abstractdata.jl:197:@test Ψt == Ψt2
./test/test_timeevolution_abstractdata.jl:201:@test norm(Ψt[end]-Ψ) < 1e-5
./test/test_timeevolution_abstractdata.jl:204:@test norm(Ψt[end]-Ψ) > 0.1
./test/test_timeevolution_abstractdata.jl:233:f(t, psi::Ket) = @test 1e-5 > norm(psi - U(t)*psi0)
./test/test_timeevolution_abstractdata.jl:238:f(t, rho) = @test 1e-5 > tracedistance(dense(rho), dm(U(t)*psi0))
./test/test_timeevolution_abstractdata.jl:242:end # testset
./test/test_timeevolution_mcwf.jl:1:@testitem "test_timeevolution_mcwf" begin
./test/test_timeevolution_mcwf.jl:6:@testset "mcwf" begin
./test/test_timeevolu
```
