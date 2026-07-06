This replaces one local `sorry` in `FormalBook/Chapter_06.lean` inside a calculation in `h_lamb_gt_q_sub_one`.

The step simplifies evaluation of `X - C lamb` at `(q : ℂ)`:

    _ = ‖q - lamb‖^2 := by simp

Locally verified with:

    lake build FormalBook.Chapter_06
