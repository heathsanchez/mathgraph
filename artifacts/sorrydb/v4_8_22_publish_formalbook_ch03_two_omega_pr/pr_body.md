This fills two local arithmetic proof holes in `FormalBook/Chapter_03.lean` using `omega`.

Patch:

    have h_3lel : 3 ≤ l := by
      omega

and

    have h_2k'len : 2 * k' ≤ n := by
      omega

Local verification:

    lake build FormalBook.Chapter_03

Result:

    Build completed successfully

Sorry/admit count change in the file:

    -2

The patch is intentionally minimal and only replaces the two local `sorry` holes.
