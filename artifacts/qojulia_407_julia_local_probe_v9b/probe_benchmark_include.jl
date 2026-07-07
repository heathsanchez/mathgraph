using Pkg
println("Julia version: ", VERSION)
println("Root project before activate: ", Base.active_project())

Pkg.activate("benchmark")
println("Activated benchmark project: ", Base.active_project())

println("Instantiating benchmark project...")
Pkg.instantiate()

println("Loading benchmark/benchmarks.jl ...")
include("benchmark/benchmarks.jl")

println("SUITE type: ", typeof(SUITE))
println("Top-level benchmark groups:")
for k in keys(SUITE)
    println("  - ", repr(k))
end

println("Nested groups:")
for k in keys(SUITE)
    println("GROUP ", repr(k), " => ", collect(keys(SUITE[k])))
end

println("INCLUDE_OK")
