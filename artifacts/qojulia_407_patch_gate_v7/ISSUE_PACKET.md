# qojulia/QuantumOptics.jl #407 Issue Packet

URL: https://github.com/qojulia/QuantumOptics.jl/issues/407
Title: Update the benchmark suite and bring it into the CI runner [$400]
State: OPEN
Labels: bug bounty, bounty:400
Assignees: (none)

## Body

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

## Comments

### nenadilic84 — 2026-02-13T07:38:13Z

I'd like to claim this bounty.

**Background:** I have experience with Julia benchmarking infrastructure (BenchmarkTools.jl, BenchmarkCI, PkgBenchmark) and Python interop via PythonCall.jl. I've recently contributed to several JuliaGraphs packages (IGraphs.jl, VNGraphs.jl, NetworkX.jl) including setting up CI pipelines.

**Plan:**

1. **Port existing benchmarks to BenchmarkTools.jl format** — adapt the current `benchmark/benchmarks.jl` to use `@benchmarkable` macros within a `BenchmarkGroup` hierarchy, matching the PkgBenchmark convention
2. **Set up BenchmarkCI infrastructure** — add `.github/workflows/Benchmark.yml` and `BenchmarkComment.yml` modeled after QuantumClifford.jl's CI, so every PR gets automatic performance regression reports
3. **Add comparative benchmarks** — use PythonCall.jl to run equivalent operations in QuTiP (Python) and add QuantumToolbox.jl comparisons, with results stored as JSON for reproducibility
4. **Create Makefile for benchmark webpage** — a simple `make benchmarks` target that runs all comparative benchmarks and generates a markdown/HTML summary page with tables and charts

I'll start with the CI infrastructure and existing benchmark port, then add the comparative benchmarks. Targeting a PR within the next few days.

### lmee — 2026-02-13T08:46:33Z

I reviewed "Update the benchmark suite and bring it into the CI runner [$400]" end-to-end and read all thread comments. The core problem appears to be: <summary <strong Bug bounty logistic details</strong (click to expand)</summary. My root-cause hypothesis is an FFI boundary mismatch (types/ownership/error handling) between wrapper code and native APIs. A key detail from the discussion is: "I'd like to claim this bounty. Background: I have experience with Julia benchmarking infrastructure (BenchmarkTools.jl, BenchmarkCI, PkgBenchmark) and Python interop via PythonCall." My plan is to define a minimal wrapper surface first, align types and ownership semantics with the native API, then add deterministic tests for correctness, memory safety, and failure-path behavior. I can start now and keep updates focused on evidence and validation. Best, Jerry Li

### nenadilic84 — 2026-02-13T20:12:10Z

Just to note, I already have a working PR up for this: #483. CI is green, benchmarks run and post comparison results on PRs. Happy to iterate on any feedback from maintainers.

### energypantry — 2026-02-16T17:10:40Z

Hi maintainers, I'd like to claim one instance of this bounty.

Plan for a reviewable first PR:
1) add a benchmark matrix for core workloads (time + allocs, stable random seeds),
2) run it in CI (nightly and PR mode with baseline vs branch comparison),
3) publish artifacts + short interpretation notes in PR comments.

I can open a small scoped first PR quickly, then iterate on your preferred benchmark coverage. If this slot is still available, I will start with CI wiring + 2 representative benchmarks.

### zhaog100 — 2026-03-29T13:24:45Z

/attempt

### Krastanov — 2026-04-28T17:52:38Z

Hi, @Ingenieralejo. You have messaged on a couple of our repos where we have bounties. I engaged in good faith in some of these posts, but given this message here, I now assume I have been talking to your LLM bot. I am blocking you from our repos and reporting you to github.
