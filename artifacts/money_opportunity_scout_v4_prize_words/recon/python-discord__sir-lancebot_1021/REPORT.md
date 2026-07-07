# Prize Recon Report

## Verdict

`PARK_RISK`

## Decision

JSON:
{
  "verdict": "PARK_RISK",
  "issue": {
    "url": "https://github.com/python-discord/sir-lancebot/issues/1021",
    "title": "Esoteric Challenges!",
    "state": "OPEN",
    "labels": [
      "type: feature",
      "status: planning"
    ],
    "comment_count": 0,
    "updatedAt": "2022-02-14T22:49:51Z"
  },
  "money": true,
  "competition": true,
  "judge": true,
  "local": true,
  "mgfit": true,
  "risk": true
}

## Cheap commands

pwd=/Users/heath/Documents/mathgraph-lean-work/external/money_opportunity_scout_v4_prize_words/python-discord__sir-lancebot_1021

README head:
# Sir Lancebot

[![Discord][3]][4]
[![CI Badge][1]][2]
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Open in Gitpod](https://img.shields.io/badge/Gitpod-ready--to--code-908a85?logo=gitpod)](https://gitpod.io/#/github.com/python-discord/sir-lancebot)

![Header](sir-lancebot-logo.png)

A Discord bot built by the Python Discord community, for the Python Discord community.

You can find our community by going to https://discord.gg/python

## Motivations

We know it can be difficult to get into the whole open source thing at first. To help out, we started the HacktoberBot community project during [Hacktoberfest 2018](https://hacktoberfest.digitalocean.com) to help introduce and encourage members to participate in contributing to open source, providing a calmer and helpful environment for those who want to be part of it.

This later evolved into a bot designed as a fun and beginner-friendly learning environment for writing bot features and learning open-source.

## Getting started
Before you start, please take some time to read through our [contributing guidelines](https://pythondiscord.com/pages/guides/pydis-guides/contributing/contributing-guidelines/).

See [Sir Lancebot's Wiki](https://pythondiscord.com/pages/contributing/sir-lancebot/) for in-depth guides on getting started with the project!

[1]:https://github.com/python-discord/sir-lancebot/workflows/CI/badge.svg?branch=main
[2]:https://github.com/python-discord/sir-lancebot/actions?query=workflow%3ACI+branch%3Amain
[3]: https://raw.githubusercontent.com/python-discord/branding/main/logos/badge/badge_github.svg
[4]: https://discord.gg/python

pyproject head:
[project]
authors = [
    {name = "Python Discord", email = "info@pythondiscord.com"},
    {name = "Owl Corp", email = "ops@owlcorp.uk"},
]
license = {text = "MIT"}
requires-python = "==3.13.*"
name = "sir-lancebot"
version = "0.1.0"
description = "A Discord bot designed as a fun and beginner-friendly learning environment for writing bot features and learning open-source."
dependencies = [
    "pydis-core[all]==11.10.0",
    "arrow==1.3.0",
    "beautifulsoup4==4.12.3",
    "colorama==0.4.6; sys_platform == \"win32\"",
    "coloredlogs==15.0.1",
    "emoji==2.14.0",
    "emojis==0.7.0",
    "lxml==6.1.0",
    "pillow==12.2.0",
    "pydantic==2.13.4",
    "pydantic-settings==2.8.1",
    "pyjokes==0.8.3",
    "PyYAML==6.0.2",
    "rapidfuzz==3.12.2",
    "sentry-sdk==2.19.2",
]

[dependency-groups]
dev = [
    "pip-licenses==5.0.0",
    "pre-commit==4.0.1",
    "python-dotenv==1.2.2",
    "ruff==0.8.4",
    "taskipy==1.14.1",
]

[tool.uv]
prerelease = "allow"

[tool.taskipy.tasks]
start = "python -m bot"
lint = "pre-commit run --all-files"
precommit = "pre-commit install"

[tool.isort]
multi_line_output = 6
order_by_type = false
case_sensitive = true
combine_as_imports = true
line_length = 120
atomic = true
known_first_party = ["bot"]

[tool.ruff]
target-version = "py313"
extend-exclude = [".cache"]
output-format = "concise"
line-length = 120
unsafe-fixes = true

[tool.ruff.lint]
select = ["ANN", "B", "C4", "D", "DTZ", "E", "F", "I", "ISC", "INT", "N", "PGH", "PIE", "Q", "RET", "RSE", "RUF", "S", "SIM", "T20", "TID", "UP", "W"]
ignore = [
    "ANN002", "ANN003", "ANN204", "ANN206", "ANN401",
    "B904",
    "C401", "C408",
    "D100", "D104", "D105", "D107", "D203", "D212", "D214", "D215", "D301",
    "D400", "D401", "D402", "D404", "D405", "D406", "D407", "D408", "D409", "D410", "D411", "D412", "D413", "D414", "D416", "D417",
    "E226", "E731",
    "RET504",
    "RUF005",
    "RUF029",
    "S311",
    "SIM102", "SIM108",
]

[tool.ruff.lint.isort]
known-first-party = ["bot"]
order-by-type = false
case-sensitive = true
combine-as-imports = true


## Issue body

## Description
Code-golf competition! 


## Proposed Implementation

1. The bot stores a queue of challenges. Staff members should be able to add new questions to the queue with a command (say, `.cg add`). Questions should be uploaded as a .json file, containing the problem description, visible test cases and hidden test cases.
2. The bot should maintain per-day leaderboards, as well as an overall one in a configured channel (top 25 entries). 
    - Per-day leaderboards should display the username and the entry length.
    - We could adopt the Advent of Code style for the overall leaderboard - people get points between 25 to 1 for their rank on the leaderboard on the day. The overall score is the sum of the points obtained on each day.
3. People should be able to assign themselves a `@Code Golf Participant` role with a `.cg join` command.
4. The bot should post a new challenge everyday at a configured time, pinging this role. The message should contain the problem description and visible test cases, a blank leaderboard for the day, and the best solution of the previous day's question.
5. People submit their solutions via Forms, trying to shorten their code as much as possible. 
6. Tests are run on the code using snekbox with the visible and hidden test cases, and the results are shown right after submission.
7. If all tests pass, the bot receives the user's name and the length of their code. If the code is short enough to make it to the top 25, the leaderboard for the day is edited. In case the same user already had an entry on the leaderboard, remove the previous entry. Ties are broken by time of submission.
8. At the end of the event, top 3 on the overall leaderboard get a vanity `@Code Golf Winner` role.


## Would you like to implement this yourself?
- [x] I'd like to implement this feature myself
- [ ] Anyone can implement this feature


## Comments



## Inventory excerpt

top files
.dockerignore
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
.git/objects/pack/pack-2eb8a75842270fa09ca78ef551b46ad944a0beaf.idx
.git/objects/pack/pack-2eb8a75842270fa09ca78ef551b46ad944a0beaf.pack
.git/objects/pack/pack-2eb8a75842270fa09ca78ef551b46ad944a0beaf.promisor
.git/objects/pack/pack-5d3a48ab1d22034c565ec6e1c9e944b43311691d.idx
.git/objects/pack/pack-5d3a48ab1d22034c565ec6e1c9e944b43311691d.pack
.git/objects/pack/pack-5d3a48ab1d22034c565ec6e1c9e944b43311691d.promisor
.git/ORIG_HEAD
.git/packed-refs
.git/refs/heads/main
.gitattributes
.github/CODEOWNERS
.github/dependabot.yml
.github/FUNDING.yml
.github/ISSUE_TEMPLATE/bug-report.md
.github/ISSUE_TEMPLATE/config.yml
.github/ISSUE_TEMPLATE/feature.md
.github/pull_request_template.md
.github/review-policy.yml
.github/workflows/build-deploy.yaml
.github/workflows/lint.yaml
.github/workflows/main.yaml
.github/workflows/sentry_release.yaml
.github/workflows/status_embed.yaml
.gitignore
.gitpod.yml
.pre-commit-config.yaml
bot/__init__.py
bot/__main__.py
bot/bot.py
bot/constants.py
bot/exts/__init__.py
bot/exts/avatar_modification/__init__.py
bot/exts/avatar_modification/_effects.py
bot/exts/avatar_modification/avatar_modify.py
bot/exts/core/__init__.py
bot/exts/core/error_handler.py
bot/exts/core/extensions.py
bot/exts/core/help.py
bot/exts/core/ping.py
bot/exts/core/source.py
bot/exts/events/__init__.py
bot/exts/fun/__init__.py
bot/exts/fun/anagram.py
bot/exts/fun/battleship.py
bot/exts/fun/catify.py
bot/exts/fun/coinflip.py
bot/exts/fun/connect_four.py
bot/exts/fun/duck_game.py
bot/exts/fun/fun.py
bot/exts/fun/game.py
bot/exts/fun/hangman.py
bot/exts/fun/latex.py
bot/exts/fun/madlibs.py
bot/exts/fun/magic_8ball.py
bot/exts/fun/minesweeper.py
bot/exts/fun/movie.py
bot/exts/fun/quack.py
bot/exts/fun/recommend_game.py
bot/exts/fun/rps.py
bot/exts/fun/space.py
bot/exts/fun/speedrun.py
bot/exts/fun/status_codes.py
bot/exts/fun/tic_tac_toe.py
bot/exts/fun/trivia_quiz.py
bot/exts/fun/uwu.py
bot/exts/fun/wonder_twins.py
bot/exts/fun/xkcd.py
bot/exts/holidays/__init__.py
bot/exts/holidays/holidayreact.py
bot/exts/utilities/__init__.py
bot/exts/utilities/bookmark.py
bot/exts/utilities/challenges.py
bot/exts/utilities/cheatsheet.py
bot/exts/utilities/colour.py
bot/exts/utilities/conversationstarters.py
bot/exts/utilities/emoji.py
bot/exts/utilities/epoch.py
bot/exts/utilities/githubinfo.py
bot/exts/utilities/logging.py
bot/exts/utilities/pythonfacts.py
bot/exts/utilities/realpython.py
bot/exts/utilities/reddit.py
bot/exts/utilities/rfc.py
bot/exts/utilities/stackoverflow.py
bot/exts/utilities/timed.py
bot/exts/utilities/twemoji.py
bot/exts/utilities/wikipedia.py
bot/exts/utilities/wolfram.py
bot/exts/utilities/wtf_python.py
bot/log.py
bot/resources/fun/all_cards.png
bot/resources/fun/anagram.json
bot/resources/fun/caesar_info.json
bot/resources/fun/ducks_help_ex.png
bot/resources/fun/hangman_words.txt
bot/resources/fun/html_colours.json
bot/resources/fun/latex_template.txt
bot/resources/fun/LuckiestGuy-Regular.ttf
bot/resources/fun/madlibs_templates.json
bot/resources/fun/magic8ball.json
bot/resources/fun/speedrun_links.json
bot/resources/fun/trivia_quiz.json
bot/resources/fun/wonder_twins.yaml
bot/resources/fun/xkcd_colours.json
bot/resources/utilities/py_topics.yaml
bot/resources/utilities/python_facts.txt
bot/resources/utilities/ryanzec_colours.json
bot/resources/utilities/starter.yaml
bot/resources/utilities/stored_repos.json
bot/resources/utilities/wtf_python_logo.jpg
bot/utils/__init__.py
bot/utils/checks.py
bot/utils/commands.py
bot/utils/converters.py
bot/utils/decorators.py
bot/utils/exceptions.py
bot/utils/halloween/__init__.py
bot/utils/halloween/spookifications.py
bot/utils/helpers.py
bot/utils/messages.py
bot/utils/pagination.py
bot/utils/quote.py
bot/utils/randomization.py
bot/utils/time.py
CODE_OF_CONDUCT.md
CONTRIBUTING.md
docker-compose.yml
Dockerfile
LICENSE
pyproject.toml
README.md
SECURITY.md
sir-lancebot-logo.png
uv.lock

build/test/competition files
./.github/ISSUE_TEMPLATE/bug-report.md
./.github/ISSUE_TEMPLATE/feature.md
./.github/pull_request_template.md
./CODE_OF_CONDUCT.md
./CONTRIBUTING.md
./Dockerfile
./pyproject.toml
./README.md
./SECURITY.md

workflows
.github/workflows/build-deploy.yaml
.github/workflows/lint.yaml
.github/workflows/main.yaml
.github/workflows/sentry_release.yaml
.github/workflows/status_embed.yaml


## Grep excerpt

===== issue body =====
## Description
Code-golf competition! 


## Proposed Implementation

1. The bot stores a queue of challenges. Staff members should be able to add new questions to the queue with a command (say, `.cg add`). Questions should be uploaded as a .json file, containing the problem description, visible test cases and hidden test cases.
2. The bot should maintain per-day leaderboards, as well as an overall one in a configured channel (top 25 entries). 
    - Per-day leaderboards should display the username and the entry length.
    - We could adopt the Advent of Code style for the overall leaderboard - people get points between 25 to 1 for their rank on the leaderboard on the day. The overall score is the sum of the points obtained on each day.
3. People should be able to assign themselves a `@Code Golf Participant` role with a `.cg join` command.
4. The bot should post a new challenge everyday at a configured time, pinging this role. The message should contain the problem description and visible test cases, a blank leaderboard for the day, and the best solution of the previous day's question.
5. People submit their solutions via Forms, trying to shorten their code as much as possible. 
6. Tests are run on the code using snekbox with the visible and hidden test cases, and the results are shown right after submission.
7. If all tests pass, the bot receives the user's name and the length of their code. If the code is short enough to make it to the top 25, the leaderboard for the day is edited. In case the same user already had an entry on the leaderboard, remove the previous entry. Ties are broken by time of submission.
8. At the end of the event, top 3 on the overall leaderboard get a vanity `@Code Golf Winner` role.


## Would you like to implement this yourself?
- [x] I'd like to implement this feature myself
- [ ] Anyone can implement this feature

===== money/competition/judge hits =====
./LICENSE:6:of this software and associated documentation files (the "Software"), to deal
./uv.lock:12:dependencies = [
./uv.lock:33:dependencies = [
./uv.lock:67:dependencies = [
./uv.lock:88:dependencies = [
./uv.lock:101:dependencies = [
./uv.lock:162:dependencies = [
./uv.lock:183:dependencies = [
./uv.lock:224:dependencies = [
./uv.lock:265:dependencies = [
./uv.lock:305:dependencies = [
./uv.lock:314:[package.optional-dependencies]
./uv.lock:373:dependencies = [
./uv.lock:544:dependencies = [
./uv.lock:566:dependencies = [
./uv.lock:582:dependencies = [
./uv.lock:648:dependencies = [
./uv.lock:681:dependencies = [
./uv.lock:696:dependencies = [
./uv.lock:722:dependencies = [
./uv.lock:735:dependencies = [
./uv.lock:747:[package.optional-dependencies]
./uv.lock:776:dependencies = [
./uv.lock:871:dependencies = [
./uv.lock:884:dependencies = [
./uv.lock:902:[package.dev-dependencies]
./uv.lock:913:    { name = "arrow", specifier = "==1.3.0" },
./uv.lock:914:    { name = "beautifulsoup4", specifier = "==4.12.3" },
./uv.lock:915:    { name = "colorama", marker = "sys_platform == 'win32'", specifier = "==0.4.6" },
./uv.lock:916:    { name = "coloredlogs", specifier = "==15.0.1" },
./uv.lock:917:    { name = "emoji", specifier = "==2.14.0" },
./uv.lock:918:    { name = "emojis", specifier = "==0.7.0" },
./uv.lock:919:    { name = "lxml", specifier = "==6.1.0" },
./uv.lock:920:    { name = "pillow", specifier = "==12.2.0" },
./uv.lock:921:    { name = "pydantic", specifier = "==2.13.4" },
./uv.lock:922:    { name = "pydantic-settings", specifier = "==2.8.1" },
./uv.lock:923:    { name = "pydis-core", extras = ["all"], specifier = "==11.10.0" },
./uv.lock:924:    { name = "pyjokes", specifier = "==0.8.3" },
./uv.lock:925:    { name = "pyyaml", specifier = "==6.0.2" },
./uv.lock:926:    { name = "rapidfuzz", specifier = "==3.12.2" },
./uv.lock:927:    { name = "sentry-sdk", specifier = "==2.19.2" },
./uv.lock:932:    { name = "pip-licenses", specifier = "==5.0.0" },
./uv.lock:933:    { name = "pre-commit", specifier = "==4.0.1" },
./uv.lock:934:    { name = "python-dotenv", specifier = "==1.2.2" },
./uv.lock:935:    { name = "ruff", specifier = "==0.8.4" },
./uv.lock:936:    { name = "taskipy", specifier = "==1.14.1" },
./uv.lock:979:dependencies = [
./uv.lock:1029:dependencies = [
./uv.lock:1050:dependencies = [
./uv.lock:1073:dependencies = [
./Dockerfile:9:# Install project dependencies with build tools available
./Dockerfile:25:# Install dependencies from build cache
./pyproject.toml:11:dependencies = [
./pyproject.toml:58:output-format = "concise"
./README.md:16:We know it can be difficult to get into the whole open source thing at first. To help out, we started the HacktoberBot community project during [Hacktoberfest 2018](https://hacktoberfest.digitalocean.com) to help introduce and encourage members to participate in contributing to open source, providing a calmer and helpful environment for those who want to be part of it.
./README.md:25:[1]:https://github.com/python-discord/sir-lancebot/workflows/CI/badge.svg?branch=main
./README.md:26:[2]:https://github.com/python-discord/sir-lancebot/actions?query=workflow%3ACI+branch%3Amain
./.gitignore:1:# bot (project-specific)
./.gitignore:45:# Unit test / coverage reports
./.gitignore:51:nosetests.xml
./.gitignore:55:.pytest_cache/
./.github/workflows/status_embed.yaml:4:  workflow_run:
./.github/workflows/status_embed.yaml:5:    workflows:
./.github/workflows/status_embed.yaml:11:  group: ${{ github.workflow }}-${{ github.ref }}
./.github/workflows/status_embed.yaml:17:    runs-on: ubuntu-latest
./.github/workflows/status_embed.yaml:20:      # A workflow_run event does not contain all the information
./.github/workflows/status_embed.yaml:22:      # with that information in the Lint workflow.
./.github/workflows/status_embed.yaml:25:        if: github.event.workflow_run.event == 'pull_request'
./.github/workflows/status_embed.yaml:27:          curl -s -H "Authorization: token $GITHUB_TOKEN" ${{ github.event.workflow_run.artifacts_url }} > artifacts.json
./.github/workflows/status_embed.yaml:51:          # We need to provide the information of the workflow that
./.github/workflows/status_embed.yaml:52:          # triggered this workflow instead of this workflow.
./.github/workflows/status_embed.yaml:53:          workflow_name: ${{ github.event.workflow_run.name }}
./.github/workflows/status_embed.yaml:54:          run_id: ${{ github.event.workflow_run.id }}
./.github/workflows/status_embed.yaml:55:          run_number: ${{ github.event.workflow_run.run_number }}
./.github/workflows/status_embed.yaml:56:          status: ${{ github.event.workflow_run.conclusion }}
./.github/workflows/status_embed.yaml:57:          sha: ${{ github.event.workflow_run.head_sha }}
./.github/workflows/main.yaml:9:  group: ${{ github.workflow }}-${{ github.ref }}
./.github/workflows/main.yaml:15:    uses: ./.github/workflows/lint.yaml
./.github/workflows/main.yaml:19:    runs-on: ubuntu-latest
./.github/workflows/main.yaml:31:    uses: ./.github/workflows/build-deploy.yaml
./.github/workflows/main.yaml:41:    uses: ./.github/workflows/sentry_release.yaml
./.github/workflows/sentry_release.yaml:3:on: workflow_call
./.github/workflows/sentry_release.yaml:7:    runs-on: ubuntu-latest
./.github/workflows/lint.yaml:3:on: workflow_call
./.github/workflows/lint.yaml:7:    name: Run linting & tests
./.github/workflows/lint.yaml:8:    runs-on: ubuntu-latest
./.github/workflows/lint.yaml:21:      - name: Install dependencies
./.github/workflows/build-deploy.yaml:4:  workflow_call:
./.github/workflows/build-deploy.yaml:14:    runs-on: ubuntu-latest
./.github/workflows/build-deploy.yaml:33:      # Repository. The container will be tagged as "latest"
./.github/workflows/build-deploy.yaml:41:          cache-from: type=registry,ref=ghcr.io/python-discord/sir-lancebot:latest
./.github/workflows/build-deploy.yaml:44:            ghcr.io/python-discord/sir-lancebot:latest
./.github/workflows/build-deploy.yaml:52:    runs-on: ubuntu-latest
./.github/pull_request_template.md:4:Issues can be skipped with explicit core dev approval, but you have to link the discussion.
./.github/review-policy.yml:2:path: review-policies/core-developers.yml
./bot/exts/core/extensions.py:40:        # Special values to reload all extensions
./bot/exts/core/help.py:2:import asyncio
./bot/exts/core/help.py:74:    as a class attribute named `category`. A description can also be specified with the attribute
./bot/exts/core/help.py:173:        await asyncio.sleep(seconds)
./bot/exts/core/source.py:39:        Raise BadArgument if `source_item` is a dynamically-created object (e.g. via internal eval).
./bot/exts/core/internal_eval/__init__.py:8:    from ._internal_eval import InternalEval
./bot/exts/core/internal_eval/_internal_eval.py:40:    """Top secret code evaluation for admins and owners."""
./bot/exts/core/internal_eval/_internal_eval.py:88:        """Upload `internal eval` output to our pastebin and return the url."""
./bot/exts/core/internal_eval/_internal_eval.py:98:            log.exception("Failed to upload `internal eval` output to paste service!")
./bot/exts/core/internal_eval/_internal_eval.py:102:        """Send the `internal eval` output to the command invocation context."""
./bot/exts/core/internal_eval/_internal_eval.py:118:    async def _eval(self, ctx: commands.Context, code: str) -> None:
./bot/exts/core/internal_eval/_internal_eval.py:119:        """Evaluate the `code` in the current evaluation context."""
./bot/exts/core/internal_eval/_internal_eval.py:131:        eval_context = EvalContext(context_vars, self.locals)
./bot/exts/core/internal_eval/_internal_eval.py:133:        log.trace("Preparing the evaluation by parsing the AST of the code")
./bot/exts/core/internal_eval/_internal_eval.py:134:        error = eval_context.prepare_eval(code)
./bot/exts/core/internal_eval/_internal_eval.py:137:            log.trace("The code can't be evaluated due to an error")
./bot/exts/core/internal_eval/_internal_eval.py:141:        log.trace("Evaluate the AST we've generated for the evaluation")
./bot/exts/core/internal_eval/_internal_eval.py:142:        new_locals = await eval_context.run_eval()
./bot/exts/core/internal_eval/_internal_eval.py:144:        log.trace("Updating locals with those set during evaluation")
./bot/exts/core/internal_eval/_internal_eval.py:148:        await self._send_output(ctx, eval_context.format_output())
./bot/exts/core/internal_eval/_internal_eval.py:157:    @internal_group.command(name="eval", aliases=("e",))
./bot/exts/core/internal_eval/_internal_eval.py:159:    async def eval(self, ctx: commands.Context, *, code: str) -> None:
./bot/exts/core/internal_eval/_internal_eval.py:160:        """Run eval in a REPL-like format."""
./bot/exts/core/internal_eval/_internal_eval.py:174:        await self._eval(ctx, code)
./bot/exts/core/internal_eval/_internal_eval.py:179:        """Reset the context and locals of the eval session."""
./bot/exts/core/internal_eval/_internal_eval.py:181:        await ctx.send("The evaluation context was reset.")
./bot/exts/core/internal_eval/_helpers.py:21:# to be evaluated. The wrapper contains one `pass` statement which
./bot/exts/core/internal_eval/_helpers.py:23:# evaluated.
./bot/exts/core/internal_eval/_helpers.py:25:# raised in the code we evaluate. The latter is used to provide a
./bot/exts/core/internal_eval/_helpers.py:28:async def _eval_wrapper_function():
./bot/exts/core/internal_eval/_helpers.py:30:        with contextlib.redirect_stdout(_eval_context.stdout):
./bot/exts/core/internal_eval/_helpers.py:35:            _eval_context._value_last_expression = _value_last_expression
./bot/exts/core/internal_eval/_helpers.py:37:            _eval_context._value_last_expression = None
./bot/exts/core/internal_eval/_helpers.py:39:        _eval_context.exc_info = sys.exc_info()
./bot/exts/core/internal_eval/_helpers.py:41:        _eval_context.locals = locals()
./bot/exts/core/internal_eval/_helpers.py:42:_eval_context.function = _eval_wrapper_function
./bot/exts/core/internal_eval/_helpers.py:44:INTERNAL_EVAL_FRAMENAME = "<internal eval>"
./bot/exts/core/internal_eval/_helpers.py:45:EVAL_WRAPPER_FUNCTION_FRAMENAME = "_eval_wrapper_function"
./bot/exts/core/internal_eval/_helpers.py:48:def format_internal_eval_exception(exc_info: ExcInfo, code: str) -> str:
./bot/exts/core/internal_eval/_helpers.py:49:    """Format an exception caught while evaluation code by inserting lines."""
./bot/exts/core/internal_eval/_helpers.py:78:    Represents the current `internal eval` context.
./bot/exts/core/internal_eval/_helpers.py:80:    The context remembers names set during earlier runs of `internal eval`. To
./bot/exts/core/internal_eval/_helpers.py:93:        self.eval_tree = None
./bot/exts/core/internal_eval/_helpers.py:96:    def dependencies(self) -> dict[str, Any]:
./bot/exts/core/internal_eval/_helpers.py:98:        Return a mapping of the dependencies for the wrapper function.
./bot/exts/core/internal_eval/_helpers.py:100:        By using a property descriptor, the mapping can't be accidentally
./bot/exts/core/internal_eval/_helpers.py:101:        mutated during evaluation. This ensures the dependencies are always
./bot/exts/core/internal_eval/_helpers.py:109:            "_eval_context": self,
./bot/exts/core/internal_eval/_helpers.py:115:        """Return a mapping of names->values needed for evaluation."""
./bot/exts/core/internal_eval/_helpers.py:116:        return {**collections.ChainMap(self.dependencies, self.context_vars, self._locals)}
./bot/exts/core/internal_eval/_helpers.py:124:    def prepare_eval(self, code: str) -> str | None:
./bot/exts/core/internal_eval/_helpers.py:125:        """Prepare an evaluation by processing the code and setting up the context."""
./bot/exts/core/internal_eval/_helpers.py:129:            log.debug("No code was attached to the evaluation command")
./bot/exts/core/internal_eval/_helpers.py:135:            log.debug("Got a SyntaxError while parsing the eval code")
./bot/exts/core/internal_eval/_helpers.py:142:        eval_tree = WrapEvalCodeTree(code_tree).wrap()
./bot/exts/core/internal_eval/_helpers.py:144:        self.eval_tree = eval_tree
./bot/exts/core/internal_eval/_helpers.py:147:    async def run_eval(self) -> Namespace:
./bot/exts/core/internal_eval/_helpers.py:148:        """Run the evaluation and return the updated locals."""
./bot/exts/core/internal_eval/_helpers.py:150:        compiled_code = compile(self.eval_tree, filename=INTERNAL_EVAL_FRAMENAME, mode="exec")
./bot/exts/core/internal_eval/_helpers.py:155:        log.trace("Awaiting the created evaluation wrapper coroutine.")
./bot/exts/core/internal_eval/_helpers.py:162:        """Format the output of the most recent evaluation."""
./bot/exts/core/internal_eval/_helpers.py:177:            output.append(format_internal_eval_exception(self.exc_info, self.code))
./bot/exts/core/internal_eval/_helpers.py:184:    """Wraps the AST of eval code with the wrapper function."""
./bot/exts/core/internal_eval/_helpers.py:186:    def __init__(self, eval_code_tree: ast.AST, *args, **kwargs):
./bot/exts/core/internal_eval/_helpers.py:188:        self.eval_code_tree = eval_code_tree
./bot/exts/core/internal_eval/_helpers.py:200:        Replace the `_ast.Pass` node in the wrapper function by the eval AST.
./bot/exts/core/internal_eval/_helpers.py:205:        return list(ast.iter_child_nodes(self.eval_code_tree))
./bot/exts/core/internal_eval/_helpers.py:228:        log.trace("Found a trailing last expression in the evaluation code")
./bot/exts/holidays/easter/egghead_quiz.py:1:import asyncio
./bot/exts/holidays/easter/egghead_quiz.py:61:        await asyncio.sleep(TIMELIMIT)
./bot/exts/holidays/easter/egghead_quiz.py:135:        """Listener to listen specifically for reactions of quiz messages."""
./bot/exts/holidays/easter/easter_riddle.py:61:        winner = None
./bot/exts/holidays/easter/easter_riddle.py:71:                winner = response.author.mention
./bot/exts/holidays/easter/easter_riddle.py:85:        if winner:
./bot/exts/holidays/easter/easter_riddle.py:86:            content = f"Well done {winner} for getting it right!"
./bot/exts/holidays/easter/egg_decorating.py:88:            replacing_colours = {colour: colours[i] for i, colour in enumerate(replaceable)}
./bot/exts/holidays/easter/egg_decorating.py:91:                if x in replacing_colours:
./bot/exts/holidays/easter/egg_decorating.py:92:                    new_data.append((*replacing_colours[x].to_rgb(), 255))
./bot/exts/holidays/halloween/spookynamerate.py:1:import asyncio
./bot/exts/holidays/halloween/spookynamerate.py:48:                "At the end of the day, the author of the message with most reactions will be the winner of the day.\n"
./bot/exts/holidays/halloween/spookynamerate.py:82:    # added, the author's id, and the author's score (which is 0 by default)
./bot/exts/holidays/halloween/spookynamerate.py:90:    # will automatically start the scoring and announcing the result (without waiting for 12, so do not expect it to.).
./bot/exts/holidays/halloween/spookynamerate.py:100:        self.checking_messages = asyncio.Lock()
./bot/exts/holidays/halloween/spookynamerate.py:101:        # Define an asyncio.Lock() to make sure the dictionary isn't changed
./bot/exts/holidays/halloween/spookynamerate.py:136:            await ctx.send("Sorry, the poll has started! You can try and participate in the next round though!")
./bot/exts/holidays/halloween/spookynamerate.py:160:                    "score": 0,
./bot/exts/holidays/halloween/spookynamerate.py:214:        """Announces the name needed to spookify every 24 hours and the winner of the previous game."""
./bot/exts/holidays/halloween/spookynamerate.py:236:                    await asyncio.sleep(2 * 60 * 60)  # sleep for two hours
./bot/exts/holidays/halloween/spookynamerate.py:238:            logger.info("Calculating score")
./bot/exts/holidays/halloween/spookynamerate.py:243:                score = 0
./bot/exts/holidays/halloween/spookynamerate.py:246:                    score += reaction_value * (reaction.count - 1)  # multiply by the num of reactions
./bot/exts/holidays/halloween/spookynamerate.py:249:                logger.debug(f"{self.bot.get_user(data['author'])} got a score of {score}")
./bot/exts/holidays/halloween/spookynamerate.py:250:                data["score"] = score
./bot/exts/holidays/halloween/spookynamerate.py:253:            # Sort the winner messages
./bot/exts/holidays/halloween/spookynamerate.py:254:            winner_messages = sorted(
./bot/exts/holidays/halloween/spookynamerate.py:256:                key=lambda x: x[1]["score"],
./bot/exts/holidays/halloween/spookynamerate.py:260:            winners = []
./bot/exts/holidays/halloween/spookynamerate.py:261:            for i, winner in enumerate(winner_messages):
./bot/exts/holidays/halloween/spookynamerate.py:262:                winners.append(winner)
./bot/exts/holidays/halloween/spookynamerate.py:263:                if len(winner_messages) > i + 1 and winner_messages[i + 1][1]["score"] != winner[1]["score"]:
./bot/exts/holidays/halloween/spookynamerate.py:267:            await channel.send("Today's Spooky Name Rate Game ends now, and the winner(s) is(are)...")
./bot/exts/holidays/halloween/spookynamerate.py:270:                await asyncio.sleep(1)  # give the drum roll feel
./bot/exts/holidays/halloween/spookynamerate.py:272:                if not winners:  # There are no winners (no participants)
./bot/exts/holidays/halloween/spookynamerate.py:273:                    await channel.send("Hmm... Looks like no one participated! :cry:")
./bot/exts/holidays/halloween/spookynamerate.py:276:                score = winners[0][1]["score"]
./bot/exts/holidays/halloween/spookynamerate.py:277:                congratulations = "to all" if len(winners) > 1 else PING.format(id=winners[0][1]["author"])
./bot/exts/holidays/halloween/spookynamerate.py:278:                names = ", ".join(f'{win[1]["name"]} ({PING.format(id=win[1]["author"])})' for win in winners)
./bot/exts/holidays/halloween/spookynamerate.py:280:                # display winners, their names and scores
./bot/exts/holidays/halloween/spookynamerate.py:283:                    f"You have a score of {score}!\n"
./bot/exts/holidays/halloween/spookynamerate.py:284:                    f"Your name{ 's were' if len(winners) > 1 else 'was'}:\n{names}"
./bot/exts/holidays/halloween/spookynamerate.py:315:            await asyncio.sleep(time_left.seconds)
./bot/exts/holidays/halloween/spookynamerate.py:320:        await asyncio.sleep((tomorrow_12pm - now).seconds)
./bot/exts/holidays/halloween/spookyrating.py:51:            description=f"{who} scored {spooky_percent}%!",
./bot/exts/holidays/halloween/monsterbio.py:23:        """Generates a name (for either monster species or monster name)."""
./bot/exts/holidays/halloween/monsterbio.py:33:        species = self.generate_name(seeded_random)
./bot/exts/holidays/halloween/monsterbio.py:35:        words = {"monster_name": name, "monster_species": species}
./bot/exts/holidays/halloween/monstersurvey.py:38:        Cast a user's vote for the specified monster.
./bot/exts/holidays/halloween/monstersurvey.py:50:    def get_name_by_leaderboard_index(self, n: int) -> str:
./bot/exts/holidays/halloween/monstersurvey.py:51:        """Return the monster at the specified leaderboard index."""
./bot/exts/holidays/halloween/monstersurvey.py:73:                    value="Show a specific monster. If none is listed, it will give you an error with valid choices.",
./bot/exts/holidays/halloween/monstersurvey.py:78:                    value="Vote for a specific monster. You get one vote, but can change it at any time.",
./bot/exts/holidays/halloween/monstersurvey.py:82:                    name=".monster leaderboard",
./bot/exts/holidays/halloween/monstersurvey.py:97:        Displays a list of monsters that can be voted for if one is not specified.
./bot/exts/holidays/halloween/monstersurvey.py:100:            await ctx.invoke(self.monster_leaderboard)
./bot/exts/holidays/halloween/monstersurvey.py:104:            # Check to see if user used a numeric (leaderboard) index to vote
./bot/exts/holidays/halloween/monstersurvey.py:107:                name = self.get_name_by_leaderboard_index(idx)
./bot/exts/holidays/halloween/monstersurvey.py:120:                    name="Use `.monster show {monster_name}` for more information on a specific monster",
./bot/exts/holidays/halloween/monstersurvey.py:147:            await ctx.invoke(self.monster_leaderboard)
./bot/exts/holidays/halloween/monstersurvey.py:151:            # Check to see if user used a numeric (leaderboard) index to vote
./bot/exts/holidays/halloween/monstersurvey.py:154:                name = self.get_name_by_leaderboard_index(idx)
./bot/exts/holidays/halloween/monstersurvey.py:172:        name="leaderboard",
./bot/exts/holidays/halloween/monstersurvey.py:175:    async def monster_leaderboard(self, ctx: Context) -> None:
./bot/exts/holidays/halloween/candy_collection.py:170:        """Get the candy leaderboard and save to JSON."""
./bot/exts/holidays/halloween/candy_collection.py:173:        def generate_leaderboard() -> str:
./bot/exts/holidays/halloween/candy_collection.py:175:                ((user_id, score) for user_id, score in records if score > 0),
./bot/exts/holidays/halloween/candy_collection.py:186:        def get_user_candy_score() -> str:
./bot/exts/holidays/halloween/candy_collection.py:187:            for user_id, score in records:
./bot/exts/holidays/halloween/candy_collection.py:189:                    return f"{ctx.author.mention}: {score}"
./bot/exts/holidays/halloween/candy_collection.py:195:            value=generate_leaderboard(),
./bot/exts/holidays/halloween/candy_collection.py:200:            value=get_user_candy_score(),
./bot/exts/holidays/halloween/eight_ball.py:1:import asyncio
./bot/exts/holidays/halloween/eight_ball.py:25:            await asyncio.sleep(rand

