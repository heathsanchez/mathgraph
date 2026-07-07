# Gold Recon Report

## Verdict

`PROMOTE_SMALL_PAID_RECON`

## Decision

```json
{
  "repo": "tailcallhq/tailcall",
  "num": 3551,
  "url": "https://github.com/tailcallhq/tailcall/issues/3551",
  "title": "Re: Bounty #272 \u2014 Reimplement analyze.sh in JS (graphql-benchmarks archived)",
  "state": "OPEN",
  "updatedAt": "2026-06-23T21:51:17Z",
  "reason": "$50 analyze.sh JS rewrite / benchmark tooling, maybe judgeable",
  "amount_estimate": 50.0,
  "money": true,
  "local_judge": true,
  "benchmark_or_metric": true,
  "has_surface": true,
  "prompt_risk": false,
  "hardware_risk": false,
  "web3_risk": false,
  "verdict": "PROMOTE_SMALL_PAID_RECON"
}
```

## Issue body excerpt

## Context

Issue [#272 on graphql-benchmarks](https://github.com/tailcallhq/graphql-benchmarks/issues/272) has a 💎 **$50 bounty** for reimplementing `analyze.sh` in JS. However, the [graphql-benchmarks repo was archived](https://github.com/tailcallhq/graphql-benchmarks), making it impossible to submit a PR or comment on the issue.

The previous PR (#352) by @daveads has been in **draft since July 2024** and was never completed.

## My Solution

I have a complete, tested JS reimplementation ready in my fork:
👉 **https://github.com/shehanrao12-cpu/graphql-benchmarks/tree/chore/reimplement-analyze-sh-in-js**

### Files:
- **`analyze.js`** — Full JS port of all analyze.sh logic
- **`package.json`** — With `canvas` dependency (replaces gnuplot)
- **`run_analyze_script.sh`** — Updated to use `node analyze.js`
- **`.github/workflows/bench.yml`** — Added Node.js setup step

### Test Results:
13 test cases, all passing ✅

### Improvements over shell:
- Removes `gnuplot` and `perl` system dependencies
- Cross-platform compatible
- Testable with unit tests
- Produces identical output

## Request

Could you either:
1. **Unarchive** the graphql-benchmarks repo so I can submit a proper PR, or
2. **Accept the bounty submission** via my fork

Thank you! 🙏

## Cheap commands

```text
pwd=/Users/heath/Documents/mathgraph-lean-work/external/money_gold_recon_v6/tailcallhq__tailcall_3551

workflows:
.github/workflows/benchmark_comment.yml
.github/workflows/benchmark_main.yml
.github/workflows/benchmark_pr_run.yml
.github/workflows/benchmark_pr_track.yml
.github/workflows/benchmark.yml
.github/workflows/build_matrix.yml
.github/workflows/build-website.yml
.github/workflows/ci.yml
.github/workflows/labels.yml
.github/workflows/lint.yml
.github/workflows/nginx-benchmark.yml
.github/workflows/pr-convention.yml
.github/workflows/release-drafter.yml
.github/workflows/release.yml
.github/workflows/spell-check.yml
.github/workflows/stale.yml

```

## Inventory excerpt

```text
.clippy.toml
.codespellignore
.cspell.json
.devcontainer/devcontainer.json
.dockerignore
.git/config
.git/description
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
.git/objects/pack/pack-8df25921d90be464cb4a579a7ea5c8315da4e998.idx
.git/objects/pack/pack-8df25921d90be464cb4a579a7ea5c8315da4e998.pack
.git/objects/pack/pack-8df25921d90be464cb4a579a7ea5c8315da4e998.promisor
.git/objects/pack/pack-f0bbc3e8ae89ee0d69b32577f87c33833c4b6b6e.idx
.git/objects/pack/pack-f0bbc3e8ae89ee0d69b32577f87c33833c4b6b6e.pack
.git/objects/pack/pack-f0bbc3e8ae89ee0d69b32577f87c33833c4b6b6e.promisor
.git/packed-refs
.git/refs/heads/main
.git/shallow
.gitattributes
.github/ISSUE_TEMPLATE/bug_report.md
.github/ISSUE_TEMPLATE/feature_request.md
.github/ISSUE_TEMPLATE/guide.md
.github/ISSUE_TEMPLATE/specification.md
.github/labels.json
.github/pull_request_template.md
.github/release-drafter.yml
.github/scripts/check_if_build.sh
.github/workflows/benchmark_comment.yml
.github/workflows/benchmark_main.yml
.github/workflows/benchmark_pr_run.yml
.github/workflows/benchmark_pr_track.yml
.github/workflows/benchmark.yml
.github/workflows/build_matrix.yml
.github/workflows/build-website.yml
.github/workflows/ci.yml
.github/workflows/labels.yml
.github/workflows/lint.yml
.github/workflows/nginx-benchmark.yml
.github/workflows/pr-convention.yml
.github/workflows/release-drafter.yml
.github/workflows/release.yml
.github/workflows/spell-check.yml
.github/workflows/stale.yml
.gitignore
.graphqlrc.yml
.nightly/rust-toolchain.toml
.prettierignore
.prettierrc
.rustfmt.toml
assets/architecture.excalidraw
assets/canvas.excalidraw
assets/logo_light.svg
assets/logo_main.svg
assets/star-our-repo.gif
benches/bench_synth.rs
benches/data_loader_bench.rs
benches/from_json_bench.rs
benches/grpc/dummy.proto
benches/handle_request_bench.rs
benches/http_execute_bench.rs
benches/impl_path_string_for_evaluation_context.rs
benches/json_like_bench.rs
benches/protobuf_convert_output.rs
benches/request_template_bench.rs
benches/tailcall_benches.rs
Cargo.lock
Cargo.toml
ci-benchmark/benchmark.graphql
ci-benchmark/nginx-benchmark.graphql
ci-benchmark/nginx.conf
ci-benchmark/sample-wrk-output.txt
ci-benchmark/wrk-output-to-md.js
ci-benchmark/wrk.lua
CODE_OF_CONDUCT.md
codecov.yml
CONTRIBUTING.md
docker.sh
Dockerfile
examples/.htpasswd
examples/.jwks
examples/apollo_federation_subgraph_post.graphql
examples/apollo_federation_subgraph_user.graphql
examples/apollo-tracing.graphql
examples/auth.graphql
examples/call.graphql
examples/cors.graphql
examples/empty-to-jsonplaceholder.graphql
examples/example.crt
examples/example.key
examples/federation/gateway.js
examples/federation/package-lock.json
examples/federation/package.json
examples/federation/README.md
examples/federation/rover.sh
examples/generate.yml
examples/graphql-composition.graphql
examples/grpc-reflection.graphql
examples/grpc.graphql
examples/jsonplaceholder_batch.graphql
examples/jsonplaceholder_http_2.graphql
examples/jsonplaceholder_script.graphql
examples/jsonplaceholder-generated.graphql
examples/jsonplaceholder.graphql
examples/jsonplaceholder.yaml
examples/lint.sh
examples/operations/routes.graphql
examples/rest-api.graphql
examples/scripts/echo.js
examples/scripts/test.js
examples/telemetry-otlp.graphql
examples/telemetry-prometheus.graphql
examples/telemetry-stdout.graphql
fly.toml
generated/.tailcallrc.graphql
generated/.tailcallrc.schema.json
install.sh
LICENSE
lint.sh
npm/gen-root.ts
npm/gen.ts
npm/package-lock.json
npm/package.json
npm/post-install.js
npm/pre-install.js
project-words.txt
README.md
renovate.json
rust-toolchain.toml
scripts/criterion_compare.rs
scripts/json_to_md.rs
src/allocator.rs
src/cli/command.rs
src/cli/fmt.rs
src/cli/generator/config.rs
src/cli/generator/generator.rs
src/cli/generator/mod.rs
src/cli/generator/source.rs
src/cli/javascript/codec.rs
src/cli/javascript/mod.rs
src/cli/javascript/runtime.rs
src/cli/llm/error.rs
src/cli/llm/infer_type_name.rs
src/cli/llm/mod.rs
src/cli/llm/wizard.rs
src/cli/metrics.rs
src/cli/mod.rs
src/cli/runtime/env.rs
src/cli/runtime/file.rs
src/cli/runtime/http.rs
src/cli/runtime/mod.rs
src/cli/server/http_1.rs
src/cli/server/http_2.rs
src/cli/server/http_server.rs
src/cli/server/mod.rs
src/cli/server/playground.rs
src/cli/server/server_config.rs
src/cli/tc/check.rs
src/cli/tc/gen.rs
src/cli/tc/helpers.rs
src/cli/tc/init.rs
src/cli/tc/mod.rs
src/cli/tc/run.rs
src/cli/tc/start.rs
src/cli/tc/validate_rc.rs
src/cli/telemetry.rs
src/cli/update_checker.rs
src/core/app_context.rs
src/core/async_graphql_hyper.rs
src/core/auth/basic.rs
src/cor
```

## Grep excerpt

```text
===== money / judge / benchmark / test hits =====
./generated/.tailcallrc.schema.json:392:      "description": "Output the telemetry metrics data to prometheus server",
./generated/.tailcallrc.schema.json:399:          "default": "/metrics",
./generated/.tailcallrc.schema.json:820:          "description": "A boolean value that determines whether to verify certificates. Setting this as `false` will make tailcall accept self-signed certificates. NOTE: use this *only* during development or testing. It is highly recommended to keep this enabled (`true`) in production.",
./Cargo.toml:53:    "metrics",
./Cargo.toml:57:opentelemetry-system-metrics = { version = "0.2.0", optional = true }
./Cargo.toml:128:opentelemetry = { version = "0.23.0", features = ["trace", "logs", "metrics"] }
./Cargo.toml:132:    "metrics",
./Cargo.toml:138:    "metrics",
./Cargo.toml:185:datatest-stable = "0.2.9"
./Cargo.toml:186:tokio-test = "0.4.4"
./Cargo.toml:205:test-log = { version = "0.2.16", default-features = false, features = [
./Cargo.toml:232:    "opentelemetry_sdk/testing",
./Cargo.toml:235:    "dep:opentelemetry-system-metrics",
./Cargo.toml:244:# This is used by default locally while developing and on CI.
./Cargo.toml:245:# We generally want to interface via CLI and have V8 enabled, while running tests.
./Cargo.toml:248:# Feature flag to force JIT engine inside integration tests
./Cargo.toml:283:[profile.benchmark]
./Cargo.toml:296:[[test]]
./Cargo.toml:300:[[test]]
./Cargo.toml:302:path = "tests/cli/gen.rs"
./Cargo.toml:305:[[test]]
./Cargo.toml:307:path = "src/core/generator/tests/json_to_config_spec.rs"
./tailcall-wasm/Cargo.toml:30:wasm-bindgen-test = "0.3.42"
./tailcall-wasm/Cargo.toml:33:unexpected_cfgs = { level = "warn", check-cfg = ['cfg(wasm_bindgen_unstable_test_coverage)'] }
./tailcall-wasm/README.md:25:For test build:
./tailcall-wasm/README.md:47:For test build:
./tailcall-wasm/src/builder.rs:72:#[cfg(test)]
./tailcall-wasm/src/builder.rs:73:mod tests {
./tailcall-wasm/src/builder.rs:83:    use wasm_bindgen_test::wasm_bindgen_test;
./tailcall-wasm/src/builder.rs:110:    #[wasm_bindgen_test]
./tailcall-wasm/src/builder.rs:111:    async fn test() {
./LICENSE:167:      and charge a fee for, acceptance of support, warranty, indemnity,
./Dockerfile:1:FROM ubuntu:latest
./tailcall-aws-lambda/Cargo.toml:14:# add the latest version of a dependency to the list,
./tailcall-aws-lambda/src/http.rs:97:#[cfg(test)]
./tailcall-aws-lambda/src/http.rs:98:mod tests {
./tailcall-aws-lambda/src/http.rs:105:    #[tokio::test]
./tailcall-aws-lambda/src/http.rs:106:    async fn test_to_request() {
./tailcall-aws-lambda/src/http.rs:127:    #[tokio::test]
./tailcall-aws-lambda/src/http.rs:128:    async fn test_to_response() {
./install.sh:6:VERSION=${1:-"latest"}
./install.sh:10:if [ "$VERSION" = "latest" ]; then
./install.sh:11:  VERSION=$(curl --silent "https://api.github.com/repos/tailcallhq/tailcall/releases/latest" | jq -r '.tag_name')
./tests/core/spec.rs:92:    // TODO: we should probably figure out a way to do this for every test
./tests/core/spec.rs:96:    // enabled for either new tests that request it or old graphql_spec
./tests/core/spec.rs:97:    // tests that were explicitly written with it in mind
./tests/core/spec.rs:137:async fn run_query_tests_on_spec(
./tests/core/spec.rs:142:    if let Some(tests) = spec.test.as_ref() {
./tests/core/spec.rs:151:        // test: Run test specs
./tests/core/spec.rs:153:        for (i, test) in tests.iter().enumerate() {
./tests/core/spec.rs:154:            let response = run_test(app_ctx.clone(), test)
./tests/core/spec.rs:181:        mock_http_client.test_hits(&spec.path);
./tests/core/spec.rs:185:async fn test_spec(spec: ExecutionSpec) {
./tests/core/spec.rs:248:    // run query tests
./tests/core/spec.rs:249:    run_query_tests_on_spec(spec, &config_module, mock_http_client).await;
./tests/core/spec.rs:252:pub async fn load_and_test_execution_spec(path: &Path) -> anyhow::Result<()> {
./tests/core/spec.rs:262:        None => test_spec(spec).await,
./tests/core/spec.rs:268:async fn run_test(
./tests/core/runtime.rs:31:    pub test: Option<Vec<APIRequest>>,
./tests/core/runtime.rs:48:    pub fn test_hits(&self, path: impl AsRef<Path>) {
./tests/core/snapshots/graphql-conformance-nested-lists.md_client.snap:2:source: tests/core/spec.rs
./tests/core/snapshots/grpc-batch.md_0.snap:2:source: tests/core/spec.rs
./tests/core/snapshots/auth-jwt.md_2.snap:2:source: tests/core/spec.rs
./tests/core/snapshots/test-description-many.md_merged.snap:2:source: tests/core/spec.rs
./tests/core/snapshots/test-description-many.md_merged.snap:12:  This is test2
./tests/core/snapshots/test-description-many.md_merged.snap:19:  This is test
./tests/core/snapshots/test-server-vars.md_merged.snap:2:source: tests/core/spec.rs
./tests/core/snapshots/graphql-conformance-http-015.md_5.snap:2:source: tests/core/spec.rs
./tests/core/snapshots/env-value.md_client.snap:2:source: tests/core/spec.rs
./tests/core/snapshots/test-required-fields.md_client.snap:2:source: tests/core/spec.rs
./tests/core/snapshots/test-scalars-builtin.md_client.snap:2:source: tests/core/spec.rs
./tests/core/snapshots/test-scalars-integers.md_10.snap:2:source: tests/core/spec.rs
./tests/core/snapshots/graphql-conformance-001.md_1.snap:2:source: tests/core/spec.rs
./tests/core/snapshots/call-mutation.md_2.snap:2:source: tests/core/spec.rs
./tests/core/snapshots/test-expr-scalar-as-string.md_merged.snap:2:source: tests/core/spec.rs
./tests/core/snapshots/test-expr-scalar-as-string.md_merged.snap:37:  entry: Entry @expr(body: {num: "0", arr: "[1, 2, 3]", str: "test", obj: "{e: 1}", bool: "true"})
./tests/core/snapshots/test-http-baseurl.md_client.snap:2:source: tests/core/spec.rs
./tests/core/snapshots/test-alias-on-enum.md_merged.snap:2:source: tests/core/spec.rs
./tests/core/snapshots/recursive-types.md_0.snap:2:source: tests/core/spec.rs
./tests/core/snapshots/union-nested-resolver.md_client.snap:2:source: tests/core/spec.rs
./tests/core/snapshots/graphql-conformance-http-005.md_0.snap:2:source: tests/core/spec.rs
./tests/core/snapshots/async-cache-global.md_merged.snap:2:source: tests/core/spec.rs
./tests/core/snapshots/graphql-conformance-http-005.md_client.snap:2:source: tests/core/spec.rs
./tests/core/snapshots/graphql-conformance-http-010.md_client.snap:2:source: tests/core/spec.rs
./tests/core/snapshots/test-scalars-builtin.md_9.snap:2:source: tests/core/spec.rs
./tests/core/snapshots/test-required-fields.md_4.snap:2:source: tests/core/spec.rs
./tests/core/snapshots/test-multiple-resolvable-directives-on-field-validation.md_error.snap:2:source: tests/core/spec.rs
./tests/core/snapshots/graphql-datasource-with-args.md_merged.snap:2:source: tests/core/spec.rs
./tests/core/snapshots/test-scalars.md_9.snap:2:source: tests/core/spec.rs
./tests/core/snapshots/graphql-conformance-015.md_1.snap:2:source: tests/core/spec.rs
./tests/core/snapshots/test-dedupe.md_merged.snap:2:source: tests/core/spec.rs
./tests/core/snapshots/batching-group-by.md_0.snap:2:source: tests/core/spec.rs
./tests/core/snapshots/graphql-conformance-http-006.md_2.snap:2:source: tests/core/spec.rs
./tests/core/snapshots/async-cache-inflight-request.md_0.snap:2:source: tests/core/spec.rs
./tests/core/snapshots/test-dedupe.md_0.snap:2:source: tests/core/spec.rs
./tests/core/snapshots/default-value-arg.md_0.snap:2:source: tests/core/spec.rs
./tests/core/snapshots/auth_order.md_0.snap:2:source: tests/core/spec.rs
./tests/core/snapshots/graphql-datasource-errors.md_merged.snap:2:source: tests/core/spec.rs
./tests/core/snapshots/graphql-conformance-http-001.md_5.snap:2:source: tests/core/spec.rs
./tests/core/snapshots/test-required-fields.md_13.snap:2:source: tests/core/spec.rs
./tests/core/snapshots/graphql-conformance-019.md_merged.snap:2:source: tests/core/spec.rs
./tests/core/snapshots/grpc-map.md_client.snap:2:source: tests/core/spec.rs
./tests/core/snapshots/batching-disabled.md_0.snap:2:source: tests/core/spec.rs
./
```
