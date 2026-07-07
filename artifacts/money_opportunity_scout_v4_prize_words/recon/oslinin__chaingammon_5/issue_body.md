@claude please implement everything below on a new branch named `learn`. Open a single PR from `learn` to `main` when complete. Use four logical commits in order: (1) skeleton, (2) AXL, (3) 0G, (4) demo.

## Project goal

Build a decentralized population-based training system for a backgammon RL agent. Each node trains its own agent via self-play, discovers peers over AXL (Gensyn's P2P network), challenges them to matches, and exchanges checkpoints. Agent weights persist to 0G Storage. Match results post to an ELO leaderboard contract on 0G Chain. Submission target: ETHGlobal Open Agents (Gensyn AXL prize + 0G Autonomous Agents/Swarms prize).

## Why backgammon

Clean benchmark domain. Stochastic (dice) so it suits population-based methods. gnubg exists as an objective external evaluator (we'll wire that up in a later PR). The classic TD-Gammon result (Tesauro 1992) shows a small MLP trained via TD(λ) self-play reaches strong play, so the compute budget is hackathon-friendly.

## Commit 1: skeleton (`backgammon/`)

Create the following modules. Keep the core training loop pure Python + PyTorch, no network deps.

### `backgammon/env.py`
- Board state: 24 points (signed integers, +White/-Black), bar[2], off[2], turn.
- `starting_state()`: standard opening — White 2 on point 0, 5 on 11, 3 on 16, 5 on 18; Black mirrored.
- White moves 0→23, bears off from 18-23. Black moves 23→0, bears off from 0-5.
- `legal_move_sequences(state, dice) -> list[(resulting_state, [(src,die), ...])]`
  - Doubles play four times.
  - Must enter from bar before any other move.
  - Must use as many dice as possible; if only one playable, must play the larger die when possible.
  - Bear-off: all checkers in home board; exact roll, or larger roll only if no checkers behind.
  - Hit blot: opponent checker alone on a point goes to bar.
- `is_terminal(state)`, `game_outcome(state) -> (winner, multiplier)` where multiplier is 1=single, 2=gammon (loser borne off 0), 3=backgammon (loser still on bar or in winner's home board).

### `backgammon/encode.py`
- TD-Gammon 198-feature encoding: per (24 points × 2 players × 4 features) = 192, plus [bar_W/2, off_W/15, bar_B/2, off_B/15, turn==W, turn==B]. The 4 per-point features are: (≥1, ≥2, ≥3, max(0, n-3)/2).

### `backgammon/net.py`
- Small MLP: 198 → hidden (default 128) → hidden → 4, sigmoid out.
- Cumulative-head outputs: [P(W wins any), P(W wins gammon+), P(B wins any), P(B wins gammon+)].
- White equity helper: (out[0] + out[1]) − (out[2] + out[3]).

### `backgammon/agent.py`
- `NetAgent(net, epsilon)`: enumerate legal sequences, encode each resulting state, score from mover's perspective (negate equity if Black to move), argmax. Epsilon-random for exploration.
- `RandomAgent` baseline.

### `backgammon/selfplay.py`
- `play_game(white_agent, black_agent, rng_py, rng_np) -> Trajectory` containing the encoded states visited and the terminal 4-vector target.
- Opening roll: re-roll until non-doubles; higher die plays first.
- `td_lambda_update(net, optimizer, traj, lam=0.7)`: backward sweep computing λ-returns toward terminal target, MSE loss, single optimizer step.

### `backgammon/train.py`
- CLI flags: `--epochs`, `--games-per-epoch`, `--lr`, `--lambda-td`, `--epsilon`, `--hidden`, `--seed`, `--ckpt-dir`.
- Per epoch: run N self-play games, TD update after each, evaluate vs RandomAgent (alternating sides), save checkpoint.
- Print `epoch | avg_moves | loss | win_rate_vs_random | time`.

### Tests (`tests/`)
- `test_env.py`: starting position has 15+15 checkers; checker conservation across 50 random rollouts; all rollouts terminate; specific roll (3,1) from start gives ≥10 candidate sequences.
- `test_net.py`: forward pass shape; equity calculation symmetric.

### Acceptance for commit 1
`python -m backgammon.train --epochs 5 --games-per-epoch 100` runs to completion and shows `vs_random` rising above 0.7 by epoch 5.

## Commit 2: AXL coordination (`backgammon/axl/`)

AXL is a P2P node binary that exposes encrypted mesh communication via localhost HTTP. Docs: https://docs.gensyn.ai/tech/agent-exchange-layer. Reference: https://github.com/gensyn-ai/axl. Verify the actual API before implementing — if it differs from what's described here, comment on this issue with the proposed adaptation rather than guessing.

### `backgammon/axl/messages.py`
Dataclasses with `to_dict`/`from_dict`:
- `ANNOUNCE {agent_id, checkpoint_hash, elo, generation}`
- `CHALLENGE {from_id, n_games, seed}`
- `MATCH_RESULT {agent_a, agent_b, score_a, score_b, n_games}`
- `WEIGHTS_REQ {checkpoint_hash}`
- `WEIGHTS_RESP {checkpoint_hash, storage_uri}` (just the URI; bytes live on 0G — see commit 3)

### `backgammon/axl/node.py`
- Wraps a single training agent.
- Background thread runs self-play training continuously.
- HTTP server on the AXL-assigned localhost port handles incoming messages.
- Every K minutes (configurable, default 2): announce checkpoint, pick a peer, challenge for 20 games, update local ELO (K-factor 32), if peer ELO exceeds self by 50+ points pull weights and replace.
- Peer pool: max 10, LRU eviction.
- Entry point: `python -m backgammon.axl.node --peers <id1,id2,...> [--no-chain] [--no-storage]`.

### Tests
- `test_axl_messages.py`: every message type round-trips through serialization.
- `test_axl_node.py`: two in-process nodes (mocked AXL transport) exchange one full match cycle, both update ELO consistently.

## Commit 3: 0G Storage + Chain (`backgammon/og/`, `contracts/`)

0G has Storage (decentralized blob store), Compute, and an EVM chain. We use Storage and Chain only. Builder hub: https://build.0g.ai. Verify SDK names/imports before implementing.

### `backgammon/og/storage.py`
- `upload_checkpoint(state_dict) -> str`: serialize state_dict, upload to 0G Storage, return URI.
- `download_checkpoint(uri) -> state_dict`.
- `upload_game_record(trajectory) -> str`.
- Storage key: `sha256(weights_bytes)` for checkpoints — content-addressed, deduplicates across nodes.

### `backgammon/og/chain.py`
- Web3.py client for the Tournament contract.
- Reads the deployed contract address from `deployments/0g_testnet.json` (do not hardcode).
- `report_match(agent_a, agent_b, score_a, sig_a, sig_b) -> tx_hash`.
- `get_elo(agent) -> int`.
- `top_n(n) -> list[(address, elo)]`.

### `contracts/Tournament.sol`
- Solidity ^0.8.20.
- Mapping `address => int32` ELO ratings, default 1500.
- `reportMatch(address a, address b, uint8 score_a, uint8 score_b, bytes sigA, bytes sigB)`:
  - Verify both signatures are EIP-712 over `(a, b, score_a, score_b, nonce)`.
  - Replay protection via incrementing per-pair nonce.
  - Update ELO with K-factor 32.
  - Emit `MatchReported(address a, address b, uint8 winner, int32 newEloA, int32 newEloB)`.
- `topN(uint256 n)` view function returning sorted leaderboard.

### Hardhat setup
- `hardhat.config.js` with Solidity 0.8.20, optimizer enabled (200 runs), and a `0g_testnet` network entry (RPC URL from `OG_RPC_URL` env var, deployer key from `DEPLOYER_PRIVATE_KEY`).
- `package.json` pinning `hardhat`, `@nomicfoundation/hardhat-toolbox`, `ethers`, `dotenv`.
- `scripts/deploy.js` deploys `Tournament` and writes the address + ABI path to `deployments/0g_testnet.json`.

### `test/Tournament.test.js`
Hardhat + ethers tests using `hardhat-toolbox` (chai matchers, network helpers). Cover:
- Happy path: valid co-signed match updates both ELOs symmetrically (sum preserved up to rounding).
- Missing signature reverts.
- Wrong-signer signature reverts.
- Replay attack (re-submitting same nonce) reverts.
- ELO drift: 100 mock matches between two equal-strength agents stays within ±50 of starting 1500 for both.

### Wire-through
- AXL `WEIGHTS_RESP` returns 0G Storage URI instead of inline bytes.
- After each AXL `MATCH_RESULT` exchange, both nodes co-sign (EIP-712) and one submits to chain.
- `backgammon/og/chain.py` loads the contract address from `deployments/0g_testnet.json`.

## Commit 4: end-to-end demo (`demo/`)

### `demo/run_local_swarm.sh`
Spin up 5 AXL nodes locally, each with: distinct seed, varied hyperparameters (sample `lambda_td ∈ {0.5, 0.7, 0.9}`, `lr ∈ {5e-4, 1e-3, 2e-3}`, `hidden ∈ {64, 128, 192}`). Pass each node the others' AXL IDs. Output logs to `demo/logs/node_N.log`.

### `demo/leaderboard.py`
Polls the chain every 30s, prints sorted leaderboard with deltas since last poll.

### `demo/README.md`
~200 words: what the demo shows, how to run (including `npx hardhat run scripts/deploy.js --network 0g_testnet` as a prerequisite), what to look for in the logs (peer discovery, first match exchange, first chain submission, ELO divergence).

### `docs/architecture.md`
~300 words + a mermaid diagram showing the three layers (training core, AXL mesh, 0G persistence) and how a single match flows through them.

## Cross-cutting requirements

- **Don't break the standalone path.** `python -m backgammon.train` must still work without AXL or 0G.
- **Feature flags.** `--no-network` and `--no-chain` skip those layers cleanly. The demo without flags requires AXL/0G; with flags, just runs local self-play.
- **Type hints throughout.** `mypy backgammon/` should pass.
- **Pinned Python dependencies** in `requirements.txt`. Brief justification per dep in the PR description.
- **Pinned JS dependencies** in `package.json` (Hardhat, ethers, toolbox, dotenv).
- **No secrets in commits.** Provide `.env.example` covering `OG_RPC_URL`, `DEPLOYER_PRIVATE_KEY`, and any AXL-specific env vars.
- **Python 3.11+, Node 20+.**

## Acceptance checklist

- [ ] Branch `learn`, four ordered commits, single PR to `main`.
- [ ] Commit 1 alone runs end-to-end and learns vs random.
- [ ] `pytest tests/` passes.
- [ ] `npx hardhat compile` produces clean artifacts.
- [ ] `npx hardhat test` passes.
- [ ] `npx hardhat run scripts/deploy.js --network hardhat` (local node) runs end-to-end and writes a deployment file. Document the command in the PR description.
- [ ] `mypy backgammon/` clean.
- [ ] `demo/run_local_swarm.sh` brings up 5 nodes that discover each other and exchange ≥1 match within 60s.
- [ ] PR description includes: architecture diagram, dependency list (Python + JS) with justification, known limitations, what's tested vs. only stubbed.

## Important: handling unknowns

The AXL and 0G SDKs may have changed since your training data. Before writing integration code in commits 2 and 3, fetch the current docs (linked above) and confirm the API surface. If the actual API differs materially from this spec, **comment on this issue with the discrepancy and your proposed adaptation, then wait for confirmation.** Don't paper over API mismatches with mocks.

If anything else is ambiguous, comment first rather than guessing.