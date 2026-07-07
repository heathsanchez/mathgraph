# Cash Refilter v20

## Real candidates

### 1. simonmichael/hledger#1825 - hledger-ui --watch consumes more CPU and RAM over time [$150 x 3]

- Real score: `130`
- Original score: `95`
- Money: `$150`
- URL: https://github.com/simonmichael/hledger/issues/1825
- Reasons: known-real-project, meaningful-payout, money≈$150, local/test/benchmark surface, patchable wording, stack fit, available language
- Snippet: An idle hledger-ui with `--watch`, left running for days, may show gradually increasing CPU usage - 1%, 2%, 3%, 4%... - and RAM usage. I have always seen this on mac, and @the-solipsist sees it on ubuntu gnu/linux. I believe it is more apparent when you have a lot of accounts / transactions. I seem to remember, or I have assumed, that it's a problem with the underlying C file-watching library (which might be different on each platform). As a workaround, you can occasionally quit and restart hled

### 2. QuantumSavory/QuantumSavory.jl#131 - More thorough benchmarks [$200]

- Real score: `127`
- Original score: `82`
- Money: `$200`
- URL: https://github.com/QuantumSavory/QuantumSavory.jl/issues/131
- Reasons: known-real-project, meaningful-payout, patchable-surface-title, money≈$200, local/test/benchmark surface, patchable wording, stack fit
- Snippet: <details> <summary><strong>Bug bounty logistic details</strong> (click to expand)</summary> To claim exclusive time to work on this bounty either post a comment here or message [skrastanov@umass.edu](mailto:skrastanov@umass.edu) with: - your name - github username - **(optional)** a brief list of previous pertinent projects you have engaged in If you want to, you can work on this project without making a claim, however claims are encouraged to give you and other contributors peace of mind. Whoev

### 3. tinygrad/tinygrad#3039 - Bounty: Fast parallel scan (Mamba, etc). 

