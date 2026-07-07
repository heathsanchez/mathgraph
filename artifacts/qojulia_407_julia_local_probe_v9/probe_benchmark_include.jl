using Pkg
println("Julia version: ", VERSION)
println("Project: ", Base.active_project())

Pkg.activate("benchmark")
Pkg.instantiate()

println("Activated benchmark project: ", Base.active_project())
println("Loading benchmark/benchmarks.jl ...")
include("benchmark/benchmarks.jl")

println("SUITE type: ", typeof(SUITE))
println("Top-level benchmark groups:")
for k in keys(SUITE)
    println("  - ", repr(k))
end

expected = ["schroedinger", "master", "stochastic_schroedinger", "stochastic_master"]
println("Expected old prob_list labels:")
for k in expected
    println("  ", k, " present=", haskey(SUITE, k))
end

println("Actual nested groups:")
for k in keys(SUITE)
    println("GROUP ", repr(k), " => ", collect(keys(SUITE[k])))
end

println("INCLUDE_OK")
