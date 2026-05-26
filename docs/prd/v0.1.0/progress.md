# ModelScope Vision MCP v0.1.0 Progress

## Status

Local implementation is complete for the first MCP skeleton. Runtime Hermes integration has not started.

## Completed

- Created independent project folder.
- Added README.
- Added PRD.
- Added spec.
- Added detailed built-in visual recognition prompt.
- Added model configuration example.
- Added implementation plan.
- Added relative path policy.
- Added Python package scaffold.
- Added relative configuration loader.
- Added daily quota state.
- Added quota-aware model selector.
- Added prompt loader.
- Added detailed output normalization and DeepSeek context builder.
- Added ModelScope OpenAI-compatible client.
- Added FastMCP server entrypoint.
- Added path portability checker.
- Added unit tests.
- Added requested ModelScope model list with 50 daily calls per model.
- Added smoke test entrypoint that reads `MODELSCOPE_TOKEN` from the environment.
- Added streaming response aggregation for ModelScope models that require `stream=True`.

## Pending

- Prepare Hermes runtime integration instructions.
- Run a real ModelScope API smoke test with a configured token and model.

## Runtime Integration

Not started. Do not modify the running Hermes instance until local validation is complete and integration is confirmed.

## Latest Local Validation

- `python -m pytest -q`: 19 passed
- `PYTHONPATH=src python -m modelscope_vision_mcp.portability_check`: pass
- Server import check with `PYTHONPATH=src`: pass

## 2026-05-26 Update

- `python -m pytest -q`: 20 passed
- `PYTHONPATH=src python -m modelscope_vision_mcp.portability_check`: pass
- Real API smoke test with `Qwen/Qwen3-VL-8B-Instruct` and an image URL: pass.
- Real API smoke test with `Qwen/Qwen3.5-35B-A3B`, `stream=True`, and an image URL: pass.
- Data URL smoke test falls back successfully when non-stream-compatible or image-input-incompatible models return empty choices.
