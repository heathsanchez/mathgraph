# tenstorrent/tt-llk #1638 Recon v1

## Issue

- Title: [Bounty $1000] Reduce RISCV instructions used to pass on tensix instructions using AI/Optimizer.
- Labels: P2, bounty, bounty_difficulty/medium, LLK
- Comments: 18

## Bounty fit

Verdict: `INSPECT_DEEPER_BEFORE_CLAIMING`

Why it fits MathGraph:

- It is a bounded optimization/search problem.
- The objective is measurable: reduce RISCV instructions while preserving tensix instruction sequence.
- There are explicit constraints around replay buffer usage.
- The likely winning loop is residual search over equivalent encodings, with local tests/benchmarks as judge.

Main risk:

- The repo may require specialized Tenstorrent hardware or domain knowledge to validate true performance.
- Do not claim/lock bounty until local objective and acceptance test are clear.

## Issue body excerpt

```text
The number of tensix instructions to do a particular task can be easily optimized with human thinking, as the main task would have an algorithm and the proper instructions and sequence can often be easily chosen. But to pass on the tensix insturctions to the tensix engine, we often use MOPs and Replay buffers to pass them so that the number of RISCV instructions are rerduced. That part has too many ways of accomplishing and is not too easy to find out what is the most optimal way all the time. 

This is where we can use AI to reduce the number of RISV instructions used, by varying the possibilities of writing the MOP and arrangement of the replay buffer. Overall the task is 

Objective : Minimize the number of RISCV instructions to issue instructions to tensix engine 
Constraints : Sequence of tensix instructions passed remains the same
                       Only specified amount of replay buffer is used (for example if Math thread uses whole of the buffer, it may clash with SFPU algorithms when they are run from a separate thread on WH/BH for the buffer being shared. 
                        Take into account two ways of writing mops and their constraints. 

An AI agent may be asked to do it for all the ops we have and then we filter out the good suggestions and apply them. 
```

## Candidate files

- No candidate files detected

## Runnable detection

```json

```

## Light probe results

```json
{}
```

## Candidate context excerpt

```text

```

## Next decision

Proceed only if the next recon can identify:

1. the exact MOP/replay-buffer source files,
2. the exact baseline instruction-count metric,
3. a local simulator/test/benchmark that can compare before/after,
4. one small op/kernel where a patch can be attempted.

If any of these are missing, park this bounty and inspect tinygrad or xevrion instead.

