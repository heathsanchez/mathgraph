# Prize Recon Report

## Verdict

`PARK_RISK`

## Decision

JSON:
{
  "verdict": "PARK_RISK",
  "issue": {
    "url": "https://github.com/moldovancsaba/matimato/issues/66",
    "title": "Competition: Arena tournaments - scheduled tables and ranked event flow",
    "state": "OPEN",
    "labels": [
      "enhancement",
      "type:data",
      "type:api",
      "type:ops",
      "quality:gds-only",
      "quality:accessibility",
      "priority:p1",
      "feature:leaderboard",
      "feature:gamification",
      "type:frontend",
      "type:contracts",
      "type:testing",
      "feature:telemetry",
      "type:product",
      "feature:tournaments"
    ],
    "comment_count": 1,
    "updatedAt": "2026-07-01T07:31:35Z"
  },
  "money": true,
  "competition": true,
  "judge": true,
  "local": true,
  "mgfit": true,
  "risk": true
}

## Cheap commands

pwd=/Users/heath/Documents/mathgraph-lean-work/external/money_opportunity_scout_v4_prize_words/moldovancsaba__matimato_66

README head:
# Matimato

A fresh Next.js + Phaser + MongoDB implementation of Matimato.

Current release: `2.7.0`.

## Commands

```bash
npm install
npm run lint
npm run dev
npm run test
npm run build
npm run verify
npm run assets:ios
npm run mobile:smoke
npm run ios:preflight
npm run ios:sync
npm run ios:build
npm run ios:archive
npm run ios:export
npm run ios:upload
npm audit --omit=dev
```

## Stack

- Next.js App Router
- Sovereign Squad General Design System `@doneisbetter/gds` 3.7.0 for React UI controls and theme bootstrap
- Phaser 3 for the game board
- MongoDB Atlas for persistence
- Vitest for rules tests
- Capacitor 8 for the iOS WKWebView wrapper
- Playwright for mobile viewport smoke checks

## Required environment

Keep `.env` / `.env.*` local and set:

```bash
MONGODB_URI="mongodb+srv://..."
MONGODB_DB="matimato"
```

## Feature flags

These flags default to enabled. Set either value to `false` for rollback.

```bash
NEXT_PUBLIC_MATIMATO_ONBOARDING=true
NEXT_PUBLIC_MATIMATO_LOBBY_V2=true
NEXT_PUBLIC_MATIMATO_DAILY_V2=true
NEXT_PUBLIC_MATIMATO_BLITZ_MODE=true
NEXT_PUBLIC_MATIMATO_TELEMETRY=true
NEXT_PUBLIC_MATIMATO_TRAINING_CHOICE=true
NEXT_PUBLIC_MATIMATO_COACH_BUBBLES=true
NEXT_PUBLIC_MATIMATO_BOARD_JOURNEY=true
NEXT_PUBLIC_MATIMATO_SERVICE_WORKER=true
NEXT_PUBLIC_MATIMATO_APP_VERSION=2.7.0
NEXT_PUBLIC_MATIMATO_IOS_BUILD_NUMBER=web
MATIMATO_BLITZ_ENABLED=true
MATIMATO_EVENTS_ENABLED=true
MATIMATO_BOARD_JOURNEY_ENABLED=true
NEXT_PUBLIC_MATIMATO_SEASONAL_EVENTS=true
MATIMATO_SEASONAL_EVENTS_ENABLED=true
NEXT_PUBLIC_MATIMATO_RULE_ASSIST=true
NEXT_PUBLIC_MATIMATO_AI_PROFILES=true
NEXT_PUBLIC_MATIMATO_FRIENDS=true
MATIMATO_FRIENDS_ENABLED=true
NEXT_PUBLIC_MATIMATO_REPLAYS=true
MATIMATO_REPLAYS_ENABLED=true
CAPACITOR_SERVER_URL=https://matimato.vercel.app
CAPACITOR_BUILD_NUMBER=local
APP_STORE_CONNECT_API_KEY_ID=
APP_STORE_CONNECT_ISSUER_ID=
APP_STORE_CONNECT_API_KEY_PATH=
```

`NEXT_PUBLIC_MATIMATO_ONBOARDING=false` disables automatic first-run tutorial entry while keeping normal solo and battle actions available.

`NEXT_PUBLIC_MATIMATO_LOBBY_V2=false` restores the direct battle create/join flow for new client sessions. Existing lobby snapshots remain readable and recoverable through `/play/[id]`.

`NEXT_PUBLIC_MATIMATO_DAILY_V2=false` hides daily challenge entry on the Quests screen without affecting solo, battle, or existing daily snapshots.

`NEXT_PUBLIC_MATIMATO_BLITZ_MODE=false` hides Blitz entry points. `MATIMATO_BLITZ_ENABLED=false` rejects new Blitz creation server-side while keeping existing saved snapshots readable.

`NEXT_PUBLIC_MATIMATO_TELEMETRY=false` disables the client event emitter. `MATIMATO_EVENTS_ENABLED=false` keeps `/api/events` accepting payloads but marks ingestion degraded and skips event storage.

`NEXT_PUBLIC_MATIMATO_TRAINING_CHOICE=false` restores the previous automatic onboarding behavior. `NEXT_PUBLIC_MATIMATO_COACH_BUBBLES=false` hides contextual tutorial explanations. `NEXT_PUBLIC_MATIMATO_BOARD_JOURNEY=false` hides the board journey UI. `MATIMATO_BOARD_JOURNEY_ENABLED=false` rejects new board purchases and active-board changes server-side while keeping stored wallet/unlock data readable.

`NEXT_PUBLIC_MATIMATO_SEASONAL_EVENTS=false` hides the seasonal album and reward track. `MATIMATO_SEASONAL_EVENTS_ENABLED=false` pauses server-side season progress evaluation while preserving saved ledgers. `NEXT_PUBLIC_MATIMATO_RULE_ASSIST=false` hides persistent help buttons. `NEXT_PUBLIC_MATIMATO_AI_PROFILES=false` falls back to the rookie solo AI profile.

`NEXT_PUBLIC_MATIMATO_FRIENDS=false` hides Friends UI and profile invite links. `MATIMATO_FRIENDS_ENABLED=false` rejects new friend/gift writes while preserving stored relationships and gift ledgers. `NEXT_PUBLIC_MATIMATO_REPLAYS=false` hides replay share entry points. `MATIMATO_REPLAYS_ENABLED=false` disables `/api/replays/[id]` without changing existing match snapshots.