- Real score: `114`
- Original score: `79`
- Money: `$500`
- URL: https://github.com/tinygrad/tinygrad/issues/3039
- Reasons: known-real-project, meaningful-payout, money≈$500, local/test/benchmark surface, patchable wording, stack fit, available language, claim/assigned language
- Snippet: It would be great to have a general parallel prefix sum (associative scan) operation in tinygrad, something like [associative_scan](https://jax.readthedocs.io/en/latest/_autosummary/jax.lax.associative_scan.html) in JAX or [scan_associative](https://www.tensorflow.org/probability/api_docs/python/tfp/math/scan_associative) in TensorFlow Probability. This operation is key for the parallelization of some algorithms in CRFs, [filtering/smoothing in state space models](https://github.com/EEA-sensors/

### 4. JuliaGraphs/Graphs.jl#446 - A reliable idiomatic wrapper for the C library `igraphs` [$400]

- Real score: `107`
- Original score: `72`
- Money: `$400`
- URL: https://github.com/JuliaGraphs/Graphs.jl/issues/446
- Reasons: known-real-project, meaningful-payout, money≈$400, local/test/benchmark surface, patchable wording, stack fit, possible hardware dependency
- Snippet: # A reliable idiomatic `igraphs` wrapper [$400] The JuliaGraphs/IGraphs.jl package already exists and provides a simple low-level wrapper for the igraph C library. A lot of this work probably will not be directly in the Graphs.jl repository. - [ ] Fast conversion and/or views between Graphs.jl types and the C structures of igraph (slow converters already exist for simple graphs and some vectors/matrices) - [ ] Complete Graph API support for the IGraph types (so that IGraph types can be used in a

### 5. QuantumSavory/QuantumSymbolics.jl#73 - A backend for QuantumCumulants.jl [$200]

- Real score: `107`
- Original score: `72`
- Money: `$200`
- URL: https://github.com/QuantumSavory/QuantumSymbolics.jl/issues/73
- Reasons: known-real-project, meaningful-payout, money≈$200, local/test/benchmark surface, patchable wording, stack fit, available language, claim/assigned language
- Snippet: # A backend for QuantumCumulants.jl [$200] The QuantumCumulants library (part of the QuantumOptics organization) provides for an elegant way to solve truncated differential equations for expectation values of quantum observables. To claim this bounty you need to create an `express` interface for converting symbolic objects from QuantumSymbolics into objects QuantumCumulants can work with. **Required skills**: Knowledge of the QuantumCumulants library **Reviewer**: Stefan Krastanov and/or @david-

### 6. tscircuit/dsn-converter#54 - We can't convert Smoothie Board to Circuit JSON

- Real score: `103`
- Original score: `68`
- Money: `$70`
- URL: https://github.com/tscircuit/dsn-converter/issues/54
- Reasons: known-real-project, patchable-surface-title, money≈$70, local/test/benchmark surface, patchable wording, stack fit, available language, claim/assigned language
- Snippet: Smoothie Board: https://github.com/freerouting/freerouting/blob/master/tests/Issue145-smoothieboard.dsn Upload to DSN Viewer: https://dsn.tscircuit.com/ This is probably a pretty hard multi-step issue. Make sure to download freerouting to make sure the snapshot resembles the DSN file. In addition to the bounty, we will likely tip for steps along the way because doing it in one big PR may be counter-productive. /bounty $70 ![Image](https://github.com/user-attachments/assets/a612114f-df22-434c-80a

### 7. tscircuit/tscircuit#328 - Build the Arduino Nano with tscircuit

- Real score: `102`
- Original score: `77`
- Money: `$1000`
- URL: https://github.com/tscircuit/tscircuit/issues/328
- Reasons: known-real-project, assigned-risk, meaningful-payout, patchable-surface-title, money≈$1000, local/test/benchmark surface, patchable wording, stack fit
- Assignees: seveibar
- Snippet: Create the Arduino Nano on tscircuit snippets. https://store-usa.arduino.cc/products/arduino-nano?queryID=undefined&selectedStore=us /bounty $100 To get the bounty, you just need to edit the README and add a link to your Arduino Nano. We will actually order your board and test it! Please share your work on discord and we will help you with design issues. tscircuit is still in active development, and this is a fairly difficult board, you may need the team to help build features as you go, stay ac

### 8. BitgesellOfficial/bitgesell#32 - BGL PR bounty hunt

- Real score: `79`
- Original score: `69`
- Money: `$100`
- URL: https://github.com/BitgesellOfficial/bitgesell/issues/32
- Reasons: meaningful-payout, money≈$100, local/test/benchmark surface, patchable wording, stack fit, available language, claim/assigned language
- Snippet: To get more people involved and provide motivation, we are announcing Bitgesell Pull Request bounty hunt! The rules are simple: - You can create any reasonable pull request that may contain any modifications, including, but not limited to: - Refactoring and simplification; - Test fixes (_1 test group/file fixed by single PR counts_!); - Cleanup of features that are no longer used (e.g. non-segwit transactions); - Documentation and comments (but if no code changes then some reasonable amount of c

### 9. SatoshiPortal/bdk-flutter#1 - Bounty for reproducible cross-compilation of rust libraries for Android, Linux, Ios and Macos targets - 0.03 BTC ($2000)

- Real score: `77`
- Original score: `77`
- Money: `$2000`
- URL: https://github.com/SatoshiPortal/bdk-flutter/issues/1
- Reasons: assigned-risk, meaningful-payout, patchable-surface-title, money≈$2000, local/test/benchmark surface, patchable wording, stack fit, assigned
- Assignees: i5hi
- Snippet: This bounty is for bdk-flutter but will also be used for lwk-dart and boltz-dart All builds are currently functional but not reproducible/verifiable. **Requirements:** Android & Linux: A build environment using bash scripts, makefile and Docker, that builds on Linux & Mac hosts iOS & MacOS: A build environment using bash scripts and makefile, that builds on Mac hosts Reproducibility: A bash (and python?) script that can verify github releases against local builds. The library developers will be 

### 10. JuliaGraphs/Graphs.jl#447 - A reliable idiomatic wrapper for the C++ library `LEMON` [$400]

- Real score: `67`
- Original score: `52`
- Money: `$400`
- URL: https://github.com/JuliaGraphs/Graphs.jl/issues/447
- Reasons: known-real-project, assigned-risk, meaningful-payout, money≈$400, local/test/benchmark surface, patchable wording, stack fit, available language
- Assignees: AJ0070
- Snippet: # A reliable idiomatic `LEMON` wrapper [$400] The JuliaGraphs/LEMONGraphs.jl package already exists and provides an extremely barebones wrapper for the LEMON C++ library. It is barely more than a proof of concept for the build infrastructure. A lot of this work probably will not be directly in the Graphs.jl repository. - [ ] Fast conversion and/or views between Graphs.jl types and the C++ structures of LEMON (slow converters already exist for simple graphs) - [ ] Complete Graph API support for t

### 11. JuliaGraphs/Graphs.jl#449 - A reliable idiomatic wrapper for networkx [$400]

- Real score: `67`
- Original score: `52`
- Money: `$400`
- URL: https://github.com/JuliaGraphs/Graphs.jl/issues/449
- Reasons: known-real-project, assigned-risk, meaningful-payout, money≈$400, local/test/benchmark surface, patchable wording, stack fit, available language
- Assignees: Syuizen
- Snippet: # A reliable idiomatic `networkx` wrapper [$400] Using networkx through PythonCall.jl is trivially easy. This bounty is mostly about creating a new NetworkX.jl wrapper (by using PythonCall.jl) that provides quality-of-life improvements, - [ ] Fast conversion and/or views between Graphs.jl types and the networkx structures - [ ] Complete Graph API support for the newly created networkx wrapper types (so that networkx types can be used in all already existing Graph.jl algorithms that do not peek b

## Immediate recommendation

1. hledger remains best if a verifier can be obtained.
2. If hledger has no local executable/toolchain, use the next real Julia/benchmark candidate instead.
3. Avoid synthetic bounty farms and mirror/proxy bounty repos.

