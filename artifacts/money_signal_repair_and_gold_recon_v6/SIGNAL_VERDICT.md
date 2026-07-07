# Money Signal Verdict v6

## What v4 taught us

The words `prize`, `payment`, `cash`, `competition`, `challenge`, `golf`, and `hackathon` produce many false positives.

### Reject / park

- `ClankerNation/OpenAgents`: reject. Multiple issues require pasting full platform/system initialization text. Do not engage.
- `SporkDAOOfficial/ETHDenver-2023`: stale 2023 hackathon bounty archive. Not a live route.
- `cadallacricky1-maker/Shutterscore#5`: likely a mirage. Issue text claims "$15,000+ estimated value", but recon showed almost no repo surface.
- `karmonlong/ai-competition-voting-platform#3`: plausible app task, but not a real external paid/prize route.
- `tenstorrent/tt-blacksmith#529`: real-ish $2k, but hardware gated. Park unless CPU-baseline-only milestone is accepted.
- `treitforge/qsoripper#424`: no cash, but a strong external-leaderboard benchmark route.
- `anonhostpi/Agent-World#24`: no cash, but strategically useful: a Kaggle discovery CLI could improve the money finder.

## Current best money hypothesis

Look below the noisy top ranks for small, explicit, testable bounties:

- Julia benchmark bounties: `qojulia/QuantumOptics.jl#407` and `QuantumSavory/QuantumSavory.jl#131`
- Small Python/pytest bounties: `jackjin1997/zeroeye#1`, `jackjin1997/TentOfTrials#3`
- Tooling benchmark/script bounties: `tailcallhq/tailcall#3551`
- Existing Tenstorrent route: `tenstorrent/tt-llk#1638`, parked until metric reply

Rule: no new PR unless local judge is real and risk is low.