`NEXT_PUBLIC_MATIMATO_SERVICE_WORKER=false` stops registering the offline shell worker for new sessions. `CAPACITOR_SERVER_URL` controls the iOS wrapper target and must stay on HTTPS for production.

## iOS mobile app

Matimato now has a production iOS delivery lane documented in [`docs/ios-mobile.md`](/Users/Shared/Projects/matimato/docs/ios-mobile.md). The chosen architecture is an installable iOS PWA plus a Capacitor WKWebView wrapper around the existing GDS/Phaser web runtime.

Key commands:

```bash
npm run assets:ios
npm run ios:sync
npm run ios:preflight
npm run ios:build
npm run ios:archive
npm run ios:export
npm run ios:upload
MATIMATO_SMOKE_URL=https://matimato.vercel.app npm run mobile:smoke
```

The local machine currently lacks full Xcode, Apple code-signing identities, provisioning profiles, and App Store Connect API credentials, so `ios:preflight` blocks archive/upload. Apple signing, App Store Connect app creation, and TestFlight upload require external Apple Developer credentials and are intentionally not stored in this repository.

## Board progression

Players now start on a 5x5 board for solo and Blitz. The Journey screen shows lifetime XP, spendable XP, unlocked boards, next-board cost, active board selection, and start actions. Bigger boards are unlocked sequentially:

| Board | Cost |
| --- | ---: |
| 5x5 | Free |
| 6x6 | 120 XP |
| 7x7 | 260 XP |
| 8x8 | 520 XP |
| 9x9 | 900 XP |

Match rewards increase both lifetime XP and spendable XP. Purchases reduce spendable XP only; lifetime XP remains the ranking/progression total. Existing profiles without a wallet split are normalized by treating current XP as both lifetime and spendable XP.

Progression APIs:

```ts
GET /api/progression?playerId=...

POST /api/progression
{ "type": "purchaseBoard", "playerId": "...", "boardSize": 6, "actionId": "uuid" }

POST /api/progression
{ "type": "selectBoard", "playerId": "...", "boardSize": 6 }

POST /api/progression
{ "type": "claimSeasonReward", "playerId": "...", "rewardId": "starter-cache" }
```

Purchases are server-validated by sequence and spendable balance, idempotent by action id or board size, and never trust client-supplied costs or final balances. Solo and Blitz creation accepts an unlocked `boardSize`; battle and daily remain on the current safe 9x9 behavior.

## Seasonal collection track

The Quests screen includes a deterministic seasonal album and reward track. Eligible authoritative actions from solo, daily, Blitz, Journey unlocks, and recap shares update server-side season progress. Rewards are granted and claimed idempotently through `/api/progression`; claimed XP increases lifetime and spendable balances once.

Season rewards are deterministic. There are no paid packs, odds, loot boxes, or tradable collectibles.

## Persistent rule assist

Every primary product screen exposes GDS-only rules help. The help dialog covers objective, turn flow, legal moves, scoring, traps, XP, board journey, recap, and ranks. Live matches include a help button over the Phaser host that derives contextual hints from public board state without solving the best move.

## Bot opponent profiles

Solo mode supports named AI profiles. Players start with `Mati Rookie`; larger unlocked boards expose stronger profiles with deterministic legal move selection, bounded decision time, and replay-safe profile metadata on snapshots.

## Blitz mode

Blitz is a turn-based quick-play mode with a server-authored per-turn clock. The client displays the countdown and can request timeout resolution, but the server decides whether the deadline expired.

```ts
POST /api/games
{ "type": "create", "mode": "blitz", "playerId": "...", "playerTag": "...", "clock": { "turnLimitMs": 30000 } }

POST /api/games
{ "type": "timeout", "matchId": "...", "playerId": "...", "deadlineVersion": 4 }
```

Existing solo, battle, and daily snapshots may omit `clock`; clients treat omitted clocks as untimed. Timeout requests are idempotent by match, side, and deadline version. Repeated Blitz timeouts use the documented forfeit policy.

## Match recap

Completed matches transition to a GDS-owned recap screen with final score, outcome reason, move replay, share action, ranks navigation, and rematch. Game snapshots now keep an optional `moveLog` so recap can replay claimed tiles and timeout resolutions without reading Phaser state.

## Friends and gifts

The Friends screen stores anonymous-player relationships created from battle lobbies, recaps, or profile invite links. Friend summaries expose tags and hashed identifiers only; raw friend player ids stay server-side or in write-only invite actions. Each active relationship supports one deterministic 15 XP gift per sender/receiver UTC day and a normal V2 battle lobby entry that still requires existing ready checks.

Friend actions use `/api/friends`:

```ts
GET /api/friends?playerId=...
POST /api/friends
{ "type": "acceptInvite", "playerId": "...", "friendPlayerId": "...", "friendTag": "...", "actionId": "uuid" }
POST /api/friends
{ "type": "sendGift", "playerId": "...", "friendshipId": "...", "actionId": "uuid" }
```

Remove and block controls require confirmation in the Friends screen. Blocked relationships reject gifts and friend battles. Gifts are idempotent by `friendshipId:senderId:yyyy-mm-dd`; retries cannot double-grant XP. There are no paid gifts, random packs, contact imports, chat, push notifications, or competitive-rank boosts.

## Read-only replays

Completed matches are shareable at `/replay/{matchId}` through a public-safe DTO from `/api/replays/[id]`. Replay responses include final score context, sanitized tags, board size, outcome, and move frames stripped of raw player ids, invite codes, and action ids. Completed legacy snapshots without `moveLog` render a summary-only replay instead of failing.

