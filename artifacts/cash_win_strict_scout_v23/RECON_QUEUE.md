# Strict Scout v23 Recon Queue

## 1. tinygrad/tinygrad#3039

- Bounty: Fast parallel scan (Mamba, etc). 
- https://github.com/tinygrad/tinygrad/issues/3039
- score `80`, amount `$500`, stars `33251`

```bash
REPO="tinygrad/tinygrad"
ISSUE="3039"
DIR="/Users/heath/Documents/mathgraph-lean-work/external/cash_win_strict_v23/tinygrad__tinygrad_3039"
mkdir -p "$(dirname "$DIR")"
if [ ! -d "$DIR/.git" ]; then gh repo clone "$REPO" "$DIR" -- --filter=blob:none; else git -C "$DIR" fetch origin; fi
gh issue view "$ISSUE" -R "$REPO" --comments
find "$DIR" -maxdepth 3 -type f | sed "s#^$DIR/##" | head -250
```

## 2. QuantumSavory/QuantumSavory.jl#132

- Improve Makie visualization capabilities [$200]
- https://github.com/QuantumSavory/QuantumSavory.jl/issues/132
- score `56`, amount `$220`, stars `66`

```bash
REPO="QuantumSavory/QuantumSavory.jl"
ISSUE="132"
DIR="/Users/heath/Documents/mathgraph-lean-work/external/cash_win_strict_v23/QuantumSavory__QuantumSavory.jl_132"
mkdir -p "$(dirname "$DIR")"
if [ ! -d "$DIR/.git" ]; then gh repo clone "$REPO" "$DIR" -- --filter=blob:none; else git -C "$DIR" fetch origin; fi
gh issue view "$ISSUE" -R "$REPO" --comments
find "$DIR" -maxdepth 3 -type f | sed "s#^$DIR/##" | head -250
```

