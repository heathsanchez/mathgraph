# qojulia PR #528 Check Inspect v13

## Known state

- PR is draft.
- PR is mergeable.
- The visible failing check is the existing `Benchmarks / benchmark (pull_request_target)` workflow.
- New workflows from forked PRs may be awaiting maintainer approval.

## Error hits

- L795: `benchmark	Run MilesCranmer/AirspeedVelocity.jl@action-v1	2026-07-07T05:50:27.2266845Z   [8] ^[[0m^[[1mbenchmark^[[22m^[[0m^[[1m(^[[22m^[[90mpackage_specs^[[39m::^[[0mVector^[[90m{Pkg.Types.PackageSpec}^[[39m; ^[[90moutput_dir^[[39m::^[[0mSt`
- L796: `benchmark	Run MilesCranmer/AirspeedVelocity.jl@action-v1	2026-07-07T05:50:27.2268324Z ^[[90m    @^[[39m ^[[35mAirspeedVelocity.Utils^[[39m ^[[90m~/.julia/packages/AirspeedVelocity/ZJ8DT/src/^[[39m^[[90m^[[4mUtils.jl:510^[[24m^[[39m`
- L797: `benchmark	Run MilesCranmer/AirspeedVelocity.jl@action-v1	2026-07-07T05:50:27.2268783Z   [9] ^[[0m^[[1mbenchmark^[[22m`
- L798: `benchmark	Run MilesCranmer/AirspeedVelocity.jl@action-v1	2026-07-07T05:50:27.2269325Z ^[[90m    @^[[39m ^[[90m~/.julia/packages/AirspeedVelocity/ZJ8DT/src/^[[39m^[[90m^[[4mUtils.jl:481^[[24m^[[39m^[[90m [inlined]^[[39m`
- L799: `benchmark	Run MilesCranmer/AirspeedVelocity.jl@action-v1	2026-07-07T05:50:27.2278541Z  [10] ^[[0m^[[1mbenchmark^[[22m^[[0m^[[1m(^[[22m^[[90mpackage_name^[[39m::^[[0mString, ^[[90mrevs^[[39m::^[[0mVector^[[90m{String}^[[39m; ^[[90moutput_dir`
- L800: `benchmark	Run MilesCranmer/AirspeedVelocity.jl@action-v1	2026-07-07T05:50:27.2280309Z ^[[90m    @^[[39m ^[[35mAirspeedVelocity.Utils^[[39m ^[[90m~/.julia/packages/AirspeedVelocity/ZJ8DT/src/^[[39m^[[90m^[[4mUtils.jl:417^[[24m^[[39m`
- L801: `benchmark	Run MilesCranmer/AirspeedVelocity.jl@action-v1	2026-07-07T05:50:27.2281803Z  [11] ^[[0m^[[1mbenchpkg^[[22m^[[0m^[[1m(^[[22m^[[90mpackage_name^[[39m::^[[0mString; ^[[90mrev^[[39m::^[[0mString, ^[[90moutput_dir^[[39m::^[[0mString, ^`
- L802: `benchmark	Run MilesCranmer/AirspeedVelocity.jl@action-v1	2026-07-07T05:50:27.2283315Z ^[[90m    @^[[39m ^[[35mAirspeedVelocity.BenchPkg^[[39m ^[[90m~/.julia/packages/AirspeedVelocity/ZJ8DT/src/^[[39m^[[90m^[[4mBenchPkg.jl:93^[[24m^[[39m`
- L803: `benchmark	Run MilesCranmer/AirspeedVelocity.jl@action-v1	2026-07-07T05:50:27.2284640Z  [12] ^[[0m^[[1mcommand_main^[[22m^[[0m^[[1m(^[[22m^[[90mARGS^[[39m::^[[0mVector^[[90m{String}^[[39m^[[0m^[[1m)^[[22m`
- L804: `benchmark	Run MilesCranmer/AirspeedVelocity.jl@action-v1	2026-07-07T05:50:27.2285646Z ^[[90m    @^[[39m ^[[35mAirspeedVelocity.BenchPkg^[[39m ^[[90m~/.julia/packages/Comonicon/F3QqZ/src/codegen/^[[39m^[[90m^[[4mjulia.jl:343^[[24m^[[39m`
- L805: `benchmark	Run MilesCranmer/AirspeedVelocity.jl@action-v1	2026-07-07T05:50:27.2286412Z  [13] ^[[0m^[[1mcommand_main^[[22m^[[0m^[[1m(^[[22m^[[0m^[[1m)^[[22m`
- L806: `benchmark	Run MilesCranmer/AirspeedVelocity.jl@action-v1	2026-07-07T05:50:27.2287317Z ^[[90m    @^[[39m ^[[35mAirspeedVelocity.BenchPkg^[[39m ^[[90m~/.julia/packages/Comonicon/F3QqZ/src/codegen/^[[39m^[[90m^[[4mjulia.jl:90^[[24m^[[39m`
- L807: `benchmark	Run MilesCranmer/AirspeedVelocity.jl@action-v1	2026-07-07T05:50:27.2287849Z  [14] top-level scope`
- L808: `benchmark	Run MilesCranmer/AirspeedVelocity.jl@action-v1	2026-07-07T05:50:27.2288118Z ^[[90m    @^[[39m ^[[90m~/.julia/bin/^[[39m^[[90m^[[4mbenchpkg:14^[[24m^[[39m`
- L809: `benchmark	Run MilesCranmer/AirspeedVelocity.jl@action-v1	2026-07-07T05:50:27.2288792Z  [15] ^[[0m^[[1minclude^[[22m^[[0m^[[1m(^[[22m^[[90mmod^[[39m::^[[0mModule, ^[[90m_path^[[39m::^[[0mString^[[0m^[[1m)^[[22m`
- L810: `benchmark	Run MilesCranmer/AirspeedVelocity.jl@action-v1	2026-07-07T05:50:27.2289618Z ^[[90m    @^[[39m ^[[90mBase^[[39m ^[[90m./^[[39m^[[90m^[[4mBase.jl:306^[[24m^[[39m`
- L811: `benchmark	Run MilesCranmer/AirspeedVelocity.jl@action-v1	2026-07-07T05:50:27.2290239Z  [16] ^[[0m^[[1mexec_options^[[22m^[[0m^[[1m(^[[22m^[[90mopts^[[39m::^[[0mBase.JLOptions^[[0m^[[1m)^[[22m`
- L812: `benchmark	Run MilesCranmer/AirspeedVelocity.jl@action-v1	2026-07-07T05:50:27.2290839Z ^[[90m    @^[[39m ^[[90mBase^[[39m ^[[90m./^[[39m^[[90m^[[4mclient.jl:317^[[24m^[[39m`
- L813: `benchmark	Run MilesCranmer/AirspeedVelocity.jl@action-v1	2026-07-07T05:50:27.2291307Z  [17] ^[[0m^[[1m_start^[[22m^[[0m^[[1m(^[[22m^[[0m^[[1m)^[[22m`
- L814: `benchmark	Run MilesCranmer/AirspeedVelocity.jl@action-v1	2026-07-07T05:50:27.2291802Z ^[[90m    @^[[39m ^[[90mBase^[[39m ^[[90m./^[[39m^[[90m^[[4mclient.jl:550^[[24m^[[39m`
- L815: `benchmark	Run MilesCranmer/AirspeedVelocity.jl@action-v1	2026-07-07T05:50:27.2292298Z in expression starting at /home/runner/.julia/bin/benchpkg:14`
- L816: `benchmark	Run MilesCranmer/AirspeedVelocity.jl@action-v1	2026-07-07T05:50:27.5795085Z ##[error]Process completed with exit code 1.`
- L817: `benchmark	Post Run MilesCranmer/AirspeedVelocity.jl@action-v1	﻿2026-07-07T05:50:27.5966118Z Post job cleanup.`
- L818: `benchmark	Post Run MilesCranmer/AirspeedVelocity.jl@action-v1	2026-07-07T05:50:27.6067492Z Post job cleanup.`
- L819: `benchmark	Post Run MilesCranmer/AirspeedVelocity.jl@action-v1	2026-07-07T05:50:27.6111506Z Post job cleanup.`
- L820: `benchmark	Post Run MilesCranmer/AirspeedVelocity.jl@action-v1	2026-07-07T05:50:27.6786824Z [command]/usr/bin/git version`
- L821: `benchmark	Post Run MilesCranmer/AirspeedVelocity.jl@action-v1	2026-07-07T05:50:27.6817279Z git version 2.54.0`
- L822: `benchmark	Post Run MilesCranmer/AirspeedVelocity.jl@action-v1	2026-07-07T05:50:27.6847412Z Temporarily overriding HOME='/home/runner/work/_temp/26ebe297-e9ca-42a7-ac10-5de62f6f6b16' before making global git config changes`
- L823: `benchmark	Post Run MilesCranmer/AirspeedVelocity.jl@action-v1	2026-07-07T05:50:27.6862096Z Adding repository directory to the temporary git global config as a safe directory`
- L824: `benchmark	Post Run MilesCranmer/AirspeedVelocity.jl@action-v1	2026-07-07T05:50:27.6862997Z [command]/usr/bin/git config --global --add safe.directory /home/runner/work/QuantumOptics.jl/QuantumOptics.jl`
- L825: `benchmark	Post Run MilesCranmer/AirspeedVelocity.jl@action-v1	2026-07-07T05:50:27.6879778Z Removing SSH command configuration`
- L826: `benchmark	Post Run MilesCranmer/AirspeedVelocity.jl@action-v1	2026-07-07T05:50:27.6884784Z [command]/usr/bin/git config --local --name-only --get-regexp core\.sshCommand`
- L827: `benchmark	Post Run MilesCranmer/AirspeedVelocity.jl@action-v1	2026-07-07T05:50:27.6936972Z [command]/usr/bin/git submodule foreach --recursive sh -c "git config --local --name-only --get-regexp 'core\.sshCommand' && git config --local --uns`
- L828: `benchmark	Post Run MilesCranmer/AirspeedVelocity.jl@action-v1	2026-07-07T05:50:27.7117489Z Removing HTTP extra header`
- L829: `benchmark	Post Run MilesCranmer/AirspeedVelocity.jl@action-v1	2026-07-07T05:50:27.7121390Z [command]/usr/bin/git config --local --name-only --get-regexp http\.https\:\/\/github\.com\/\.extraheader`
- L830: `benchmark	Post Run MilesCranmer/AirspeedVelocity.jl@action-v1	2026-07-07T05:50:27.7146406Z [command]/usr/bin/git submodule foreach --recursive sh -c "git config --local --name-only --get-regexp 'http\.https\:\/\/github\.com\/\.extraheader' `
- L831: `benchmark	Post Run MilesCranmer/AirspeedVelocity.jl@action-v1	2026-07-07T05:50:27.7329080Z Removing includeIf entries pointing to credentials config files`
- L832: `benchmark	Post Run MilesCranmer/AirspeedVelocity.jl@action-v1	2026-07-07T05:50:27.7335297Z [command]/usr/bin/git config --local --name-only --get-regexp ^includeIf\.gitdir:`
- L833: `benchmark	Post Run MilesCranmer/AirspeedVelocity.jl@action-v1	2026-07-07T05:50:27.7360019Z [command]/usr/bin/git submodule foreach --recursive git config --local --show-origin --name-only --get-regexp remote.origin.url`
- L835: `benchmark	Complete job	2026-07-07T05:50:27.7895095Z ##[warning]Node.js 20 is deprecated. The following actions target Node.js 20 but are being forced to run on Node.js 24: actions/cache@5a3ec84eff668545956fd18022155c47e93e2684, julia-action`