Replay pages are read-only. Conversion actions create new solo, Blitz, or V2 battle sessions through the existing `

## Issue body

## Executive Summary

Add a scheduled Arena tournament layer that lets Matimato run weekly competitive events with clear entry, deterministic scoring, leaderboard visibility, and operational controls. This builds on #37 rather than duplicating the ranks read model, turning competition from a passive leaderboard into a time-boxed reason to return.

Canonical issue structure: https://github.com/sovereignsquad/general-design-system/issues/81

## Business / Product Context

Board Game Arena demonstrates strong demand for structured competition: its 2025 recap reported almost 80k tournaments, top tournament games such as Carcassonne, Can't Stop, and Azul, and Arena games with millions of tables created. BGA also markets real-time and turn-based play, ranked games, and broad web/mobile access. Dune: Imperium Digital similarly keeps players returning with achievements, challenges, and rotating Skirmish Mode. Matimato has daily, Blitz, seasonal album, and one open ranks issue, but it lacks scheduled events that package those loops into a visible competition.

References: https://en.boardgamearena.com/news?id=1025 | https://en.boardgamearena.com/ | https://play.google.com/store/apps/details?id=com.direwolfdigital.dune | https://github.com/moldovancsaba/matimato/issues/37

## Current State

- Daily challenge exists with weekly daily leaderboard.
- Blitz exists with server-owned clocks.
- Ranks #37 is open for fair weekly/mode leaderboards and player rank lookup.
- Seasonal album exists but its tasks are individual progression goals, not joined competitions.
- No tournament collection, event registration, tournament entry screen, or tournament-specific scoring exists.

## Problem Statement

Matimato currently has modes, but no shared competitive calendar. Players can complete daily or Blitz alone, yet they cannot join a visible weekly race, see event-specific standings, or understand when an event starts/ends. That weakens retention and makes ranks less actionable.

## Goals

### Functional Goals

- Define Arena tournament definitions with mode, schedule, eligibility, scoring, and reward policy.
- Let players join an active tournament from Quests/Ranks using a GDS-only flow.
- Record eligible match completions into tournament standings idempotently.
- Show tournament status, player's rank, top rows, reset/end time, and scoring explanation.
- Support v1 tournament modes: Daily Sprint and Blitz Ladder.

### Technical Goals

- Reuse #37 rank score/tie-break where possible, with tournament-specific window ids.
- Store tournament participation and result contributions separately from profile XP.
- Prevent duplicate match contribution and rank inflation.
- Keep tournaments deterministic and fully server-authoritative.

### UX Goals

- Entry is clear: open, joined, completed, locked, ended, and rewards claimable.
- Players understand what to play next and why their score changed.
- Errors are recoverable and do not hide existing daily/Blitz entry points.

## Non-Goals

- No synchronous bracket matchmaking in v1.
- No cash prizes, paid entry, purchasable score boosts, or randomized rewards.
- No push notifications or external calendar integration.
- No replacement for #37; this depends on or reuses its read model.

## Mandatory Technical Constraints

All UI/UX/frontend work must exclusively use https://github.com/sovereignsquad/general-design-system. Accessibility is mandatory. Tournament tables, filters, join controls, and status messaging must use GDS primitives and token-driven styling only.

## Architecture

Ownership boundaries:

- `lib/shared/types.ts` owns `TournamentDefinition`, `TournamentEntry`, `TournamentStanding`, and API DTOs.
- `lib/game/tournaments.ts` owns schedule, scoring, eligibility, and deterministic active tournament selection.
- `lib/server/store.ts` owns MongoDB persistence and idempotent contribution writes.
- `app/api/tournaments/route.ts` owns list/join/standings APIs.
- Match completion path calls `recordTournamentContribution` after authoritative completion.
- Ranks/Quests screens render GDS tournament cards and standings.

Runtime flow:

```text
GET /api/tournaments?playerId
  -> returns active + upcoming tournament summaries
player joins active event
  -> POST join writes TournamentEntry if eligible
player completes daily/blitz match
  -> completeGame calls tournament evaluator
  -> evaluator records contribution if mode/window/player eligible
  -> standings read model updates or derives ranks
UI fetches standings
  -> shows player rank, top rows, scoring, and reset/end state
```

## Data Model / Contracts

```ts
type TournamentMode = 'daily-sprint' | 'blitz-ladder';
type TournamentStatus = 'upcoming' | 'active' | 'ended' | 'claimable';

type TournamentDefinition = {
  tournamentId: string;
  title: string;
  mode: TournamentMode;
  startsAt: string;
  endsAt: string;
  scoringVersion: number;
  eligibility: { minBoardSize?: 5 | 6 | 7 | 8 | 9; requiresJoin: boolean };
};

type TournamentEntry = {
  id: string; // tournamentId:playerId
  tournamentId: string;
  playerId: string;
  tag: string;
  joinedAt: string;
};

type TournamentContribution = {
  id: string; // tournamentId:matchId:playerId
  tournamentId: string;
  matchId: string;
  playerId: string;
  mode: GameMode;
  score: number;
  outcome: 'victory' | 'draw' | 'defeat';
  completedAt: string;
};

