## Summary
Propose adding a GraphSAGE training workload to tt-blacksmith

## Proposed Scope
- Primary focus: training
- Secondary stretch goal: inference if time permits
- Hardware target: Wormhole N300
- Initial datasets:
  - Reddit (main target)
  - PubMed (smaller fallback / bring-up option)

## Initial Plan
1. Build a CPU baseline
2. Profile the workload and identify the most important stages
3. Port the model into a tt-blacksmith experiment structure using TT-supported ops where possible
4. Run on Tenstorrent hardware
5. Compare correctness and performance against CPU
6. Document limitations, blocked ops, and optimisation opportunities

## Deliverables
- Working CPU baseline
- Working TT implementation for the training workload (or core training stages)
- CPU vs TT parity checks
- Benchmarking / profiling results
- Reproducible setup and documentation

## Success Criteria
- TT execution on hardware, with only targeted CPU fallbacks if necessary
- Clear correctness checks against CPU
- Measurable benchmarking results
- Documentation of unsupported or difficult stages and possible next steps

## Open Questions
- Preferred dataset for initial bring-up: Reddit vs PubMed?
- Preferred framework path inside tt-blacksmith / Forge?
- What level of TT execution is acceptable for the first milestone?
- Should milestones be split similarly to other training workload issues?