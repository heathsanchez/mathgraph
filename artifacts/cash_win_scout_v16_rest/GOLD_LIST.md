# Cash Win Scout v16 REST

## Verdict

- Dedup search results: `1488`
- Enriched issue views: `120`
- Promoted recon candidates: `36`

## Top promoted candidates

### 1. simonmichael/hledger#1825 — hledger-ui --watch consumes more CPU and RAM over time [$150 x 3]

- Verdict: `PROMOTE_RECON`
- Score: `95`
- Money: `$150`
- URL: https://github.com/simonmichael/hledger/issues/1825
- Reasons: money≈$150, local/test/benchmark surface, patchable wording, stack fit, available language
- Snippet: An idle hledger-ui with `--watch`, left running for days, may show gradually increasing CPU usage - 1%, 2%, 3%, 4%... - and RAM usage. I have always seen this on mac, and @the-solipsist sees it on ubuntu gnu/linux. I believe it is more apparent when you have a lot of accounts / transactions. I seem to remember, or I have assumed, that it's a problem with the underlying C file-watching library (which might be different on each platform). As a workaround, you can occasionally quit and restart hledger-ui (`q`, `C-p`, `enter`), or suspend and resume it when not in use (`C-z`, `fg`, `enter`). It's quite unfortunate. ---- See also - #836 - #1617 - https://github.com/haskell-fswatch/hfsnotify/issue

### 2. xevrion-v2/agent-playground#875 — Seed Good First Issues workflow recreates duplicate starter issues

- Verdict: `PROMOTE_RECON`
- Score: `93`
- Money: `$50`
- URL: https://github.com/xevrion-v2/agent-playground/issues/875
- Reasons: money≈$50, local/test/benchmark surface, patchable wording, stack fit, available language
- Snippet: /bounty $50 References #33. ## Problem The manual `Seed Good First Issues` workflow always calls `github.rest.issues.create` for every starter issue. If a maintainer reruns the workflow, it recreates the same seeded bounty issues instead of treating the seed as an idempotent operation. That creates duplicate issues for the same starter tasks, splits contributor attempts across copies, and can confuse bounty tracking. ## Expected behavior The seed workflow should inspect existing repository issues before creating starter issues. If an issue with the same starter title already exists, it should skip creation and continue with the remaining missing starter issues. ## Acceptance criteria - Updat

### 3. Markp1598M/cobra#1 — 🎯 Fix panic on duplicate shell completion registration for inherited persistent flags

- Verdict: `PROMOTE_RECON`
- Score: `83`
- Money: `$250`
- URL: https://github.com/Markp1598M/cobra/issues/1
- Reasons: money≈$250, local/test/benchmark surface, patchable wording, stack fit
- Snippet: ## 📝 Description When using the Cobra library, registering a shell completion function for a persistent flag can cause a panic under certain conditions. Specifically, if a persistent flag is defined on a parent command and has a completion function registered, and a subcommand inherits this persistent flag, attempting to register a completion function for the same flag on the subcommand—or generating the shell completion scripts (Bash, Zsh, Fish, PowerShell) for the command tree—results in a runtime panic. This panic typically occurs due to duplicate registration conflicts in the internal completion maps or nil pointer dereferences when traversing the command hierarchy to resolve flag comple

### 4. QuantumSavory/QuantumSavory.jl#131 — More thorough benchmarks [$200]

- Verdict: `PROMOTE_RECON`
- Score: `82`
- Money: `$200`
- URL: https://github.com/QuantumSavory/QuantumSavory.jl/issues/131
- Reasons: money≈$200, local/test/benchmark surface, patchable wording, stack fit
- Snippet: <details> <summary><strong>Bug bounty logistic details</strong> (click to expand)</summary> To claim exclusive time to work on this bounty either post a comment here or message [skrastanov@umass.edu](mailto:skrastanov@umass.edu) with: - your name - github username - **(optional)** a brief list of previous pertinent projects you have engaged in If you want to, you can work on this project without making a claim, however claims are encouraged to give you and other contributors peace of mind. Whoever has made a claim takes precedence when solutions are considered. You can always propose your own funded project, if you would like to contribute something of value that is not yet covered by an off