type TournamentStanding = {
  rank: number;
  tag: string;
  score: number;
  wins: number;
  matches: number;
  bestScore: number;
  playerRank?: boolean;
};
```

## API Contracts

`GET /api/tournaments?playerId=...` returns `{ active: TournamentSummary[], upcoming: TournamentSummary[], serverNow }`.

`POST /api/tournaments` with `{ type: 'join', tournamentId, playerId, tag, actionId }` returns updated summary.

`GET /api/tournaments/[id]/standings?playerId=...` returns `{ tournament, rows, playerRank, scoringVersion, serverNow }`.

Invalid tournament, inactive tournament, missing eligibility, duplicate join, and unsupported mode return stable error codes.

## Algorithm / Processing Logic

```ts
function recordTournamentContribution(snapshot, player) {
  const tournaments = activeTournamentsForMode(snapshot.mode, snapshot.completedAt);
  for (const tournament of tournaments) {
    if (tournament.eligibility.requiresJoin && !hasEntry(tournament.id, player.id)) continue;
    const contributionId = `${tournament.id}:${snapshot.id}:${player.id}`;
    insertContributionIfAbsent(contributionId, buildContribution(snapshot, player));
    upsertStanding(tournament.id, player.id, scoreContribution(snapshot, player, tournament.scoringVersion));
  }
}
```

## Mathematical / Ranking Logic

Use #37 rank scoring as the base. Tournament v1 score:

```text
contributionScore = winPoints + max(0, score) * 2 + completionBonus + speedBonus
winPoints = victory ? 100 : draw ? 35 : 0
completionBonus = 10
speedBonus = daily-sprint ? max(0, 30 - attemptsOrMinutesBucket) : 0
```

Tie-break: score desc, wins desc, bestScore desc, earliestContributionAt asc, hashedPlayerId asc. Exact constants must be documented with `scoringVersion = 1` and covered by tests.

## UX / Operator Behaviour

States: loading tournament list, no active tournaments, upcoming tournament, join available, joined, contribution pending, ranked, player outside top rows, ended, claimable reward, server unavailable, offline write blocked, and scoring info. Tournament UI must never hide normal Daily/Blitz actions if tournament APIs fail.

## Accessibility Requirements

Tournament cards and standings must be keyboard accessible and screen-reader compatible. Active state, end time, rank, score, and eligibility reason must be text-visible. Tables/lists use semantic GDS patterns. Focus returns after join confirmation. Time remaining is not color-only. Reduced motion is respected for rank changes.

## Edge Cases

Week boundary during match completion, tournament ends during request, duplicate completion retry, player joins after completing eligible match, player changes tag, inactive tournament standings, empty standings, MongoDB write succeeds but standings read fails, and rollback while tournament data exists.

## Performance Expectations

Standing reads return top 50 plus player row with indexed `tournamentId`, `score`, and `playerId`. Contribution writes are O(1) with unique ids. No leaderboard request may perform unbounded profile/history scans.

## Security / Privacy Requirements

Expose display tags and aggregate scores only. Do not expose raw player ids in UI or telemetry. Server validates tournament id, time window, mode, and eligibility. No client-supplied score or completion time is trusted.

## Observability

Emit `tournament_list_viewed`, `tournament_joined`, `tournament_join_failed`, `tournament_contribution_recorded`, `tournament_standings_viewed`, `tournament_empty`, and `tournament_error` with tournamentId, mode, status, rank bucket, durationMs, and stable error code.

## Retries / Timeouts

Join is idempotent by `tournamentId:playerId` and action id. Contribution writes are idempotent by `tournamentId:matchId:playerId`. Client fetches use timeout and retry button. If contribution write fails during match completion, completeGame remains successful and records a recoverable ops error for replay/backfill.

## Rollback / Recovery

Gate UI with `NEXT_PUBLIC_MATIMATO_TOURNAMENTS=false`. Gate server contribution and join writes with `MATIMATO_TOURNAMENTS_ENABLED=false`. Rollback hides tournament surfaces and pauses contribution writes while preserving existing standings. Provide a backfill script or documented function to replay completed match summaries for a tournament window if contribution recording was down.

## Testing Requirements

Unit tests for active tournament selection, scoring, tie-breaks, eligibility, and window boundaries. API tests for list/join/standings errors and duplicate joins. Integration tests for daily and Blitz completion contribution idempotency. Component/E2E tests for join flow, standings table, player outside top rows, empty state, and 320px mobile layout.

## Documentation Requirements

Update README flags, architecture tournament section, scoringVersion docs, telemetry allowlist, and release QA. Document operator steps to create/disable an event and backfill contributions.

## Dependencies / Execution Order

Depends on #37 for fair rank read model or must implement a compatible tournament-local standing model if #37 is not shipped first. Uses delivered Daily, Blitz, telemetry, and progression foundations. Delivery order: 360.

## Acceptance Criteria

- [ ] Active/upcoming Arena tournaments are available through server contracts.
- [ ] Players can join a tournament through GDS-only accessible UI.
- [ ] Daily and Blitz completions contribute idempotently when eligible.
- [ ] Standings show top rows, player rank, scoring, and event timing.
- [ ] No duplicate retries inflate score.
- [ ] Tests, docs, observability, rollback, and backfill behavior are complete.

## Handover

### What Changed
Tournament definitions, join/standings APIs, match contribution recording, GDS UI, telemetry, tests, and docs.

### How to Run
`npm run dev`, `npm test`, `npm run build`, `npm run verify`.

### Configuration
`NEXT_PUBLIC_MATIMATO_TOURNAMENTS=true`, `MATIMATO_TOURNAMENTS_ENABLED=true`.

### How to Verify
Join an active event, complete a Daily/Blitz match, retry completion/contribution, and confirm standing rank is stable.

### Known Limitations
V1 has no bracket matchmaking, cash prizes, or push notifications.

### Rollback Plan
Set tournament flags to `false`; existing Daily, Blitz, Ranks, and season flows continue.

## Comments

## moldovancsaba — 2026-07-01T07:31:35Z

Architect maintenance pass, 2026-07-01:

Moved from Todo to Backlog for sequencing. Arena tournaments remain valuable but are larger than the next two-item delivery lane and should follow after social/replay foundations clarify sharing, identity, and competitive retention behavior. Keep milestone and priority; revisit after the selected Todo items land.

## Inventory excerpt

top files
.env.example
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
.git/objects/pack/pack-1cf0aec889101a89a7e9e711b817c2beec8be978.idx
.git/objects/pack/pack-1cf0aec889101a89a7e9e711b817c2beec8be978.pack
.git/objects/pack/pack-1cf0aec889101a89a7e9e711b817c2beec8be978.promisor
.git/objects/pack/pack-f99bd16e979642ff3ad64f7fe6fb38726cd181bb.idx
.git/objects/pack/pack-f99bd16e979642ff3ad64f7fe6fb38726cd181bb.pack
.git/objects/pack/pack-f99bd16e979642ff3ad64f7fe6fb38726cd181bb.promisor
.git/ORIG_HEAD
.git/packed-refs
.git/refs/heads/main
.gitignore
app/api/events/route.ts
app/api/friends/route.ts
app/api/games/route.ts
app/api/health/route.ts
app/api/history/route.ts
app/api/leaderboard/route.ts
app/api/profile/route.ts
app/api/progression/route.ts
app/globals.css
app/layout.tsx
app/manifest.ts
app/page.tsx
app/play/[id]/page.tsx
app/replay/[id]/page.tsx
capacitor.config.ts
components/GameApp.tsx
components/GdsRoot.tsx
components/PhaserGameRoot.tsx
components/ReplayViewer.tsx
components/RulesHelpDialog.tsx
docs/ARCHITECTURE.md
docs/ios-mobile.md
docs/release/2.5.0.md
docs/release/2.6.0.md
docs/release/2.7.0.md
eslint.config.mjs
ios/.gitignore
ios/App/App.xcodeproj/project.pbxproj
ios/App/App/AppDelegate.swift
ios/App/App/Info.plist
ios/App/CapApp-SPM/.gitignore
ios/App/CapApp-SPM/Package.swift
ios/App/CapApp-SPM/README.md
ios/debug.xcconfig
ios/exportOptions.plist
lib/client/api.ts
lib/client/iosRuntime.ts
lib/client/telemetry.ts
lib/game/ai.ts
lib/game/daily.ts
lib/game/lobby.ts
lib/game/progression.ts
lib/game/replay.ts
lib/game/rules-help.ts
lib/game/rules.ts
lib/game/seasons.ts
lib/game/social.ts
lib/game/tutorial.ts
lib/phaser/actors/BlobActor.ts
lib/phaser/actors/BoardActor.ts
lib/phaser/actors/TileActor.ts
lib/phaser/boot.ts
lib/phaser/bootPayload.ts
lib/phaser/geometry/BoardGeometry.ts
lib/phaser/MatimatoScene.ts
lib/phaser/network/NetworkBridge.ts
lib/phaser/state/ActionMachine.ts
lib/phaser/types.ts
lib/server/http.ts
lib/server/mongo.ts
lib/server/store.ts
lib/server/telemetry.ts
lib/shared/telemetry.ts
lib/shared/types.ts
next-env.d.ts
next.config.ts
package-lock.json
package.json
public/icon.svg
public/icons/apple-touch-icon.png
public/icons/icon-192.png
public/icons/icon-512.png
public/icons/maskable-512.png
public/sw.js
README.md
scripts/generate-ios-assets.mjs
scripts/ios-testflight-preflight.mjs
scripts/ios-testflight-upload.mjs
scripts/mobile-smoke.mjs
tests/ai.test.ts
tests/daily.test.ts
tests/ios-runtime.test.ts
tests/lobby.test.ts
tests/phaser-runtime.test.ts
tests/progression.test.ts
tests/replay.test.ts
tests/rules-help.test.ts
tests/rules.test.ts
tests/seasons.test.ts
tests/social.test.ts
tests/telemetry.test.ts
tests/tutorial.test.ts
tsconfig.json
vitest.config.ts

build/test/competition files
./docs/ARCHITECTURE.md
./docs/ios-mobile.md
./docs/release/2.5.0.md
./docs/release/2.6.0.md
./docs/release/2.7.0.md
./ios/App/CapApp-SPM/README.md
./package.json
./README.md

workflows


## Grep excerpt

===== issue body =====
## Executive Summary

Add a scheduled Arena tournament layer that lets Matimato run weekly competitive events with clear entry, deterministic scoring, leaderboard visibility, and operational controls. This builds on #37 rather than duplicating the ranks read model, turning competition from a passive leaderboard into a time-boxed reason to return.

Canonical issue structure: https://github.com/sovereignsquad/general-design-system/issues/81

## Business / Product Context

Board Game Arena demonstrates strong demand for structured competition: its 2025 recap reported almost 80k tournaments, top tournament games such as Carcassonne, Can't Stop, and Azul, and Arena games with millions of tables created. BGA also markets real-time and turn-based play, ranked games, and broad web/mobile access. Dune: Imperium Digital similarly keeps players returning with achievements, challenges, and rotating Skirmish Mode. Matimato has daily, Blitz, seasonal album, and one open ranks issue, but it lacks scheduled events that package those loops into a visible competition.

References: https://en.boardgamearena.com/news?id=1025 | https://en.boardgamearena.com/ | https://play.google.com/store/apps/details?id=com.direwolfdigital.dune | https://github.com/moldovancsaba/matimato/issues/37

## Current State

- Daily challenge exists with weekly daily leaderboard.
- Blitz exists with server-owned clocks.
- Ranks #37 is open for fair weekly/mode leaderboards and player rank lookup.
- Seasonal album exists but its tasks are individual progression goals, not joined competitions.
- No tournament collection, event registration, tournament entry screen, or tournament-specific scoring exists.

## Problem Statement

Matimato currently has modes, but no shared competitive calendar. Players can complete daily or Blitz alone, yet they cannot join a visible weekly race, see event-specific standings, or understand when an event starts/ends. That weakens retention and makes ranks less actionable.

## Goals

### Functional Goals

- Define Arena tournament definitions with mode, schedule, eligibility, scoring, and reward policy.
- Let players join an active tournament from Quests/Ranks using a GDS-only flow.
- Record eligible match completions into tournament standings idempotently.
- Show tournament status, player's rank, top rows, reset/end time, and scoring explanation.
- Support v1 tournament modes: Daily Sprint and Blitz Ladder.

### Technical Goals

- Reuse #37 rank score/tie-break where possible, with tournament-specific window ids.
- Store tournament participation and result contributions separately from profile XP.
- Prevent duplicate match contribution and rank inflation.
- Keep tournaments deterministic and fully server-authoritative.

### UX Goals

- Entry is clear: open, joined, completed, locked, ended, and rewards claimable.
- Players understand what to play next and why their score changed.
- Errors are recoverable and do not hide existing daily/Blitz entry points.

## Non-Goals

- No synchronous bracket matchmaking in v1.
- No cash prizes, paid entry, purchasable score boosts, or randomized rewards.
- No push notifications or external calendar integration.
- No replacement for #37; this depends on or reuses its read model.

## Mandatory Technical Constraints

All UI/UX/frontend work must exclusively use https://github.com/sovereignsquad/general-design-system. Accessibility is mandatory. Tournament tables, filters, join controls, and status messaging must use GDS primitives and token-driven styling only.

## Architecture

Ownership boundaries:

- `lib/shared/types.ts` owns `TournamentDefinition`, `TournamentEntry`, `TournamentStanding`, and API DTOs.
- `lib/game/tournaments.ts` owns schedule, scoring, eligibility, and deterministic active tournament selection.
- `lib/server/store.ts` owns MongoDB persistence and idempotent contribution writes.
- `app/api/tournaments/route.ts` owns list/join/standings APIs.
- Match completion path calls `recordTournamentContribution` after authoritative completion.
- Ranks/Quests screens render GDS tournament cards and standings.

Runtime flow:

```text
GET /api/tournaments?playerId
  -> returns active + upcoming tournament summaries
