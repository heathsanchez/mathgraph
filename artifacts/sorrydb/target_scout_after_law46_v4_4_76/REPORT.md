# SorryDB v4.4.76 — Target Scout After Law46

## Purpose

Find the next SorryDB target after parking Law46.

Law43 is solved. Law46 is parked as a named semantic/canonicalization obstruction.

## Exclusions

- equational_theories/Definability/Law43.lean
- equational_theories/Definability/Law46.lean

## Candidate Count

1

## Top Candidates

### 1. equational_theories/FactsSyntax.lean

- score: 4.35
- active_sorry_count: 1
- line_count: 67
- flags: {"definability": false, "equations_all": false, "toFin": false, "satisfies_or_models": true, "models_iff": false, "termdef": false, "aesop": false}

First sorry window:

0056:       discard <| withCurrHeartbeats <| Tactic.run goal.mvarId! do evalTactic tac
0057:       s := s.push (quote n)
0058:     catch _ =>
0059:       r := r.push (quote n)
0060:   /-
0061:   let factS : Term ← `(term|Facts $Gs [ $(.mk s),* ] [ $(.mk r),* ])
0062:   let suggest ← `(command|
0063:       example : Facts $Gs [ $(.mk (s.map fun n => quote n)),* ] [ $(.mk (r.map fun n => quote n)),* ]
0064:          := by sorry)
0065:   TryThis.addSuggestion tk suggest
0066:   -/
0067:   logInfo m!"These equations can be solved by the tactic:\n{s}\nAnd these cannot:\n{r}"

## Recommended Next Target

equational_theories/FactsSyntax.lean

Reason: lowest score after penalizing Law46-like semantic/toFin/canonicalization traps.