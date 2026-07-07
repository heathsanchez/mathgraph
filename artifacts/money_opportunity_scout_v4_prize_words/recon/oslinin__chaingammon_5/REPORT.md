# Prize Recon Report

## Verdict

`PARK_RISK`

## Decision

JSON:
{
  "verdict": "PARK_RISK",
  "issue": {
    "url": "https://github.com/oslinin/chaingammon/issues/5",
    "title": "learning bg",
    "state": "OPEN",
    "labels": [],
    "comment_count": 1,
    "updatedAt": "2026-04-29T06:19:46Z"
  },
  "money": true,
  "competition": true,
  "judge": true,
  "local": true,
  "mgfit": true,
  "risk": true
}

## Cheap commands

pwd=/Users/heath/Documents/mathgraph-lean-work/external/money_opportunity_scout_v4_prize_words/oslinin__chaingammon_5

README head:
# Chaingammon

> **An open protocol for portable backgammon reputation.** Your wallet (or your AI agent) is your player profile. Your ENS subname is your portable identity. Your full match archive lives on 0G Storage, owned by you forever.

A decentralised, verifiable ELO ledger for backgammon — humans and agents share one identity layer.

- **Open identity.** ENS subnames written only by the protocol. Reserved text records (`elo`, `match_count`, `kind`, `inft_id`, `style_uri`, `archive_uri`) cannot be self-claimed; any third-party tool reads them without coordinating with us.
- **Verifiable.** Every match settles to `MatchRegistry` on Sepolia. The on-chain record carries the 32-byte 0G Storage hash of the full archive (every move, every dice roll) — anyone can audit any rating change end-to-end.
- **Living agents.** Each AI agent is an ERC-7857 iNFT (with ERC-721 fallback). It pins two `dataHashes`: a starter NN initialised from gnubg's published weights, and a per-agent checkpoint that grows match by match. Transfer the token, transfer the brain.
- **Trustless dice.** Each turn's dice are `keccak256(drand_round_digest, turn_index) mod 36`. The server passes drand's BLS12-381 signature through to the client so an auditor can independently verify the round against drand's group public key.
- **Optional stakes.** A match can be free (ELO-only) or staked (per-side ETH deposit, winner takes the pot). Agent funds live in `AgentVault` — only the NFT owner can withdraw; the server operator key can stake but not steal. Settlement is browser-direct via `settleWithSessionKeys`, with KeeperHub as fallback.
- **No central server.** Move evaluation runs in the browser (ONNX Runtime Web). The coach LLM runs on 0G Compute (Qwen 2.5 7B) with a local fallback. KeeperHub orchestrates settlement.
- **Serverless human-vs-human (in progress).** Press Play to be matched — by nearest ELO — with another human who is also searching, with no matchmaking server and nothing volatile on-chain: presence and the WebRTC handshake ride public Nostr relays, moves flow peer-to-peer over a WebRTC data channel, dice stay drand-verifiable, and settlement fires automatically from session keys both players sign before the game.

For detailed architecture, component design, and infrastructure docs see [ARCHITECTURE.md](ARCHITECTURE.md).

---

## How it works

1. Connect a wallet → frontend resolves (or auto-mints) `<name>.chaingammon.eth` on Sepolia.
2. Pick an opponent — another player's subname or an AI agent (e.g. `gnubg-classic.chaingammon.eth`).
3. Per-turn loop:
   - KeeperHub pulls drand round R → dice are deterministic from the round digest.
   - The active side's agent runs a value-network forward pass (browser or 0G Compute) and selects the highest-equity legal move.
   - The move is appended to the in-progress `GameRecord`; KeeperHub validates legality via the WASM rules engine.
4. Game ends → browser uploads `GameRecord` to 0G Storage → `MatchRegistry.settleWithSessionKeys` called directly from the browser → `post-settle-audit` KeeperHub workflow fires → ENS text records updated → audit trail anchored.
5. Any other tool reads your ENS subname and reconstructs your full backgammon DNA — ELO, games played, playing style.

---

## Running locally

### Prerequisites

