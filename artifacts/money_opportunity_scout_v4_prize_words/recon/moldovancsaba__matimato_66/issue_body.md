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