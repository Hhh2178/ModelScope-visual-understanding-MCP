# ModelScope Vision MCP v0.1.0 Changelog

## Unreleased

- Created independent MCP project folder.
- Added PRD and spec.
- Added detailed visual recognition prompt.
- Added model quota configuration example.
- Added implementation plan.
- Added relative path portability requirement.
- Added Python MCP package scaffold.
- Added relative config, prompt, and state path handling.
- Added daily model usage state and quota-aware model selector.
- Added detailed vision output normalization and DeepSeek context generation.
- Added ModelScope client using OpenAI-compatible chat completions.
- Added FastMCP server entrypoint with `analyze_image`.
- Added local path portability checker.
- Added unit tests for config, state, selector, output, image input preparation, and portability scanning.
- Added configured model list: `Qwen/Qwen3-VL-8B-Instruct`, `Qwen/Qwen3.5-35B-A3B`, `Qwen/Qwen3.5-27B`, `Qwen/Qwen3.5-397B-A17B`, `Qwen/Qwen3.5-122B-A10B`, and `moonshotai/Kimi-K2.5`.
- Set each configured model to 50 daily calls.
- Added smoke test module that reads `MODELSCOPE_TOKEN` from the environment and redacts token-like strings from output.
- Added streaming response support for ModelScope chat completions.
- Verified real image URL smoke tests against `Qwen/Qwen3-VL-8B-Instruct` and `Qwen/Qwen3.5-35B-A3B`.
- Added Hermes installation notes and a narrow MCP result dedupe patch for runtimes that duplicate `result` into `structuredContent.result`.
