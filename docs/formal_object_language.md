# Formal Object-Language IR

The v16.10 object-language IR records terms and formulas from external formal
worlds without pretending to parse or verify the whole source language.

`ObjectLanguageTerm` and `ObjectLanguageFormula` keep raw text, normalized text,
type expression, denotation status, formal-world context, and payload metadata.
They are containers for future Lean/Isabelle/AOT importers.

This IR is not a theorem prover. Non-denoting or unknown-denoting terms remain
advisory and cannot be promoted by text import alone.
