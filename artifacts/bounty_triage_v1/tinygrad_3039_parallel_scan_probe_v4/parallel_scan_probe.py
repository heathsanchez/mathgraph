from __future__ import annotations

def _norm_axis(axis: int, ndim: int) -> int:
  return axis + ndim if axis < 0 else axis

def _shift_right_zero(x, axis: int, offset: int):
  """Shift tensor right along axis by offset, filling left side with zero."""
  axis = _norm_axis(axis, len(x.shape))
  pads = [(0, 0)] * len(x.shape)
  pads[axis] = (offset, 0)
  y = x.pad(tuple(pads))

  slices = [(0, s) for s in x.shape]
  return y.shrink(tuple(slices))

def hillis_steele_cumsum(x, axis: int = 0):
  """Inclusive parallel-prefix sum using log2(n) staged shifted adds."""
  axis = _norm_axis(axis, len(x.shape))
  n = x.shape[axis]
  y = x
  step = 1
  while step < n:
    y = y + _shift_right_zero(y, axis, step)
    step *= 2
  return y
