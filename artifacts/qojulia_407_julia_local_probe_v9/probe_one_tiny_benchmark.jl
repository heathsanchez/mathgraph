using Pkg
Pkg.activate("benchmark")
Pkg.instantiate()
include("benchmark/benchmarks.jl")

# Pick the smallest intended benchmark if present. This is deliberately tiny:
# it checks that the suite is runnable, not that timing numbers are stable.
candidates = [
    ("schroedinger", "base array types", "1//2"),
    ("schroedinger", "qo types", "1//2"),
    ("master", "base array types", "1//2"),
]

picked = nothing
for (a,b,c) in candidates
    if haskey(SUITE, a) && haskey(SUITE[a], b) && haskey(SUITE[a][b], c)
        global picked = (a,b,c)
        break
    end
end

if picked === nothing
    error("No tiny benchmark candidate found in SUITE")
end

a,b,c = picked
println("Running tiny benchmark candidate: ", picked)
bench = SUITE[a][b][c]
tune!(bench)
result = run(bench; seconds=0.25, samples=1, evals=1)
println(result)
println("TINY_BENCHMARK_OK")