player joins active event
  -> POST join writes TournamentEntry if eligible
player completes daily/blitz match
  -> completeGame calls tournament evaluator
  -> evaluator records contribution if mode/window/player eligible
  -> standings read model updates or derives ranks
UI fetches standings
  -> shows player rank, top rows, scoring, and reset/end state
```

## Data Model / Contracts

```ts
type TournamentMode = 'daily-sprint' | 'blitz-ladder';
type TournamentStatus = 'upcoming' | 'active' | 'ended' | 'claimable';

type TournamentDefinition = {
  tournamentId: string;
  title: string;
  mode: TournamentMode;
  startsAt: string;
  endsAt: string;
  scoringVersion: number;
  eligibility: { minBoardSize?: 5 | 6 | 7 | 8 | 9; requiresJoin: boolean };
};

type TournamentEntry = {
  id: string; // tournamentId:playerId
  tournamentId: string;
  playerId: string;
  tag: string;
  joinedAt: string;
};

type TournamentContribution = {
  id: string; // tournamentId:matchId:playerId
  tournamentId: string;
  matchId: string;
  playerId: string;
  mode: GameMode;
  score: number;
  outcome: 'victory' | 'draw' | 'defeat';
  completedAt: string;
};

type TournamentStanding = {
  rank: number;
  tag: string;
  score: number;
  wins: number;
  matches: number;
  bestScore: number;
  playerRank?: boolean;
};
```

## API Contracts

`GET /api/tournaments?playerId=...` returns `{ active: TournamentSummary[], upcoming: TournamentSummary[], serverNow }`.

`POST /api/tournaments` with `{ type: 'join', tournamentId, playerId, tag, actionId }` returns updated summary.

`GET /api/tournaments/[id]/standings?playerId=...` returns `{ tournament, rows, playerRank, scoringVersion, serverNow }`.

Invalid tournament, inactive tournament, missing eligibility, duplicate join, and unsupported mode return stable error codes.

## Algorithm / Processing Logic

```ts
function recordTournamentContribution(snapshot, player) {
  const tournaments = activeTournamentsForMode(snapshot.mode, snapshot.completedAt);
  for (const tournament of tournaments) {
    if (tournament.eligibility.requiresJoin && !hasEntry(tournament.id, player.id)) continue;
    const contributionId = `${tournament.id}:${snapshot.id}:${player.id}`;
    insertContributionIfAbsent(contributionId, buildContribution(snapshot, player));
    upsertStanding(tournament.id, player.id, scoreContribution(snapshot, player, tournament.scoringVersion));
  }
}
```

## Mathematical / Ranking Logic

Use #37 rank scoring as the base. Tournament v1 score:

```text
contributionScore = winPoints + max(0, score) * 2 + completionBonus + speedBonus
winPoints = victory ? 100 : draw ? 35 : 0
completionBonus = 10
speedBonus = daily-sprint ? max(0, 30 - attemptsOrMinutesBucket) : 0
```

Tie-break: score desc, wins desc, bestScore desc, earliestContributionAt asc, hashedPlayerId asc. Exact constants must be documented with `scoringVersion = 1` and covered by tests.

## UX / Operator Behaviour

States: loading tournament list, no active tournaments, upcoming tournament, join available, joined, contribution pending, ranked, player outside top rows, ended, claimable reward, server unavailable, offline write blocked, and scoring info. Tournament UI must never hide normal Daily/Blitz actions if tournament APIs fail.

## Accessibility Requirements

Tournament cards and standings must be keyboard accessible and screen-reader compatible. Active state, end time, rank, score, and eligibility reason must be text-visible. Tables/lists use semantic GDS patterns. Focus returns after join confirmation. Time remaining is not color-only. Reduced motion is respected for rank changes.

## Edge Cases

Week boundary during match completion, tournament ends during request, duplicate completion retry, player joins after completing eligible match, player changes tag, inactive tournament standings, empty standings, MongoDB write succeeds but standings read fails, and rollback while tournament data exists.

## Performance Expectations

Standing reads return top 50 plus player row with indexed `tournamentId`, `score`, and `playerId`. Contribution writes are O(1) with unique ids. No leaderboard request may perform unbounded profile/history scans.

## Security / Privacy Requirements

Expose display tags and aggregate scores only. Do not expose raw player ids in UI or telemetry. Server validates tournament id, time window, mode, and eligibility. No client-supplied score or completion time is trusted.

## Observability

Emit `tournament_list_viewed`, `tournament_joined`, `tournament_join_failed`, `tournament_contribution_recorded`, `tournament_standings_viewed`, `tournament_empty`, and `tournament_error` with tournamentId, mode, status, rank bucket, durationMs, and stable error code.

## Retries / Timeouts

Join is idempotent by `tournamentId:playerId` and action id. Contribution writes are idempotent by `tournamentId:matchId:playerId`. Client fetches use timeout and retry button. If contribution write fails during match completion, completeGame remains successful and records a recoverable ops error for replay/backfill.

## Rollback / Recovery

Gate UI with `NEXT_PUBLIC_MATIMATO_TOURNAMENTS=false`. Gate server contribution and join writes with `MATIMATO_TOURNAMENTS_ENABLED=false`. Rollback hides tournament surfaces and pauses contribution writes while preserving existing standings. Provide a backfill script or documented function to replay completed match summaries for a tournament window if contribution recording was down.

## Testing Requirements

Unit tests for active tournament selection, scoring, tie-breaks, eligibility, and window boundaries. API tests for list/join/standings errors and duplicate joins. Integration tests for daily and Blitz completion contribution idempotency. Component/E2E tests for join flow, standings table, player outside top rows, empty state, and 320px mobile layout.

## Documentation Requirements

Update README flags, architecture tournament section, scoringVersion docs, telemetry allowlist, and release QA. Document operator steps to create/disable an event and backfill contributions.

## Dependencies / Execution Order

Depends on #37 for fair rank read model or must implement a compatible tournament-local standing model if #37 is not shipped first. Uses delivered Daily, Blitz, telemetry, and progression foundations. Delivery order: 360.

## Acceptance Criteria

- [ ] Active/upcoming Arena tournaments are available through server contracts.
- [ ] Players can join a tournament through GDS-only accessible UI.
- [ ] Daily and Blitz completions contribute idempotently when eligible.
- [ ] Standings show top rows, player rank, scoring, and event timing.
- [ ] No duplicate retries inflate score.
- [ ] Tests, docs, observability, rollback, and backfill behavior are complete.

## Handover

### What Changed
Tournament definitions, join/standings APIs, match contribution recording, GDS UI, telemetry, tests, and docs.

### How to Run
`npm run dev`, `npm test`, `npm run build`, `npm run verify`.

### Configuration
`NEXT_PUBLIC_MATIMATO_TOURNAMENTS=true`, `MATIMATO_TOURNAMENTS_ENABLED=true`.

### How to Verify
Join an active event, complete a Daily/Blitz match, retry completion/contribution, and confirm standing rank is stable.

### Known Limitations
V1 has no bracket matchmaking, cash prizes, or push notifications.

### Rollback Plan
Set tournament flags to `false`; existing Daily, Blitz, Ranks, and season flows continue.
===== money/competition/judge hits =====
./app/api/leaderboard/route.ts:6:    return ok({ leaderboard: await getLeaderboard() });
./app/api/replays/[id]/route.ts:13:      { headers: { 'cache-control': 'public, max-age=60, stale-while-revalidate=300' } }
./app/api/progression/route.ts:31:    source: z.enum(['daily', 'solo', 'battle', 'blitz', 'journey', 'recap', 'rank', 'social']),
./app/api/progression/route.ts:32:    metric: z.enum(['complete_match', 'win_match', 'score_threshold', 'unlock_board', 'replay_move', 'share_recap', 'view_rank', 'send_friend_gift']),
./app/api/progression/route.ts:34:    score: z.number().optional(),
./app/api/progression/route.ts:40:    rewardId: z.string().min(1).max(80)
./app/api/games/route.ts:25:  z.object({ type: z.literal('timeout'), matchId: z.string().min(1), playerId: z.string().min(1), deadlineVersion: z.number().int().min(0) }),
./app/api/games/route.ts:46:  const scores = { north: next.players.north?.score ?? 0, south: next.players.south?.score ?? 0 };
./app/api/games/route.ts:47:  const outcome = next.outcome ?? computeOutcome(next.board, next.legalTarget, scores);
./app/api/games/route.ts:82:        if (!isValidTodayDailyId(input.dailyId)) throw new Error('Daily challenge is not available.');
./app/api/games/route.ts:85:        if (completedDaily) throw new Error('Daily challenge already completed.');
./app/api/games/route.ts:120:      const timeout = applyTimeout(snapshot, side, input.deadlineVersion);
./app/api/games/route.ts:121:      const resolved = timeout.resolved ? resolveAutomatedTurns(timeout.snapshot, `timeout:${input.deadlineVersion}`) : { snapshot: timeout.snapshot, frames: [] as MoveFrame[] };
./app/globals.css:10:h1,h2,p { margin:0; } h1 { font-size:1.85rem; line-height:1; letter-spacing:0; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; } h2 { font-size:1.65rem; line-height:1.05; letter-spacing:0; margin:4px 0 8px; overflow-wrap:anywhere; }
./app/globals.css:11:.status-pill,.chip { border:1px solid rgba(255,106,42,.35); color:#ffb06f; background:rgba(255,106,42,.13); border-radius:999px; padding:6px 9px; font-size:10px; font-weight:900; letter-spacing:.08em; text-transform:uppercase; white-space:nowrap; max-width:100%; overflow:hidden; text-overflow:ellipsis; }
./app/globals.css:18:.btn { min-height:46px; border:0; color:white; background:linear-gradient(90deg,var(--mat-hot),var(--mat-pink)); border-radius:8px; font-weight:950; padding:0 14px; box-shadow:0 12px 30px rgba(255,63,147,.22); } .btn.secondary { background:rgba(255,255,255,.05); border:1px solid var(--mat-line); box-shadow:none; color:var(--mat-text); } .btn.mode { min-height:68px; font-size:16px; letter-spacing:0; }
./app/globals.css:58:.badge-tile.locked { opacity:.58; }
./app/globals.css:59:.reward-list { display:grid; gap:8px; }
./app/globals.css:60:.reward-row { display:grid; grid-template-columns:minmax(0,1fr) auto; align-items:center; gap:8px; }
./app/globals.css:80:.board-chip.locked { opacity:.5; }
./app/globals.css:84:.score-row { display:grid; grid-template-columns:1fr 1fr; gap:12px; }
./app/globals.css:85:.invite-code { border:1px dashed var(--mat-line); border-radius:8px; padding:18px; font-size:2rem; font-weight:950; text-align:center; letter-spacing:.18em; user-select:all; background:rgba(255,255,255,.04); }
./app/globals.css:91:.tutorial-tile:disabled { opacity:.34; cursor:not-allowed; }
./app/globals.css:94:.recap-shell .score-row { gap:10px; }
./app/globals.css:98:@media (max-width:430px) { .app-shell { padding:calc(8px + var(--safe-top)) 10px calc(8px + max(var(--safe-bottom),var(--browser-bottom))); gap:8px; } .top-card { min-height:56px; padding:8px 10px; } .logo { width:34px; height:34px; } h1 { font-size:1.55rem; } h2 { font-size:1.42rem; margin-bottom:6px; } .copy { font-size:14px; } .panel { padding:12px; } .nav { gap:4px; padding:6px; height:56px; min-height:56px; max-height:56px; } .nav button { height:42px; } .nav svg { width:22px; height:22px; } .coach-modal { grid-template-columns:1fr; top:58px; } .hero-tag { font-size:13px; padding:6px 10px; } .list-card,.kpi { padding:10px; } .kpi strong { font-size:21px; } .score-row { gap:8px; } }
./tests/rules.test.ts:1:import { describe, expect, it } from 'vitest';
./tests/rules.test.ts:6:  it('creates default 9x9 boards and explicit 5x5 through 9x9 boards', () => {
./tests/rules.test.ts:7:    const game = newGame('test-game', 'solo', 'p1', 'Player');
./tests/rules.test.ts:10:    const small = newGame('test-game-small', 'solo', 'p1', 'Player', { boardSize: 5 });
./tests/rules.test.ts:30:    const game = newGame('test-game-2', 'solo', 'p1', 'Player');
./tests/rules.test.ts:37:    const game = newGame('test-game-3', 'battle', 'p1', 'Player');
./tests/rules.test.ts:38:    const first = applyMove({ ...game, status: 'active', players: { ...game.players, south: { id: 'p2', tag: 'Rival', side: 'south', score: 0 } } }, 'north', 1, 3, 'a1');
./tests/rules.test.ts:53:    expect(game.clock?.deadlineVersion).toBe(0);
./tests/rules.test.ts:54:    expect(game.clock?.deadlineAt).toBe('2026-06-25T10:00:05.000Z');
./tests/rules.test.ts:60:    expect(firstTimeout.snapshot.clock?.deadlineVersion).toBe(1);
./tests/rules.test.ts:61:    expect(firstTimeout.frames[0].timeout).toMatchObject({ side: 'north', deadlineVersion: 0, count: 1 });
./tests/rules.test.ts:74:    expect(northSecond.snapshot.outcome).toEqual({ winner: 'south', reason: 'timeout-forfeit' });
./tests/social.test.ts:1:import { describe, expect, it } from 'vitest';
./tests/social.test.ts:2:import { buildGiftLedgerEntry, friendshipIdForPlayers, normalizeFriendTag, relationshipBlocksActions, utcGiftDate } from '@/lib/game/social';
./tests/telemetry.test.ts:1:import { describe, expect, it } from 'vitest';
./tests/telemetry.test.ts:76:      name: 'season_reward_claimed',
./tests/telemetry.test.ts:84:        rewardId: 'starter-cache',
./tests/telemetry.test.ts:90:    expect(event?.properties).toEqual({ seasonId: 'founders-chase-2026', rewardId: 'starter-cache', xp: 40, newlyClaimed: true });
./tests/ios-runtime.test.ts:1:import { describe, expect, it, vi } from 'vitest';
./tests/progression.test.ts:1:import { describe, expect, it } from 'vitest';
./tests/progression.test.ts:22:  it('rejects skipped boards and insufficient XP', () => {
./tests/seasons.test.ts:1:import { describe, expect, it } from 'vitest';
./tests/seasons.test.ts:6:    const first = applySeasonAction(createSeasonProgress('p1'), { playerId: 'p1', source: 'solo', metric: 'complete_match', actionId: 'match-1' }, new Date('2026-06-26T10:00:00.000Z'));
./tests/seasons.test.ts:7:    const duplicate = applySeasonAction(first, { playerId: 'p1', source: 'solo', metric: 'complete_match', actionId: 'match-1' }, new Date('2026-06-26T10:00:01.000Z'));
./tests/seasons.test.ts:12:  it('builds badge album and claimable rewards from progress', () => {
./tests/seasons.test.ts:14:    progress = applySeasonAction(progress, { playerId: 'p1', source: 'solo', metric: 'complete_match', actionId: 'match-1' }, new Date('2026-06-26T10:00:00.000Z'));
./tests/seasons.test.ts:20:    expect(claim.reward.xp).toBe(40);
./tests/tutorial.test.ts:1:import { describe, expect, it } from 'vitest';
./tests/daily.test.ts:1:import { describe, expect, it } from 'vitest';
./tests/daily.test.ts:6:describe('daily challenge contracts', () => {
./tests/daily.test.ts:29:  it('ranks weekly results by score, completion time, attempts, and stable hash', () => {
./tests/daily.test.ts:44:function result(playerId: string, score: number, attempts: number, completedAt: string): DailyResult {
./tests/daily.test.ts:47:    challengeId: '2026-06-24',
./tests/daily.test.ts:50:    score,
./tests/daily.test.ts:53:    outcome: { winner: 'north', reason: 'board-complete' }
./tests/rules-help.test.ts:1:import { describe, expect, it } from 'vitest';
./tests/rules-help.test.ts:7:    expect(RULES_HELP_TOPICS.map((topic) => topic.topicId)).toEqual(['objective', 'turns', 'legal-moves', 'scoring', 'traps', 'xp', 'boards', 'recap', 'ranks']);
./tests/replay.test.ts:1:import { describe, expect, it } from 'vitest';
./tests/replay.test.ts:12:        south: { id: 'south-raw-id', tag: 'South Tag', side: 'south' as const, score: 0 }
./tests/replay.test.ts:20:      outcome: { winner: 'north' as const, reason: 'board-complete' as const },
./tests/replay.test.ts:26:    expect(replay.players).toEqual(expect.arrayContaining([{ side: 'north', tag: 'North Tag', score: expect.any(Number) }]));
./tests/replay.test.ts:40:      outcome: { winner: 'north', reason: 'no-legal-cells' },
./tests/replay.test.ts:53:      outcome: { winner: 'draw', reason: 'board-complete' },
./tests/lobby.test.ts:1:import { describe, expect, it } from 'vitest';
./tests/ai.test.ts:1:import { describe, expect, it } from 'vitest';
./tests/phaser-runtime.test.ts:1:import { describe, expect, it, vi } from 'vitest';
./docs/ARCHITECTURE.md:10:- MongoDB owns games, profiles, history, and leaderboard data.
./docs/ARCHITECTURE.md:11:- Capacitor owns the optional iOS WKWebView wrapper and native build packaging. It does not own gameplay or visible product UI.
./docs/ARCHITECTURE.md:27:The iOS mobile strategy is PWA-first, then Capacitor for App Store packaging. The native shell is configured in `capacitor.config.ts` with bundle id `app.vercel.matimato`, app name `Matimato`, HTTPS server URL `https://matimato.vercel.app`, no webview zoom, automatic iOS content insets, and no extra plugin permissions.
./docs/ARCHITECTURE.md:32:Capacitor WKWebView or iOS Safari
./docs/ARCHITECTURE.md:38:The service worker caches only shell/static assets and never caches authoritative mutation responses. Unsafe writes are blocked while offline, and safe reads use bounded retry/timeouts. Runtime telemetry distinguishes `safari`, `standalone-pwa`, `capacitor-ios`, and desktop `browser` sessions.
./docs/ARCHITECTURE.md:40:Rollback is split by layer: Vercel rollback for web/PWA regressions, service-worker registration flag plus cache version bump for offline-shell regressions, and TestFlight build expiration or Capacitor config revert for native wrapper regressions.
./docs/ARCHITECTURE.md:63:Matimato is now a progressive board-size game for solo and Blitz. Players start on 5x5 and unlock 6x6, 7x7, 8x8, then 9x9 by spending XP. Battle and daily continue to use the safe 9x9 behavior until those modes receive explicit progression work.
./docs/ARCHITECTURE.md:75:Profile `xp` remains lifetime XP. `spendableXp` is initialized from legacy `xp` when missing and increments with match rewards. Board purchases reduce only `spendableXp`; they never reduce `xp`, leaderboard rank, or level. Stored board unlocks include a purchase ledger with board size, cost, action id, and timestamp for idempotency/recovery.
./docs/ARCHITECTURE.md:100:Seasonal events live inside the progression/profile boundary so rewards share the same XP wallet and rollback story. `GET /api/progression` returns `activeSeason`, `badgeAlbum`, and `serverNow` when events are enabled. `POST /api/progression` accepts `seasonAction` for non-match actions such as recap share and `claimSeasonReward` for idempotent claims.
./docs/ARCHITECTURE.md:102:Match completion, daily completion, Blitz completion, and Journey unlocks are recorded only after an authoritative server action succeeds. The season evaluator deduplicates by source, metric, and action id. Reward grants are deterministic and never use paid odds or random packs.
./docs/ARCHITECTURE.md:104:Rollback controls are `NEXT_PUBLIC_MATIMATO_SEASONAL_EVENTS=false` for UI and `MATIMATO_SEASONAL_EVENTS_ENABLED=false` for server evaluation. Rollback hides new progress surfaces and pauses new grants while preserving existing profile `seasonProgress` and XP data.
./docs/ARCHITECTURE.md:126:The server validates profile availability against the active board size and falls back to the rookie profile when a requested profile is unavailable. AI move selection is legal-only, deterministic under snapshot/version seed, and bounded by profile decision limits. Rollback is `NEXT_PUBLIC_MATIMATO_AI_PROFILES=false`, which leaves solo mode on the rookie/default profile.
./docs/ARCHITECTURE.md:128:## Daily challenge loop
./docs/ARCHITECTURE.md:130:Daily challenges live inside the existing game and progression boundaries. The challenge id 

