# tinygrad #3039 patch sketch

This probe does not patch tinygrad yet. It tests whether tinygrad's existing primitives can express a log-depth inclusive scan.

Candidate helper:

    def _shift_right_zero(x, axis, offset):
      pads = [(0, 0)] * len(x.shape)
      pads[axis] = (offset, 0)
      y = x.pad(tuple(pads))
      return y.shrink(tuple((0, s) for s in x.shape))

    def hillis_steele_cumsum(x, axis=0):
      y = x
      step = 1
      while step < x.shape[axis]:
        y = y + _shift_right_zero(y, axis, step)
        step *= 2
      return y

If correctness passes, the next real PR shape is one of:

1. Add a private helper for associative scan over addition and route Tensor.cumsum through it for supported static-shape cases.
2. Add Tensor.associative_scan(fn, axis=0) with cumsum as the first use case.
3. Add an experimental helper plus tests first, then optimize lowering/codegen after maintainer feedback.

A draft PR is only worthwhile if the probe shows correctness and either:
- better runtime for meaningful sizes, or
- clearer graph depth / operation-count improvement over the current implementation.
