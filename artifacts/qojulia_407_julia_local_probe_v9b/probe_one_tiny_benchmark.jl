using Pkg
Pkg.activate("benchmark")
Pkg.instantiate()
include("benchmark/benchmarks.jl")

candidates = [
    ("schroedinger", "base array types", "1//2"),
    ("schroedinger", "qo types", "1//2"),
    ("master", "base array types", "1//2"),
    ("master", "qo types", "1//2"),
]

picked = nothing
for (a,b,c) in candidates
    if haskey(SUITE, a) && haskey(SUITE[a], b) && haskey(SUITE[a][b], c)
        global picked = (a,b,c)
        break
    end
end

if picked === nothing
    println("Available SUITE shape:")
    for a in keys(SUITE)
        println("A=", repr(a), " keys=", collect(keys(SUITE[a])))
    end
    error("No tiny benchmark candidate found in SUITE")
end

a,b,c = picked
println("Running tiny benchmark candidate: ", picked)
bench = SUITE[a][b][c]
tune!(bench)
result = run(bench; seconds=0.25, samples=1, evals=1)
println(result)
println("TINY_BENCHMARK_OK")
