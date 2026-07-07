# hledger #1825 Watch Autopsy v19

## Verdict

`REPRO_HARNESS_FIRST`

## Claim

- Claim comment: https://github.com/simonmichael/hledger/issues/1825#issuecomment-4901262602

## Signals

- claim_post_visible: `True`
- watch_refs: `137`
- fsnotify_refs: `39`
- async_refs: `284`
- reload_refs: `235`
- stack_available: `False`
- cabal_available: `False`
- ghc_available: `False`
- hledger_ui_available: `False`

## Likely files

- `hledger/hledger.1`
- `hledger/hledger.info`
- `hledger/test/README.md`
- `hledger/hledger.m4.md`
- `hledger/Hledger/Cli/Commands/Import.txt`
- `hledger/Hledger/Cli/Commands/Import.md`
- `hledger/CHANGES.md`
- `hledger/hledger.txt`
- `hledger-ui/test/uitest.md`
- `hledger-ui/Hledger/UI/Main.hs`
- `hledger-ui/Hledger/UI/UITypes.hs`
- `hledger-ui/Hledger/UI/UIOptions.hs`
- `hledger-ui/Hledger/UI/AccountsScreen.hs`
- `hledger-ui/Hledger/UI/RegisterScreen.hs`
- `hledger-ui/hledger-ui.txt`
- `hledger-ui/hledger-ui.1`
- `hledger-ui/CHANGES.md`
- `hledger-ui/hledger-ui.m4.md`
- `hledger-ui/hledger-ui.info`
- `hledger-lib/Hledger/Reports/ReportOptions.hs`
- `hledger/embeddedfiles/install.cast`
- `hledger-ui/test/UITestUtils.hs`
- `hledger-ui/Hledger/UI/UIUtils.hs`
- `hledger-ui/Hledger/UI/TransactionScreen.hs`
- `hledger-ui/Hledger/UI/ErrorScreen.hs`
- `hledger-ui/Hledger/UI/MenuScreen.hs`
- `hledger-ui/hledger-ui.cabal`
- `hledger-ui/package.yaml`
- `hledger-ui/LICENSE`
- `hledger-ui/test/UITest.hs`

## Next move

Do not patch blindly. First create a measurable reproduction. The local machine currently has only `make` visible from the Haskell toolchain scan, so either use an installed `hledger-ui` binary if present, or defer local build until stack/cabal/ghc are available.

Diagnostic harness written:

- `/Users/heath/Documents/mathgraph-lean-work/artifacts/hledger_1825_watch_autopsy_v19/hledger_watch_measure.sh`

## Patch target if reproduction confirms leak

Focus on the watch manager/event loop/reload scheduling path, not unrelated UI code.

