I tested a simple Tensor-level Hillis-Steele/tree-style inclusive cumsum as a first pass for #3039. It was correct against `Tensor.cumsum`, but locally it was slower than the existing implementation across small powers of two, because repeated `pad + shrink + add` at Tensor level creates too much overhead.

So I’m not opening a PR from that route. The next plausible route seems lower-level: adding a scheduler/UOp/codegen primitive for associative scan rather than composing it from existing Tensor ops. If there’s a preferred lowering target or benchmark for this bounty, I can aim at that.