### 5. tinygrad/tinygrad#3039 — Bounty: Fast parallel scan (Mamba, etc). 

- Verdict: `PROMOTE_RECON`
- Score: `79`
- Money: `$500`
- URL: https://github.com/tinygrad/tinygrad/issues/3039
- Reasons: money≈$500, local/test/benchmark surface, patchable wording, stack fit, available language, claim/assigned language
- Snippet: It would be great to have a general parallel prefix sum (associative scan) operation in tinygrad, something like [associative_scan](https://jax.readthedocs.io/en/latest/_autosummary/jax.lax.associative_scan.html) in JAX or [scan_associative](https://www.tensorflow.org/probability/api_docs/python/tfp/math/scan_associative) in TensorFlow Probability. This operation is key for the parallelization of some algorithms in CRFs, [filtering/smoothing in state space models](https://github.com/EEA-sensors/sequential-parallelization-examples/blob/main/python/temporal-parallelization-bayes-smoothers/parallel_kalman_jax.ipynb), mamba etc. Additional Reference https://arxiv.org/abs/2311.06281 --- Current B

### 6. dev-kp-eloper/BountyScout#364 — 🎯 Bounty Alert: 6 New Opportunityies found

- Verdict: `PROMOTE_RECON`
- Score: `78`
- Money: `$50`
- URL: https://github.com/dev-kp-eloper/BountyScout/issues/364
- Reasons: money≈$50, local/test/benchmark surface, patchable wording, stack fit
- Snippet: ### Active Bounty Scan Results **Scan Time:** 2026-07-03 00:09 UTC #### 1. [Dataset spotlight tip: finance + worldview open benchmarks](https://github.com/huggingface/blog/issues/3446) - **Repository:** [huggingface/blog](https://github.com/huggingface/blog) - **Comments:** 0 - **Last Updated:** 2026-07-03T00:06:11Z #### 2. [[bounty] Name the threshold-crossing lexeme — the word for entering something new](https://github.com/Eaprime1/custos/issues/187) - **Repository:** [Eaprime1/custos](https://github.com/Eaprime1/custos) - **Comments:** 8 - **Last Updated:** 2026-07-03T00:04:56Z #### 3. [[TEST BOUNTY $50] Document project status](https://github.com/jessedaustin93/Open-Aeon/issues/1) - **Re

### 7. xevrion-v2/agent-playground#4934 — Add is-ideographic-space-present API utility

- Verdict: `PROMOTE_RECON`
- Score: `78`
- Money: `$50`
- URL: https://github.com/xevrion-v2/agent-playground/issues/4934
- Reasons: money≈$50, local/test/benchmark surface, patchable wording, stack fit
- Snippet: ## Scope Add a small API utility that returns whether a string contains the requested Unicode spacing character. ## Bounty /bounty $50 Parent bounty program: #33

### 8. xevrion-v2/agent-playground#4936 — Add is-figure-space-present API utility

- Verdict: `PROMOTE_RECON`
- Score: `78`
- Money: `$50`
- URL: https://github.com/xevrion-v2/agent-playground/issues/4936
- Reasons: money≈$50, local/test/benchmark surface, patchable wording, stack fit
- Snippet: ## Scope Add a small API utility that returns whether a string contains the requested Unicode spacing character. ## Bounty /bounty $50 Parent bounty program: #33

### 9. xevrion-v2/agent-playground#4938 — Add is-punctuation-space-present API utility

- Verdict: `PROMOTE_RECON`
- Score: `78`
- Money: `$50`
- URL: https://github.com/xevrion-v2/agent-playground/issues/4938
- Reasons: money≈$50, local/test/benchmark surface, patchable wording, stack fit
- Snippet: ## Scope Add a small API utility that returns whether a string contains the requested Unicode spacing character. ## Bounty /bounty $50 Parent bounty program: #33

### 10. xevrion-v2/agent-playground#4940 — Add is-medium-mathematical-space-present API utility

- Verdict: `PROMOTE_RECON`
- Score: `78`
- Money: `$50`
- URL: https://github.com/xevrion-v2/agent-playground/issues/4940
- Reasons: money≈$50, local/test/benchmark surface, patchable wording, stack fit
- Snippet: ## Scope Add a small API utility that returns whether a string contains the requested Unicode spacing character. ## Bounty /bounty $50 Parent bounty program: #33

### 11. xevrion-v2/agent-playground#4971 — Add is-line-separator-present API utility

- Verdict: `PROMOTE_RECON`
- Score: `78`
- Money: `$50`
- URL: https://github.com/xevrion-v2/agent-playground/issues/4971
- Reasons: money≈$50, local/test/benchmark surface, patchable wording, stack fit
- Snippet: ## Scope Add a small API utility that returns whether a string contains the requested Unicode separator or spacing character. ## Bounty /bounty $50 Parent bounty program: #33

### 12. xevrion-v2/agent-playground#4973 — Add is-paragraph-separator-present API utility

- Verdict: `PROMOTE_RECON`
- Score: `78`
- Money: `$50`
- URL: https://github.com/xevrion-v2/agent-playground/issues/4973
- Reasons: money≈$50, local/test/benchmark surface, patchable wording, stack fit
- Snippet: ## Scope Add a small API utility that returns whether a string contains the requested Unicode separator or spacing character. ## Bounty /bounty $50 Parent bounty program: #33

### 13. xevrion-v2/agent-playground#4975 — Add is-narrow-no-break-space-present API utility

- Verdict: `PROMOTE_RECON`
- Score: `78`
- Money: `$50`
- URL: https://github.com/xevrion-v2/agent-playground/issues/4975
- Reasons: money≈$50, local/test/benchmark surface, patchable wording, stack fit
- Snippet: ## Scope Add a small API utility that returns whether a string contains the requested Unicode separator or spacing character. ## Bounty /bounty $50 Parent bounty program: #33

### 14. xevrion-v2/agent-playground#4978 — Add is-mongolian-vowel-separator-present API utility

- Verdict: `PROMOTE_RECON`
- Score: `78`
- Money: `$50`
- URL: https://github.com/xevrion-v2/agent-playground/issues/4978
- Reasons: money≈$50, local/test/benchmark surface, patchable wording, stack fit
- Snippet: ## Scope Add a small API utility that returns whether a string contains the requested Unicode separator or spacing character. ## Bounty /bounty $50 Parent bounty program: #33

### 15. xevrion-v2/agent-playground#5005 — Add is-word-joiner-present API utility

- Verdict: `PROMOTE_RECON`
- Score: `78`
- Money: `$50`
- URL: https://github.com/xevrion-v2/agent-playground/issues/5005
- Reasons: money≈$50, local/test/benchmark surface, patchable wording, stack fit
- Snippet: Parent: #33 /bounty $50 ## Scope Add a focused TaskFlow API utility for detecting the Unicode word joiner character (U+2060) in a string. ## Acceptance Criteria - Add $helperPath exporting $fn(input: string): boolean. - Return rue only when the input contains the word joiner character. - Keep the helper dependency-free and safe for reuse in API validation paths. - Include local TypeScript proof for positive, negative, and empty-string cases.

### 16. xevrion-v2/agent-playground#5013 — Add is-invisible-times-present API utility

- Verdict: `PROMOTE_RECON`
- Score: `78`
- Money: `$50`
- URL: https://github.com/xevrion-v2/agent-playground/issues/5013
- Reasons: money≈$50, local/test/benchmark surface, patchable wording, stack fit
- Snippet: Parent: #33 /bounty $50 ## Scope Add a focused TaskFlow API utility for detecting the Unicode invisible times character (U+2062) in a string. ## Acceptance Criteria - Add $path exporting $(System.Collections.Hashtable.fn)(input: string): boolean. - Return rue only when the input contains the invisible times character. - Keep the helper dependency-free and safe for reuse in API validation paths. - Include local TypeScript proof for positive, negative, and empty-string cases.

### 17. xevrion-v2/agent-playground#5014 — Add is-invisible-separator-present API utility

- Verdict: `PROMOTE_RECON`
- Score: `78`
- Money: `$50`
- URL: https://github.com/xevrion-v2/agent-playground/issues/5014
- Reasons: money≈$50, local/test/benchmark surface, patchable wording, stack fit
- Snippet: Parent: #33 /bounty $50 ## Scope Add a focused TaskFlow API utility for detecting the Unicode invisible separator character (U+2063) in a string. ## Acceptance Criteria - Add $path exporting $(System.Collections.Hashtable.fn)(input: string): boolean. - Return rue only when the input contains the invisible separator character. - Keep the helper dependency-free and safe for reuse in API validation paths. - Include local TypeScript proof for positive, negative, and empty-string cases.

### 18. xevrion-v2/agent-playground#5015 — Add is-invisible-plus-present API utility

- Verdict: `PROMOTE_RECON`
- Score: `78`
- Money: `$50`
- URL: https://github.com/xevrion-v2/agent-playground/issues/5015
- Reasons: money≈$50, local/test/benchmark surface, patchable wording, stack fit
- Snippet: Parent: #33 /bounty $50 ## Scope Add a focused TaskFlow API utility for detecting the Unicode invisible plus character (U+2064) in a string. ## Acceptance Criteria - Add $path exporting $(System.Collections.Hashtable.fn)(input: string): boolean. - Return rue only when the input contains the invisible plus character. - Keep the helper dependency-free and safe for reuse in API validation paths. - Include local TypeScript proof for positive, negative, and empty-string cases.

### 19. xevrion-v2/agent-playground#5016 — Add is-left-to-right-embedding-present API utility

- Verdict: `PROMOTE_RECON`
- Score: `78`
- Money: `$50`
- URL: https://github.com/xevrion-v2/agent-playground/issues/5016
- Reasons: money≈$50, local/test/benchmark surface, patchable wording, stack fit
- Snippet: Parent: #33 /bounty $50 ## Scope Add a focused TaskFlow API utility for detecting the Unicode left-to-right embedding character (U+202A) in a string. ## Acceptance Criteria - Add $path exporting $(System.Collections.Hashtable.fn)(input: string): boolean. - Return rue only when the input contains the left-to-right embedding character. - Keep the helper dependency-free and safe for reuse in API validation paths. - Include local TypeScript proof for positive, negative, and empty-string cases.

### 20. xevrion-v2/agent-playground#5844 — Add is-cjk-radical-lame-four-present API utility

- Verdict: `PROMOTE_RECON`
- Score: `78`
- Money: `$50`
- URL: https://github.com/xevrion-v2/agent-playground/issues/5844
- Reasons: money≈$50, local/test/benchmark surface, patchable wording, stack fit
- Snippet: Parent: #33 /bounty $50 ## Task Add a small API utility named $fn() that detects whether a string contains the Unicode cjk radical lame four character (U+2E91). ## Acceptance Criteria - Add ^Gpps/api/src/utils/is-cjk-radical-lame-four-present.ts. - Export $fn(input: string): boolean. - Return rue only when the input contains the cjk radical lame four character. - Keep the helper dependency-free and covered by the batch TypeScript smoke tests.

### 21. SatoshiPortal/bdk-flutter#1 — Bounty for reproducible cross-compilation of rust libraries for Android, Linux, Ios and Macos targets - 0.03 BTC ($2000)

- Verdict: `PROMOTE_RECON`
- Score: `77`
- Money: `$2000`
- URL: https://github.com/SatoshiPortal/bdk-flutter/issues/1
- Reasons: money≈$2000, local/test/benchmark surface, patchable wording, stack fit, assigned, claim/assigned language
- Assignees: i5hi
- Snippet: This bounty is for bdk-flutter but will also be used for lwk-dart and boltz-dart All builds are currently functional but not reproducible/verifiable. **Requirements:** Android & Linux: A build environment using bash scripts, makefile and Docker, that builds on Linux & Mac hosts iOS & MacOS: A build environment using bash scripts and makefile, that builds on Mac hosts Reproducibility: A bash (and python?) script that can verify github releases against local builds. The library developers will be publishing binaries as github releases. We require a validation script that compares the libary's github release and compare them against local builds. Reference: https://github.com/signalapp/Signal-A

### 22. tscircuit/tscircuit#328 — Build the Arduino Nano with tscircuit

- Verdict: `PROMOTE_RECON`
- Score: `77`
- Money: `$1000`
- URL: https://github.com/tscircuit/tscircuit/issues/328
- Reasons: money≈$1000, local/test/benchmark surface, patchable wording, stack fit, assigned
- Assignees: seveibar
- Snippet: Create the Arduino Nano on tscircuit snippets. https://store-usa.arduino.cc/products/arduino-nano?queryID=undefined&selectedStore=us /bounty $100 To get the bounty, you just need to edit the README and add a link to your Arduino Nano. We will actually order your board and test it! Please share your work on discord and we will help you with design issues. tscircuit is still in active development, and this is a fairly difficult board, you may need the team to help build features as you go, stay active on the discord- we're here to help!

### 23. xevrion-v2/agent-playground#17 — Calculate the exact value of PI

- Verdict: `PROMOTE_RECON`
- Score: `77`
- Money: `$1000`
- URL: https://github.com/xevrion-v2/agent-playground/issues/17
- Reasons: money≈$1000, local/test/benchmark surface, patchable wording, stack fit, claim/assigned language
- Snippet: Currently we are able to calculate the exact value of pie up to 100 decimal places: 3.1415926535897932384626433832795028841971693993751058209749445923078164062862089986280348253421170679 This is a huge problem, we must calculate the exact value of pie up to the very last decimal point. Please help us achieve this goal by commenting on this discussion. Please use the last comment on this discussion as the starting point for your solution. Using Google and AI for such calculations is highly encouraged. Please star this repository to help us reach more people. /bounty $1000 Note: bounty can only be paid upon successful PR merges only.

### 24. UnsafeLabs/Bounty-Hunters#763 — [ FastAPI ] Implement dynamic CORS origin validation with callback support

- Verdict: `PROMOTE_RECON`
- Score: `74`
- Money: `$300`
- URL: https://github.com/UnsafeLabs/Bounty-Hunters/issues/763
- Reasons: money≈$300, local/test/benchmark surface, patchable wording, stack fit, available language, claim/assigned language
- Snippet: The CORS middleware at `fastapi/fastapi/middleware/cors.py` re-exports from Starlette but does not provide a way to dynamically configure allowed origins based on the incoming request. ### Implementation - Create a new `DynamicCORSMiddleware` class in `fastapi/fastapi/middleware/cors.py` that accepts an `allow_origin_func` callback - The callback receives the origin string and returns True/False to dynamically allow or deny - Support both sync and async callbacks - Add a `cors_max_age` parameter for configuring the Access-Control-Max-Age header value - Keep the existing CORSMiddleware export unchanged ### Acceptance Criteria - DynamicCORSMiddleware calls the provided function to check each o

### 25. LennyMalcolm0/bitcoin#28 — Write unit tests for core functionalities. ($400)

- Verdict: `PROMOTE_RECON`
- Score: `73`
- Money: `$400`
- URL: https://github.com/LennyMalcolm0/bitcoin/issues/28
- Reasons: money≈$400, local/test/benchmark surface, patchable wording
- Snippet: Accept task [here](https://devasign.com/developer/8a313a64-afac-47d7-8e2c-7a070fc147a0). **Description:** Develop automated tests to verify the correctness and robustness of the implemented core functionalities. **Timeline:** 3 weeks **Bounty:** 400 USD

## Maybe candidates

1. `39` $50 — vansh-09/BountyScout#199 — 🎯 Bounty Alert: 7 New Opportunityies found — https://github.com/vansh-09/BountyScout/issues/199
2. `37` $400 — UnsafeLabs/Bounty-Hunters#798 — [ FastAPI ] Add SSE disconnect detection, event filtering, and reconnect replay — https://github.com/UnsafeLabs/Bounty-Hunters/issues/798

## Counts

- PROMOTE_RECON: 36
- PARK_ASSIGNED: 7
- MAYBE: 2
- REJECT_RISK: 72
- PARK: 3