- Python 3.12+, [uv](https://github.com/astral-sh/uv)
- Node 20+, [pnpm](https://pnpm.io)
- `gnubg` (for local debugging only) — `sudo apt install gnubg` (Ubuntu/Debian) or `brew install gnubg` (macOS)

### One-time setup

```bash
git clone <repo> && cd chaingammon
pnpm install                    # frontend + contracts (workspace)
cd agent && uv sync && cd ..    # agent Python deps
cp contracts/.env.example contracts/.env       # add DEPLOYER_PRIVATE_KEY + Sepolia RPC_URL
cp frontend/.env.example frontend/.env.local
```

Fund the deployer wallet with Sepolia ETH from any public faucet.

### Bootstrap and run

```bash
# 1. deploy + verify settlement contracts on Sepolia (one shot)
./scripts/bootstrap-network.sh

# 2. start the frontend (from repo root)
pnpm frontend:dev                # Next.js on :3000
```

The FastAPI backend (`server/`) runs on a persistent VPS at `http://132.145.158.84` and is already live — the frontend's `NEXT_PUBLIC_SERVER_URL` points there by default. To run a local backend instead:

```bash
# terminal A — backend
cd server && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000

# frontend/.env.local — point frontend at local server
NEXT_PUBLIC_SERVER_URL=http://localhost:8000
```

Or use the VS Code Tasks workflow (`.vscode/tasks.json`) — `Tasks: Run Task` → `Localhost: launch all` fires hardhat node → deploy contracts → FastAPI server → Next.js frontend in sequence.

### Local dev with Hardhat

```bash
cd contracts && pnpm exec hardhat node            # local chain (chainId 31337)
cd contracts && pnpm exec hardhat run script/deploy.js --network localhost
```

Switch chains in MetaMask; the frontend re-targets the new chain's contracts automatically (see `frontend/app/chains.ts`).

### Test commands

```bash
pnpm test                  # all tests: agent (pytest) + contracts (hardhat) + frontend (build)
pnpm contracts:test
pnpm agent:test
pnpm frontend:test
```

---

## VPS ops

```bash
export CG_VPS=ubuntu@132.145.158.84
export CG_KEY=~/Documents/ssh/ssh-key-2026-05-17.key
```

**Deploy a change:**
```bash
ssh -i $CG_KEY $CG_VPS "cd /home/ubuntu/chaingammon && bash server/scripts/deploy.sh"
```

**Restart everything** (after a reboot or crash):
```bash
ssh -i $CG_KEY $CG_VPS
# FastAPI backend
sudo systemctl restart chaingammon-server

# WebRTC TURN relay
pkill turnserver; turnserver -c /tmp/turnserver.conf --daemon
sudo sslh -p 0.0.0.0:443 --tls=127.0.0.1:8443 --anyprot=127.0.0.1:3479 -P /tmp/sslh.pid

# Frontend (static, port 3001; nginx proxies 443 → 3001)
pkill -f "serve.*out"; npm exec serve@latest /home/ubuntu/chaingammon/frontend/out -- -p 3001 -s &
```

**Logs:**
```bash
journalctl -u chaingammon-server -f
```

Full VPS architecture (coturn, sslh, nginx layout): [ARCHITECTURE.md](ARCHITECTURE.md).

---

## Deployed contracts

**Sepolia:**

- [MatchRegistry](https://sepolia.etherscan.io/address/0x507d78149AE2092a5438825B1BA3F12737FAeC0C)
- [MatchEscrow](https://sepolia.etherscan.io/address/0x1206A93a9B76652382BC1F5164a8383a9F2A2e16)
- [AgentRegistry](https://sepolia.etherscan.io/address/0xE23B83cE16B292e420cd8820ac9d303A45333D17)
- [PlayerSubnameRegistrar](https://sepolia.etherscan.io/address/0x48285B8C9B04C6a3D61bBA067a4DE4399A5a4aEb)

Full deployment records: `contracts/deployments/*.json`.

---

## Roadmap

- **Current:** human-vs-agent gameplay; on-chain ELO; ENS subnames; agent iNFTs with hash-committed weights; 0G Storage match archive; drand dice; KeeperHub-orchestrated settlement on Sepolia.
- **In progress — serverless human-vs-human:** one-press, ELO-biased matchmaking and live play with no central server. Presence + WebRTC signaling ride public Nostr relays, moves flow peer-to-peer, settlement is automatic from pre-authorized session keys.
- **Next:** all-agent autonomous tournaments; 0G Compute for TEE-attested fine-tuning; team / chouette mode with the career head; per-agent cube doubling.
- **Later:** ZK proofs of agent inference (zkML); betting markets and ELO derivative tokens; mainnet on Base/Optimism.

See [ROADMAP.md](ROADMAP.md) for the full version. Architecture details: [ARCHITECTURE.md](ARCHITECTURE.md).

package scripts:
{
  "contracts:compile": "pnpm --filter contracts exec hardhat compile",
  "contracts:test": "pnpm --filter contracts exec hardhat test",
  "contracts:deploy": "pnpm --filter contracts exec hardhat run script/deploy.js --network sepolia",
  "contracts:verify": "pnpm --filter contracts exec hardhat run script/verify.js --network sepolia",
  "contracts:deploy-and-verify": "pnpm contracts:deploy && pnpm contracts:verify",
  "contracts:deploy:base-sepolia": "pnpm --filter contracts exec hardhat run script/deploy.js --network base-sepolia",
  "contracts:deploy:avalanche-fuji": "pnpm --filter contracts exec hardhat run script/deploy.js --network avalanche-fuji",
  "contracts:deploy:polygon-amoy": "pnpm --filter contracts exec hardhat run script/deploy.js --network polygon-amoy",
  "contracts:deploy:optimism-sepolia": "pnpm --filter contracts exec hardhat run script/deploy.js --network optimism-sepolia",
  "contracts:deploy:multichain": "pnpm contracts:deploy:base-sepolia && pnpm contracts:deploy:avalanche-fuji && pnpm contracts:deploy:polygon-amoy && pnpm contracts:deploy:optimism-sepolia",
  "frontend:dev": "pnpm --filter frontend dev",
  "frontend:build": "pnpm --filter frontend build",
  "frontend:test": "pnpm --filter frontend test",
  "agent:test": "cd agent && uv run pytest tests/",
  "test": "pnpm agent:test && pnpm --filter contracts test && pnpm --filter frontend test"
}


## Issue body

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

## Comments

## claude — 2026-04-29T05:52:58Z

**Claude finished @oslinin's task in 26m 34s** —— [View job](https://github.com/oslinin/chaingammon/actions/runs/25093179789) • [`claude/issue-5-20260429-0553`](https://github.com/oslinin/chaingammon/tree/claude/issue-5-20260429-0553) • [Create PR ➔](https://github.com/oslinin/chaingammon/compare/master...claude/issue-5-20260429-0553?quick_pull=1&title=feat%3A%20decentralised%20backgammon%20RL%20swarm%20%28AXL%20%2B%200G%29&body=Closes%20%235%0A%0A%23%23%20Summary%0A%0A-%20**Commit%201%3A%20Skeleton**%20%E2%80%94%20Pure%20Python%20%2B%20PyTorch%20TD-Gammon%20self-play%20training%20core%3A%20env%2C%20198-feature%20encoding%2C%20MLP%2C%20agents%2C%20TD(%CE%BB)%20updater%2C%20CLI%20trainer.%0A-%20**Commit%202%3A%20AXL**%20%E2%80%94%20P2P%20coordination%3A%20message%20dataclasses%2C%20BackgammonNode%20with%20background%20training%2C%20peer%20cycle%2C%20Flask%20HTTP%20handler%2C%20in-process%20test%20transport.%0A-%20**Commit%203%3A%200G**%20%E2%80%94%200G%20Storage%20checkpoint%20persistence%20(via%20og-bridge)%2C%20Tournament.sol%20ELO%20contract%20(EIP-712%2C%20replay%20protection%2C%20K%3D32%2C%20topN)%2C%20Hardhat%20deploy%20script.%0A-%20**Commit%204%3A%20Demo**%20%E2%80%94%205-node%20local%20swarm%20script%2C%20leaderboard%20poller%2C%20architecture%20docs%20with%20Mermaid%20diagram.%0A%0A%23%23%20Architecture%0A%0ASee%20%60docs%2Farchitecture.md%60%20for%20the%20full%20Mermaid%20sequence%20diagram%20and%20layer%20breakdown.%0A%0A%23%23%20AXL%20API%20Note%0A%0AThe%20AXL%20outbound-send%20HTTP%20API%20could%20not%20be%20verified%20(WebFetch%20unavailable).%20The%20assumed%20endpoint%20is%20%60POST%20localhost%3AAXL_PORT%2Fsend%60.%20If%20it%20differs%2C%20update%20%60AXLTransport.send()%60%20in%20%60backgammon%2Faxl%2Fnode.py%60.%0A%0A%23%23%20Test%20plan%0A%0A-%20%5B%20%5D%20%60pytest%20tests%2F%60%20passes%0A-%20%5B%20%5D%20%60npx%20hardhat%20compile%60%20clean%0A-%20%5B%20%5D%20%60npx%20hardhat%20test%60%20passes%0A-%20%5B%20%5D%20%60npx%20hardhat%20run%20contracts%2Fscript%2Fdeploy_tournament.js%20--network%20hardhat%60%20writes%20deployments%2F0g_testnet.json%0A-%20%5B%20%5D%20%60mypy%20backgammon%2F%60%20clean%0A-%20%5B%20%5D%20%60bash%20demo%2Frun_local_swarm.sh%20--no-network%60%20starts%205%20nodes%0A%0AGenerated%20with%20%5BClaude%20Code%5D(https%3A%2F%2Fclaude.ai%2Fcode))

---
### Implementing Decentralized Backgammon RL System

All four commits implemented and pushed to `claude/issue-5-20260429-0553`.

### Tasks

- [x] Read CONTEXT.md and understand existing repo structure
- [x] Note AXL/0G API verification limitation
- [x] Commit 1: skeleton (`backgammon/`) — pure Python + PyTorch
  - [x] `backgammon/env.py` — board state, legal_move_sequences, is_terminal, game_outcome
  - [x] `backgammon/encode.py` — 198-feature TD-Gammon encoding
  - [x] `backgammon/net.py` — BackgammonNet MLP with cumulative heads
  - [x] `backgammon/agent.py` — NetAgent (ε-greedy) + RandomAgent
  - [x] `backgammon/selfplay.py` — play_game + td_lambda_update
  - [x] `backgammon/train.py` — CLI with all flags, eval loop, checkpointing
  - [x] `tests/test_env.py` + `tests/test_net.py`
  - [x] `requirements.txt` + `conftest.py`
- [x] Commit 2: AXL coordination (`backgammon/axl/`)
  - [x] `backgammon/axl/messages.py` — 5 message dataclasses with round-trip serde
  - [x] `backgammon/axl/node.py` — BackgammonNode with training thread, peer cycle, Flask HTTP
  - [x] `tests/test_axl_messages.py` + `tests/test_axl_node.py`
- [x] Commit 3: 0G Storage + Chain
  - [x] `backgammon/og/storage.py` — upload/download via og-bridge shim
  - [x] `backgammon/og/chain.py` — Web3 client for Tournament
  - [x] `contracts/src/Tournament.sol` — EIP-712 + nonce replay protection + ELO + topN
  - [x] `contracts/script/deploy_tournament.js` — writes `deployments/0g_testnet.json`
  - [x] `contracts/test/Tournament.test.js` — 8 test cases
  - [x] `contracts/hardhat.config.js` — added `0g_testnet` alias with `OG_RPC_URL`
- [x] Commit 4: demo
  - [x] `demo/run_local_swarm.sh` — 5 nodes, varied hyperparams, `--no-network` flag
  - [x] `demo/leaderboard.py` — 30s poll with ELO deltas
  - [x] `demo/README.md` + `docs/architecture.md` (Mermaid diagram)
  - [x] `.env.example`
- [x] Push branch

---

### Known limitations

**AXL outbound API not verified** — `WebFetch` was unavailable in this environment. The AXL send endpoint is assumed to be `POST http://localhost:<AXL_PORT>/send` with `{to, service, data}`. If the actual endpoint differs, update `AXLTransport.send()` in `backgammon/axl/node.py`. The `InProcessTransport` in tests bypasses this entirely.

**Tests not run locally** — `uv` is not installed in this runner environment and `python`/`pip` commands require user approval. Tests are structurally correct and import-clean; CI will validate them on push.

**EIP-712 co-signatures in production** — `BackgammonNode._submit_match_chain()` passes empty `sig_a`/`sig_b` as stubs. Full production flow requires each node's Ethereum private key to sign EIP-712 structured data; the contract verifies both sigs correctly.

**ELO arithmetic** — The Solidity `_pow10scaled()` uses a piecewise linear approximation. The test verifies ≤±50 drift over 100 equal matches.

### Deployment command

```bash
# Local Hardhat network (for acceptance check):
npx hardhat run contracts/script/deploy_tournament.js --network hardhat

# 0G testnet:
npx hardhat run contracts/script/deploy_tournament.js --network 0g-testnet
# (or --network 0g_testnet with OG_RPC_URL set)
```

### Python dependency justification

| Package | Justification |
|---------|---------------|
| `torch` | Neural network, autograd, checkpoint serialisation |
| `numpy` | Random number generation, feature array construction |
| `flask` | Lightweight HTTP server for AXL message handler |
| `requests` | Outbound HTTP calls to AXL send API |
| `web3` | EVM JSON-RPC client for Tournament contract reads/writes |
| `pytest` | Test runner |
 |

## Inventory excerpt

top files
.claude/settings.json
.claudeignore
.clauderules
.git/config
.git/description
.git/FETCH_HEAD
.git/HEAD
.git/hooks/applypatch-msg.sample
.git/hooks/commit-msg.sample
.git/hooks/fsmonitor-watchman.sample
.git/hooks/post-update.sample
.git/hooks/pre-applypatch.sample
.git/hooks/pre-commit.sample
.git/hooks/pre-merge-commit.sample
.git/hooks/pre-push.sample
.git/hooks/pre-rebase.sample
.git/hooks/pre-receive.sample
.git/hooks/prepare-commit-msg.sample
.git/hooks/push-to-checkout.sample
.git/hooks/update.sample
.git/index
.git/info/exclude
.git/logs/HEAD
.git/objects/pack/pack-b9a8cc4a733b9a6c9a9402ad2f2b74d565f78aef.idx
.git/objects/pack/pack-b9a8cc4a733b9a6c9a9402ad2f2b74d565f78aef.pack
.git/objects/pack/pack-b9a8cc4a733b9a6c9a9402ad2f2b74d565f78aef.promisor
.git/objects/pack/pack-d8c942f45d7d91fd06bec3f1371abcd695593553.idx
.git/objects/pack/pack-d8c942f45d7d91fd06bec3f1371abcd695593553.pack
.git/objects/pack/pack-d8c942f45d7d91fd06bec3f1371abcd695593553.promisor
.git/ORIG_HEAD
.git/packed-refs
.git/refs/heads/master
.github/workflows/claude-code-review.yml
.github/workflows/claude.yml
.github/workflows/pages.yml
.gitignore
.vscode/settings.json
.vscode/tasks.json
agent/agent_profile.py
agent/agent_state_io.py
agent/career_features.py
agent/challenge_policy.py
agent/challenge_trainer.py
agent/checkpoint_encryption.py
agent/coach_compute_client.py
agent/coach_dialogue.py
agent/coach_service.py
agent/data/gnubg_core.pt
agent/drand_dice.py
agent/flowchart.svg
agent/full_board_state.py
agent/gnubg_distill.py
agent/gnubg_encoder.py
agent/gnubg_net.py
agent/gnubg_onnx.py
agent/gnubg_search.py
agent/gnubg_service.py
agent/gnubg_state.py
agent/move_tagger.py
agent/og_compute_eval_client.py
agent/og_storage_download.py
agent/og_storage_upload.py
agent/onnx_board_state.py
agent/pyproject.toml
agent/round_robin_trainer.py
agent/rules_engine.py
agent/sample_trainer.py
agent/search.py
agent/sklearn_agent.py
agent/team_challenge_trainer.py
agent/teammate_selection.py
agent/tests/__init__.py
agent/tests/data/gnubg_0ply_reference.json
agent/tests/test_agent_profile.py
agent/tests/test_career_features.py
agent/tests/test_challenge_policy.py
agent/tests/test_challenge_trainer.py
agent/tests/test_checkpoint_encryption.py
agent/tests/test_coach_dialogue.py
agent/tests/test_drand_dice.py
agent/tests/test_full_board_dispatch.py
agent/tests/test_full_board_state.py
agent/tests/test_gnubg_distill.py
agent/tests/test_gnubg_encoder.py
agent/tests/test_gnubg_net.py
agent/tests/test_gnubg_onnx.py
agent/tests/test_gnubg_search.py
agent/tests/test_gnubg_state.py
agent/tests/test_model_agnostic_style.py
agent/tests/test_og_storage_download.py
agent/tests/test_og_storage_upload.py
agent/tests/test_phase76_chief_of_staff.py
agent/tests/test_phase76_move_tagger.py
agent/tests/test_round_robin.py
agent/tests/test_rules_engine.py
agent/tests/test_sample_trainer.py
agent/tests/test_sklearn_agent.py
agent/tests/test_status_file.py
agent/tests/test_teammate_selection.py
agent/uv.lock
AGENTS.md
ARCHITECTURE.md
chaingammon.pptx
CHANGELOG.md
CLAUDE.md
CONTEXT.md
contracts/.env.example
contracts/deployments/0g-testnet.json
contracts/deployments/avalanche-fuji.json
contracts/deployments/base-sepolia.json
contracts/deployments/localhost.json
contracts/deployments/optimism-sepolia.json
contracts/deployments/polygon-amoy.json
contracts/deployments/sepolia.json
contracts/hardhat.config.js
contracts/package.json
contracts/pnpm-lock.yaml
contracts/script/approve_registrar.js
contracts/script/deploy_agent_vault.js
contracts/script/deploy_matchescrow_only.js
contracts/script/deploy_matchregistry_only.js
contracts/script/deploy_registrar.js
contracts/script/deploy_usdc_contracts.js
contracts/script/deploy.js
contracts/script/remint_subnames.js
contracts/script/revoke_player_subnames.js
contracts/script/seed_agent_subnames.js
contracts/script/set_match_escrow.js
contracts/script/set_settler.js
contracts/script/verify.js
contracts/src/AgentRegistry.sol
contracts/src/AgentVault.sol
contracts/src/AgentVaultToken.sol
contracts/src/EloMath.sol
contracts/src/EloMathHarness.sol
contracts/src/MatchEscrow.sol
contracts/src/MatchEscrowUsdc.sol
contracts/src/MatchRegistry.sol
contracts/src/MockOgStorage.sol
contracts/src/mocks/MockNameWrapper.sol
contracts/src/mocks/MockResolver.sol
contracts/src/PlayerSubnameRegistrar.sol
contracts/test/phase_burnAgent.test.js
contracts/test/phase_MatchEscrow.test.js
contracts/test/phase_MatchRegistry_escrow.test.js
contracts/test/phase_MockOgStorage.test.js
contracts/test/phase_seed_agent_subnames.test.js
contracts/test/phase_settleWithSessionKeys.test.js
contracts/test/phase_settleWithSessionKeysAndSplit.test.js
contracts/test/phase0_scaffold.test.js
contracts/test/phase10_PlayerSubnameRegistrar.test.js
contracts/test/phase2_AgentRegistry.test.js
contracts/test/phase2_EloMath.test.js
contracts/test/phase2_MatchRegistry.test.js
contracts/test/phase22_selfMintSubname.test.js
contracts/test/phase3_MatchRegistry_gameRecord.test.js
contracts/test/phase32_reserved_keys.test.js
contracts/test/phase32_unified_mint.test.js
contracts/test/phase5_AgentRegistry_iNFT.test.js
docs/agents/domain.md
docs/agents/issue-tracker.md
docs/agents/triage-labels.md
docs/coach-dialogue.md
docs/demo-script.md
docs/design/prompt_1.md
docs/design/prompt_2.md
docs/design/prompt_3.md
docs/ENS_SCHEMA.md
docs/game.png
docs/github-issue-overlay-kv.md
docs/human-vs-human.md
docs/image0.jpeg
docs/image1.jpeg
docs/keeperhub-feedback.md
docs/keeperhub-workflow.md
docs/keeperhub-workflow.schema.json
docs/limitations.md
docs/logo-mark.svg
docs/slides.html
docs/superpowers/plans/2026-04-28-network-dropdown.md
docs/superpowers/plans/2026-06-13-ethglobal-nyc-2026.md
docs/superpowers/specs/2026-04-28-network-dropdown-design.md
docs/team-mode.md
frontend/.env.example
frontend/.gitignore
frontend/AGENTS.md
frontend/app/AgentCard.tsx
frontend/app/AgentsList.tsx
frontend/app/AgentWalletPanel.tsx
frontend/app/AppModeContext.tsx
frontend/app/Board.tsx
frontend/app/BoardThemePicker.tsx
frontend/app/boardThemes.ts
frontend/app/calibrate/page.tsx
frontend/app/chains.ts
frontend/app/ChiefOfStaffPanel.tsx
frontend/app/ComputeBackendsContext.tsx
frontend/app/ComputeBackendsPill.tsx
frontend/app/ConditionalComputePill.tsx
frontend/app/ConnectButton.tsx
frontend/app/contracts.ts
frontend/app/create-agent/ModelAdvisorPanel.tsx
frontend/app/create-agent/page.tsx
frontend/app/dice.ts
frontend/app/DiceRoll.tsx
frontend/app/DiscoveryList.tsx
frontend/app/favicon.ico
frontend/app/FindHumanButton.tsx
frontend/app/globals.css
frontend/app/HeaderLinks.tsx
frontend/app/help/HelpTocSidebar.tsx
frontend/app/help/MermaidChart.tsx
frontend/app/help/page.tsx
frontend/app/HomeActionChips.tsx
frontend/app/i18n.tsx
frontend/app/layout.tsx
frontend/app/match/page.tsx
frontend/app/MobileNav.tsx
frontend/app/MoveCycler.tsx
frontend/app/NetworkDropdown.tsx
frontend/app/NetworkDropdownView.tsx
frontend/app/og-weights-reader.ts
frontend/app/page.tsx
frontend/app/PersonCard.tsx
frontend/app/play-human/page.tsx
frontend/app/play-human/PlayHumanClient.tsx
frontend/app/PlayerStatusCard.tsx
frontend/app/ProfileBadge.tsx
frontend/app/providers.tsx
frontend/app/settings/page.tsx
frontend/app/SettingsModal.tsx
frontend/app/stages/page.tsx
frontend/app/team-demo/CubeModal.tsx
frontend/app/team-demo/CubeTransactionOverlay.tsx
frontend/app/team-demo/page.tsx
frontend/app/test-chief-of-staff/page.tsx
frontend/app/tournament/page.tsx
frontend/app/training/page.tsx
frontend/app/transactions.ts
frontend/app/transactions/page.tsx
frontend/app/UsdcBalanceDisplay.tsx
frontend/app/useAgentMatchSummary.ts
frontend/app/useChaingammonName.ts
frontend/app/useChaingammonProfile.ts
frontend/app/useEnsName.ts
frontend/app/useHumanMatchSummary.ts
frontend/app/useOgWeights.ts
frontend/app/useSponsoredWrite.ts
frontend/app/wagmi.ts
frontend/chaingammon-frontend.service
frontend/CLAUDE.md
frontend/eslint.config.mjs
frontend/frontend/tests/model_advisor.png
frontend/lib/agent_model_loader.ts
frontend/lib/calibration/board_celtic.json
frontend/lib/calibration/board_cyber2.json
frontend/lib/calibration/board_darkwood.json
frontend/lib/calibration/board_medieval.json
frontend/lib/calibration/board_steampunk.json
frontend/lib/calibration/board_tokyo.json
frontend/lib/career_features.ts
frontend/lib/drand_dice.ts
frontend/lib/gnubg_state_decode.ts
frontend/lib/gnubg_state.ts
frontend/lib/match_engine.ts
frontend/lib/matchmaker.ts
frontend/lib/move_tagger.ts
frontend/lib/move_tags.tsx
frontend/lib/nostr.ts
frontend/lib/og_training.ts
frontend/lib/onnx_eval.ts
frontend/lib/onnx_worker.ts
frontend/lib/peer_connections.ts
frontend/lib/pip.ts
frontend/lib/rules_engine.ts
frontend/lib/useTaggedCandidates.ts
frontend/lib/webrtc_match.ts
frontend/next.config.ts
frontend/onnxruntime-web-1.16.3.tgz
frontend/package.json
frontend/playwright.config.ts
frontend/playwright.sandbox.config.ts
frontend/pnpm-lock.yaml
frontend/postcss.config.mjs
frontend/public/.nojekyll
frontend/public/404.html
frontend/public/backgammon_net.onnx
frontend/public/chaingammon-banner.svg
frontend/public/chaingammon-icon-mono.svg
frontend/public/chaingammon-icon.svg
frontend/public/file.svg
frontend/public/ghpages-redirect.js
frontend/public/globe.svg
frontend/public/js/ort-wasm-simd.wasm
frontend/public/js/ort-wasm.wasm
frontend/public/next.svg
frontend/public/vercel.svg
frontend/public/window.svg
frontend/README_SYNPRESS.md
frontend/README.md
frontend/scripts/square_coins.mjs
frontend/tailwind.config.ts
frontend/tests/agent-teammate.spec.ts
frontend/tests/board-landscape.spec.ts
frontend/tests/debug-privy-modal.spec.ts
frontend/tests/game-flow.spec.ts
frontend/tests/human_game_flow.spec.ts
frontend/tests/human_vs_human_synpress.spec.ts
frontend/tests/human_vs_human.spec.ts
frontend/tests/hvh_test_utils.ts
frontend/tests/live_relay_hvh.spec.ts
frontend/tests/mobile_connect.spec.ts
frontend/tests/move_dedup.spec.ts
frontend/tests/onnx_parity.spec.ts
frontend/tests/privy-metamask-login.spec.ts
frontend/tests/rules_engine.spec.ts
frontend/tests/team_play.spec.ts
frontend/tests/test_model_advisor_e2e.spec.ts
frontend/tests/test_model_advisor.spec.ts
frontend/tests/wallet_persistence.spec.ts
frontend/tsconfig.json
keeperhub/.env.example
keeperhub/match-settle.yaml
keeperhub/post-settle-audit.yaml
MISSION.md
og-bridge/package.json
og-bridge/README.md
og-bridge/src/download.mjs
og-bridge/src/kv-get.mjs
og-bridge/src/kv-put.mjs
og-bridge/src/upload.mjs
og-bridge/test/round_trip.mjs
og-compute-bridge/package.json
og-compute-bridge/README.md
og-compute-bridge/src/eval.mjs
og-compute-bridge/src/register_provider.mjs
og-compute-bridge/test/eval.test.mjs
package.json
pnpm-lock.yaml
pnpm-workspace.yaml
README.md
ROADMAP.md
scripts/bootstrap-network.sh
scripts/download_board_sprite.mjs
scripts/fetch_drand_round.py
scripts/make_deck.py
scripts/setup-keeper.sh
scripts/upload_gnubg_docs.py
scripts/vscode-tasks.json
server/.env.example
server/.python-version
server/app/agent_overlay.py
server/app/agent_wallets.py
server/app/chain_client.py
server/app/deployments.py
server/app/ens_client.py
server/app/game_record.py
server/app/game_state.py
server/app/gnubg_client.py
server/app/keeper_workflow.py
server/app/main.py
server/app/og_storage_client.py
server/app/team_mode.py
server/app/teammate_advisor.py
server/app/training_service.py
server/app/weights.py
server/chaingammon-server.service
server/pyproject.toml
server/README.md
server/scripts/deploy.sh
server/scripts/setup.sh
server/scripts/upload_base_weights.py
server/SHORTLIST.md
server/tests/test_agent_move_body.py
server/tests/test_agent_move_per_agent_nn.py
server/tests/test_agent_wallets.py
server/tests/test_counter_separation.py
server/tests/test_game_record_drand_series.py
server/tests/test_game_record_team.py
server/tests/test_gnubg_client.py
server/tests/test_keeper_workflow.py
server/tests/test_keeperhub_workflow_schema.py
server/tests/test_og_kv.py
server/tests/test_phase0_scaffold.py
server/tests/tes

## Grep excerpt

===== issue body =====
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
===== money/competition/judge hits =====
./pnpm-lock.yaml:12:    dependencies:
./pnpm-lock.yaml:14:        specifier: ^5.6.1
./pnpm-lock.yaml:16:    devDependencies:
./pnpm-lock.yaml:18:        specifier: ^6.1.2
./pnpm-lock.yaml:21:        specifier: ^25.6.0
./pnpm-lock.yaml:24:        specifier: ^17.4.2
./pnpm-lock.yaml:27:        specifier: ^2.28.6
./pnpm-lock.yaml:30:        specifier: ^10.9.2
./pnpm-lock.yaml:33:        specifier: ^6.0.3
./pnpm-lock.yaml:37:    dependencies:
./pnpm-lock.yaml:39:        specifier: 1.0.0-beta.8
./pnpm-lock.yaml:40:        version: 1.0.0-beta.8(@types/circomlibjs@0.1.6)(@types/crypto-js@4.2.2)(bufferutil@4.1.0)(circomlibjs@0.1.7(bufferutil@4.1.0)(utf-8-validate@5.0.10))(crypto-js@4.2.0)(ethers@6.16.0(bufferutil@4.1.0)(utf-8-validate@5.0.10))(rollup@4.60.2)(typechain@8.3.2(typescript@5.9.3))(typescript@5.9.3)(utf-8-validate@5.0.10)(ws@8.18.3(bufferutil@4.1.0)(utf-8-validate@5.0.10))(zod@3.25.76)
./pnpm-lock.yaml:42:        specifier: ^3.27.1
./pnpm-lock.yaml:45:        specifier: ^4.0.8
./pnpm-lock.yaml:48:        specifier: ^5.100.5
./pnpm-lock.yaml:51:        specifier: ^8.0.4
./pnpm-lock.yaml:54:        specifier: 3.4.6
./pnpm-lock.yaml:57:        specifier: ^2.21.1
./pnpm-lock.yaml:60:        specifier: ^6.16.0
./pnpm-lock.yaml:63:        specifier: ^0.8.3
./pnpm-lock.yaml:66:        specifier: ^11.15.0
./pnpm-lock.yaml:69:        specifier: 16.2.4
./pnpm-lock.yaml:70:        version: 16.2.4(@babel/core@7.29.0)(@playwright/test@1.59.1)(react-dom@19.2.4(react@19.2.4))(react@19.2.4)
./pnpm-lock.yaml:72:        specifier: ^2.10.4
./pnpm-lock.yaml:75:        specifier: 1.16.3
./pnpm-lock.yaml:78:        specifier: 19.2.4
./pnpm-lock.yaml:81:        specifier: 19.2.4
./pnpm-lock.yaml:84:        specifier: ^10.1.0
./pnpm-lock.yaml:87:        specifier: ^4.0.1
./pnpm-lock.yaml:90:        specifier: ^2.48.4
./pnpm-lock.yaml:93:        specifier: ^3.6.4
./pnpm-lock.yaml:95:    devDependencies:
./pnpm-lock.yaml:96:      '@playwright/test':
./pnpm-lock.yaml:97:        specifier: ^1.59.1
./pnpm-lock.yaml:100:        specifier: 0.0.14
./pnpm-lock.yaml:101:        version: 0.0.14(@depay/solana-web3.js@1.98.3)(@depay/web3-blockchains@9.8.13)(@playwright/test@1.59.1)(bufferutil@4.1.0)(ethers@6.16.0(bufferutil@4.1.0)(utf-8-validate@5.0.10))(typescript@5.9.3)(utf-8-validate@5.0.10)(zod@3.25.76)
./pnpm-lock.yaml:103:        specifier: ^4.1.2
./pnpm-lock.yaml:104:        version: 4.1.2(@depay/solana-web3.js@1.98.3)(@depay/web3-blockchains@9.8.13)(@playwright/test@1.59.1)(bufferutil@4.1.0)(ethers@6.16.0(bufferutil@4.1.0)(utf-8-validate@5.0.10))(playwright-core@1.48.2)(postcss@8.5.11)(ts-node@10.9.2(@types/node@20.19.39)(typescript@5.9.3))(typescript@5.9.3)(utf-8-validate@5.0.10)(zod@3.25.76)
./pnpm-lock.yaml:106:        specifier: 0.0.14
./pnpm-lock.yaml:109:        specifier: 0.0.14
./pnpm-lock.yaml:110:        version: 0.0.14(@playwright/test@1.59.1)
./pnpm-lock.yaml:112:        specifier: 0.0.14
./pnpm-lock.yaml:113:        version: 0.0.14(@playwright/test@1.59.1)(bufferutil@4.1.0)(playwright-core@1.48.2)(postcss@8.5.11)(ts-node@10.9.2(@types/node@20.19.39)(typescript@5.9.3))(typescript@5.9.3)(utf-8-validate@5.0.10)
./pnpm-lock.yaml:115:        specifier: ^4
./pnpm-lock.yaml:118:        specifier: ^20
./pnpm-lock.yaml:121:        specifier: ^19
./pnpm-lock.yaml:124:        specifier: ^19
./pnpm-lock.yaml:127:        specifier: ^9
./pnpm-lock.yaml:130:        specifier: 16.2.4
./pnpm-lock.yaml:133:        specifier: ^4
./pnpm-lock.yaml:136:        specifier: ^5
./pnpm-lock.yaml:140:    dependencies:
./pnpm-lock.yaml:142:        specifier: ^1.2.6
./pnpm-lock.yaml:145:        specifier: ^6.15.0
./pnpm-lock.yaml:149:    dependencies:
./pnpm-lock.yaml:151:        specifier: 1.0.0-beta.8
./pnpm-lock.yaml:152:        version: 1.0.0-beta.8(@types/circomlibjs@0.1.6)(@types/crypto-js@4.2.2)(bufferutil@4.1.0)(circomlibjs@0.1.7(bufferutil@4.1.0)(utf-8-validate@5.0.10))(crypto-js@4.2.0)(ethers@6.16.0(bufferutil@4.1.0)(utf-8-validate@5.0.10))(rollup@4.60.2)(typechain@8.3.2(typescript@6.0.3))(typescript@6.0.3)(utf-8-validate@5.0.10)(ws@8.20.1(bufferutil@4.1.0)(utf-8-validate@5.0.10))(zod@3.25.76)
./pnpm-lock.yaml:154:        specifier: ^6.15.0
./pnpm-lock.yaml:162:    peerDependencies:
./pnpm-lock.yaml:170:    peerDependencies:
./pnpm-lock.yaml:171:      '@types/circomlibjs': ^0.1.6
./pnpm-lock.yaml:173:      circomlibjs: ^0.1.6
./pnpm-lock.yaml:198:    resolution: {integrity: sha512-T1NCJqT/j9+cn8fvkt7jtwbLBfLC/1y1c7NtCeXFRgzGTsafi68MRv8yzkYSapBnFA6L3U2VSc02ciDzoAJhJg==}
./pnpm-lock.yaml:224:    peerDependencies:
./pnpm-lock.yaml:306:    peerDependencies:
./pnpm-lock.yaml:319:  '@ecies/ciphers@0.2.6':
./pnpm-lock.yaml:322:    peerDependencies:
./pnpm-lock.yaml:323:      '@noble/ciphers': ^1.0.0
./pnpm-lock.yaml:395:    resolution: {integrity: sha512-AjEcivGAlPs3UAcJedMa9qYg9eSfU6FnGHJjT8s346HSKkrcWlYezGE8VaO2xKfvvlZkgAhyvl06OJOxiMgOYQ==}
./pnpm-lock.yaml:619:    peerDependencies:
./pnpm-lock.yaml:784:    peerDependencies:
./pnpm-lock.yaml:790:    peerDependencies:
./pnpm-lock.yaml:799:    peerDependencies:
./pnpm-lock.yaml:807:    peerDependencies:
./pnpm-lock.yaml:814:    peerDependencies:
./pnpm-lock.yaml:820:    peerDependencies:
./pnpm-lock.yaml:1009:    resolution: {integrity: sha512-NdbMQUSfXLYIQol5VyMtinm9pZDciiMfN7RtmSuSB78io1hqwJ0naYfxyW6vgxWBkzWymQa/3uLDlbfmshtCaA==}
./pnpm-lock.yaml:1051:    peerDependencies:
./pnpm-lock.yaml:1059:    peerDependencies:
./pnpm-lock.yaml:1105:    resolution: {integrity: sha512-5yb2gMI1BDm0JybZezeoX/3XhPDOtTbcFvpTXM9kxsoZjPZFh4XciqRbpD6N86HYZqWDhEaKUDuOyR0sQHEjMA==}
./pnpm-lock.yaml:1115:    peerDependencies:
./pnpm-lock.yaml:1117:      eciesjs: '*'
./pnpm-lock.yaml:1219:  '@noble/ciphers@1.2.1':
./pnpm-lock.yaml:1223:  '@noble/ciphers@1.3.0':
./pnpm-lock.yaml:1227:  '@noble/ciphers@2.1.1':
./pnpm-lock.yaml:1258:    resolution: {integrity: sha512-gbKGcRUYIjA3/zCCNaWDciTMFI0dCkvou3TL8Zmy5Nc7sJ47a0jtOeZoTaMxkuqRo9cRhjOdZJXegxYE5FN/xw==}
./pnpm-lock.yaml:1349:    peerDependencies:
./pnpm-lock.yaml:1357:    peerDependencies:
./pnpm-lock.yaml:1363:    peerDependencies:
./pnpm-lock.yaml:1372:    peerDependencies:
./pnpm-lock.yaml:1378:    peerDependencies:
./pnpm-lock.yaml:1383:    peerDependencies:
./pnpm-lock.yaml:1405:    peerDependencies:
./pnpm-lock.yaml:1460:  '@playwright/test@1.59.1':
./pnpm-lock.yaml:1482:    peerDependencies:
./pnpm-lock.yaml:1487:    peerDependencies:
./pnpm-lock.yaml:1490:    peerDependenciesMeta:
./pnpm-lock.yaml:1501:    peerDependencies:
./pnpm-lock.yaml:1511:    peerDependenciesMeta:
./pnpm-lock.yaml:1535:    peerDependencies:
./pnpm-lock.yaml:1573:    peerDependencies:
./pnpm-lock.yaml:1579:    peerDependencies:
./pnpm-lock.yaml:1585:    peerDependencies:
./pnpm-lock.yaml:1591:  '@reown/appkit-common@1.8.17-wc-circular-dependencies-fix.0':
./pnpm-lock.yaml:1600:  '@reown/appkit-controllers@1.8.17-wc-circular-dependencies-fix.0':
./pnpm-lock.yaml:1609:  '@reown/appkit-pay@1.8.17-wc-circular-dependencies-fix.0':
./pnpm-lock.yaml:1618:  '@reown/appkit-polyfills@1.8.17-wc-circular-dependencies-fix.0':
./pnpm-lock.yaml:1627:  '@reown/appkit-scaffold-ui@1.8.17-wc-circular-dependencies-fix.0':
./pnpm-lock.yaml:1636:  '@reown/appkit-ui@1.8.17-wc-circular-dependencies-fix.0':
./pnpm-lock.yaml:1640:    resolution: {integrity: sha512-WR17ql77KOMKfyDh7RW4oSfmj+p5gIl0u8Wmopzbx5Hd0HcPVZ5HmTDpwOM9WCSxYcin0fsSAoI+nVdvrhWNtw==}
./pnpm-lock.yaml:1644:    peerDependencies:
./pnpm-lock.yaml:1647:  '@reown/appkit-utils@1.8.17-wc-circular-dependencies-fix.0':
./pnpm-lock.yaml:1649:    peerDependencies:
./pnpm-lock.yaml:1654:    peerDependencies:
./pnpm-lock.yaml:1660:  '@reown/appkit-wallet@1.8.17-wc-circular-dependencies-fix.0':
./pnpm-lock.yaml:1661:    resolution: {integrity: sha512-s0RTVNtgPtXGs+eZELVvTu1FRLuN15MyhVS//3/4XafVQkBBJarciXk9pFP71xeSHRzjYR1lXHnVw28687cUvQ==}
./pnpm-lock.yaml:1669:  '@reown/appkit@1.8.17-wc-circular-dependencies-fix.0':
./pnpm-lock.yaml:1678:    peerDependencies:
./pnpm-lock.yaml:1680:    peerDependenciesMeta:
./pnpm-lock.yaml:1687:    peerDependencies:
./pnpm-lock.yaml:1689:    peerDependenciesMeta:
./pnpm-lock.yaml:1696:    peerDependencies:
./pnpm-lock.yaml:1698:    peerDependenciesMeta:
./pnpm-lock.yaml:1705:    peerDependencies:
./pnpm-lock.yaml:1709:    peerDependenciesMeta:
./pnpm-lock.yaml:1718:    peerDependencies:
./pnpm-lock.yaml:1720:    peerDependenciesMeta:
./pnpm-lock.yaml:1735:    resolution: {integrity: sha512-UwRE7CGpvSVEQS8gUMBe1uADWjNnVgP3Iusyda1nSRwNDCsRjnGc7w6El6WLQsXmZTbLZx9cecegumcitNfpmA==}
./pnpm-lock.yaml:1937:  '@sentry/tracing@5.30.0':
./pnpm-lock.yaml:1960:    peerDependencies:
./pnpm-lock.yaml:1965:    peerDependencies:
./pnpm-lock.yaml:1970:    peerDependencies:
./pnpm-lock.yaml:1976:    peerDependencies:
./pnpm-lock.yaml:1982:    peerDependencies:
./pnpm-lock.yaml:1984:    peerDependenciesMeta:
./pnpm-lock.yaml:1991:    peerDependencies:
./pnpm-lock.yaml:1993:    peerDependenciesMeta:
./pnpm-lock.yaml:2000:    peerDependencies:
./pnpm-lock.yaml:2002:    peerDependenciesMeta:
./pnpm-lock.yaml:2009:    peerDependencies:
./pnpm-lock.yaml:2011:    peerDependenciesMeta:
./pnpm-lock.yaml:2018:    peerDependencies:
./pnpm-lock.yaml:2020:    peerDependenciesMeta:
./pnpm-lock.yaml:2027:    peerDependencies:
./pnpm-lock.yaml:2029:    peerDependenciesMeta:
./pnpm-lock.yaml:2036:    peerDependencies:
./pnpm-lock.yaml:2037:      fastestsmallesttextencoderdecoder: ^1.0.22
./pnpm-lock.yaml:2039:    peerDependenciesMeta:
./pnpm-lock.yaml:2040:      fastestsmallesttextencoderdecoder:
./pnpm-lock.yaml:2048:    peerDependencies:
./pnpm-lock.yaml:2050:    peerDependenciesMeta:
./pnpm-lock.yaml:2058:    peerDependencies:
./pnpm-lock.yaml:2060:    peerDependenciesMeta:
./pnpm-lock.yaml:2067:    peerDependencies:
./pnpm-lock.yaml:2069:    peerDependenciesMeta:
./pnpm-lock.yaml:2076:    peerDependencies:
./pnpm-lock.yaml:2078:    peerDependenciesMeta:
./pnpm-lock.yaml:2085:    peerDependencies:
./pnpm-lock.yaml:2087:    peerDependenciesMeta:
./pnpm-lock.yaml:2094:    peerDependencies:
./pnpm-lock.yaml:2096:    peerDependenciesMeta:
./pnpm-lock.yaml:2103:    peerDependencies:
./pnpm-lock.yaml:2105:    peerDependenciesMeta:
./pnpm-lock.yaml:2112:    peerDependencies:
./pnpm-lock.yaml:2114:    peerDependenciesMeta:
./pnpm-lock.yaml:2121:    peerDependencies:
./pnpm-lock.yaml:2123:    peerDependenciesMeta:
./pnpm-lock.yaml:2130:    peerDependencies:
./pnpm-lock.yaml:2132:    peerDependenciesMeta:
./pnpm-lock.yaml:2139:    peerDependencies:
./pnpm-lock.yaml:2141:    peerDependenciesMeta:
./pnpm-lock.yaml:2148:    peerDependencies:
./pnpm-lock.yaml:2150:    peerDependenciesMeta:
./pnpm-lock.yaml:2157:    peerDependencies:
./pnpm-lock.yaml:2159:    peerDependenciesMeta:
./pnpm-lock.yaml:2166:    peerDependencies:
./pnpm-lock.yaml:2168:    peerDependenciesMeta:
./pnpm-lock.yaml:2175:    peerDependencies:
./pnpm-lock.yaml:2177:    peerDependenciesMeta:
./pnpm-lock.yaml:2184:    peerDependencies:
./pnpm-lock.yaml:2186:    peerDependenciesMeta:
./pnpm-lock.yaml:2193:    peerDependencies:
./pnpm-lock.yaml:2195:    peerDependenciesMeta:
./pnpm-lock.yaml:2202:    peerDependencies:
./pnpm-lock.yaml:2204:    peerDependenciesMeta:
./pnpm-lock.yaml:2211:    peerDependencies:
./pnpm-lock.yaml:2213:    peerDependenciesMeta:
./pnpm-lock.yaml:2220:    peerDependencies:
./pnpm-lock.yaml:2222:    peerDependenciesMeta:
./pnpm-lock.yaml:2229:    peerDependencies:
./pnpm-lock.yaml:2231:    peerDependenciesMeta:
./pnpm-lock.yaml:2238:    peerDependencies:
./pnpm-lock.yaml:2240:    peerDependenciesMeta:
./pnpm-lock.yaml:2247:    peerDependencies:
./pnpm-lock.yaml:2249:    peerDependenciesMeta:
./pnpm-lock.yaml:2256:    peerDependencies:
./pnpm-lock.yaml:2258:    peerDependenciesMeta:
./pnpm-lock.yaml:2265:    peerDependencies:
./pnpm-lock.yaml:2267:    peerDependenciesMeta:
./pnpm-lock.yaml:2272:    resolution: {integrity: sha512-ku8zTUMrkCWci66PRIBC+1mXepEnZH/q1f3ck0kJZ95a06bOTl5KU7HeXWtskkyefzARJ5zvCs54AD5nxjQJ+A==}
./pnpm-lock.yaml:2274:    peerDependencies:
./pnpm-lock.yaml:2276:    peerDependenciesMeta:
./pnpm-lock.yaml:2283:    peerDependencies:
./pnpm-lock.yaml:2285:    peerDependenciesMeta:
./pnpm-lock.yaml:2292:    peerDependencies:
./pnpm-lock.yaml:2294:    peerDependenciesMeta:
./pnpm-lock.yaml:2301:    peerDependencies:
./pnpm-lock.yaml:2303:    peerDependenciesMeta:
./pnpm-lock.yaml:2310:    peerDependencies:
./pnpm-lock.yaml:2312:    peerDependenciesMeta:
./pnpm-lock.yaml:2319:    peerDependencies:
./pnpm-lock.yaml:2321:    peerDependenciesMeta:
./pnpm-lock.yaml:2328:    peerDependencies:
./pnpm-lock.yaml:2330:    peerDependenciesMeta:
./pnpm-lock.yaml:2346:    peerDependencies:
./pnpm-lock.yaml:2347:      '@playwright/test': '*'
./pnpm-lock.yaml:2352:    peerDependencies:
./pnpm-lock.yaml:2357:    peerDependencies:
./pnpm-lock.yaml:2358:      '@playwright/test': '*'
./pnpm-lock.yaml:2362:    peerDependencies:
./pnpm-lock.yaml:2363:      '@playwright/test': '*'
./pnpm-lock.yaml:2367:    peerDependencies:
./pnpm-lock.yaml:2368:      '@playwright/test': 1.48.2
./pnpm-lock.yaml:2373:    peerDependencies:
./pnpm-lock.yaml:2374:      '@playwright/test': '*'
./pnpm-lock.yaml:2441:    bundledDependencies:
./pnpm-lock.yaml:2473:    peerDepen

